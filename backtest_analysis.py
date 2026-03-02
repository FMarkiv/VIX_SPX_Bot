"""
SPX-VIX Quantitative Backtesting and Statistical Analysis Model
================================================================
Loads SPX, VIX, and VIX3M data, calculates the VIX/VIX3M ratio,
forward returns, and forward maximum drawdowns for various time horizons.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_and_merge_data(data_dir: str) -> pd.DataFrame:
    """
    Load SPX, VIX, and VIX3M CSVs and merge on Date column.

    Returns a DataFrame with datetime index and forward-filled missing values.
    """
    data_path = Path(data_dir)

    # Load SPX
    spx = pd.read_csv(data_path / "SPX.csv", parse_dates=["Date"])
    spx.columns = ["Date", "SPX_Close"]

    # Load VIX
    vix = pd.read_csv(data_path / "VIX.csv", parse_dates=["Date"])
    vix.columns = ["Date", "VIX_Close"]

    # Load VIX3M (has different column names)
    vix3m = pd.read_csv(data_path / "VIX3M_History.csv", parse_dates=["DATE"])
    vix3m = vix3m[["DATE", "CLOSE"]].copy()
    vix3m.columns = ["Date", "VIX3M_Close"]

    # Merge all datasets on Date
    df = spx.merge(vix, on="Date", how="outer")
    df = df.merge(vix3m, on="Date", how="outer")

    # Sort by date and set as index
    df = df.sort_values("Date").reset_index(drop=True)
    df.set_index("Date", inplace=True)

    # Forward-fill missing values
    df = df.ffill()

    # Drop rows where we still have NaN (beginning of series)
    df = df.dropna()

    return df


def calculate_vix_vix3m_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the VIX/VIX3M ratio (term structure indicator).

    Ratio < 1: Contango (normal, complacent market)
    Ratio > 1: Backwardation (inverted, fearful market)
    """
    df = df.copy()
    df["VIX_VIX3M_Ratio"] = df["VIX_Close"] / df["VIX3M_Close"]
    return df


def calculate_moving_averages(df: pd.DataFrame,
                               windows: list[int] = None) -> pd.DataFrame:
    """
    Calculate Simple Moving Averages (SMA) and Exponential Moving Averages (EMA)
    for SPX across multiple time windows.

    SPX above MA: Generally bullish trend
    SPX below MA: Generally bearish trend

    EMA gives more weight to recent prices, making it more responsive to new data.
    """
    if windows is None:
        windows = [10, 20, 43, 50, 100, 200]

    df = df.copy()

    for w in windows:
        # Simple Moving Average
        df[f"SPX_{w}d_SMA"] = df["SPX_Close"].rolling(window=w, min_periods=w).mean()

        # Exponential Moving Average
        df[f"SPX_{w}d_EMA"] = df["SPX_Close"].ewm(span=w, adjust=False).mean()

    return df


def calculate_forward_returns(df: pd.DataFrame,
                               windows: list[int] = None) -> pd.DataFrame:
    """
    Calculate forward returns for SPX over specified trading day intervals.

    Forward return on day T for window N:
        Return = (Close[T+N] / Close[T]) - 1

    This correctly avoids look-ahead bias: on day T, we're measuring
    the return that WILL occur over the next N days.
    """
    if windows is None:
        windows = [1, 5, 21, 63, 126, 252, 504]

    df = df.copy()

    for n in windows:
        # Shift the close price backwards by N to get future price
        # Then calculate return from current price to future price
        future_price = df["SPX_Close"].shift(-n)
        df[f"SPX_Fwd_Return_{n}d"] = (future_price / df["SPX_Close"]) - 1

    return df


