#!/usr/bin/env python3
"""
Exit Strategy Simulation for SPX LEAPS
=======================================
Simulates various exit strategies for trades triggered by the Combined Live Signal.

Matrix 1: Time-Based Exits (Theta Management)
Matrix 2: Regime Reversion Exits (Term Structure Normalization)
Matrix 3: Equity Profit Targets (The 'Free Ride' Exits)
"""

import warnings
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yfinance as yf

warnings.filterwarnings("ignore")

# Configuration
MAX_HOLDING_PERIOD = 504  # ~2 years in trading days


def fetch_full_history() -> pd.DataFrame:
    """Fetch maximum available historical data."""
    print("[*] Fetching full historical data...")

    tickers = ["^GSPC", "^VIX", "^VIX3M"]

    data = yf.download(
        tickers,
        period="max",
        interval="1d",
        progress=False,
        auto_adjust=True
    )

    closes = data["Close"].copy()
    closes.columns = ["SPX", "VIX", "VIX3M"]
    closes = closes.dropna()

    print(f"    Retrieved {len(closes)} trading days")
    print(f"    Date range: {closes.index[0].strftime('%Y-%m-%d')} to {closes.index[-1].strftime('%Y-%m-%d')}")

    return closes


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all required indicators."""
    print("\n[*] Calculating indicators...")

    data = df.copy()

    # Core ratio
    data["VIX_VIX3M_Ratio"] = data["VIX"] / data["VIX3M"]

    # 5-day SMA of ratio (smoother signal)
    data["Ratio_5d_SMA"] = data["VIX_VIX3M_Ratio"].rolling(window=5).mean()

    # Trend filters
    data["SPX_EMA_200"] = data["SPX"].ewm(span=200, adjust=False).mean()
    data["SPX_SMA_43"] = data["SPX"].rolling(window=43).mean()

    return data


def evaluate_combined_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate the Combined Live Signal.

    Signal fires when EITHER:
      Scenario 1: Ratio_5d_SMA > 1.0 AND SPX < SPX_EMA_200
      Scenario 2: Ratio_5d_SMA > 1.0 AND SPX > SPX_SMA_43
    """
    data = df.copy()

    # Base condition (common to both)
    ratio_elevated = data["Ratio_5d_SMA"] > 1.0

    # Scenario 1: Below 200d EMA (bearish trend)
    scenario_1 = ratio_elevated & (data["SPX"] < data["SPX_EMA_200"])

    # Scenario 2: Above 43d SMA (short-term uptrend)
    scenario_2 = ratio_elevated & (data["SPX"] > data["SPX_SMA_43"])

    # Combined signal (OR logic)
    data["Signal"] = scenario_1 | scenario_2

    return data


def identify_first_trigger_dates(df: pd.DataFrame, gap_days: int = 10) -> List[pd.Timestamp]:
    """
    Identify the first trigger date of each distinct signal cluster.
    This avoids overlapping trades from consecutive signal days.
    """
    signal_dates = df[df["Signal"]].index.tolist()

    if not signal_dates:
        return []

    first_triggers = [signal_dates[0]]

    for date in signal_dates[1:]:
        # If gap is larger than threshold, this is a new cluster
        if (date - first_triggers[-1]).days > gap_days:
            first_triggers.append(date)

    return first_triggers


# =============================================================================
# MATRIX 1: TIME-BASED EXITS
# =============================================================================

def simulate_time_based_exits(
    df: pd.DataFrame,
    trigger_dates: List[pd.Timestamp],
    exit_days_list: List[int]
) -> pd.DataFrame:
    """Simulate time-based exits after N trading days."""

    results = []

    for exit_days in exit_days_list:
        returns = []

        for entry_date in trigger_dates:
            entry_idx = df.index.get_loc(entry_date)
            exit_idx = entry_idx + exit_days

            # Skip if we don't have enough forward data
            if exit_idx >= len(df):
                continue

            entry_price = df.iloc[entry_idx]["SPX"]
            exit_price = df.iloc[exit_idx]["SPX"]

            pct_return = (exit_price - entry_price) / entry_price * 100
            returns.append(pct_return)

        if returns:
            avg_return = np.mean(returns)
            median_return = np.median(returns)
            win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100

            results.append({
                "Exit Days": exit_days,
                "Label": f"{exit_days} Days ({exit_days/21:.0f}M)",
                "N Trades": len(returns),
                "Avg Return (%)": avg_return,
                "Median Return (%)": median_return,
                "Win Rate (%)": win_rate
            })

    return pd.DataFrame(results)


