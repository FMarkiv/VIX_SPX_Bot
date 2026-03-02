"""
Distribution Analysis of Statistically Significant Signals
===========================================================
Part 1: Detailed Distribution Statistics
Part 2: KDE and Boxplot Visualizations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')


def load_data():
    """Load the prepared dataset."""
    df = pd.read_csv('spx_vix_analysis_data.csv', index_col='Date', parse_dates=True)
    return df


def calculate_distribution_stats(series, name):
    """Calculate comprehensive distribution statistics for a series."""
    clean = series.dropna()
    return {
        'Scenario': name,
        'N': len(clean),
        'Mean': clean.mean() * 100,
        'Median': clean.median() * 100,
        'Std Dev': clean.std() * 100,
        'Min': clean.min() * 100,
        'P25': clean.quantile(0.25) * 100,
        'P75': clean.quantile(0.75) * 100,
        'Max': clean.max() * 100,
        'Skew': clean.skew(),
    }


def part1_distribution_statistics(df):
    """
    Part 1: Detailed Distribution Statistics for winning signals.
    """
    print("\n" + "=" * 130)
    print("PART 1: DETAILED DISTRIBUTION STATISTICS")
    print("=" * 130)

    # Define scenarios
    scenarios = {
        'Unconditional': df.index.notna(),
        'Backwardation': df['Backwardation'] == True,
        'Aptus Two-Factor': df['Aptus_Two_Factor'] == True,
        'MA Smoother': df['MA_Smoother_Signal'] == True,
    }

    horizons = ['21d', '63d', '252d']

    for horizon in horizons:
        return_col = f'SPX_Fwd_Return_{horizon}'
        mdd_col = f'SPX_Fwd_MDD_{horizon}'

        print(f"\n{'='*130}")
        print(f"HORIZON: {horizon} FORWARD")
        print(f"{'='*130}")

        # =====================================================================
        # FORWARD RETURNS
        # =====================================================================
        print(f"\n{'-'*130}")
        print(f"FORWARD RETURNS ({horizon})")
        print(f"{'-'*130}")
        print(f"{'Scenario':<20} {'N':>6} {'Mean':>8} {'Median':>8} {'Std':>8} "
              f"{'Min':>9} {'P25':>8} {'P75':>8} {'Max':>9} {'Skew':>7}")
        print(f"{'-'*130}")

        return_stats = []
        for name, mask in scenarios.items():
            subset = df[mask]
            stats = calculate_distribution_stats(subset[return_col], name)
            return_stats.append(stats)
            print(f"{stats['Scenario']:<20} {stats['N']:>6} {stats['Mean']:>8.2f} {stats['Median']:>8.2f} "
                  f"{stats['Std Dev']:>8.2f} {stats['Min']:>9.2f} {stats['P25']:>8.2f} "
                  f"{stats['P75']:>8.2f} {stats['Max']:>9.2f} {stats['Skew']:>7.2f}")

        # =====================================================================
        # MAX DRAWDOWN
        # =====================================================================
        print(f"\n{'-'*130}")
        print(f"MAX DRAWDOWN ({horizon})")
        print(f"{'-'*130}")
        print(f"{'Scenario':<20} {'N':>6} {'Mean':>8} {'Median':>8} {'Std':>8} "
              f"{'Min':>9} {'P25':>8} {'P75':>8} {'Worst':>9} {'Skew':>7}")
        print(f"{'-'*130}")

        for name, mask in scenarios.items():
            subset = df[mask]
            stats = calculate_distribution_stats(subset[mdd_col], name)
            print(f"{stats['Scenario']:<20} {stats['N']:>6} {stats['Mean']:>8.2f} {stats['Median']:>8.2f} "
                  f"{stats['Std Dev']:>8.2f} {stats['Min']:>9.2f} {stats['P25']:>8.2f} "
                  f"{stats['P75']:>8.2f} {stats['Max']:>9.2f} {stats['Skew']:>7.2f}")

    # =========================================================================
    # COMPARATIVE SUMMARY TABLE
    # =========================================================================
    print("\n\n" + "=" * 130)
    print("COMPARATIVE SUMMARY: KEY METRICS")
    print("=" * 130)

    print(f"\n{'Scenario':<20} | {'------- 63d Forward -------':^35} | {'------ 252d Forward ------':^35}")
    print(f"{'':<20} | {'Mean Ret':>8} {'Med Ret':>8} {'Mean MDD':>9} {'Worst MDD':>9} | "
          f"{'Mean Ret':>8} {'Med Ret':>8} {'Mean MDD':>9} {'Worst MDD':>9}")
    print("-" * 130)

    for name, mask in scenarios.items():
        subset = df[mask]

        # 63d stats
        ret_63_mean = subset['SPX_Fwd_Return_63d'].mean() * 100
        ret_63_med = subset['SPX_Fwd_Return_63d'].median() * 100
        mdd_63_mean = subset['SPX_Fwd_MDD_63d'].mean() * 100
        mdd_63_worst = subset['SPX_Fwd_MDD_63d'].max() * 100

        # 252d stats
        ret_252_mean = subset['SPX_Fwd_Return_252d'].mean() * 100
        ret_252_med = subset['SPX_Fwd_Return_252d'].median() * 100
        mdd_252_mean = subset['SPX_Fwd_MDD_252d'].mean() * 100
        mdd_252_worst = subset['SPX_Fwd_MDD_252d'].max() * 100

        print(f"{name:<20} | {ret_63_mean:>8.2f} {ret_63_med:>8.2f} {mdd_63_mean:>9.2f} {mdd_63_worst:>9.2f} | "
              f"{ret_252_mean:>8.2f} {ret_252_med:>8.2f} {mdd_252_mean:>9.2f} {mdd_252_worst:>9.2f}")

    print("=" * 130)

    # =========================================================================
    # TAIL RISK ANALYSIS
    # =========================================================================
    print("\n\n" + "=" * 130)
    print("TAIL RISK ANALYSIS: WORST OUTCOMES")
    print("=" * 130)

    for name, mask in scenarios.items():
        subset = df[mask]
        print(f"\n{name.upper()}")
        print("-" * 80)

        # Worst 5 returns at 252d
        worst_returns = subset.nsmallest(5, 'SPX_Fwd_Return_252d')[['SPX_Fwd_Return_252d', 'SPX_Fwd_MDD_252d', 'VIX_Close', 'VIX_VIX3M_Ratio']]
        print("  5 Worst 252d Forward Returns:")
        for idx, row in worst_returns.iterrows():
            print(f"    {idx.date()}: Return={row['SPX_Fwd_Return_252d']*100:>7.2f}%, "
                  f"MDD={row['SPX_Fwd_MDD_252d']*100:>6.2f}%, VIX={row['VIX_Close']:>5.1f}, "
                  f"Ratio={row['VIX_VIX3M_Ratio']:.3f}")

        # Count of negative 252d returns
        neg_count = (subset['SPX_Fwd_Return_252d'] < 0).sum()
        total = subset['SPX_Fwd_Return_252d'].notna().sum()
        print(f"\n  Negative 252d Returns: {neg_count} of {total} ({neg_count/total*100:.1f}%)")

        # Count of severe drawdowns (>20%)
        severe_dd = (subset['SPX_Fwd_MDD_252d'] > 0.20).sum()
        print(f"  Severe MDD (>20%): {severe_dd} of {total} ({severe_dd/total*100:.1f}%)")


def part2_visualizations(df):
    """
    Part 2: KDE and Boxplot visualizations.
    """
    print("\n\n" + "=" * 80)
    print("PART 2: GENERATING DISTRIBUTION VISUALIZATIONS")
    print("=" * 80)

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")

    # Define scenarios and colors
    scenarios = {
        'Unconditional': df.index.notna(),
        'Backwardation': df['Backwardation'] == True,
        'Aptus Two-Factor': df['Aptus_Two_Factor'] == True,
        'MA Smoother': df['MA_Smoother_Signal'] == True,
    }

    colors = {
        'Unconditional': '#666666',
        'Backwardation': '#e74c3c',
        'Aptus Two-Factor': '#3498db',
        'MA Smoother': '#2ecc71',
    }

    # =========================================================================
    # FIGURE 1: KDE Distribution Overlay (252d Returns)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(14, 8))

    for name, mask in scenarios.items():
        subset = df[mask]['SPX_Fwd_Return_252d'].dropna() * 100
        median_val = subset.median()

        # Plot KDE
        linewidth = 3 if name != 'Unconditional' else 2
        linestyle = '-' if name != 'Unconditional' else '--'
        sns.kdeplot(subset, ax=ax1, label=f'{name} (n={len(subset)}, med={median_val:.1f}%)',
                    color=colors[name], linewidth=linewidth, linestyle=linestyle)

        # Add vertical median line
        ax1.axvline(median_val, color=colors[name], linestyle=':', alpha=0.7, linewidth=1.5)

    ax1.axvline(0, color='black', linestyle='-', alpha=0.3, linewidth=1)
    ax1.set_xlabel('252-Day Forward Return (%)', fontsize=12)
    ax1.set_ylabel('Density', fontsize=12)
    ax1.set_title('Distribution of 252-Day Forward Returns\nKernel Density Estimate by Signal Regime',
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=10)
    ax1.set_xlim(-60, 80)

    plt.tight_layout()
    fig1.savefig('kde_252d_returns.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("  Saved: kde_252d_returns.png")

    # =========================================================================
    # FIGURE 2: Boxplots of Forward Returns (63d & 252d)
    # =========================================================================
    fig2, axes2 = plt.subplots(1, 2, figsize=(16, 8))

    for idx, horizon in enumerate(['63d', '252d']):
        ax = axes2[idx]
        return_col = f'SPX_Fwd_Return_{horizon}'

        # Prepare data for boxplot
        plot_data = []
        labels = []
        for name, mask in scenarios.items():
            subset = df[mask][return_col].dropna() * 100
            plot_data.append(subset)
            labels.append(name)

        # Create boxplot
        bp = ax.boxplot(plot_data, labels=labels, patch_artist=True, showfliers=True,
                        flierprops=dict(marker='o', markerfacecolor='gray', markersize=3, alpha=0.5))

        # Color the boxes
        for patch, name in zip(bp['boxes'], labels):
            patch.set_facecolor(colors[name])
            patch.set_alpha(0.7)

        # Add horizontal line at 0
        ax.axhline(0, color='black', linestyle='--', alpha=0.5, linewidth=1)

        # Add mean markers
        means = [data.mean() for data in plot_data]
        ax.scatter(range(1, len(means)+1), means, marker='D', color='white',
                   edgecolor='black', s=80, zorder=5, label='Mean')

        ax.set_ylabel(f'{horizon} Forward Return (%)', fontsize=12)
        ax.set_title(f'{horizon} Forward Returns by Signal Regime', fontsize=13, fontweight='bold')
        ax.tick_params(axis='x', rotation=15)

        # Add annotations for medians
        medians = [data.median() for data in plot_data]
        for i, (med, mean) in enumerate(zip(medians, means)):
            ax.annotate(f'Med: {med:.1f}%\nMean: {mean:.1f}%',
                       xy=(i+1, med), xytext=(i+1.3, med),
                       fontsize=9, ha='left', va='center')

    plt.suptitle('Boxplot Comparison: Forward Returns by Signal Regime\n(Diamond = Mean, Line = Median)',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig2.savefig('boxplot_returns.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("  Saved: boxplot_returns.png")

    # =========================================================================
    # FIGURE 3: Boxplots of Max Drawdowns (63d & 252d)
    # =========================================================================
    fig3, axes3 = plt.subplots(1, 2, figsize=(16, 8))

    for idx, horizon in enumerate(['63d', '252d']):
        ax = axes3[idx]
        mdd_col = f'SPX_Fwd_MDD_{horizon}'

        # Prepare data for boxplot
        plot_data = []
        labels = []
        for name, mask in scenarios.items():
            subset = df[mask][mdd_col].dropna() * 100
            plot_data.append(subset)
            labels.append(name)

        # Create boxplot
        bp = ax.boxplot(plot_data, labels=labels, patch_artist=True, showfliers=True,
                        flierprops=dict(marker='o', markerfacecolor='darkred', markersize=3, alpha=0.5))

        # Color the boxes
        for patch, name in zip(bp['boxes'], labels):
            patch.set_facecolor(colors[name])
            patch.set_alpha(0.7)

        # Add mean markers
        means = [data.mean() for data in plot_data]
        ax.scatter(range(1, len(means)+1), means, marker='D', color='white',
                   edgecolor='black', s=80, zorder=5, label='Mean')

        ax.set_ylabel(f'{horizon} Max Drawdown (%)', fontsize=12)
        ax.set_title(f'{horizon} Max Drawdown by Signal Regime', fontsize=13, fontweight='bold')
        ax.tick_params(axis='x', rotation=15)

        # Add annotations
        medians = [data.median() for data in plot_data]
        maxes = [data.max() for data in plot_data]
        for i, (med, mean, mx) in enumerate(zip(medians, means, maxes)):
            ax.annotate(f'Med: {med:.1f}%\nWorst: {mx:.1f}%',
                       xy=(i+1, med), xytext=(i+1.3, med),
                       fontsize=9, ha='left', va='center')

    plt.suptitle('Boxplot Comparison: Max Drawdown by Signal Regime\n(Diamond = Mean, Outliers = Extreme Events)',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig3.savefig('boxplot_drawdowns.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("  Saved: boxplot_drawdowns.png")

    # =========================================================================
    # FIGURE 4: Combined KDE for 21d, 63d, 252d (Signal vs Unconditional)
    # =========================================================================
    fig4, axes4 = plt.subplots(1, 3, figsize=(18, 6))

    horizons = ['21d', '63d', '252d']

    for idx, horizon in enumerate(horizons):
        ax = axes4[idx]
        return_col = f'SPX_Fwd_Return_{horizon}'

        for name, mask in scenarios.items():
            subset = df[mask][return_col].dropna() * 100

            linewidth = 2.5 if name != 'Unconditional' else 2
            linestyle = '-' if name != 'Unconditional' else '--'
            sns.kdeplot(subset, ax=ax, label=name, color=colors[name],
                        linewidth=linewidth, linestyle=linestyle)

        ax.axvline(0, color='black', linestyle='-', alpha=0.3, linewidth=1)
        ax.set_xlabel(f'{horizon} Forward Return (%)', fontsize=11)
        ax.set_ylabel('Density', fontsize=11)
        ax.set_title(f'{horizon} Returns', fontsize=12, fontweight='bold')

        if idx == 2:
            ax.legend(loc='upper right', fontsize=9)

    plt.suptitle('Return Distributions Across Time Horizons\nSignal Regimes vs Unconditional Baseline',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig4.savefig('kde_all_horizons.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("  Saved: kde_all_horizons.png")

    # =========================================================================
    # FIGURE 5: Histogram with percentile markers
    # =========================================================================
    fig5, axes5 = plt.subplots(2, 2, figsize=(16, 12))

    for idx, (name, mask) in enumerate(scenarios.items()):
        ax = axes5.flat[idx]
        subset = df[mask]['SPX_Fwd_Return_252d'].dropna() * 100

        # Plot histogram
        ax.hist(subset, bins=50, color=colors[name], alpha=0.7, edgecolor='white', linewidth=0.5)

        # Add percentile lines
        p5 = subset.quantile(0.05)
        p25 = subset.quantile(0.25)
        p50 = subset.median()
        p75 = subset.quantile(0.75)
        p95 = subset.quantile(0.95)

        ax.axvline(p5, color='red', linestyle='--', linewidth=2, label=f'P5: {p5:.1f}%')
        ax.axvline(p25, color='orange', linestyle='--', linewidth=1.5, label=f'P25: {p25:.1f}%')
        ax.axvline(p50, color='black', linestyle='-', linewidth=2, label=f'Median: {p50:.1f}%')
        ax.axvline(p75, color='green', linestyle='--', linewidth=1.5, label=f'P75: {p75:.1f}%')
        ax.axvline(p95, color='darkgreen', linestyle='--', linewidth=2, label=f'P95: {p95:.1f}%')
        ax.axvline(0, color='gray', linestyle='-', alpha=0.5)

        ax.set_xlabel('252d Forward Return (%)', fontsize=11)
        ax.set_ylabel('Frequency', fontsize=11)
        ax.set_title(f'{name} (n={len(subset)})', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=8)

    plt.suptitle('252-Day Forward Return Histograms with Percentile Markers',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout()
    fig5.savefig('histogram_percentiles.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("  Saved: histogram_percentiles.png")

    plt.close('all')


def main():
    """Main execution."""
    print("=" * 80)
    print("DISTRIBUTION ANALYSIS OF STATISTICALLY SIGNIFICANT SIGNALS")
    print("=" * 80)

    # Load data
    print("\nLoading data...")
    df = load_data()
    print(f"Loaded {len(df):,} observations")

    # Part 1: Distribution Statistics
    part1_distribution_statistics(df)

    # Part 2: Visualizations
    part2_visualizations(df)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print("\nOutput files:")
    print("  - kde_252d_returns.png")
    print("  - boxplot_returns.png")
    print("  - boxplot_drawdowns.png")
    print("  - kde_all_horizons.png")
    print("  - histogram_percentiles.png")


if __name__ == "__main__":
    main()
