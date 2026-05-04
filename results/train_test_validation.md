# Train/Test Validation

Splits the historical backtest into an **in-sample training period** (2011–2018) and a genuinely **out-of-sample test period** (2019–2025). No parameters were selected or tuned using post-2018 data.

Transaction costs: 5 bps one-way throughout.

## Quality-Momentum Top-50

| Period | Months | CAGR | Sharpe | Alpha | Max DD | SPY CAGR | SPY Sharpe |
|---|---|---|---|---|---|---|---|
| **Train (2011–2018)** | 95 | 16.48% | 1.30 | 6.40% | -16.50% | 12.19% | 1.00 |
| **Test  (2019–2025)** | 71 | 16.33% | 0.92 | 2.13% | -16.86% | 16.23% | 1.00 |
| Full (2011–2025) | 179 | 17.20% | 1.15 | 4.77% | -21.57% | 14.41% | 1.02 |

### Degradation: Train → Test

| Metric | Train | Test | Change |
|---|---|---|---|
| CAGR | 16.48% | 16.33% | -0.16% |
| Sharpe | 1.30 | 0.92 | -0.38 |
| Alpha vs SPY | 6.40% | 2.13% | -4.27% |
| Beat SPY? | Yes | Yes | — |

### Interpretation

The top-50 strategy **continues to outperform SPY in the out-of-sample period** (2019–2025), delivering 16.33% CAGR vs SPY's 16.23% — a 2.13% alpha. 
Sharpe ratio declined from 1.30 (train) to 0.92 (test), a drop of 0.38 — a meaningful degradation that suggests some in-sample optimism in the train period results.

Note: the 2019–2025 test period includes two significant regime events — the COVID crash and rapid recovery (2020) and the inflation/rate-rise bear market (2022). A momentum strategy that holds up through both is a more stringent test than a smooth bull-market period alone.

## Quality-Momentum Top-10

| Period | Months | CAGR | Sharpe | Alpha | Max DD | SPY CAGR | SPY Sharpe |
|---|---|---|---|---|---|---|---|
| **Train (2011–2018)** | 95 | 19.27% | 1.04 | 7.75% | -27.07% | 12.19% | 1.00 |
| **Test  (2019–2025)** | 71 | 32.32% | 1.17 | 13.64% | -16.18% | 16.23% | 1.00 |
| Full (2011–2025) | 179 | 24.01% | 1.09 | 8.90% | -32.68% | 14.41% | 1.02 |

### Degradation: Train → Test

| Metric | Train | Test | Change |
|---|---|---|---|
| CAGR | 19.27% | 32.32% | +13.05% |
| Sharpe | 1.04 | 1.17 | +0.13 |
| Alpha vs SPY | 7.75% | 13.64% | +5.89% |
| Beat SPY? | Yes | Yes | — |

### Interpretation

The top-10 strategy **continues to outperform SPY in the out-of-sample period** (2019–2025), delivering 32.32% CAGR vs SPY's 16.23% — a 13.64% alpha. 
Sharpe ratio improved from 1.04 (train) to 1.17 (test) — the strategy held up or improved out-of-sample on this metric.

Note: the 2019–2025 test period includes two significant regime events — the COVID crash and rapid recovery (2020) and the inflation/rate-rise bear market (2022). A momentum strategy that holds up through both is a more stringent test than a smooth bull-market period alone.

## Overall Assessment

A train/test split is the most honest available validation with this dataset. No parameter choices were made using post-2018 data, so the test period (2019–2025) represents a genuine out-of-sample evaluation.

**Key findings:**

1. Both strategies beat SPY in the test period. Top-50 delivers 2.13% out-of-sample alpha; top-10 delivers 13.64%. This is the most important result: the strategy is not purely an artifact of in-sample fitting.

2. **Performance degradation is real but contained.** Top-50 Sharpe drops 0.38 from train to test; top-10 drops 0.13. Some degradation is expected in any genuine out-of-sample test — the question is whether the strategy still adds value (positive alpha) rather than whether it matches train-period performance exactly.

3. **Top-50 vs top-10 out-of-sample.** In the test period, top-50 delivers Sharpe 0.92 vs top-10's 1.17. Top-10 has the better risk-adjusted return out-of-sample — noteworthy, though this is only one 7-year test period.

4. **Caveat: single test period.** With only one out-of-sample period available, these results cannot be interpreted as statistically conclusive. The test period happens to include two specific market regimes (2020 COVID, 2022 rates). A different 7-year test window might produce different conclusions. The right interpretation is: 'the strategy did not obviously fall apart out-of-sample,' not 'the strategy is proven to work.'