# =============================================================================
# MATRIX 2: REGIME REVERSION EXITS
# =============================================================================

def simulate_regime_reversion_exits(
    df: pd.DataFrame,
    trigger_dates: List[pd.Timestamp],
    ratio_thresholds: List[float]
) -> pd.DataFrame:
    """Simulate exits when VIX/VIX3M ratio drops below threshold."""

    results = []

    for threshold in ratio_thresholds:
        returns = []
        days_held_list = []

        for entry_date in trigger_dates:
            entry_idx = df.index.get_loc(entry_date)
            entry_price = df.iloc[entry_idx]["SPX"]

            # Look forward up to MAX_HOLDING_PERIOD days
            exit_idx = None
            for i in range(1, MAX_HOLDING_PERIOD + 1):
                forward_idx = entry_idx + i
                if forward_idx >= len(df):
                    break

                ratio = df.iloc[forward_idx]["VIX_VIX3M_Ratio"]
                if ratio < threshold:
                    exit_idx = forward_idx
                    break

            # If threshold never hit, exit at day 504 (or end of data)
            if exit_idx is None:
                exit_idx = min(entry_idx + MAX_HOLDING_PERIOD, len(df) - 1)
                if exit_idx <= entry_idx:
                    continue

            exit_price = df.iloc[exit_idx]["SPX"]
            days_held = exit_idx - entry_idx

            pct_return = (exit_price - entry_price) / entry_price * 100
            returns.append(pct_return)
            days_held_list.append(days_held)

        if returns:
            avg_return = np.mean(returns)
            win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100
            avg_days = np.mean(days_held_list)

            results.append({
                "Ratio Threshold": f"< {threshold:.2f}",
                "N Trades": len(returns),
                "Avg Return (%)": avg_return,
                "Win Rate (%)": win_rate,
                "Avg Days Held": avg_days
            })

    return pd.DataFrame(results)


# =============================================================================
# MATRIX 3: PROFIT TARGET EXITS
# =============================================================================

def simulate_profit_target_exits(
    df: pd.DataFrame,
    trigger_dates: List[pd.Timestamp],
    profit_targets: List[float]
) -> Tuple[pd.DataFrame, Dict[str, List[int]]]:
    """Simulate exits when SPX hits profit target. Returns summary and raw data."""

    results = []
    days_to_target_data = {}  # For boxplot visualization

    for target_pct in profit_targets:
        days_to_target = []
        hits = 0
        total = 0

        for entry_date in trigger_dates:
            entry_idx = df.index.get_loc(entry_date)
            entry_price = df.iloc[entry_idx]["SPX"]
            target_price = entry_price * (1 + target_pct / 100)

            total += 1
            hit_target = False

            # Look forward up to MAX_HOLDING_PERIOD days
            for i in range(1, MAX_HOLDING_PERIOD + 1):
                forward_idx = entry_idx + i
                if forward_idx >= len(df):
                    break

                price = df.iloc[forward_idx]["SPX"]
                if price >= target_price:
                    hits += 1
                    days_to_target.append(i)
                    hit_target = True
                    break

        if total > 0:
            hit_rate = hits / total * 100
            avg_days = np.mean(days_to_target) if days_to_target else np.nan
            median_days = np.median(days_to_target) if days_to_target else np.nan

            label = f"+{target_pct:.0f}%"
            days_to_target_data[label] = days_to_target

            results.append({
                "Profit Target": label,
                "N Trades": total,
                "Hits": hits,
                "Hit Rate (%)": hit_rate,
                "Avg Days to Target": avg_days,
                "Median Days to Target": median_days
            })

    return pd.DataFrame(results), days_to_target_data


