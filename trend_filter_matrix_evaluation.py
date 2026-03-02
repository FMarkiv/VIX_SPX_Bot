#!/usr/bin/env python3
"""
Trend Filter Matrix Evaluation
==============================
Backtests 32 combinations of base signals crossed with trend filters
to identify the optimal parameters for the SPX/VIX trading strategy.

Base Signals:
- Raw Backwardation: VIX/VIX3M Ratio > 1.0
- MA Smoother: 5d SMA of Ratio > 1.0

Trend Filters:
- 10, 20, 50, 100-day SMAs and EMAs
- Both Above and Below conditions
"""

import warnings
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yfinance as yf

warnings.filterwarnings("ignore")


def fetch_historical_data() -> pd.DataFrame:
    """
    Fetch maximum available historical data for SPX, VIX, and VIX3M.

    Returns:
        DataFrame with aligned close prices
    """
    print("[*] Fetching historical data...")

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

    print(f"   Retrieved {len(closes)} trading days")
    print(f"   Date range: {closes.index[0].strftime('%Y-%m-%d')} to {closes.index[-1].strftime('%Y-%m-%d')}")

    return closes


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all required indicators for the matrix evaluation.

    Args:
        df: DataFrame with SPX, VIX, VIX3M columns

    Returns:
        DataFrame with all indicator columns added
    """
    print("\n[*] Calculating indicators...")

    data = df.copy()

    # Base signal indicators
    data["VIX_VIX3M_Ratio"] = data["VIX"] / data["VIX3M"]
    data["Ratio_5d_SMA"] = data["VIX_VIX3M_Ratio"].rolling(window=5).mean()

    # Trend filter moving averages (SMA)
    for period in [10, 20, 50, 100]:
        data[f"SPX_SMA_{period}"] = data["SPX"].rolling(window=period).mean()
        data[f"SPX_EMA_{period}"] = data["SPX"].ewm(span=period, adjust=False).mean()

    # Forward 252-day returns for performance measurement
    data["SPX_Return_252d"] = data["SPX"].pct_change(252).shift(-252) * 100

    # Forward 252-day max drawdown calculation
    data["SPX_MaxDD_252d"] = calculate_forward_max_drawdowns(data["SPX"], 252)

    print(f"   Calculated {len([c for c in data.columns if 'SMA' in c or 'EMA' in c])} moving averages")

    return data


def calculate_forward_max_drawdowns(prices: pd.Series, forward_days: int) -> pd.Series:
    """
    Calculate the maximum drawdown over the next N days for each date.

    Args:
        prices: Series of prices
        forward_days: Number of days to look forward

    Returns:
        Series of max drawdown percentages (negative values)
    """
    max_dds = []

    for i in range(len(prices)):
        if i + forward_days >= len(prices):
            max_dds.append(np.nan)
            continue

        forward_prices = prices.iloc[i:i + forward_days + 1].values
        entry_price = forward_prices[0]

        # Calculate running max and drawdowns
        running_max = entry_price
        max_dd = 0

        for price in forward_prices[1:]:
            running_max = max(running_max, price)
            drawdown = (price - running_max) / running_max * 100
            max_dd = min(max_dd, drawdown)

        max_dds.append(max_dd)

    return pd.Series(max_dds, index=prices.index)


def evaluate_scenario(
    df: pd.DataFrame,
    base_signal_col: str,
    trend_col: str,
    trend_direction: str
) -> dict:
    """
    Evaluate a single scenario combination.

    Args:
        df: DataFrame with all indicators
        base_signal_col: Column name for base signal condition
        trend_col: Column name for trend MA
        trend_direction: 'above' or 'below'

    Returns:
        Dictionary with performance metrics
    """
    data = df.dropna(subset=[base_signal_col, trend_col, "SPX_Return_252d", "SPX_MaxDD_252d"])

    # Apply base signal filter
    if base_signal_col == "VIX_VIX3M_Ratio":
        base_mask = data[base_signal_col] > 1.0
    else:  # Ratio_5d_SMA
        base_mask = data[base_signal_col] > 1.0

    # Apply trend filter
    if trend_direction == "above":
        trend_mask = data["SPX"] > data[trend_col]
    else:
        trend_mask = data["SPX"] < data[trend_col]

    # Combined signal
    signal_mask = base_mask & trend_mask
    signal_data = data[signal_mask]

    n = len(signal_data)

    if n < 5:
        return None

    returns = signal_data["SPX_Return_252d"]
    max_dds = signal_data["SPX_MaxDD_252d"]

    avg_return = returns.mean()
    median_return = returns.median()
    avg_mdd = max_dds.mean()
    worst_mdd = max_dds.min()
    win_rate = (returns > 0).sum() / n * 100

    # Return/MDD ratio (use absolute value of MDD for ratio)
    return_mdd_ratio = avg_return / abs(avg_mdd) if avg_mdd != 0 else np.nan

    return {
        "N": n,
        "Avg_Return": avg_return,
        "Median_Return": median_return,
        "Avg_MDD": avg_mdd,
        "Worst_MDD": worst_mdd,
        "Win_Rate": win_rate,
        "Return_MDD_Ratio": return_mdd_ratio
    }


def build_evaluation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the complete evaluation matrix for all 32 combinations.

    Args:
        df: DataFrame with all indicators

    Returns:
        DataFrame with evaluation results for all scenarios
    """
    print("\n[*] Evaluating 32 scenario combinations...")

    base_signals = {
        "Backwardation": "VIX_VIX3M_Ratio",
        "MA_Smoother": "Ratio_5d_SMA"
    }

    trend_periods = [10, 20, 50, 100]
    ma_types = ["SMA", "EMA"]
    trend_directions = ["above", "below"]

    results = []

    for base_name, base_col in base_signals.items():
        for period in trend_periods:
            for ma_type in ma_types:
                for direction in trend_directions:
                    trend_col = f"SPX_{ma_type}_{period}"

                    # Create scenario name
                    dir_symbol = ">" if direction == "above" else "<"
                    scenario_name = f"{base_name} + SPX {dir_symbol} {ma_type}_{period}"

                    metrics = evaluate_scenario(df, base_col, trend_col, direction)

                    if metrics:
                        results.append({
                            "Scenario": scenario_name,
                            "Base_Signal": base_name,
                            "Trend_Period": period,
                            "MA_Type": ma_type,
                            "Direction": direction,
                            **metrics
                        })

    results_df = pd.DataFrame(results)

    # Sort by Return/MDD Ratio descending
    results_df = results_df.sort_values("Return_MDD_Ratio", ascending=False)
    results_df = results_df.reset_index(drop=True)

    print(f"   Evaluated {len(results_df)} valid scenarios")

    return results_df


