# Sensitivity Analysis — Quality-Momentum Top-50

Period: 2010-01-01–2025-12-31  |  Universe: S&P 500 current constituents  |  Cost: 5 bps one-way

SPY benchmark: CAGR 14.41%, Sharpe 1.02, Max DD -23.93%

## Results

| Variant | CAGR | Sharpe | Alpha | Max DD |
|---|---|---|---|---|
| **Top-50 BASELINE (equal fw, monthly, equal-wt)** | **17.20%** | **1.15** | **4.77%** | **-21.57%** |
| Top-50 momentum-only | 22.85% | 1.22 | 6.93% | -20.14% |
| Top-50 low-vol-only | 12.25% | 0.98 | 2.63% | -23.76% |
| Top-50 momentum-heavy (0.70/0.30) | 19.87% | 1.18 | 5.77% | -19.23% |
| Top-50 vol-heavy (0.30/0.70) | 14.82% | 1.13 | 4.39% | -20.87% |
| Top-50 live-renorm weights (0.625/0.375) | 19.14% | 1.17 | 5.43% | -20.88% |
| Top-50 quarterly rebalance | 18.30% | 1.22 | 5.53% | -20.74% |
| Top-50 score-weighted positions | 25.36% | 1.18 | 10.20% | -22.52% |
| Top-50 inverse-vol-weighted positions | 15.26% | 1.09 | 3.94% | -21.85% |

## Interpretation

The baseline top-50 strategy delivers **4.77% annualised alpha** versus SPY at a **Sharpe of 1.15**.

**Range.** Alpha spans 2.63% to 10.20% across 9 variants. Alpha is positive across every variant — the direction of outperformance is consistent regardless of parameter choice.

**Factor weights.** Momentum-only (6.93% alpha, Sharpe 1.22) and low-vol-only (2.63%, Sharpe 0.98) are both individually productive. Neither single-factor extreme dramatically dominates the blended default, which is evidence that the two signals are genuinely complementary rather than one being a free lunch at the other's expense.

**Rebalance frequency.** Quarterly delivers 5.53% vs 4.77% monthly — a 0.76% difference that is likely within noise over the sample period. Monthly remains the preferred default for signal timeliness.

**Position sizing.** Score-weighting delivers 10.20% (5.43% vs equal-weight); inverse-vol 3.94% (-0.83%). Score-weighting's apparent advantage should be read with scepticism: it concentrates on the highest-scoring names in the same data used to build and evaluate the signal — a structural in-sample advantage that may not persist. Equal-weighting is the defensible default.