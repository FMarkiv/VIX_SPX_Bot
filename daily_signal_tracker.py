#!/usr/bin/env python3
"""
Daily Signal Execution Tracker
==============================
Monitors SPX/VIX/VIX3M indicators and sends trading signals via Telegram.

Strategy Logic:
- BUY SIGNAL when VIX/VIX3M ratio (5d SMA) > 1.0 AND SPX is below its 200d MA
- This indicates elevated short-term fear relative to medium-term expectations
  combined with a market trading below its long-term trend.

Regime Analysis:
- Calculates forward returns dynamically from full historical data (~2006+)
- Divides VIX/VIX3M ratio into 10 deciles with actual historical performance metrics
"""

import os
from datetime import datetime

import numpy as np
import requests
import yfinance as yf
import pandas as pd


def fetch_market_data_full() -> pd.DataFrame:
    """
    Download full historical data for SPX, VIX, and VIX3M.

    Returns:
        DataFrame with aligned close prices for all three instruments
    """
    tickers = ["^GSPC", "^VIX", "^VIX3M"]

    # Fetch full history (VIX3M starts around 2007)
    data = yf.download(
        tickers,
        period="max",
        interval="1d",
        progress=False,
        auto_adjust=True
    )

    # Extract close prices and rename columns
    closes = data["Close"].copy()
    closes.columns = ["SPX", "VIX", "VIX3M"]

    # Drop any rows with missing data
    closes = closes.dropna()

    return closes


def calculate_forward_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate forward returns and risk metrics for SPX.

    Args:
        df: DataFrame with SPX, VIX, VIX3M columns

    Returns:
        DataFrame with forward return columns added
    """
    data = df.copy()

    # Calculate VIX/VIX3M ratio
    data["VIX_VIX3M_Ratio"] = data["VIX"] / data["VIX3M"]

    # Forward returns (negative shift = look forward)
    data["Fwd_21d"] = data["SPX"].pct_change(periods=21).shift(-21) * 100
    data["Fwd_63d"] = data["SPX"].pct_change(periods=63).shift(-63) * 100
    data["Fwd_252d"] = data["SPX"].pct_change(periods=252).shift(-252) * 100
    data["Fwd_504d"] = data["SPX"].pct_change(periods=504).shift(-504) * 100

    # 252-day forward max drawdown
    # For each day, look at the next 252 days and find the max drawdown
    max_dd_list = []
    win_rate_list = []

    spx_values = data["SPX"].values

    for i in range(len(data)):
        if i + 252 < len(data):
            future_prices = spx_values[i:i + 253]  # Include starting day
            start_price = future_prices[0]
            # Calculate rolling max and drawdowns
            rolling_max = np.maximum.accumulate(future_prices)
            drawdowns = (future_prices - rolling_max) / rolling_max * 100
            max_dd = drawdowns.min()
            max_dd_list.append(max_dd)

            # Win rate: was 252d return positive?
            end_price = spx_values[i + 252]
            win_rate_list.append(1 if end_price > start_price else 0)
        else:
            max_dd_list.append(np.nan)
            win_rate_list.append(np.nan)

    data["Fwd_252d_MaxDD"] = max_dd_list
    data["Fwd_252d_Win"] = win_rate_list

    return data


def create_decile_stats(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create decile buckets for VIX/VIX3M ratio and calculate statistics.

    Args:
        df: DataFrame with forward returns already calculated

    Returns:
        Tuple of (full DataFrame with decile labels, decile statistics DataFrame)
    """
    data = df.copy()

    # Filter to rows where we have complete forward return data
    # Exclude last 504 days where 2Y forward returns are NaN
    analysis_data = data.dropna(subset=["Fwd_21d", "Fwd_63d", "Fwd_252d", "Fwd_504d",
                                        "Fwd_252d_MaxDD", "Fwd_252d_Win"])

    # Create deciles based on VIX/VIX3M ratio (1 = lowest ratio, 10 = highest)
    analysis_data = analysis_data.copy()
    analysis_data["Decile"] = pd.qcut(
        analysis_data["VIX_VIX3M_Ratio"],
        q=10,
        labels=range(1, 11),
        duplicates='drop'
    )

    # Calculate statistics for each decile
    decile_stats = analysis_data.groupby("Decile").agg({
        "VIX_VIX3M_Ratio": ["min", "max", "mean"],
        "Fwd_21d": "mean",
        "Fwd_63d": "mean",
        "Fwd_252d": "mean",
        "Fwd_504d": "mean",
        "Fwd_252d_MaxDD": "mean",
        "Fwd_252d_Win": "mean"
    })

    # Flatten column names
    decile_stats.columns = [
        "Ratio_Min", "Ratio_Max", "Ratio_Mean",
        "Avg_1M_Return", "Avg_3M_Return", "Avg_1Y_Return", "Avg_2Y_Return",
        "Avg_1Y_MaxDD", "Avg_1Y_WinRate"
    ]

    # Convert win rate to percentage
    decile_stats["Avg_1Y_WinRate"] = decile_stats["Avg_1Y_WinRate"] * 100

    return analysis_data, decile_stats


