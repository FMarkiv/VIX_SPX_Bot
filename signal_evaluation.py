"""
Signal Evaluation and Statistical Analysis
==========================================
Part 1: Core Scenarios Evaluation with Statistical Significance
Part 2: Ventile Risk & Consistency Matrix
Part 3: Heatmap Visualizations
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


def load_data():
    """Load the prepared dataset."""
    df = pd.read_csv('spx_vix_analysis_data.csv', index_col='Date', parse_dates=True)
    return df


def calculate_win_rate(series):
    """Calculate percentage of positive returns."""
    valid = series.dropna()
    if len(valid) == 0:
        return np.nan
    return (valid > 0).sum() / len(valid) * 100


def welch_ttest(sample, baseline):
    """Perform Welch's t-test comparing sample to baseline."""
    sample_clean = sample.dropna()
    baseline_clean = baseline.dropna()
    if len(sample_clean) < 2 or len(baseline_clean) < 2:
        return np.nan
    _, p_value = stats.ttest_ind(sample_clean, baseline_clean, equal_var=False)
    return p_value


def part1_core_scenarios(df):
    """
    Part 1: Core Scenarios Evaluation Table
    Compare 6 boolean signals against unconditional baseline.
    """
    print("\n" + "=" * 120)
    print("PART 1: CORE SCENARIOS EVALUATION TABLE")
    print("=" * 120)

    # Define return and MDD columns
    return_cols = ['SPX_Fwd_Return_1d', 'SPX_Fwd_Return_5d', 'SPX_Fwd_Return_21d',
                   'SPX_Fwd_Return_63d', 'SPX_Fwd_Return_126d', 'SPX_Fwd_Return_252d']
    mdd_cols = ['SPX_Fwd_MDD_1d', 'SPX_Fwd_MDD_5d', 'SPX_Fwd_MDD_21d',
                'SPX_Fwd_MDD_63d', 'SPX_Fwd_MDD_126d', 'SPX_Fwd_MDD_252d']

    # Define scenarios
    scenarios = {
        'Unconditional (Baseline)': df.index.notna(),  # All rows
        'Backwardation': df['Backwardation'] == True,
        'Exiting Backwardation': df['Exiting_Backwardation'] == True,
        'Aptus Two-Factor': df['Aptus_Two_Factor'] == True,
        'MA Smoother (5d SMA > 1)': df['MA_Smoother_Signal'] == True,
        'Contango Streak 20d': df['Contango_Streak_20d'] == True,
        'Volatility Spike (>15% ROC)': df['Volatility_Spike'] == True,
    }

    # Store baseline for t-tests
    baseline_63d = df['SPX_Fwd_Return_63d']
    baseline_252d = df['SPX_Fwd_Return_252d']

    # Build results
    results = []

    for scenario_name, mask in scenarios.items():
        subset = df[mask]
        n = len(subset)

        row = {'Scenario': scenario_name, 'N': n}

        # Average returns (as %)
        for col in return_cols:
            horizon = col.split('_')[-1]
            row[f'Ret_{horizon}'] = subset[col].mean() * 100

        # Average MDD (as %)
        for col in mdd_cols:
            horizon = col.split('_')[-1]
            row[f'MDD_{horizon}'] = subset[col].mean() * 100

        # Win rates
        row['WinRate_63d'] = calculate_win_rate(subset['SPX_Fwd_Return_63d'])
        row['WinRate_252d'] = calculate_win_rate(subset['SPX_Fwd_Return_252d'])

        # P-values (skip for baseline)
        if scenario_name == 'Unconditional (Baseline)':
            row['p_val_63d'] = np.nan
            row['p_val_252d'] = np.nan
        else:
            row['p_val_63d'] = welch_ttest(subset['SPX_Fwd_Return_63d'], baseline_63d)
            row['p_val_252d'] = welch_ttest(subset['SPX_Fwd_Return_252d'], baseline_252d)

        results.append(row)

    results_df = pd.DataFrame(results)

    # Print Section A: Average Forward Returns
    print("\n" + "-" * 120)
    print("SECTION A: Average Forward Returns (%)")
    print("-" * 120)
    print(f"{'Scenario':<30} {'N':>6} {'1d':>7} {'5d':>7} {'21d':>7} {'63d':>7} {'126d':>7} {'252d':>7}")
    print("-" * 120)

    for _, row in results_df.iterrows():
        print(f"{row['Scenario']:<30} {row['N']:>6} {row['Ret_1d']:>7.2f} {row['Ret_5d']:>7.2f} "
              f"{row['Ret_21d']:>7.2f} {row['Ret_63d']:>7.2f} {row['Ret_126d']:>7.2f} {row['Ret_252d']:>7.2f}")

    # Print Section B: Average Forward Max Drawdown
    print("\n" + "-" * 120)
    print("SECTION B: Average Forward Max Drawdown (%)")
    print("-" * 120)
    print(f"{'Scenario':<30} {'N':>6} {'1d':>7} {'5d':>7} {'21d':>7} {'63d':>7} {'126d':>7} {'252d':>7}")
    print("-" * 120)

    for _, row in results_df.iterrows():
        print(f"{row['Scenario']:<30} {row['N']:>6} {row['MDD_1d']:>7.2f} {row['MDD_5d']:>7.2f} "
              f"{row['MDD_21d']:>7.2f} {row['MDD_63d']:>7.2f} {row['MDD_126d']:>7.2f} {row['MDD_252d']:>7.2f}")

    # Print Section C: Win Rates & Statistical Significance
    print("\n" + "-" * 120)
    print("SECTION C: Win Rates & Statistical Significance (Welch's t-test vs Baseline)")
    print("-" * 120)
    print(f"{'Scenario':<30} {'N':>6} {'WR_63d':>8} {'WR_252d':>8} {'p-val 63d':>12} {'p-val 252d':>12} {'Sig?':>6}")
    print("-" * 120)

    for _, row in results_df.iterrows():
        p63 = row['p_val_63d']
        p252 = row['p_val_252d']

        # Format p-values
        p63_str = f"{p63:.4f}" if not np.isnan(p63) else "---"
        p252_str = f"{p252:.4f}" if not np.isnan(p252) else "---"

        # Significance flag
        sig = ""
        if not np.isnan(p63) and p63 < 0.05:
            sig += "63d* "
        if not np.isnan(p252) and p252 < 0.05:
            sig += "252d*"
        if sig == "":
            sig = "---"

        print(f"{row['Scenario']:<30} {row['N']:>6} {row['WinRate_63d']:>7.1f}% {row['WinRate_252d']:>7.1f}% "
              f"{p63_str:>12} {p252_str:>12} {sig:>6}")

    print("-" * 120)
    print("* p < 0.05 indicates statistically significant difference from baseline")

    return results_df