# =============================================================================
# VISUALIZATION
# =============================================================================

def create_velocity_boxplot(days_data: Dict[str, List[int]]) -> None:
    """Create boxplot showing distribution of days to target."""

    # Prepare data for seaborn
    plot_data = []
    for target, days in days_data.items():
        for d in days:
            plot_data.append({"Profit Target": target, "Days to Target": d})

    if not plot_data:
        print("\n[!] No data available for boxplot (no targets hit)")
        return

    plot_df = pd.DataFrame(plot_data)

    # Create figure
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")

    # Create boxplot
    ax = sns.boxplot(
        data=plot_df,
        x="Profit Target",
        y="Days to Target",
        palette="Blues_d",
        width=0.6
    )

    # Add individual points (strip plot)
    sns.stripplot(
        data=plot_df,
        x="Profit Target",
        y="Days to Target",
        color="darkblue",
        alpha=0.3,
        size=4,
        jitter=True
    )

    # Customize
    plt.title("Velocity of Profit Target Achievement\n(Distribution of Days to Hit Target)", fontsize=14, fontweight="bold")
    plt.xlabel("SPX Profit Target", fontsize=12)
    plt.ylabel("Trading Days to Hit Target", fontsize=12)

    # Add reference lines
    ax.axhline(y=126, color="gray", linestyle="--", alpha=0.5, label="6 Months")
    ax.axhline(y=252, color="gray", linestyle="-.", alpha=0.5, label="1 Year")
    ax.axhline(y=378, color="gray", linestyle=":", alpha=0.5, label="1.5 Years")

    plt.legend(loc="upper right")
    plt.tight_layout()

    # Save figure
    plt.savefig("exit_strategy_velocity_boxplot.png", dpi=150, bbox_inches="tight")
    print("\n[+] Boxplot saved to: exit_strategy_velocity_boxplot.png")
    plt.close()


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def print_matrix_1(df: pd.DataFrame) -> None:
    """Print Time-Based Exits matrix."""
    print("\n")
    print("=" * 80)
    print("  MATRIX 1: TIME-BASED EXITS (Theta Management)")
    print("=" * 80)
    print()
    print("  Strategy: Close the trade after exactly N trading days.")
    print("  Purpose:  Manage theta decay by exiting before LEAP acceleration.")
    print()
    print("-" * 80)
    print(f"  {'Exit Days':<20} {'N':>8} {'Avg Return':>14} {'Median Return':>14} {'Win Rate':>12}")
    print(f"  {'-'*20} {'-'*8} {'-'*14} {'-'*14} {'-'*12}")

    for _, row in df.iterrows():
        print(f"  {row['Label']:<20} {row['N Trades']:>8} "
              f"{row['Avg Return (%)']:>13.2f}% {row['Median Return (%)']:>13.2f}% "
              f"{row['Win Rate (%)']:>11.1f}%")

    print()
    print("=" * 80)


def print_matrix_2(df: pd.DataFrame) -> None:
    """Print Regime Reversion Exits matrix."""
    print("\n")
    print("=" * 80)
    print("  MATRIX 2: REGIME REVERSION EXITS (Term Structure Normalization)")
    print("=" * 80)
    print()
    print("  Strategy: Hold until VIX/VIX3M ratio drops below threshold, or exit at day 504.")
    print("  Purpose:  Exit when fear normalizes and term structure returns to contango.")
    print()
    print("-" * 80)
    print(f"  {'Ratio Threshold':<18} {'N':>8} {'Avg Return':>14} {'Win Rate':>12} {'Avg Days Held':>16}")
    print(f"  {'-'*18} {'-'*8} {'-'*14} {'-'*12} {'-'*16}")

    labels = {
        "< 0.90": "Normalizing",
        "< 0.85": "Complacent",
        "< 0.80": "Deep Sleep"
    }

    for _, row in df.iterrows():
        threshold = row["Ratio Threshold"]
        label = labels.get(threshold, "")
        print(f"  {threshold:<18} {row['N Trades']:>8} "
              f"{row['Avg Return (%)']:>13.2f}% {row['Win Rate (%)']:>11.1f}% "
              f"{row['Avg Days Held']:>15.1f}")

    print()
    print("  Regime Labels: < 0.90 (Normalizing), < 0.85 (Complacent), < 0.80 (Deep Sleep)")
    print()
    print("=" * 80)


