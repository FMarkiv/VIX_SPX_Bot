# Trend Filter Analysis: Enhancing Term Structure Signals

## Objective

Evaluate whether combining winning VIX term structure signals (Raw Backwardation and MA Smoother) with SPX price trend filters improves the Return-to-Drawdown profile and reduces worst-case drawdown exposure.

---

## Methodology

### Base Signals Tested
| Signal | Definition |
|--------|------------|
| **Raw Backwardation** | VIX/VIX3M Ratio > 1.0 |
| **MA Smoother** | 5-day SMA of VIX/VIX3M Ratio > 1.0 |

### Trend Filters Applied
| Filter | Condition |
|--------|-----------|
| SMA_43 Above/Below | SPX Price vs 43-day Simple Moving Average |
| EMA_43 Above/Below | SPX Price vs 43-day Exponential Moving Average |
| SMA_200 Above/Below | SPX Price vs 200-day Simple Moving Average |
| EMA_200 Above/Below | SPX Price vs 200-day Exponential Moving Average |

### Metrics Evaluated (252-day Forward Horizon)
- Average Return
- Median Return
- Average Max Drawdown
- Worst-Case Max Drawdown
- Win Rate
- **Return/MDD Ratio** (primary ranking metric)

---

## Results

### Complete Ranking Table

| Rank | Scenario | N | Avg Ret | Med Ret | Avg MDD | Worst MDD | Win Rate | Ret/MDD |
|------|----------|--:|--------:|--------:|--------:|----------:|---------:|--------:|
| 1 | MA_Smoother + SMA_43_Above | 14 | 33.09% | 40.38% | 10.35% | 20.18% | 100.0% | **3.20** |
| 2 | MA_Smoother + EMA_43_Above | 20 | 30.68% | 34.84% | 11.17% | 20.18% | 100.0% | **2.75** |
| 3 | MA_Smoother + EMA_200_Below | 162 | 26.06% | 21.99% | 11.71% | 28.74% | 96.3% | **2.23** |
| 4 | MA_Smoother + SMA_200_Below | 146 | 26.27% | 21.75% | 12.07% | 28.74% | 95.9% | **2.18** |
| 5 | Backwardation + EMA_200_Below | 180 | 24.47% | 21.10% | 12.10% | 34.10% | 95.6% | 2.02 |
| 6 | Backwardation + SMA_200_Below | 162 | 24.62% | 20.21% | 12.31% | 34.10% | 95.1% | 2.00 |
| 7 | MA_Smoother + SMA_43_Below | 218 | 21.75% | 19.55% | 13.47% | 34.10% | 96.8% | 1.61 |
| 8 | MA_Smoother + EMA_43_Below | 216 | 21.54% | 19.49% | 13.53% | 34.10% | 96.8% | 1.59 |
| 9 | Backwardation + EMA_43_Above | 33 | 22.00% | 17.93% | 14.13% | 34.10% | 90.9% | 1.56 |
| 10 | Backwardation + SMA_43_Above | 28 | 21.06% | 17.90% | 13.82% | 34.10% | 89.3% | 1.52 |
| 11 | Backwardation + SMA_43_Below | 257 | 20.41% | 18.47% | 13.65% | 34.10% | 95.3% | 1.50 |
| 12 | Backwardation + EMA_43_Below | 255 | 20.20% | 18.30% | 13.63% | 34.10% | 95.3% | 1.48 |
| 13 | MA_Smoother + SMA_200_Above | 66 | 14.49% | 13.64% | 17.02% | 34.10% | 98.5% | 0.85 |
| 14 | Backwardation + SMA_200_Above | 102 | 13.81% | 15.19% | 16.26% | 34.10% | 93.1% | 0.85 |
| 15 | MA_Smoother + EMA_200_Above | 74 | 14.10% | 13.64% | 16.88% | 34.10% | 98.6% | 0.83 |
| 16 | Backwardation + EMA_200_Above | 108 | 13.64% | 14.37% | 16.33% | 34.10% | 93.5% | 0.83 |

