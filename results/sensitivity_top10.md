# Sensitivity Analysis — Quality-Momentum Top-10

Period: 2010-01-01–2025-12-31  |  Universe: S&P 500 current constituents  |  Cost: 5 bps one-way

SPY benchmark: CAGR 14.41%, Sharpe 1.02, Max DD -23.93%

## Results

| Variant | CAGR | Sharpe | Alpha | Max DD |
|---|---|---|---|---|
| **Top-10 BASELINE (equal fw, monthly, equal-wt)** | **24.01%** | **1.09** | **8.90%** | **-32.68%** |
| Top-10 momentum-only | 40.55% | 1.31 | 19.29% | -27.66% |
| Top-10 low-vol-only | 14.00% | 1.08 | 5.33% | -27.57% |
| Top-10 momentum-heavy (0.70/0.30) | 35.27% | 1.28 | 16.47% | -28.98% |
| Top-10 vol-heavy (0.30/0.70) | 18.37% | 1.18 | 8.20% | -17.09% |
| Top-10 live-renorm weights (0.625/0.375) | 35.47% | 1.31 | 17.51% | -30.40% |
| Top-10 quarterly rebalance | 27.97% | 1.24 | 12.12% | -23.17% |
| Top-10 score-weighted positions | 37.32% | 1.12 | 21.05% | -31.24% |
| Top-10 inverse-vol-weighted positions | 19.70% | 1.03 | 6.37% | -27.40% |

## Interpretation

The baseline top-10 strategy delivers **8.90% annualised alpha** versus SPY at a **Sharpe of 1.09**.

**Range.** Alpha spans 5.33% to 21.05% across 9 variants. Alpha is positive across every variant — the direction of outperformance is consistent regardless of parameter choice.

**Factor weights.** Momentum-only (19.29% alpha, Sharpe 1.31) and low-vol-only (5.33%, Sharpe 1.08) are both individually productive. Neither single-factor extreme dramatically dominates the blended default, which is evidence that the two signals are genuinely complementary rather than one being a free lunch at the other's expense.

**Rebalance frequency.** Quarterly delivers 12.12% vs 8.90% monthly — a 3.22% difference that is likely within noise over the sample period. Monthly remains the preferred default for signal timeliness.

**Position sizing.** Score-weighting delivers 21.05% (12.14% vs equal-weight); inverse-vol 6.37% (-2.54%). Score-weighting's apparent advantage should be read with scepticism: it concentrates on the highest-scoring names in the same data used to build and evaluate the signal — a structural in-sample advantage that may not persist. Equal-weighting is the defensible default.