def print_matrix_3(df: pd.DataFrame) -> None:
    """Print Profit Target Exits matrix."""
    print("\n")
    print("=" * 80)
    print("  MATRIX 3: EQUITY PROFIT TARGETS (The 'Free Ride' Exits)")
    print("=" * 80)
    print()
    print("  Strategy: Hold until SPX hits profit target, within 504 trading days.")
    print("  Purpose:  Lock in LEAP gains (e.g., +20% SPX ~ +100% LEAP).")
    print()
    print("-" * 80)
    print(f"  {'Target':<12} {'N':>8} {'Hits':>8} {'Hit Rate':>12} {'Avg Days':>14} {'Median Days':>14}")
    print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*12} {'-'*14} {'-'*14}")

    for _, row in df.iterrows():
        avg_days_str = f"{row['Avg Days to Target']:.1f}" if not np.isnan(row['Avg Days to Target']) else "N/A"
        median_days_str = f"{row['Median Days to Target']:.1f}" if not np.isnan(row['Median Days to Target']) else "N/A"

        print(f"  {row['Profit Target']:<12} {row['N Trades']:>8} {row['Hits']:>8} "
              f"{row['Hit Rate (%)']:>11.1f}% {avg_days_str:>14} {median_days_str:>14}")

    print()
    print("  Note: +20% SPX move typically = ~100% LEAP gain (2-2.5x leverage)")
    print()
    print("=" * 80)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main execution flow."""
    print("=" * 80)
    print("       EXIT STRATEGY SIMULATION FOR SPX LEAPS")
    print("       Combined Live Signal Trade Lifecycle Analysis")
    print("=" * 80)

    # Fetch data
    df = fetch_full_history()

    # Calculate indicators
    df = calculate_indicators(df)

    # Evaluate combined signal
    df = evaluate_combined_signal(df)

    # Get first trigger dates (one per cluster)
    trigger_dates = identify_first_trigger_dates(df, gap_days=10)
    print(f"\n[*] Identified {len(trigger_dates)} distinct signal triggers (clusters)")

    # Filter to triggers with enough forward data
    valid_triggers = [d for d in trigger_dates if df.index.get_loc(d) + MAX_HOLDING_PERIOD < len(df)]
    print(f"[*] {len(valid_triggers)} triggers have full 504-day forward data")

    # ==========================================================================
    # MATRIX 1: Time-Based Exits
    # ==========================================================================
    print("\n[*] Simulating Matrix 1: Time-Based Exits...")
    exit_days = [126, 252, 378]  # 6M, 1Y, 1.5Y
    matrix_1 = simulate_time_based_exits(df, trigger_dates, exit_days)
    print_matrix_1(matrix_1)

    # ==========================================================================
    # MATRIX 2: Regime Reversion Exits
    # ==========================================================================
    print("\n[*] Simulating Matrix 2: Regime Reversion Exits...")
    ratio_thresholds = [0.90, 0.85, 0.80]
    matrix_2 = simulate_regime_reversion_exits(df, trigger_dates, ratio_thresholds)
    print_matrix_2(matrix_2)

    # ==========================================================================
    # MATRIX 3: Profit Target Exits
    # ==========================================================================
    print("\n[*] Simulating Matrix 3: Profit Target Exits...")
    profit_targets = [10, 20, 30]  # +10%, +20%, +30%
    matrix_3, days_data = simulate_profit_target_exits(df, trigger_dates, profit_targets)
    print_matrix_3(matrix_3)

    # ==========================================================================
    # VISUALIZATION
    # ==========================================================================
    print("\n[*] Generating velocity boxplot...")
    create_velocity_boxplot(days_data)

    print("\n[+] Exit strategy simulation complete.\n")


if __name__ == "__main__":
    main()