def get_regime_context_dynamic(raw_ratio: float, decile_stats: pd.DataFrame) -> dict:
    """
    Map the current raw VIX/VIX3M ratio to historical regime expectations.

    Uses dynamically calculated decile statistics from full historical data.

    Args:
        raw_ratio: The raw (non-smoothed) VIX/VIX3M ratio
        decile_stats: DataFrame with decile statistics

    Returns:
        Dictionary with regime metrics
    """
    # Find which decile this ratio falls into
    current_decile = None

    for decile in decile_stats.index:
        ratio_min = decile_stats.loc[decile, "Ratio_Min"]
        ratio_max = decile_stats.loc[decile, "Ratio_Max"]

        if ratio_min <= raw_ratio <= ratio_max:
            current_decile = decile
            break

    # Handle edge cases (ratio outside historical range)
    if current_decile is None:
        if raw_ratio < decile_stats["Ratio_Min"].min():
            current_decile = 1  # Below historical minimum
        else:
            current_decile = 10  # Above historical maximum

    # Map decile to regime name
    if current_decile <= 2:
        regime_name = "Deep Contango"
    elif current_decile <= 4:
        regime_name = "Mild Contango"
    elif current_decile <= 7:
        regime_name = "Normal"
    elif current_decile <= 9:
        regime_name = "Transition/Elevated"
    else:
        regime_name = "Backwardation/Panic"

    # Get statistics for this decile
    stats = decile_stats.loc[current_decile]

    return {
        "decile": int(current_decile),
        "regime_name": regime_name,
        "return_1m": stats["Avg_1M_Return"],
        "return_3m": stats["Avg_3M_Return"],
        "return_1y": stats["Avg_1Y_Return"],
        "return_2y": stats["Avg_2Y_Return"],
        "max_dd_1y": stats["Avg_1Y_MaxDD"],
        "win_rate_1y": stats["Avg_1Y_WinRate"]
    }


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all required technical indicators.

    Args:
        df: DataFrame with SPX, VIX, VIX3M columns

    Returns:
        DataFrame with additional indicator columns
    """
    data = df.copy()

    # Core ratio: VIX / VIX3M
    # Values > 1.0 indicate inverted term structure (short-term fear elevated)
    data["VIX_VIX3M_Ratio"] = data["VIX"] / data["VIX3M"]

    # 5-day Simple Moving Average of the ratio (smooths daily noise)
    data["Ratio_5d_SMA"] = data["VIX_VIX3M_Ratio"].rolling(window=5).mean()

    # 200-day Simple Moving Average of SPX (long-term trend)
    data["SPX_SMA_200"] = data["SPX"].rolling(window=200).mean()

    # 200-day Exponential Moving Average of SPX (more responsive to recent price)
    data["SPX_EMA_200"] = data["SPX"].ewm(span=200, adjust=False).mean()

    return data


def evaluate_signals(row: pd.Series) -> dict:
    """
    Evaluate buy signal conditions on the current data.

    Scenario 1: Ratio_5d_SMA > 1.0 AND SPX < SPX_SMA_200
    Scenario 2: Ratio_5d_SMA > 1.0 AND SPX < SPX_EMA_200

    Args:
        row: Series containing current day's values

    Returns:
        Dictionary with signal evaluation results
    """
    ratio_elevated = row["Ratio_5d_SMA"] > 1.0
    spx_below_sma = row["SPX"] < row["SPX_SMA_200"]
    spx_below_ema = row["SPX"] < row["SPX_EMA_200"]

    scenario_1 = ratio_elevated and spx_below_sma
    scenario_2 = ratio_elevated and spx_below_ema

    return {
        "ratio_elevated": ratio_elevated,
        "spx_below_sma": spx_below_sma,
        "spx_below_ema": spx_below_ema,
        "scenario_1": scenario_1,
        "scenario_2": scenario_2,
        "buy_signal": scenario_1 or scenario_2
    }


def calculate_distances(row: pd.Series) -> dict:
    """
    Calculate percentage distance of SPX from its moving averages.

    Args:
        row: Series containing current day's values

    Returns:
        Dictionary with distance percentages
    """
    spx = row["SPX"]
    sma_200 = row["SPX_SMA_200"]
    ema_200 = row["SPX_EMA_200"]

    distance_from_sma = ((spx - sma_200) / sma_200) * 100
    distance_from_ema = ((spx - ema_200) / ema_200) * 100

    return {
        "distance_from_sma_pct": distance_from_sma,
        "distance_from_ema_pct": distance_from_ema
    }


def format_message(row: pd.Series, signals: dict, distances: dict, regime: dict) -> str:
    """
    Format the output message for Telegram.

    Args:
        row: Series containing current day's values
        signals: Dictionary with signal evaluation results
        distances: Dictionary with distance percentages
        regime: Dictionary with historical regime context

    Returns:
        Formatted message string
    """
    # Determine verdict
    if signals["buy_signal"]:
        verdict = "[GO] GO (BUY SIGNAL)"
        verdict_detail = []
        if signals["scenario_1"]:
            verdict_detail.append("Scenario 1: Ratio > 1 & SPX < SMA200")
        if signals["scenario_2"]:
            verdict_detail.append("Scenario 2: Ratio > 1 & SPX < EMA200")
        verdict_info = "\n   ".join(verdict_detail)
    else:
        verdict = "[STOP] NO-GO (WAIT)"
        verdict_info = "Conditions not met"

    # Format distance signs
    sma_sign = "+" if distances["distance_from_sma_pct"] >= 0 else ""
    ema_sign = "+" if distances["distance_from_ema_pct"] >= 0 else ""

    # Format return signs
    r1m_sign = "+" if regime["return_1m"] >= 0 else ""
    r3m_sign = "+" if regime["return_3m"] >= 0 else ""
    r1y_sign = "+" if regime["return_1y"] >= 0 else ""
    r2y_sign = "+" if regime["return_2y"] >= 0 else ""

    # Build message
    message = f"""
