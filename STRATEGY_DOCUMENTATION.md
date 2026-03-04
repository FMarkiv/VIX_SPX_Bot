# SPX-VIX Term Structure Trading System
## Master Documentation

*Last Updated: March 2026*
*Data Coverage: July 2006 - March 2026 (~4,938 trading days)*

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Theoretical Foundation](#theoretical-foundation)
3. [Dynamic Regime Analysis (Decile System)](#dynamic-regime-analysis-decile-system)
4. [Trading Signal System](#trading-signal-system)
5. [Backtested Performance](#backtested-performance)
6. [Risk Management](#risk-management)
7. [Technical Implementation](#technical-implementation)
8. [Appendix: Complete Decile Statistics](#appendix-complete-decile-statistics)

---

## Executive Summary

This system monitors the VIX term structure (VIX/VIX3M ratio) to identify high-probability entry points for SPX exposure. The core thesis is that **VIX term structure inversion (backwardation)** signals elevated short-term fear that historically precedes strong forward returns.

### Key Findings

| Metric | Current Regime (Decile 9) | Unconditional Baseline |
|--------|---------------------------|------------------------|
| 1Y Forward Return | +6.4% | +9.6% |
| 2Y Forward Return | +18.5% | +20.6% |
| 1Y Max Drawdown | -19.8% | -15.7% |
| 1Y Win Rate | 69% | 78% |

### Signal Performance (Backtested)

| Strategy | Avg 1Y Return | Win Rate | Return/MDD |
|----------|---------------|----------|------------|
| Unconditional (Buy & Hold) | +12.5% | 86.3% | 0.91 |
| Pure Backwardation | +20.4% | 94.8% | 1.49 |
| MA Smoother (5d SMA > 1.0) | +22.3% | 97.0% | 1.67 |
| MA Smoother + SPX < 200d SMA | +26.3% | 95.9% | **2.18** |

---

## Theoretical Foundation

### VIX Term Structure Basics

The VIX measures implied volatility of S&P 500 options over the next 30 days, while VIX3M measures implied volatility over 90 days. Under normal market conditions:

```
VIX < VIX3M  →  Contango (normal)
VIX > VIX3M  →  Backwardation (fear)
```

**The VIX/VIX3M Ratio** quantifies this relationship:
- **Ratio < 1.0**: Contango - markets calm, short-term vol lower than long-term
- **Ratio > 1.0**: Backwardation - panic, short-term vol spikes above long-term
- **Ratio = 1.0**: Flat term structure - transition zone

### Why Backwardation Signals Opportunity

When VIX spikes above VIX3M, it indicates:
1. **Short-term panic** - investors buying near-term protection
2. **Mean reversion expected** - elevated VIX historically reverts quickly
3. **Capitulation potential** - often marks selling exhaustion

Historical data shows that buying during backwardation produces superior risk-adjusted returns compared to unconditional exposure.

---

## Dynamic Regime Analysis (Decile System)

The system divides the entire historical distribution of VIX/VIX3M ratios into 10 equal-sized buckets (deciles) and calculates forward-looking metrics for each.

### Decile Overview

| Decile | Ratio Range | Regime Name | Description |
|--------|-------------|-------------|-------------|
| 1-2 | 0.71 - 0.84 | Deep Contango | Extreme complacency |
| 3-4 | 0.84 - 0.88 | Mild Contango | Normal calm markets |
| 5-7 | 0.88 - 0.94 | Normal | Typical market conditions |
| 8-9 | 0.94 - 1.01 | Transition/Elevated | Increasing concern |
| 10 | 1.01 - 1.43 | Backwardation/Panic | Active fear |

### Complete Decile Statistics

| Decile | Ratio Range | 1M Fwd | 3M Fwd | 1Y Fwd | 2Y Fwd | 1Y Max DD | 1Y Win Rate | N |
|--------|-------------|--------|--------|--------|--------|-----------|-------------|---|
| 1 | 0.710 - 0.815 | +0.55% | +1.61% | +8.49% | +18.13% | -12.68% | 75.2% | 444 |
| 2 | 0.815 - 0.841 | +0.61% | +1.61% | +10.18% | +23.59% | -13.98% | 80.8% | 443 |
| 3 | 0.841 - 0.861 | +0.39% | +1.90% | +8.86% | +21.82% | -14.35% | 78.1% | 443 |
| 4 | 0.861 - 0.881 | +0.80% | +2.34% | +10.31% | +23.32% | -14.06% | 82.0% | 445 |
| 5 | 0.881 - 0.899 | +0.91% | +2.70% | +11.59% | +20.32% | -13.38% | 86.7% | 442 |
| 6 | 0.899 - 0.918 | +0.73% | +2.46% | +11.52% | +20.13% | -13.77% | 84.2% | 443 |
| 7 | 0.918 - 0.942 | +0.71% | +2.93% | +11.10% | +21.15% | -15.30% | 84.0% | 444 |
| 8 | 0.942 - 0.968 | +0.81% | +2.15% | +6.68% | +17.95% | -18.81% | 71.1% | 443 |
| 9 | 0.968 - 1.008 | +1.01% | +2.56% | +6.41% | +18.54% | -19.80% | 69.3% | 443 |
| 10 | 1.008 - 1.431 | +1.35% | +2.79% | +11.13% | +20.70% | -21.10% | 68.9% | 444 |
| **Baseline** | All Data | +0.79% | +2.30% | +9.63% | +20.57% | -15.72% | 78.0% | 4,434 |

### Key Observations

#### 1. The "Smile" Pattern in 1Y Returns
Returns are highest at the extremes and lowest in the transition zone:
- **Deciles 1-7**: Stable returns (~8-12% annually)
- **Deciles 8-9**: Lowest returns (~6.4-6.7%) with highest drawdowns
- **Decile 10**: Strong recovery (+11.1%) despite elevated risk

#### 2. Short-Term vs Long-Term Divergence
Higher deciles (more fear) show:
- **Better short-term returns** (1M: +1.35% in D10 vs +0.55% in D1)
- **Higher drawdown risk** (-21% in D10 vs -12.7% in D1)
- **Lower win rates** (69% in D10 vs 75% in D1)

#### 3. The Transition Zone Warning (Deciles 8-9)
The transition zone (ratio 0.94-1.01) is the **worst risk-adjusted regime**:
- Lowest 1Y returns (+6.4-6.7%)
- Elevated drawdowns (-18.8% to -19.8%)
- Lowest win rates (69-71%)

**Interpretation**: Markets are uncertain but haven't capitulated. This is "no man's land."

#### 4. Backwardation Recovery (Decile 10)
Once backwardation is confirmed (ratio > 1.0):
- Returns improve significantly (+11.1% vs +6.4% in D9)
- Drawdowns remain elevated (-21%)
- Classic "buy the fear" territory

---

## Trading Signal System

### Signal Definition

The system generates a **GO (BUY) Signal** when BOTH conditions are met:

| Condition | Indicator | Threshold |
|-----------|-----------|-----------|
| **VIX Term Structure Inverted** | 5-day SMA of VIX/VIX3M Ratio | > 1.0 |
| **SPX Below Long-Term Trend** | SPX Price | < 200d SMA or EMA |

### Signal Logic

```
BUY_SIGNAL = (Ratio_5d_SMA > 1.0) AND (SPX < SPX_200d_MA)
```

**Rationale**: Combining term structure inversion with price weakness captures "panic during downtrend" - historically the strongest forward return setup.

### Daily Output Format

```
[HISTORY] REGIME CONTEXT
Current Regime: Transition/Elevated (Decile: 9/10)
   -> Returns: 1M: +1.0% | 3M: +2.6% | 1Y: +6.4% | 2Y: +18.5%
   -> 1Y Risk: Max DD: -19.8% | Win Rate: 69%

Baseline (Unconditional Market)
   -> Returns: 1M: +0.8% | 3M: +2.3% | 1Y: +9.6% | 2Y: +20.6%
   -> 1Y Risk: Max DD: -15.7% | Win Rate: 78%
```

This comparison allows you to see at a glance whether the current regime is:
- **Better than baseline** (positive edge)
- **Worse than baseline** (elevated risk)
- **Similar to baseline** (no edge)

---

## Backtested Performance

### Signal Comparison Matrix

| Scenario | N | Avg 1Y Ret | Med 1Y Ret | Avg MDD | Worst MDD | Win Rate | Ret/MDD |
|----------|--:|----------:|----------:|--------:|----------:|---------:|--------:|
| Unconditional | 3,911 | 12.50% | 13.40% | -13.69% | -34.10% | 86.3% | 0.91 |
| Pure Backwardation | 288 | 20.41% | 18.30% | -13.69% | -34.10% | 94.8% | 1.49 |
| MA Smoother | 236 | 22.31% | 19.58% | -13.33% | -34.10% | 97.0% | 1.67 |
| **MA Smoother + SPX < 200d SMA** | 146 | 26.27% | 21.75% | -12.07% | -28.74% | 95.9% | **2.18** |
| MA Smoother + SPX < 200d EMA | 162 | 26.06% | 21.99% | -11.71% | -28.74% | 96.3% | **2.23** |

### Trend Filter Analysis

#### Best Performing Combinations

| Rank | Strategy | Return/MDD | Comment |
|------|----------|------------|---------|
| 1 | MA Smoother + SMA 43d Above | 3.20 | Small sample (N=14) |
| 2 | MA Smoother + EMA 43d Above | 2.75 | Small sample (N=20) |
| 3 | MA Smoother + EMA 200d Below | 2.23 | **Best practical choice** |
| 4 | MA Smoother + SMA 200d Below | 2.18 | **Best practical choice** |

#### Counterintuitive Finding: Below Trend Outperforms

| Position | Avg Return/MDD | Interpretation |
|----------|----------------|----------------|
| Below 200d MA | 2.18-2.23 | Captures recovery from panic |
| Above 200d MA | 0.83-0.85 | Less upside, same drawdown |

**Key Insight**: Backwardation during downtrends (SPX < 200d MA) produces the best risk-adjusted returns because it captures the recovery phase from capitulation.

---

## Risk Management

### Drawdown Analysis

| Regime | Avg 1Y Max DD | Worst Case | Risk Level |
|--------|---------------|------------|------------|
| Deep Contango (D1-2) | -12.7% to -14.0% | Low |
| Normal (D3-7) | -13.4% to -15.3% | Moderate |
| Transition (D8-9) | -18.8% to -19.8% | **Elevated** |
| Backwardation (D10) | -21.1% | **High** |
| Baseline | -15.7% | Moderate |

### Position Sizing Considerations

Given the regime-dependent risk profile:

1. **Reduce exposure in Transition Zone (D8-9)**
   - Worst risk-adjusted returns
   - Elevated drawdowns without corresponding return boost

2. **Size appropriately for Backwardation (D10)**
   - Highest short-term returns but also highest drawdowns
   - Consider scaling in rather than full allocation

3. **Normal allocation in Contango/Normal (D1-7)**
   - Consistent returns with moderate risk

### Win Rate by Regime

| Regime | 1Y Win Rate | Interpretation |
|--------|-------------|----------------|
| Deep Contango (D1-2) | 75-81% | Reliable but lower returns |
| Normal (D3-7) | 78-87% | Optimal risk/reward |
| Transition (D8-9) | 69-71% | **Worst reliability** |
| Backwardation (D10) | 69% | Higher returns justify lower win rate |

---

## Technical Implementation

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Daily Signal Tracker                   │
├─────────────────────────────────────────────────────────┤
│  1. Fetch Data (yfinance)                               │
│     └── SPX, VIX, VIX3M full history                   │
│                                                         │
│  2. Calculate Forward Returns                           │
│     └── 1M, 3M, 1Y, 2Y returns + Max DD + Win Rate     │
│                                                         │
│  3. Build Decile Statistics                             │
│     └── Dynamic buckets based on full history          │
│                                                         │
│  4. Calculate Unconditional Baseline                    │
│     └── Mean across all historical data                │
│                                                         │
│  5. Calculate Current Indicators                        │
│     └── Ratio, 5d SMA, 200d SMA/EMA                    │
│                                                         │
│  6. Evaluate Signal Conditions                          │
│     └── GO/NO-GO determination                         │
│                                                         │
│  7. Format & Send Telegram Alert                        │
│     └── Current regime vs baseline comparison          │
└─────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `daily_signal_tracker.py` | Main bot - live signals + Telegram alerts |
| `trend_filter_matrix_evaluation.py` | Backtesting framework |
| `exit_strategy_simulation.py` | LEAPS exit strategy analysis |
| `backtest_analysis.py` | Historical performance analysis |
| `distribution_analysis.py` | Return distribution analysis |

### Automation (GitHub Actions)

The system runs automatically at **4:30 PM ET every weekday** via GitHub Actions:

```yaml
on:
  schedule:
    - cron: '30 21 * * 1-5'  # 21:30 UTC = 4:30 PM ET
  workflow_dispatch:  # Manual trigger
```

### Dependencies

```
yfinance>=0.2.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.28.0
matplotlib>=3.7.0
seaborn>=0.12.0
```

---

## Appendix: Complete Decile Statistics

### Decile 1: Deep Contango (Extreme)
- **Ratio Range**: 0.7104 - 0.8148
- **Sample Size**: 444 days
- **Regime**: Extreme complacency, VIX very low relative to VIX3M

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.55% | +0.99% |
| 3M Forward Return | +1.61% | +2.76% |
| 1Y Forward Return | +8.49% | +12.84% |
| 2Y Forward Return | +18.13% | +18.77% |
| 1Y Max Drawdown | -12.68% | - |
| 1Y Win Rate | 75.2% | - |

---

### Decile 2: Deep Contango
- **Ratio Range**: 0.8149 - 0.8408
- **Sample Size**: 443 days

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.61% | +1.07% |
| 3M Forward Return | +1.61% | +3.12% |
| 1Y Forward Return | +10.18% | +12.17% |
| 2Y Forward Return | +23.59% | +21.62% |
| 1Y Max Drawdown | -13.98% | - |
| 1Y Win Rate | 80.8% | - |

---

### Decile 3: Mild Contango
- **Ratio Range**: 0.8409 - 0.8614
- **Sample Size**: 443 days

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.39% | +1.04% |
| 3M Forward Return | +1.90% | +3.08% |
| 1Y Forward Return | +8.86% | +10.00% |
| 2Y Forward Return | +21.82% | +19.81% |
| 1Y Max Drawdown | -14.35% | - |
| 1Y Win Rate | 78.1% | - |

---

### Decile 4: Mild Contango
- **Ratio Range**: 0.8614 - 0.8808
- **Sample Size**: 445 days

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.80% | +1.58% |
| 3M Forward Return | +2.34% | +3.58% |
| 1Y Forward Return | +10.31% | +12.39% |
| 2Y Forward Return | +23.32% | +21.88% |
| 1Y Max Drawdown | -14.06% | - |
| 1Y Win Rate | 82.0% | - |

---

### Decile 5: Normal
- **Ratio Range**: 0.8808 - 0.8990
- **Sample Size**: 442 days

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.91% | +1.53% |
| 3M Forward Return | +2.70% | +3.66% |
| 1Y Forward Return | +11.59% | +12.87% |
| 2Y Forward Return | +20.32% | +19.89% |
| 1Y Max Drawdown | -13.38% | - |
| 1Y Win Rate | 86.7% | - |

---

### Decile 6: Normal
- **Ratio Range**: 0.8990 - 0.9183
- **Sample Size**: 443 days

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.73% | +1.65% |
| 3M Forward Return | +2.46% | +3.61% |
| 1Y Forward Return | +11.52% | +12.61% |
| 2Y Forward Return | +20.13% | +20.64% |
| 1Y Max Drawdown | -13.77% | - |
| 1Y Win Rate | 84.2% | - |

---

### Decile 7: Normal
- **Ratio Range**: 0.9183 - 0.9415
- **Sample Size**: 444 days

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.71% | +1.94% |
| 3M Forward Return | +2.93% | +4.65% |
| 1Y Forward Return | +11.10% | +12.55% |
| 2Y Forward Return | +21.15% | +26.26% |
| 1Y Max Drawdown | -15.30% | - |
| 1Y Win Rate | 84.0% | - |

---

### Decile 8: Transition/Elevated
- **Ratio Range**: 0.9415 - 0.9684
- **Sample Size**: 443 days
- **Warning**: Worst risk-adjusted regime

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +0.81% | +1.77% |
| 3M Forward Return | +2.15% | +4.28% |
| 1Y Forward Return | +6.68% | +11.27% |
| 2Y Forward Return | +17.95% | +22.53% |
| 1Y Max Drawdown | -18.81% | - |
| 1Y Win Rate | 71.1% | - |

---

### Decile 9: Transition/Elevated
- **Ratio Range**: 0.9684 - 1.0076
- **Sample Size**: 443 days
- **Warning**: Elevated risk, low returns

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +1.01% | +1.82% |
| 3M Forward Return | +2.56% | +4.19% |
| 1Y Forward Return | +6.41% | +13.69% |
| 2Y Forward Return | +18.54% | +23.98% |
| 1Y Max Drawdown | -19.80% | - |
| 1Y Win Rate | 69.3% | - |

---

### Decile 10: Backwardation/Panic
- **Ratio Range**: 1.0077 - 1.4309
- **Sample Size**: 444 days
- **Signal**: BUY opportunity when combined with trend filter

| Metric | Mean | Median |
|--------|------|--------|
| 1M Forward Return | +1.35% | +2.52% |
| 3M Forward Return | +2.79% | +4.05% |
| 1Y Forward Return | +11.13% | +14.84% |
| 2Y Forward Return | +20.70% | +24.40% |
| 1Y Max Drawdown | -21.10% | - |
| 1Y Win Rate | 68.9% | - |

---

### Unconditional Baseline (All Data)
- **Sample Size**: 4,434 days with complete forward data
- **Date Range**: July 2006 - March 2026

| Metric | Value |
|--------|-------|
| 1M Forward Return | +0.79% |
| 3M Forward Return | +2.30% |
| 1Y Forward Return | +9.63% |
| 2Y Forward Return | +20.57% |
| 1Y Max Drawdown | -15.72% |
| 1Y Win Rate | 78.0% |

---

## Disclaimer

This documentation is for educational and informational purposes only. It is not financial advice. Past performance does not guarantee future results. The statistics presented are based on historical data and may not reflect future market conditions. Always do your own research and consult with a qualified financial advisor before making investment decisions.

---

*Generated: March 2026*
*System: SPX-VIX Term Structure Trading System v2.0*