### Baseline Comparison

| Scenario | N | Avg Ret | Med Ret | Avg MDD | Worst MDD | Win Rate | Ret/MDD |
|----------|--:|--------:|--------:|--------:|----------:|---------:|--------:|
| **Unconditional** | 3,911 | 12.50% | 13.40% | 13.69% | 34.10% | 86.3% | 0.91 |
| Pure Backwardation | 288 | 20.41% | 18.30% | 13.69% | 34.10% | 94.8% | 1.49 |
| Pure MA Smoother | 236 | 22.31% | 19.58% | 13.33% | 34.10% | 97.0% | 1.67 |

---

## Key Findings

### 1. Best Risk-Adjusted Performance
**MA_Smoother + SMA_43_Above** dominates on all key metrics:
- Return/MDD Ratio: **3.20** (vs 0.91 baseline — 3.5x improvement)
- Worst-Case Drawdown: **20.18%** (vs 34.10% baseline — 41% reduction)
- Average Return: **33.09%** (vs 12.50% baseline — 2.6x improvement)
- Win Rate: **100%**
- Caveat: Small sample (N=14)

### 2. Best Practical Signal (Higher Sample Size)
**MA_Smoother + 200d Below** offers the best balance:
- N = 146-162 observations
- Return/MDD Ratio: **2.18-2.23**
- Worst-Case Drawdown: **28.74%** (16% reduction from baseline)
- Win Rate: **~96%**

### 3. Counterintuitive Pattern: Below Trend Outperforms Above

| Trend Position | Avg Return/MDD | Avg Worst MDD |
|----------------|---------------:|---------------:|
| **Below Trend** | 1.83 | 32.76% |
| Above Trend | 1.55 | 30.62% |

**Interpretation**: Backwardation occurring during downtrends captures recovery phases from panic selloffs, which historically produce the strongest forward returns.

### 4. Trend Filter Impact on Tail Risk

| Filter Added | Worst MDD Reduction |
|--------------|--------------------:|
| 43d Above (SMA/EMA) | 34.10% → **20.18%** |
| 200d Below (SMA/EMA) | 34.10% → **28.74%** |
| 200d Above (SMA/EMA) | No improvement |

---

## Visual Summary

![Risk/Reward Scatter Plot](trend_filter_risk_reward.png)

*Scatter plot showing all 16 scenario combinations. Points in the upper-left quadrant represent optimal risk-adjusted performance (high return, low drawdown). The dashed line represents the unconditional baseline Return/MDD ratio of 0.91.*

---

## Conclusions

1. **Adding short-term trend filters (43d MA) dramatically improves risk-adjusted returns** when price is ABOVE the moving average, though at the cost of reduced signal frequency.

2. **The MA Smoother consistently outperforms Raw Backwardation** across all trend filter combinations, confirming earlier findings about the value of smoothing.

3. **Being below the 200d MA during backwardation is not a warning sign** — it's actually associated with better forward returns than being above it. This aligns with the "buy fear" thesis.

4. **Worst-case drawdown can be reduced from 34% to 20%** by requiring price to be above the short-term trend before acting on backwardation signals.

5. **Trade-off**: The highest Return/MDD scenarios have the smallest sample sizes. For practical implementation, the 200d Below filter offers a good balance of sample size and improved risk metrics.

---

## Implementation Considerations

| Strategy | Signal Frequency | Ret/MDD | Worst MDD | Recommended Use |
|----------|------------------|---------|-----------|-----------------|
| MA_Smoother + 43d Above | Very Rare | 2.75-3.20 | 20% | Aggressive entry timing |
| MA_Smoother + 200d Below | Moderate | 2.18-2.23 | 29% | Core signal filter |
| Pure MA Smoother | Regular | 1.67 | 34% | Base case exposure |

---

*Analysis Date: March 2026*
*Data Period: September 2009 – February 2026*
*Forward Horizon: 252 trading days*