===============================
[CHART] DAILY SIGNAL EXECUTION TRACKER
===============================

[DATE] Date: {row.name.strftime('%Y-%m-%d')}

[UP] MARKET LEVELS
   SPX:    {row['SPX']:,.2f}
   VIX:    {row['VIX']:.2f}
   VIX3M:  {row['VIX3M']:.2f}

[CALC] KEY INDICATORS
   VIX/VIX3M Ratio:     {row['VIX_VIX3M_Ratio']:.4f}
   Ratio 5d SMA:        {row['Ratio_5d_SMA']:.4f}
   SPX 200d SMA:        {row['SPX_SMA_200']:,.2f}
   SPX 200d EMA:        {row['SPX_EMA_200']:,.2f}

[RULER] SPX DISTANCE FROM MAs
   From 200d SMA:  {sma_sign}{distances['distance_from_sma_pct']:.2f}%
   From 200d EMA:  {ema_sign}{distances['distance_from_ema_pct']:.2f}%

[TARGET] SIGNAL CONDITIONS
   Ratio 5d SMA > 1.0:  {'[YES] YES' if signals['ratio_elevated'] else '[NO] NO'}
   SPX < 200d SMA:      {'[YES] YES' if signals['spx_below_sma'] else '[NO] NO'}
   SPX < 200d EMA:      {'[YES] YES' if signals['spx_below_ema'] else '[NO] NO'}