def calculate_signal_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate core event triggers and regime variables based on VIX/VIX3M ratio.

    Part A: Boolean Event Triggers
    Part B: Distribution Analysis Bins
    """
    df = df.copy()
    ratio = df["VIX_VIX3M_Ratio"]
    vix = df["VIX_Close"]

    # =========================================================================
    # PART A: Core Event Triggers (Boolean True/False)
    # =========================================================================

    # 1. Backwardation: True if Ratio > 1.0
    df["Backwardation"] = ratio > 1.0

    # 2. Exiting Backwardation: True if Ratio was > 1.0 yesterday, <= 1.0 today
    df["Exiting_Backwardation"] = (ratio.shift(1) > 1.0) & (ratio <= 1.0)

    # 3. Aptus Two-Factor Model: True if VIX > 20 AND Ratio > 1.0
    df["Aptus_Two_Factor"] = (vix > 20) & (ratio > 1.0)

    # 4. Moving Average Smoother: 5-day SMA of Ratio > 1.0
    df["Ratio_5d_SMA"] = ratio.rolling(window=5, min_periods=5).mean()
    df["MA_Smoother_Signal"] = df["Ratio_5d_SMA"] > 1.0

    # 5. Contango Streak: True if Ratio < 0.85 for exactly 20 consecutive days
    # (triggers on the 20th day only)
    deep_contango = (ratio < 0.85).astype(int)
    # Calculate consecutive streak length
    streak_reset = deep_contango.ne(deep_contango.shift()).cumsum()
    contango_streak_length = deep_contango.groupby(streak_reset).cumsum()
    df["Contango_Streak_Length"] = contango_streak_length
    df["Contango_Streak_20d"] = (contango_streak_length == 20) & (ratio < 0.85)

    # 6. Volatility Spike (Rate of Change): True if Ratio increased > 15% over 3 days
    ratio_3d_ago = ratio.shift(3)
    ratio_pct_change_3d = (ratio - ratio_3d_ago) / ratio_3d_ago
    df["Ratio_3d_ROC"] = ratio_pct_change_3d
    df["Volatility_Spike"] = ratio_pct_change_3d > 0.15

    # =========================================================================
    # PART B: Full Gradient Matrices (Distribution Analysis)
    # =========================================================================

    # 1. Absolute Uniform Bins: 0.70 to 1.35, step 0.025
    bin_edges = np.arange(0.70, 1.375, 0.025)  # 1.375 to include 1.35 endpoint
    bin_labels = [f"{edge:.3f}-{edge + 0.025:.3f}" for edge in bin_edges[:-1]]
    df["Ratio_Absolute_Bins"] = pd.cut(
        ratio,
        bins=bin_edges,
        labels=bin_labels,
        include_lowest=True
    )

    # 2. Quantile Bins (Ventiles): 20 equal-sized buckets (~5% each)
    df["Ratio_Quantile_Bins"] = pd.qcut(
        ratio,
        q=20,
        labels=[f"Ventile_{i:02d}" for i in range(1, 21)],
        duplicates="drop"
    )

    return df


def calculate_forward_max_drawdown(df: pd.DataFrame,
                                    windows: list[int] = None) -> pd.DataFrame:
    """
    Calculate forward-looking Maximum Drawdown for SPX over specified windows.

    For each day T and window N, we look at prices from T to T+N and calculate
    the maximum peak-to-trough decline that occurs within that forward window.

    MDD is returned as a positive value (e.g., 0.10 = 10% drawdown).
    """
    if windows is None:
        windows = [1, 5, 21, 63, 126, 252, 504]

    df = df.copy()
    prices = df["SPX_Close"].values
    n_rows = len(prices)

    for window in windows:
        mdd_values = np.full(n_rows, np.nan)

        for i in range(n_rows - window):
            # Get the forward window of prices (from day i to day i+window inclusive)
            forward_prices = prices[i:i + window + 1]

            # Calculate running maximum (peak) up to each point
            running_max = np.maximum.accumulate(forward_prices)

            # Calculate drawdown at each point: (peak - current) / peak
            drawdowns = (running_max - forward_prices) / running_max

            # Maximum drawdown is the largest drawdown in this window
            mdd_values[i] = np.max(drawdowns)

        df[f"SPX_Fwd_MDD_{window}d"] = mdd_values

    return df


def main():
    """Main execution function."""
    # Configuration
    DATA_DIR = "data"
    FORWARD_WINDOWS = [1, 5, 21, 63, 126, 252, 504]

    print("=" * 60)
    print("SPX-VIX Backtesting Model - Data Preparation")
    print("=" * 60)

    # Step 1: Load and merge data
    print("\n[1/5] Loading and merging CSV files...")
    df = load_and_merge_data(DATA_DIR)
    print(f"      Loaded {len(df):,} rows from {df.index.min().date()} to {df.index.max().date()}")

    # Step 2: Calculate VIX/VIX3M ratio
    print("\n[2/5] Calculating VIX/VIX3M ratio...")
    df = calculate_vix_vix3m_ratio(df)
    print(f"      Ratio range: {df['VIX_VIX3M_Ratio'].min():.3f} to {df['VIX_VIX3M_Ratio'].max():.3f}")

    # Step 3: Calculate moving averages (SMA and EMA)
    MA_WINDOWS = [10, 20, 43, 50, 100, 200]
    print("\n[3/5] Calculating SPX moving averages (SMA and EMA)...")
    df = calculate_moving_averages(df, windows=MA_WINDOWS)
    print(f"      Windows: {MA_WINDOWS}")
    for w in MA_WINDOWS:
        valid_sma = df[f"SPX_{w}d_SMA"].notna().sum()
        valid_ema = df[f"SPX_{w}d_EMA"].notna().sum()
        print(f"      {w:>3}d: SMA {valid_sma:,} obs, EMA {valid_ema:,} obs")

    # Step 4: Calculate signal flags and regime variables
    print("\n[4/7] Calculating signal flags and regime variables...")
    df = calculate_signal_flags(df)

    # Print signal flag summaries
    print(f"      Backwardation days: {df['Backwardation'].sum():,} ({df['Backwardation'].mean()*100:.1f}%)")
    print(f"      Exiting Backwardation events: {df['Exiting_Backwardation'].sum():,}")
    print(f"      Aptus Two-Factor signals: {df['Aptus_Two_Factor'].sum():,} ({df['Aptus_Two_Factor'].mean()*100:.1f}%)")
    print(f"      MA Smoother (5d SMA > 1) signals: {df['MA_Smoother_Signal'].sum():,}")
    print(f"      Contango Streak (20d) triggers: {df['Contango_Streak_20d'].sum():,}")
    print(f"      Volatility Spike (>15% 3d ROC): {df['Volatility_Spike'].sum():,}")

    # Step 5: Calculate forward returns
    print("\n[5/7] Calculating forward returns...")
    df = calculate_forward_returns(df, windows=FORWARD_WINDOWS)
    for w in FORWARD_WINDOWS:
        col = f"SPX_Fwd_Return_{w}d"
        valid = df[col].notna().sum()
        print(f"      {w:>3}d forward return: {valid:,} valid observations")

    # Step 6: Calculate forward maximum drawdowns
    print("\n[6/7] Calculating forward maximum drawdowns...")
    df = calculate_forward_max_drawdown(df, windows=FORWARD_WINDOWS)
    for w in FORWARD_WINDOWS:
        col = f"SPX_Fwd_MDD_{w}d"
        valid = df[col].notna().sum()
        mean_mdd = df[col].mean() * 100
        print(f"      {w:>3}d forward MDD: {valid:,} obs, avg MDD: {mean_mdd:.2f}%")

    # Step 7: Quantile Bin Distribution Summary
    print("\n[7/7] Quantile Bins (Ventiles) Distribution:")
    print("-" * 50)
    ventile_counts = df["Ratio_Quantile_Bins"].value_counts().sort_index()
    total_obs = len(df)
    print(f"{'Ventile':<15} {'Count':>8} {'Pct':>8}  Ratio Range")
    print("-" * 50)

    # Get the ratio range for each ventile
    for ventile in ventile_counts.index:
        count = ventile_counts[ventile]
        pct = count / total_obs * 100
        mask = df["Ratio_Quantile_Bins"] == ventile
        ratio_min = df.loc[mask, "VIX_VIX3M_Ratio"].min()
        ratio_max = df.loc[mask, "VIX_VIX3M_Ratio"].max()
        print(f"{ventile:<15} {count:>8,} {pct:>7.1f}%  [{ratio_min:.4f} - {ratio_max:.4f}]")

    print("-" * 50)
    print(f"{'TOTAL':<15} {total_obs:>8,} {100.0:>7.1f}%")

    # Summary statistics
    print("\n" + "=" * 60)
    print("Data Summary")
    print("=" * 60)
    print(f"\nDate Range: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Total Observations: {len(df):,}")

    print("\nColumn Overview:")
    print("-" * 40)
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"  {col:<25} {non_null:>6,} non-null")

    print("\nDescriptive Statistics (Key Columns):")
    print("-" * 40)
    key_cols = ["SPX_Close", "VIX_Close", "VIX3M_Close", "VIX_VIX3M_Ratio"]
    print(df[key_cols].describe().round(2).to_string())

    print("\nMoving Average Statistics (200d):")
    print("-" * 40)
    ma_cols = ["SPX_Close", "SPX_200d_SMA", "SPX_200d_EMA"]
    print(df[ma_cols].describe().round(2).to_string())

    # Save to CSV
    output_file = "spx_vix_analysis_data.csv"
    df.to_csv(output_file)
    print(f"\n[OUTPUT] Saved prepared dataset to: {output_file}")

    return df


if __name__ == "__main__":
    df = main()
