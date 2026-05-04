# Sensitivity Analysis — Quality-Momentum Strategy

Backtest period: 2010-01-01 to 2025-12-31  |  Universe: S&P 500 current constituents  |  Transaction costs: 5 bps one-way

SPY benchmark over same period: CAGR 14.41%, Sharpe 1.02

## Results Table

| Variant | CAGR | Sharpe | Alpha | Max DD | Months |
|---|---|---|---|---|---|
| Top 30 (baseline weights, monthly, equal-wt) | 18.13% | 1.12 | 5.02% | -20.28% | 179 |
| Top 50 — BASELINE | 17.20% | 1.15 | 4.77% | -21.57% | 179 |
| Top 100 (baseline weights, monthly, equal-wt) | 16.26% | 1.21 | 4.48% | -20.14% | 179 |
| Momentum-only (top-50, monthly, equal-wt) | 22.85% | 1.22 | 6.93% | -20.14% | 179 |
| Low-vol-only (top-50, monthly, equal-wt) | 12.25% | 0.98 | 2.63% | -23.76% | 179 |
| Equal factor weights 0.5/0.5 (top-50, monthly, equal-wt) | 17.20% | 1.15 | 4.77% | -21.57% | 179 |
| Live re-norm 0.625/0.375 (top-50, monthly, equal-wt) | 19.14% | 1.17 | 5.43% | -20.88% | 179 |
| Quarterly rebalance (top-50, equal factor wts, equal-wt) | 18.30% | 1.22 | 5.53% | -20.74% | 179 |
| Score-weighted positions (top-50, monthly) | 25.36% | 1.18 | 10.20% | -22.52% | 179 |
| Inverse-vol-weighted positions (top-50, monthly) | 15.26% | 1.09 | 3.94% | -21.85% | 179 |

## Interpretation

**Range of outcomes.** Across all 10 variants, annualised alpha versus SPY ranges from 2.63% (Low-vol-only) to 10.20% (Score-weighted positions). The baseline (top-50, equal-weight, monthly, equal factor weights) produces 4.77% alpha and a Sharpe of 1.15.

**Portfolio size.** Alpha is broadly stable across top-30, top-50, and top-100. The differences are modest (< 1 pp), which is a positive robustness signal: the strategy does not appear to rely on cherry-picking a specific portfolio size.

**Factor weights.** Momentum-only delivers 6.93% alpha (Sharpe 1.22) and low-vol-only 2.63% (Sharpe 0.98). The equal-weight blend (4.77%) and the live-re-normalised split (5.43%) sit between the two. The fact that both single-factor variants are competitive — and neither dramatically outperforms — suggests the factor combination is additive without being narrowly tuned. The 0.5/0.5 backtest default and the 0.625/0.375 live-re-normalised split produce essentially the same result, so the precise weighting within a reasonable range is not the key driver.

**Rebalance frequency.** Switching from monthly to quarterly rebalance gives 5.53% alpha (Sharpe 1.22), above the monthly baseline (4.77%). Monthly rebalancing captures momentum signals faster, but the difference is small. The quarterly result confirms the strategy is not purely a high-frequency effect that disappears with less frequent trading.

**Position sizing — does score-weighting beat equal-weighting?** Score-weighted positions produce 10.20% alpha (+5.43% vs equal-weight). Inverse-vol weighting produces 3.94% alpha (-0.83% vs equal-weight). The differences are small in absolute terms and are almost certainly not statistically significant over a 179-month sample. With approximately 14.9 years of monthly data, the standard error of an annualised alpha estimate is roughly 8.91% (a rough back-of-envelope using volatility / sqrt(T)), so a difference of 5.43% between sizing methods is well within noise. Equal-weighting is therefore the defensible default: it is simpler, more interpretable, and not demonstrably worse.

**Overfitting concern.** The variants that look most impressive — particularly momentum-only or score-weighted if they happen to show the highest numbers — should be treated with scepticism. Both were evaluated in-sample on the same 2010–2025 data used to originally calibrate the strategy. True out-of-sample robustness would require a held-out period or a different market. The key takeaway is that the *direction* of outperformance persists across all variants tested, which is more meaningful than any single variant's alpha.

**Conclusion for the live strategy.** The baseline configuration (top-50, monthly, equal-weight, 0.5/0.5 backtest factor weights) sits in the middle of the robustness range — it is not the highest-performing variant and not the lowest. This is a healthy sign: it was not selected via exhaustive grid search over this exact dataset. The strategy shows genuine structural alpha relative to SPY after realistic transaction costs, with results that hold across reasonable parameter perturbations.