[HISTORY] REGIME CONTEXT
   Current Regime: {regime['regime_name']} (Decile: {regime['decile']}/10)
   Returns: 1M: {r1m_sign}{regime['return_1m']:.1f}% | 3M: {r3m_sign}{regime['return_3m']:.1f}% | 1Y: {r1y_sign}{regime['return_1y']:.1f}% | 2Y: {r2y_sign}{regime['return_2y']:.1f}%
   1Y Risk: Max DD: {regime['max_dd_1y']:.1f}% | Win Rate: {regime['win_rate_1y']:.0f}%

===============================
[SIGNAL] VERDICT: {verdict}
   {verdict_info}
===============================
"""
    return message.strip()


def send_telegram_message(message: str, bot_token: str, chat_id: str) -> bool:
    """
    Send a message via Telegram Bot API.

    Args:
        message: Text message to send
        bot_token: Telegram bot token
        chat_id: Target chat ID

    Returns:
        True if successful, False otherwise
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("[YES] Telegram message sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[NO] Failed to send Telegram message: {e}")
        return False


def main():
    """Main execution flow."""
    print("=" * 50)
    print("DAILY SIGNAL EXECUTION TRACKER")
    print("=" * 50)
    print(f"\n[TIME] Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Fetch full historical market data
    print("[DL] Fetching full historical market data...")
    try:
        df_full = fetch_market_data_full()
        print(f"   Retrieved {len(df_full)} trading days of data")
        print(f"   Date range: {df_full.index[0].strftime('%Y-%m-%d')} to {df_full.index[-1].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"[NO] Failed to fetch data: {e}")
        return

    # Step 2: Calculate forward returns on full history
    print("\n[CALC] Calculating forward returns...")
    df_with_returns = calculate_forward_returns(df_full)

    # Step 3: Create decile statistics
    print("[BUCKET] Creating decile buckets and statistics...")
    _, decile_stats = create_decile_stats(df_with_returns)

    print("\n   Decile Statistics Summary:")
    print(f"   {'Decile':<8} {'Ratio Range':<18} {'1Y Avg Return':<15} {'1Y Win Rate':<12}")
    print("   " + "-" * 55)
    for decile in decile_stats.index:
        row = decile_stats.loc[decile]
        print(f"   {decile:<8} {row['Ratio_Min']:.3f} - {row['Ratio_Max']:.3f}      "
              f"{row['Avg_1Y_Return']:>+6.1f}%         {row['Avg_1Y_WinRate']:>5.0f}%")

    # Step 4: Calculate indicators on recent data
    print("\n[CHART] Calculating current indicators...")
    df_indicators = calculate_indicators(df_full)

    # Step 5: Get latest row and evaluate signals
    latest = df_indicators.iloc[-1]
    signals = evaluate_signals(latest)
    distances = calculate_distances(latest)
    regime = get_regime_context_dynamic(latest["VIX_VIX3M_Ratio"], decile_stats)

    print(f"   Latest data point: {latest.name.strftime('%Y-%m-%d')}")
    print(f"   Current ratio: {latest['VIX_VIX3M_Ratio']:.4f} -> Decile {regime['decile']} ({regime['regime_name']})")

    # Step 6: Format message
    message = format_message(latest, signals, distances, regime)

    # Print to console
    print("\n" + message)

    # Step 7: Send via Telegram if credentials are available
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if bot_token and chat_id:
        print("\n[SEND] Sending to Telegram...")
        send_telegram_message(message, bot_token, chat_id)
    else:
        print("\n[!]  Telegram credentials not found in environment variables.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable notifications.")


if __name__ == "__main__":
    main()