def calculate_baseline_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate unconditional baseline market metrics.

    Args:
        df: DataFrame with SPX data

    Returns:
        Dictionary with baseline metrics
    """
    data = df.dropna(subset=["SPX_Return_252d", "SPX_MaxDD_252d"])

    baseline = {
        "N": len(data),
        "Avg_Return": data["SPX_Return_252d"].mean(),
        "Avg_MDD": data["SPX_MaxDD_252d"].mean(),
        "Return_MDD_Ratio": data["SPX_Return_252d"].mean() / abs(data["SPX_MaxDD_252d"].mean())
    }

    return baseline


def format_results_table(results_df: pd.DataFrame, min_n: int = 10) -> pd.DataFrame:
    """
    Format the results table for display.

    Args:
        results_df: Raw results DataFrame
        min_n: Minimum sample size filter

    Returns:
        Formatted DataFrame
    """
    # Filter by minimum N
    filtered = results_df[results_df["N"] >= min_n].copy()

    # Format columns for display
    display_df = filtered[[
        "Scenario", "N", "Avg_Return", "Median_Return",
        "Avg_MDD", "Worst_MDD", "Win_Rate", "Return_MDD_Ratio"
    ]].copy()

    # Round numeric columns
    display_df["Avg_Return"] = display_df["Avg_Return"].round(2)
    display_df["Median_Return"] = display_df["Median_Return"].round(2)
    display_df["Avg_MDD"] = display_df["Avg_MDD"].round(2)
    display_df["Worst_MDD"] = display_df["Worst_MDD"].round(2)
    display_df["Win_Rate"] = display_df["Win_Rate"].round(1)
    display_df["Return_MDD_Ratio"] = display_df["Return_MDD_Ratio"].round(3)

    return display_df


def create_risk_reward_plot(
    results_df: pd.DataFrame,
    baseline: dict,
    output_path: str,
    min_n: int = 10
) -> None:
    """
    Create the risk/reward scatter plot visualization.

    Args:
        results_df: Results DataFrame
        baseline: Baseline metrics dictionary
        output_path: Path to save the plot
        min_n: Minimum sample size filter
    """
    print("\n[*] Generating risk/reward scatter plot...")

    # Filter data
    plot_data = results_df[results_df["N"] >= min_n].copy()

    # Set up the plot style
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)

    # Color palette for trend periods
    period_colors = {
        10: "#e74c3c",   # Red
        20: "#3498db",   # Blue
        50: "#2ecc71",   # Green
        100: "#9b59b6"   # Purple
    }

    # Marker styles for base signals
    base_markers = {
        "Backwardation": "o",    # Circle
        "MA_Smoother": "s"       # Square
    }

    # Plot each point
    for _, row in plot_data.iterrows():
        ax.scatter(
            abs(row["Avg_MDD"]),  # Use absolute value for x-axis
            row["Avg_Return"],
            c=period_colors[row["Trend_Period"]],
            marker=base_markers[row["Base_Signal"]],
            s=150,
            alpha=0.7,
            edgecolors="black",
            linewidths=0.5
        )

    # Add baseline reference line
    baseline_x = abs(baseline["Avg_MDD"])
    baseline_y = baseline["Avg_Return"]
    baseline_slope = baseline_y / baseline_x

    x_range = np.linspace(0, ax.get_xlim()[1] * 1.1, 100)
    y_baseline = baseline_slope * x_range

    ax.plot(
        x_range, y_baseline,
        linestyle="--",
        color="gray",
        linewidth=2,
        alpha=0.7,
        label=f"Baseline (Ratio: {baseline['Return_MDD_Ratio']:.2f})"
    )

    # Mark baseline point
    ax.scatter(
        baseline_x, baseline_y,
        c="gray",
        marker="D",
        s=200,
        edgecolors="black",
        linewidths=2,
        zorder=5,
        label=f"Unconditional Market"
    )

    # Annotate top 3 scenarios
    top_3 = plot_data.nlargest(3, "Return_MDD_Ratio")

    for i, (_, row) in enumerate(top_3.iterrows()):
        x_pos = abs(row["Avg_MDD"])
        y_pos = row["Avg_Return"]

        # Offset annotations to avoid overlap
        offsets = [(30, 20), (-30, -30), (30, -20)]

        ax.annotate(
            f"#{i+1}: {row['Scenario']}\n"
            f"Ratio: {row['Return_MDD_Ratio']:.2f}",
            xy=(x_pos, y_pos),
            xytext=offsets[i],
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2")
        )

    # Create custom legend
    legend_elements = []

    # Period colors
    for period, color in period_colors.items():
        legend_elements.append(
            plt.scatter([], [], c=color, marker="o", s=100,
                       label=f"{period}-Day Trend", edgecolors="black")
        )

    # Separator
    legend_elements.append(plt.Line2D([0], [0], color="white", label=""))

    # Base signal markers
    legend_elements.append(
        plt.scatter([], [], c="gray", marker="o", s=100,
                   label="○ = Backwardation", edgecolors="black")
    )
    legend_elements.append(
        plt.scatter([], [], c="gray", marker="s", s=100,
                   label="□ = MA Smoother", edgecolors="black")
    )

    ax.legend(
        handles=legend_elements,
        loc="upper left",
        fontsize=10,
        framealpha=0.9
    )

    # Labels and title
    ax.set_xlabel("252d Average Max Drawdown (%)", fontsize=12, fontweight="bold")
    ax.set_ylabel("252d Average Return (%)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Trend Filter Matrix: Risk/Reward Trade-off Analysis\n"
        "(32 Combinations: 2 Base Signals × 4 Periods × 2 MA Types × 2 Directions)",
        fontsize=14,
        fontweight="bold",
        pad=20
    )

    # Add grid
    ax.grid(True, alpha=0.3)

    # Set axis limits with padding
    x_max = plot_data["Avg_MDD"].abs().max() * 1.15
    y_min = plot_data["Avg_Return"].min() * 1.1 if plot_data["Avg_Return"].min() < 0 else 0
    y_max = plot_data["Avg_Return"].max() * 1.15

    ax.set_xlim(0, x_max)
    ax.set_ylim(y_min, y_max)

    # Add reference lines
    ax.axhline(y=0, color="black", linewidth=0.5, alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()

    print(f"   Saved plot to: {output_path}")


def print_formatted_table(display_df: pd.DataFrame, top_n: int = 10) -> None:
    """
    Print a nicely formatted table to console.

    Args:
        display_df: Formatted results DataFrame
        top_n: Number of rows to display
    """
    print("\n" + "=" * 120)
    print("TREND FILTER MATRIX EVALUATION RESULTS (Top 10 by Return/MDD Ratio)")
    print("=" * 120)

    # Column headers
    headers = ["Rank", "Scenario", "N", "Avg Ret%", "Med Ret%", "Avg MDD%", "Worst MDD%", "Win%", "Ret/MDD"]
    widths = [6, 40, 6, 10, 10, 10, 12, 8, 10]

    # Print header
    header_line = ""
    for h, w in zip(headers, widths):
        header_line += f"{h:>{w}} "
    print(header_line)
    print("-" * 120)

    # Print rows
    for i, (_, row) in enumerate(display_df.head(top_n).iterrows()):
        line = f"{i+1:>6} "
        line += f"{row['Scenario']:<40} "
        line += f"{row['N']:>6} "
        line += f"{row['Avg_Return']:>10.2f} "
        line += f"{row['Median_Return']:>10.2f} "
        line += f"{row['Avg_MDD']:>10.2f} "
        line += f"{row['Worst_MDD']:>12.2f} "
        line += f"{row['Win_Rate']:>8.1f} "
        line += f"{row['Return_MDD_Ratio']:>10.3f} "
        print(line)

    print("=" * 120)


def main():
    """Main execution flow."""
    print("=" * 60)
    print("TREND FILTER MATRIX EVALUATION")
    print("=" * 60)

    # Step 1: Fetch data
    df = fetch_historical_data()

    # Step 2: Calculate all indicators
    df = calculate_all_indicators(df)

    # Step 3: Calculate baseline metrics
    baseline = calculate_baseline_metrics(df)
    print(f"\n[*] Baseline Metrics (Unconditional Market):")
    print(f"   N: {baseline['N']}")
    print(f"   Avg 252d Return: {baseline['Avg_Return']:.2f}%")
    print(f"   Avg 252d MDD: {baseline['Avg_MDD']:.2f}%")
    print(f"   Return/MDD Ratio: {baseline['Return_MDD_Ratio']:.3f}")

    # Step 4: Build evaluation matrix
    results_df = build_evaluation_matrix(df)

    # Step 5: Format and display results
    display_df = format_results_table(results_df, min_n=10)
    print_formatted_table(display_df, top_n=10)

    # Step 6: Create visualization
    output_path = "C:/Projects/Modelling/DEPLOY/SPX-VIX/trend_filter_remaining_risk_reward.png"
    create_risk_reward_plot(results_df, baseline, output_path, min_n=10)

    # Step 7: Save full results to CSV
    csv_path = "C:/Projects/Modelling/DEPLOY/SPX-VIX/trend_filter_matrix_results.csv"
    display_df.to_csv(csv_path, index=False)
    print(f"\n[+] Full results saved to: {csv_path}")

    # Summary insights
    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)

    top_scenario = display_df.iloc[0]
    print(f"\n[#1] Best Scenario: {top_scenario['Scenario']}")
    print(f"   Return/MDD Ratio: {top_scenario['Return_MDD_Ratio']:.3f}")
    print(f"   vs Baseline Ratio: {baseline['Return_MDD_Ratio']:.3f}")
    print(f"   Improvement: {(top_scenario['Return_MDD_Ratio'] / baseline['Return_MDD_Ratio'] - 1) * 100:.1f}%")

    # Group analysis
    print("\n[*] Average Return/MDD by Trend Period:")
    period_avg = results_df[results_df["N"] >= 10].groupby("Trend_Period")["Return_MDD_Ratio"].mean()
    for period in sorted(period_avg.index):
        print(f"   {period:>3}d: {period_avg[period]:.3f}")

    print("\n[*] Average Return/MDD by Direction:")
    dir_avg = results_df[results_df["N"] >= 10].groupby("Direction")["Return_MDD_Ratio"].mean()
    for direction, ratio in dir_avg.items():
        symbol = ">" if direction == "above" else "<"
        print(f"   SPX {symbol} MA: {ratio:.3f}")


if __name__ == "__main__":
    main()
