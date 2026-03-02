#!/usr/bin/env python3
"""
Daily Signal Execution Tracker
==============================
Monitors SPX/VIX/VIX3M indicators and sends trading signals via Telegram.

Strategy Logic:
- BUY SIGNAL when VIX/VIX3M ratio (5d SMA) > 1.0 AND SPX is below its 200d MA
- This indicates elevated short-term fear relative to medium-term expectations
  combined with a market trading below its long-term trend.
"""

import os
from datetime import datetime

import requests
import yfinance as yf
import pandas as pd


def fetch_market_data(period_days: int = 250) -> pd.DataFrame:
    """
    Download historical data for SPX, VIX, and VIX3M.

    Args:
        period_days: Number of trading days to fetch (default 250)

    Returns:
        DataFrame with aligned close prices for all three instruments
    """
    tickers = ["^GSPC", "^VIX", "^VIX3M"]

    # Fetch ~18 months to ensure we have 250+ trading days after weekends/holidays
    data = yf.download(
        tickers,
        period="18mo",
        interval="1d",
        progress=False,
        auto_adjust=True
    )

    # Extract close prices and rename columns
    closes = data["Close"].copy()
    closes.columns = ["SPX", "VIX", "VIX3M"]

    # Drop any rows with missing data and take last N days
    closes = closes.dropna().tail(period_days)

    return closes


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


def format_message(row: pd.Series, signals: dict, distances: dict) -> str:
    """
    Format the output message for Telegram.

    Args:
        row: Series containing current day's values
        signals: Dictionary with signal evaluation results
        distances: Dictionary with distance percentages

    Returns:
        Formatted message string
    """
    # Determine verdict
    if signals["buy_signal"]:
        verdict = "🟢 GO (BUY SIGNAL)"
        verdict_detail = []
        if signals["scenario_1"]:
            verdict_detail.append("Scenario 1: Ratio > 1 & SPX < SMA200")
        if signals["scenario_2"]:
            verdict_detail.append("Scenario 2: Ratio > 1 & SPX < EMA200")
        verdict_info = "\n   ".join(verdict_detail)
    else:
        verdict = "🔴 NO-GO (WAIT)"
        verdict_info = "Conditions not met"

    # Format distance signs
    sma_sign = "+" if distances["distance_from_sma_pct"] >= 0 else ""
    ema_sign = "+" if distances["distance_from_ema_pct"] >= 0 else ""

    # Build message
    message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DAILY SIGNAL EXECUTION TRACKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Date: {row.name.strftime('%Y-%m-%d')}

📈 MARKET LEVELS
   SPX:    {row['SPX']:,.2f}
   VIX:    {row['VIX']:.2f}
   VIX3M:  {row['VIX3M']:.2f}

📐 KEY INDICATORS
   VIX/VIX3M Ratio:     {row['VIX_VIX3M_Ratio']:.4f}
   Ratio 5d SMA:        {row['Ratio_5d_SMA']:.4f}
   SPX 200d SMA:        {row['SPX_SMA_200']:,.2f}
   SPX 200d EMA:        {row['SPX_EMA_200']:,.2f}

📏 SPX DISTANCE FROM MAs
   From 200d SMA:  {sma_sign}{distances['distance_from_sma_pct']:.2f}%
   From 200d EMA:  {ema_sign}{distances['distance_from_ema_pct']:.2f}%

🎯 SIGNAL CONDITIONS
   Ratio 5d SMA > 1.0:  {'✅ YES' if signals['ratio_elevated'] else '❌ NO'}
   SPX < 200d SMA:      {'✅ YES' if signals['spx_below_sma'] else '❌ NO'}
   SPX < 200d EMA:      {'✅ YES' if signals['spx_below_ema'] else '❌ NO'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚦 VERDICT: {verdict}
   {verdict_info}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Telegram message sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False


def main():
    """Main execution flow."""
    print("=" * 50)
    print("DAILY SIGNAL EXECUTION TRACKER")
    print("=" * 50)
    print(f"\n⏰ Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Step 1: Fetch market data
    print("📥 Fetching market data...")
    try:
        df = fetch_market_data(period_days=250)
        print(f"   Retrieved {len(df)} trading days of data")
        print(f"   Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return

    # Step 2: Calculate indicators
    print("\n📊 Calculating indicators...")
    df = calculate_indicators(df)

    # Step 3: Get latest row and evaluate signals
    latest = df.iloc[-1]
    signals = evaluate_signals(latest)
    distances = calculate_distances(latest)

    print(f"   Latest data point: {latest.name.strftime('%Y-%m-%d')}")

    # Step 4: Format message
    message = format_message(latest, signals, distances)

    # Print to console
    print("\n" + message)

    # Step 5: Send via Telegram if credentials are available
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if bot_token and chat_id:
        print("\n📤 Sending to Telegram...")
        send_telegram_message(message, bot_token, chat_id)
    else:
        print("\n⚠️  Telegram credentials not found in environment variables.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable notifications.")


if __name__ == "__main__":
    main()
