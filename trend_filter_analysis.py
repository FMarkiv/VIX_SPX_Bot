"""
Trend Filter Evaluation for Term Structure Signals
===================================================
Part 1: Evaluation Matrix crossing Base Signals with Trend Filters
Part 2: Risk/Reward Scatter Plot Visualization
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


def calculate_scenario_metrics(df, mask, name):
    """Calculate comprehensive metrics for a given scenario mask."""
    subset = df[mask]

    # Get 252d forward returns and MDD
    returns = subset['SPX_Fwd_Return_252d'].dropna()
    mdd = subset['SPX_Fwd_MDD_252d'].dropna()

    if len(returns) == 0:
        return None

    avg_return = returns.mean() * 100
    median_return = returns.median() * 100
    avg_mdd = mdd.mean() * 100
    worst_mdd = mdd.max() * 100
    win_rate = (returns > 0).mean() * 100

    # Return/MDD Ratio (using average MDD)
    ret_mdd_ratio = avg_return / avg_mdd if avg_mdd > 0 else np.nan

    return {
        'Scenario': name,
        'N': len(returns),
        'Avg_Return': avg_return,
        'Med_Return': median_return,
        'Avg_MDD': avg_mdd,
        'Worst_MDD': worst_mdd,
        'Win_Rate': win_rate,
        'Ret_MDD_Ratio': ret_mdd_ratio
    }


def part1_trend_filter_matrix(df):
    """
    Part 1: Evaluate all combinations of Base Signals x Trend Filters.
    """
    print("\n" + "=" * 140)
    print("PART 1: TREND FILTER EVALUATION MATRIX")
    print("=" * 140)

    # =========================================================================
    # Define Base Signals
    # =========================================================================
    base_signals = {
        'Backwardation': df['VIX_VIX3M_Ratio'] > 1.0,
        'MA_Smoother': df['Ratio_5d_SMA'] > 1.0
    }

    # =========================================================================
    # Define Trend Filters
    # =========================================================================
    trend_filters = {
        'SMA_43_Above': df['SPX_Close'] > df['SPX_43d_SMA'],
        'SMA_43_Below': df['SPX_Close'] < df['SPX_43d_SMA'],
        'EMA_43_Above': df['SPX_Close'] > df['SPX_43d_EMA'],
        'EMA_43_Below': df['SPX_Close'] < df['SPX_43d_EMA'],
        'SMA_200_Above': df['SPX_Close'] > df['SPX_200d_SMA'],
        'SMA_200_Below': df['SPX_Close'] < df['SPX_200d_SMA'],
        'EMA_200_Above': df['SPX_Close'] > df['SPX_200d_EMA'],
        'EMA_200_Below': df['SPX_Close'] < df['SPX_200d_EMA'],
    }

    # =========================================================================
    # Calculate metrics for all 16 combinations
    # =========================================================================
    results = []

    for base_name, base_mask in base_signals.items():
        for trend_name, trend_mask in trend_filters.items():
            # Combined mask
            combined_mask = base_mask & trend_mask

            # Create descriptive scenario name
            scenario_name = f"{base_name} + {trend_name}"

            # Calculate metrics
            metrics = calculate_scenario_metrics(df, combined_mask, scenario_name)

            if metrics:
                # Add breakdown info for plotting
                metrics['Base_Signal'] = base_name
                metrics['Trend_Filter'] = trend_name

                # Extract trend type for coloring
                if 'SMA_43' in trend_name:
                    metrics['Trend_Type'] = 'SMA_43'
                elif 'EMA_43' in trend_name:
                    metrics['Trend_Type'] = 'EMA_43'
                elif 'SMA_200' in trend_name:
                    metrics['Trend_Type'] = 'SMA_200'
                else:
                    metrics['Trend_Type'] = 'EMA_200'

                results.append(metrics)

    # Create DataFrame and sort by Return/MDD Ratio
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Ret_MDD_Ratio', ascending=False).reset_index(drop=True)

    # =========================================================================
    # Print formatted table
    # =========================================================================
    print(f"\n{'Rank':<4} {'Scenario':<40} {'N':>6} {'Avg Ret':>9} {'Med Ret':>9} "
          f"{'Avg MDD':>9} {'Worst MDD':>10} {'Win Rate':>9} {'Ret/MDD':>8}")
    print("-" * 140)

    for i, row in results_df.iterrows():
        print(f"{i+1:<4} {row['Scenario']:<40} {row['N']:>6} "
              f"{row['Avg_Return']:>9.2f}% {row['Med_Return']:>8.2f}% "
              f"{row['Avg_MDD']:>9.2f}% {row['Worst_MDD']:>9.2f}% "
              f"{row['Win_Rate']:>8.1f}% {row['Ret_MDD_Ratio']:>8.2f}")

    print("-" * 140)

    # =========================================================================
    # Add baseline unconditional for reference
    # =========================================================================
    print("\n" + "=" * 140)
    print("BASELINE COMPARISON")
    print("=" * 140)

    # Unconditional baseline
    uncond_metrics = calculate_scenario_metrics(df, df.index.notna(), 'Unconditional')

    # Pure base signals (no trend filter)
    pure_backwardation = calculate_scenario_metrics(df, base_signals['Backwardation'], 'Pure Backwardation')
    pure_ma_smoother = calculate_scenario_metrics(df, base_signals['MA_Smoother'], 'Pure MA Smoother')

    print(f"\n{'Scenario':<40} {'N':>6} {'Avg Ret':>9} {'Med Ret':>9} "
          f"{'Avg MDD':>9} {'Worst MDD':>10} {'Win Rate':>9} {'Ret/MDD':>8}")
    print("-" * 140)

    for metrics in [uncond_metrics, pure_backwardation, pure_ma_smoother]:
        print(f"{metrics['Scenario']:<40} {metrics['N']:>6} "
              f"{metrics['Avg_Return']:>9.2f}% {metrics['Med_Return']:>8.2f}% "
              f"{metrics['Avg_MDD']:>9.2f}% {metrics['Worst_MDD']:>9.2f}% "
              f"{metrics['Win_Rate']:>8.1f}% {metrics['Ret_MDD_Ratio']:>8.2f}")

    print("=" * 140)

    # =========================================================================
    # Summary insights
    # =========================================================================
    print("\n" + "=" * 140)
    print("KEY INSIGHTS")
    print("=" * 140)

    # Best Return/MDD
    best = results_df.iloc[0]
    print(f"\n1. BEST RETURN/MDD RATIO:")
    print(f"   {best['Scenario']}")
    print(f"   Return/MDD: {best['Ret_MDD_Ratio']:.2f} | Avg Return: {best['Avg_Return']:.2f}% | "
          f"Avg MDD: {best['Avg_MDD']:.2f}% | Worst MDD: {best['Worst_MDD']:.2f}%")

    # Lowest worst drawdown
    lowest_dd = results_df.loc[results_df['Worst_MDD'].idxmin()]
    print(f"\n2. LOWEST WORST-CASE DRAWDOWN:")
    print(f"   {lowest_dd['Scenario']}")
    print(f"   Worst MDD: {lowest_dd['Worst_MDD']:.2f}% | Return/MDD: {lowest_dd['Ret_MDD_Ratio']:.2f} | "
          f"Avg Return: {lowest_dd['Avg_Return']:.2f}%")

    # Highest average return
    highest_ret = results_df.loc[results_df['Avg_Return'].idxmax()]
    print(f"\n3. HIGHEST AVERAGE RETURN:")
    print(f"   {highest_ret['Scenario']}")
    print(f"   Avg Return: {highest_ret['Avg_Return']:.2f}% | Return/MDD: {highest_ret['Ret_MDD_Ratio']:.2f} | "
          f"Worst MDD: {highest_ret['Worst_MDD']:.2f}%")

    # Compare Above vs Below trend
    above_trend = results_df[results_df['Trend_Filter'].str.contains('Above')]
    below_trend = results_df[results_df['Trend_Filter'].str.contains('Below')]

    print(f"\n4. ABOVE VS BELOW TREND COMPARISON:")
    print(f"   Above Trend Average Return/MDD: {above_trend['Ret_MDD_Ratio'].mean():.2f}")
    print(f"   Below Trend Average Return/MDD: {below_trend['Ret_MDD_Ratio'].mean():.2f}")
    print(f"   Above Trend Avg Worst MDD: {above_trend['Worst_MDD'].mean():.2f}%")
    print(f"   Below Trend Avg Worst MDD: {below_trend['Worst_MDD'].mean():.2f}%")

    return results_df, uncond_metrics


def part2_visualization(results_df, uncond_metrics):
    """
    Part 2: Create risk/reward scatter plot visualization.
    """
    print("\n" + "=" * 140)
    print("PART 2: GENERATING RISK/REWARD SCATTER PLOT")
    print("=" * 140)

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))

    # =========================================================================
    # Color mapping for Trend Filters
    # =========================================================================
    trend_colors = {
        'SMA_43': '#e74c3c',    # Red
        'EMA_43': '#f39c12',    # Orange
        'SMA_200': '#3498db',   # Blue
        'EMA_200': '#9b59b6'    # Purple
    }

    # =========================================================================
    # Marker styles for Base Signals
    # =========================================================================
    base_markers = {
        'Backwardation': 'o',   # Circle
        'MA_Smoother': 's'      # Square
    }

    # =========================================================================
    # Plot each scenario
    # =========================================================================
    for _, row in results_df.iterrows():
        color = trend_colors[row['Trend_Type']]
        marker = base_markers[row['Base_Signal']]

        ax.scatter(row['Avg_MDD'], row['Avg_Return'],
                   c=color, marker=marker, s=200, alpha=0.8,
                   edgecolors='black', linewidth=1.5, zorder=5)

    # =========================================================================
    # Add baseline unconditional reference
    # =========================================================================
    uncond_x = uncond_metrics['Avg_MDD']
    uncond_y = uncond_metrics['Avg_Return']
    uncond_ratio = uncond_metrics['Ret_MDD_Ratio']

    # Plot unconditional point
    ax.scatter(uncond_x, uncond_y, c='gray', marker='X', s=300,
               edgecolors='black', linewidth=2, zorder=6, label='Unconditional')

    # Draw dashed line representing baseline Return/MDD ratio
    # Line passes through origin with slope = uncond_ratio
    x_line = np.linspace(0, results_df['Avg_MDD'].max() * 1.1, 100)
    y_line = x_line * uncond_ratio
    ax.plot(x_line, y_line, 'k--', linewidth=1.5, alpha=0.5,
            label=f'Baseline Ret/MDD = {uncond_ratio:.2f}')

    # =========================================================================
    # Annotate top 3 performing scenarios
    # =========================================================================
    top3 = results_df.head(3)

    for i, row in top3.iterrows():
        # Create label
        short_name = row['Scenario'].replace(' + ', '\n')
        label = f"#{i+1}: {short_name}\nRet/MDD: {row['Ret_MDD_Ratio']:.2f}"

        # Calculate offset based on position
        x_offset = 0.3
        y_offset = 1.5 if i % 2 == 0 else -2.5

        ax.annotate(label, xy=(row['Avg_MDD'], row['Avg_Return']),
                    xytext=(row['Avg_MDD'] + x_offset, row['Avg_Return'] + y_offset),
                    fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow',
                              edgecolor='gray', alpha=0.9),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1',
                                    color='gray'))

    # =========================================================================
    # Create legend
    # =========================================================================
    # Trend filter legend (colors)
    trend_handles = [plt.scatter([], [], c=color, marker='o', s=100, label=trend)
                     for trend, color in trend_colors.items()]

    # Base signal legend (markers)
    base_handles = [plt.scatter([], [], c='gray', marker=marker, s=100, label=base)
                    for base, marker in base_markers.items()]

    # Combine legends
    legend1 = ax.legend(handles=trend_handles, title='Trend Filter',
                        loc='upper left', fontsize=10, title_fontsize=11)
    ax.add_artist(legend1)

    legend2 = ax.legend(handles=base_handles, title='Base Signal',
                        loc='lower right', fontsize=10, title_fontsize=11)
    ax.add_artist(legend2)

    # Add baseline to legend
    ax.legend(handles=[plt.scatter([], [], c='gray', marker='X', s=200, label='Unconditional'),
                       plt.Line2D([0], [0], linestyle='--', color='black',
                                   label=f'Baseline Ret/MDD = {uncond_ratio:.2f}')],
              loc='center right', fontsize=10)

    # =========================================================================
    # Labels and formatting
    # =========================================================================
    ax.set_xlabel('252d Average Max Drawdown (%)', fontsize=13, fontweight='bold')
    ax.set_ylabel('252d Average Return (%)', fontsize=13, fontweight='bold')
    ax.set_title('Risk/Reward Trade-off: Term Structure Signals + Trend Filters\n'
                 '252-Day Forward Horizon | Higher-Left is Better',
                 fontsize=14, fontweight='bold')

    # Set axis limits with padding
    ax.set_xlim(0, results_df['Avg_MDD'].max() * 1.15)
    ax.set_ylim(results_df['Avg_Return'].min() * 0.8, results_df['Avg_Return'].max() * 1.15)

    # Add grid
    ax.grid(True, alpha=0.3)

    # Add quadrant labels
    mid_x = (results_df['Avg_MDD'].min() + results_df['Avg_MDD'].max()) / 2
    mid_y = (results_df['Avg_Return'].min() + results_df['Avg_Return'].max()) / 2

    plt.tight_layout()

    # Save
    fig.savefig('trend_filter_risk_reward.png', dpi=150, bbox_inches='tight', facecolor='white')
    print("\n  Saved: trend_filter_risk_reward.png")

    plt.close()


def main():
    """Main execution."""
    print("=" * 140)
    print("TREND FILTER EVALUATION FOR TERM STRUCTURE SIGNALS")
    print("=" * 140)

    # Load data
    print("\nLoading data...")
    df = load_data()
    print(f"Loaded {len(df):,} observations from {df.index.min().date()} to {df.index.max().date()}")

    # Part 1: Evaluation Matrix
    results_df, uncond_metrics = part1_trend_filter_matrix(df)

    # Part 2: Visualization
    part2_visualization(results_df, uncond_metrics)

    print("\n" + "=" * 140)
    print("ANALYSIS COMPLETE")
    print("=" * 140)
    print("\nOutput: trend_filter_risk_reward.png")


if __name__ == "__main__":
    main()