def part2_ventile_risk_matrix(df):
    """
    Part 2: Ventile Risk & Consistency Matrix
    """
    print("\n\n" + "=" * 120)
    print("PART 2: VENTILE RISK & CONSISTENCY MATRIX")
    print("=" * 120)

    # Group by ventile
    grouped = df.groupby('Ratio_Quantile_Bins')

    results = []

    for ventile, group in grouped:
        # Get ratio range
        ratio_min = group['VIX_VIX3M_Ratio'].min()
        ratio_max = group['VIX_VIX3M_Ratio'].max()

        row = {
            'Ventile': ventile,
            'Ratio_Range': f"[{ratio_min:.3f}-{ratio_max:.3f}]",
            'N': len(group),
            # Average returns
            'Ret_21d': group['SPX_Fwd_Return_21d'].mean() * 100,
            'Ret_63d': group['SPX_Fwd_Return_63d'].mean() * 100,
            'Ret_252d': group['SPX_Fwd_Return_252d'].mean() * 100,
            # Average MDD
            'MDD_21d': group['SPX_Fwd_MDD_21d'].mean() * 100,
            'MDD_63d': group['SPX_Fwd_MDD_63d'].mean() * 100,
            'MDD_252d': group['SPX_Fwd_MDD_252d'].mean() * 100,
            # Win rates
            'WinRate_63d': calculate_win_rate(group['SPX_Fwd_Return_63d']),
            'WinRate_252d': calculate_win_rate(group['SPX_Fwd_Return_252d']),
        }

        # Return-to-Drawdown ratio (252d)
        if row['MDD_252d'] > 0:
            row['Ret_MDD_Ratio_252d'] = row['Ret_252d'] / row['MDD_252d']
        else:
            row['Ret_MDD_Ratio_252d'] = np.nan

        results.append(row)

    results_df = pd.DataFrame(results)

    # Print the table
    print("\n" + "-" * 140)
    print(f"{'Ventile':<12} {'Ratio Range':<18} {'N':>5} "
          f"{'Ret_21d':>8} {'Ret_63d':>8} {'Ret_252d':>8} "
          f"{'MDD_21d':>8} {'MDD_63d':>8} {'MDD_252d':>8} "
          f"{'WR_63d':>7} {'WR_252d':>7} {'Ret/MDD':>8}")
    print("-" * 140)

    for _, row in results_df.iterrows():
        print(f"{row['Ventile']:<12} {row['Ratio_Range']:<18} {row['N']:>5} "
              f"{row['Ret_21d']:>8.2f} {row['Ret_63d']:>8.2f} {row['Ret_252d']:>8.2f} "
              f"{row['MDD_21d']:>8.2f} {row['MDD_63d']:>8.2f} {row['MDD_252d']:>8.2f} "
              f"{row['WinRate_63d']:>6.1f}% {row['WinRate_252d']:>6.1f}% {row['Ret_MDD_Ratio_252d']:>8.2f}")

    # Summary row
    print("-" * 140)
    total_n = results_df['N'].sum()
    avg_ret_21d = df['SPX_Fwd_Return_21d'].mean() * 100
    avg_ret_63d = df['SPX_Fwd_Return_63d'].mean() * 100
    avg_ret_252d = df['SPX_Fwd_Return_252d'].mean() * 100
    avg_mdd_21d = df['SPX_Fwd_MDD_21d'].mean() * 100
    avg_mdd_63d = df['SPX_Fwd_MDD_63d'].mean() * 100
    avg_mdd_252d = df['SPX_Fwd_MDD_252d'].mean() * 100
    wr_63d = calculate_win_rate(df['SPX_Fwd_Return_63d'])
    wr_252d = calculate_win_rate(df['SPX_Fwd_Return_252d'])
    ret_mdd = avg_ret_252d / avg_mdd_252d if avg_mdd_252d > 0 else np.nan

    print(f"{'ALL':<12} {'[0.710-1.344]':<18} {total_n:>5} "
          f"{avg_ret_21d:>8.2f} {avg_ret_63d:>8.2f} {avg_ret_252d:>8.2f} "
          f"{avg_mdd_21d:>8.2f} {avg_mdd_63d:>8.2f} {avg_mdd_252d:>8.2f} "
          f"{wr_63d:>6.1f}% {wr_252d:>6.1f}% {ret_mdd:>8.2f}")
    print("=" * 140)

    return results_df


def part3_heatmaps(df):
    """
    Part 3: Generate and save heatmap visualizations.
    """
    print("\n\n" + "=" * 80)
    print("PART 3: GENERATING HEATMAP VISUALIZATIONS")
    print("=" * 80)

    # Prepare data for heatmaps
    horizons = ['1d', '5d', '21d', '63d', '126d', '252d']
    return_cols = [f'SPX_Fwd_Return_{h}' for h in horizons]
    mdd_cols = [f'SPX_Fwd_MDD_{h}' for h in horizons]

    grouped = df.groupby('Ratio_Quantile_Bins')

    # Build matrices
    ventiles = []
    ratio_ranges = []
    return_matrix = []
    mdd_matrix = []

    # Calculate unconditional means for excess returns
    unconditional_returns = [df[col].mean() * 100 for col in return_cols]

    for ventile, group in grouped:
        ventiles.append(ventile)
        ratio_min = group['VIX_VIX3M_Ratio'].min()
        ratio_max = group['VIX_VIX3M_Ratio'].max()
        ratio_ranges.append(f"{ventile} [{ratio_min:.2f}-{ratio_max:.2f}]")

        # Returns (as excess over unconditional)
        returns = [group[col].mean() * 100 for col in return_cols]
        excess_returns = [r - u for r, u in zip(returns, unconditional_returns)]
        return_matrix.append(excess_returns)

        # MDD
        mdds = [group[col].mean() * 100 for col in mdd_cols]
        mdd_matrix.append(mdds)

    return_df = pd.DataFrame(return_matrix, index=ratio_ranges, columns=horizons)
    mdd_df = pd.DataFrame(mdd_matrix, index=ratio_ranges, columns=horizons)

    # Set up the figure style
    plt.style.use('seaborn-v0_8-whitegrid')

    # =========================================================================
    # HEATMAP 1: Excess Returns
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(12, 14))

    # Create custom colormap: red for negative, white for zero, green for positive
    cmap_returns = sns.diverging_palette(10, 130, as_cmap=True)

    # Find symmetric bounds for color scale
    abs_max = max(abs(return_df.values.min()), abs(return_df.values.max()))

    sns.heatmap(
        return_df,
        annot=True,
        fmt='.2f',
        cmap=cmap_returns,
        center=0,
        vmin=-abs_max,
        vmax=abs_max,
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'label': 'Excess Return vs Unconditional (%)'},
        ax=ax1
    )

    ax1.set_title('VIX/VIX3M Ratio Ventiles: Excess Forward Returns (%)\n'
                  'Green = Outperformance | Red = Underperformance',
                  fontsize=14, fontweight='bold', pad=20)
    ax1.set_xlabel('Forward Horizon', fontsize=12)
    ax1.set_ylabel('Ventile [Ratio Range]', fontsize=12)

    # Add arrow annotation
    ax1.annotate('← Deepest Contango', xy=(0, 0.5), xytext=(-0.3, 0.5),
                 fontsize=10, ha='right', va='center',
                 xycoords='axes fraction', textcoords='axes fraction')
    ax1.annotate('← Extreme Backwardation', xy=(0, 0.98), xytext=(-0.3, 0.98),
                 fontsize=10, ha='right', va='center',
                 xycoords='axes fraction', textcoords='axes fraction')

    plt.tight_layout()
    fig1.savefig('heatmap_excess_returns.png', dpi=150, bbox_inches='tight',
                 facecolor='white', edgecolor='none')
    print("  Saved: heatmap_excess_returns.png")

    # =========================================================================
    # HEATMAP 2: Max Drawdown
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(12, 14))

    # Create colormap: white to deep red
    cmap_mdd = sns.light_palette("darkred", as_cmap=True)

    sns.heatmap(
        mdd_df,
        annot=True,
        fmt='.2f',
        cmap=cmap_mdd,
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'label': 'Average Max Drawdown (%)'},
        ax=ax2
    )

    ax2.set_title('VIX/VIX3M Ratio Ventiles: Average Forward Max Drawdown (%)\n'
                  'White = Low Risk | Dark Red = High Risk',
                  fontsize=14, fontweight='bold', pad=20)
    ax2.set_xlabel('Forward Horizon', fontsize=12)
    ax2.set_ylabel('Ventile [Ratio Range]', fontsize=12)

    plt.tight_layout()
    fig2.savefig('heatmap_max_drawdown.png', dpi=150, bbox_inches='tight',
                 facecolor='white', edgecolor='none')
    print("  Saved: heatmap_max_drawdown.png")

    # =========================================================================
    # BONUS: Return-to-Risk Heatmap (Return / MDD)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(12, 14))

    # Calculate return/MDD ratio (using absolute returns, not excess)
    grouped = df.groupby('Ratio_Quantile_Bins')
    return_abs_matrix = []

    for ventile, group in grouped:
        returns = [group[col].mean() * 100 for col in return_cols]
        return_abs_matrix.append(returns)

    return_abs_df = pd.DataFrame(return_abs_matrix, index=ratio_ranges, columns=horizons)

    # Avoid division by zero
    risk_adj_df = return_abs_df / mdd_df.replace(0, np.nan)

    # Custom colormap for risk-adjusted
    cmap_risk = sns.diverging_palette(10, 130, as_cmap=True)

    sns.heatmap(
        risk_adj_df,
        annot=True,
        fmt='.2f',
        cmap=cmap_risk,
        center=1.0,
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'label': 'Return / Max Drawdown Ratio'},
        ax=ax3
    )

    ax3.set_title('VIX/VIX3M Ratio Ventiles: Return-to-Drawdown Ratio\n'
                  'Higher = Better Risk-Adjusted Returns',
                  fontsize=14, fontweight='bold', pad=20)
    ax3.set_xlabel('Forward Horizon', fontsize=12)
    ax3.set_ylabel('Ventile [Ratio Range]', fontsize=12)

    plt.tight_layout()
    fig3.savefig('heatmap_risk_adjusted.png', dpi=150, bbox_inches='tight',
                 facecolor='white', edgecolor='none')
    print("  Saved: heatmap_risk_adjusted.png")

    plt.close('all')

    return return_df, mdd_df


def main():
    """Main execution."""
    print("=" * 80)
    print("SIGNAL EVALUATION AND STATISTICAL ANALYSIS")
    print("=" * 80)

    # Load data
    print("\nLoading data...")
    df = load_data()
    print(f"Loaded {len(df):,} observations from {df.index.min().date()} to {df.index.max().date()}")

    # Part 1: Core Scenarios
    scenarios_df = part1_core_scenarios(df)

    # Part 2: Ventile Risk Matrix
    ventile_df = part2_ventile_risk_matrix(df)

    # Part 3: Heatmaps
    return_heatmap, mdd_heatmap = part3_heatmaps(df)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nOutput files:")
    print("  - heatmap_excess_returns.png")
    print("  - heatmap_max_drawdown.png")
    print("  - heatmap_risk_adjusted.png")

    return scenarios_df, ventile_df


if __name__ == "__main__":
    scenarios_df, ventile_df = main()
