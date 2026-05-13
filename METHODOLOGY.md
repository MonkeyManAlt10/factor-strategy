# Strategy Methodology

## On Running Two Strategies

This project tracks two portfolios — top-50 and top-10 — but they are not two equally validated strategies. The distinction matters and should be understood before reading any of the numbers below.

**Top-50 is the primary, academically grounded strategy.** It holds 50 names at 2% each. It is the version this project stands behind: it has the better risk-adjusted backtest (Sharpe 1.15 vs SPY's 1.02), the shallower drawdown (-21.6% vs SPY's -23.9%), and the more defensible out-of-sample behavior (Sharpe declines mildly from 1.30 to 0.92 between the training and test periods, with alpha still positive at +2.1%). Live tracking write-ups will focus on this portfolio.

**Top-10 is a concentration experiment, not a validated strategy.** It holds 10 names at 10% each, using the same scoring logic. It is included to answer one specific live question: does extra concentration earn its risk premium? Three properties make it explicitly not a strategy we are recommending:

1. **Worse Sharpe in-sample.** Top-10's higher CAGR (24% vs 17%) does not survive risk-adjustment. Its Sharpe (1.09) is lower than top-50's (1.15). Buying CAGR with extra volatility is the kind of trade that looks attractive in a backtest and disappointing in a drawdown.

2. **Materially worse drawdown.** Top-10's max drawdown of -32.7% is 11 percentage points deeper than top-50's. For a portfolio that is meant to be held through a real cycle, this is not a small difference.

3. **Suspicious out-of-sample behavior.** Top-10's alpha *increased* from the training period (+7.8%) to the test period (+13.6%), and its Sharpe *improved* (1.04 → 1.17). When an out-of-sample test produces *better* results than the in-sample fit, the strongly likely explanation is regime change, not signal robustness. The 2023–2025 test window contains the mega-cap momentum rally, which a 10-name concentrated portfolio is disproportionately exposed to. A different test window — one that included the 2000–2002 tech bust, the 2008 financial crisis, or the early-2022 momentum crash — would very plausibly have produced the opposite result. The honest reading is that top-10 is regime-sensitive in a way that the test period happened to flatter.

The top-10 portfolio is tracked live because the live track record is the only honest test that can resolve the question. It is not promoted to "strategy" status until that test is run, and may never be.

When you see "the strategy" in this document, it refers to top-50 unless otherwise stated. Top-10 numbers are reported for comparison and learning, not as evidence of an edge.

---

## What This Strategy Does and Why

This project implements a systematic, long-only equity strategy that selects stocks from the S&P 500 universe using two quantitative signals: price momentum and low volatility. The strategy scores every stock on both factors each month, ranks them, and holds the top names in an equal-weight portfolio until the next rebalance.

Two portfolio variants are tracked in parallel, and the distinction between them matters:

**Top-50 is the primary strategy.** It holds 50 names at 2% each. This is the version with the stronger academic basis, the better risk-adjusted backtest performance (Sharpe 1.15 vs SPY's 1.02), and the shallower maximum drawdown (-21.6% vs -23.9%). Diversification across 50 names reduces idiosyncratic noise so that the systematic factor signal is the dominant driver of returns. This is the portfolio that will be the focus of live tracking beginning June 5, 2026.

**Top-10 is a concentrated comparison portfolio.** It holds 10 names at 10% each, using the same scoring and rebalance schedule. It is tracked in parallel as a live experiment to test one specific question: does the higher concentration — and the higher in-sample backtest returns that come with it (CAGR 24% vs 17% net of costs) — justify the materially higher drawdown (-32.7% vs -21.6%) and volatility (22% vs 15% annualised)? The honest answer is: we don't know yet. The in-sample numbers suggest it does not on a risk-adjusted basis (Sharpe 1.09 vs 1.15), but in-sample Sharpe comparisons on the same 15-year dataset are not statistically conclusive. The live track record will be the real test.

**Top-10 carries explicit caveats:** It has not been validated out-of-sample in a way that separates genuine concentration alpha from survivorship and selection effects in the 2010–2025 data. Higher position sizing also means transaction costs matter more at scale. It is included as a comparison tool, not as a recommendation. See `results/train_test_validation.md` for the train/test split analysis.

The underlying motivation is straightforward. Academic finance has documented a handful of persistent return premia — patterns in stock returns that appear to compensate investors for bearing risk or exploiting behavioral inefficiencies. This project targets two of the most replicated: the momentum premium and the low-volatility anomaly. A third factor, quality (ROA), is used in the live strategy but excluded from the historical backtest for look-ahead bias reasons explained below.

The goal is not to beat the market every month. It is to construct a disciplined, rules-based process that, on average over long horizons, tilts the portfolio toward characteristics associated with above-benchmark returns, while keeping costs and complexity low enough that the alpha is not consumed by friction.

---

## The Three Factors

### Momentum (weight: 50%)

The momentum effect was documented systematically by Jegadeesh and Titman (1993) in their paper *"Returns to Buying Winners and Selling Losers."* They showed that stocks with strong returns over the past 6 to 12 months tend to continue outperforming over the next 3 to 12 months. This cross-sectional pattern has since been replicated across markets, asset classes, and time periods and is one of the most robust anomalies in empirical asset pricing.

The mechanism is debated. Behavioral explanations point to under-reaction: investors update their views about a company's prospects too slowly in response to earnings surprises or improving fundamentals, and the price continues drifting in the direction of the news. Risk-based explanations argue that momentum strategies have hidden tail risk — they crash sharply when markets reverse suddenly (as in 2009 and 2020), which investors implicitly demand compensation for.

This strategy implements the standard *12-1 month* specification: the momentum signal is the total return from 12 months ago to 1 month ago, skipping the most recent month. The skip is important. At very short horizons (less than one month), price returns *reverse* rather than continue — a pattern known as short-term reversal, likely driven by microstructure effects like bid-ask bounce. Skipping the most recent month removes this noise.

The raw 12-1 return for each stock is converted to a cross-sectional z-score (mean zero, standard deviation one across the universe). This standardizes the signal regardless of the level of the overall market.

### Low Volatility (weight: 30% live / 50% backtest)

The low-volatility anomaly — sometimes called the low-beta anomaly — is the observation that stocks with lower historical volatility tend to *outperform* on a risk-adjusted basis over the long run, and in some periods even on an absolute basis. This contradicts the basic Capital Asset Pricing Model prediction that higher risk should be compensated with higher return.

The most thorough academic treatment is by Asness, Frazzini, and Pedersen (2014) in *"Frazzini-Pedersen: Betting Against Beta"* (Journal of Financial Economics). They argue that many investors face constraints — leverage limits, mandates to stay fully invested, benchmarking pressure — that prevent them from simply using low-risk assets with leverage to hit return targets. These constrained investors instead reach for high-beta stocks, pushing their prices up and future expected returns down. The inverse holds for boring, low-volatility stocks: limited institutional demand means they remain cheap relative to their true risk.

This strategy measures volatility as the annualised standard deviation of monthly returns over the trailing 12 months. The signal is then *inverted* — low volatility receives a high z-score — so that quiet, stable stocks rank well in the composite.

### Quality (weight: 20%, live strategy only)

The quality factor targets stocks with strong fundamentals: high profitability, consistent earnings, low debt, and efficient use of assets. Among the many quality proxies in the literature, return on assets (ROA) is one of the most practical for a data-constrained setup: it is clean, widely reported, and captures core economic profitability without the noise of leverage.

The theoretical basis draws from Novy-Marx (2013), *"The Other Side of Value: The Gross Profitability Premium,"* and the broader literature on fundamental quality investing. The intuition is that highly profitable companies tend to reinvest at better rates, compound capital more efficiently, and are less likely to require dilutive financing or face distress. These advantages can persist for several years before competition erodes them.

**Why quality is excluded from the backtest.** The free financial data available from Yahoo Finance (`yfinance`) returns the *most recent* balance sheet values — not the values that would have been publicly available at each past rebalance date. Using today's ROA as an input to a 2015 backtest rebalance would give the strategy information that was not available at the time, inflating historical returns. This is called look-ahead bias and it is one of the most common and most damaging errors in systematic strategy research. Rather than accept a biased backtest, this project excludes quality entirely from the historical simulation. The backtest re-normalizes the remaining momentum and low-vol weights to sum to 1.

---

## The Quality Factor Caveat

This deserves to be stated as plainly as possible, because it has direct implications for how the backtest numbers should be read:

**The backtest does not represent the strategy that is being run live.**

- The **backtest** (2010–2025) uses two factors: momentum (50%) and low-vol (50%).
- The **live strategy** (June 2026 onward) uses three factors: momentum (50%), low-vol (30%), and quality / ROA (20%).

These are not the same composite. They cannot be. Quality requires point-in-time fundamental data, and `yfinance` only returns the *current* values of those fundamentals. Putting today's ROA at a 2015 rebalance date is the textbook look-ahead bias error, and the resulting backtest numbers would be meaningfully inflated. The honest choice is to leave quality out of the historical simulation entirely, and to be explicit that the live strategy is therefore an unbacktested variant.

A few practical points worth being clear about:

1. **The live strategy has never been backtested in its exact live form.** The closest the backtest gets is the price-only momentum + low-vol composite, with weights re-normalised over the two factors that are available. The live composite — momentum 50%, low-vol 30%, quality 20% — has no historical performance record on this dataset.

2. **Quality is the smallest of the three live weights, so its effect on rankings is probably modest.** A 20% weight means the quality z-score has roughly the same influence as a 20% shift in either of the other two factors. It will tilt the live portfolio toward more profitable names at the margin but will not radically change the composition. In practice, on the most recent live picks, the top-10 names that come out of the price-only composite and the full live composite tend to overlap substantially.

3. **This is a constraint, not a design choice.** A proper institutional version of this strategy would use a point-in-time fundamentals dataset (Compustat, FactSet, Bloomberg) and would include quality in the backtest alongside the live strategy. The split between a two-factor backtest and a three-factor live strategy is forced by the free-data limitation. If point-in-time data became available, the two would be reconciled.

4. **The honest interpretation:** the backtest provides evidence that *the price-only composite* (momentum + low-vol) has produced positive alpha historically on this universe and dataset. The live strategy adds a third signal that the literature suggests is also productive but that this project cannot independently validate with this data. Whether the live three-factor version outperforms or underperforms the two-factor backtest version is genuinely unknown until the live track record is in.

---

## Why These Weights?

The weights — 50% momentum, 30% low-vol, 20% quality — are informed by the factor literature but are, in the end, somewhat arbitrary. A few considerations:

**Momentum is given the most weight** because it is the strongest single factor in the backtest. The sensitivity analysis in `results/sensitivity_top50.md` shows that momentum-only delivers approximately 6.9% annualised alpha versus SPY over 2010–2025, compared with 2.6% for low-vol-only. Giving momentum the largest share reflects this empirical signal.

**Low-vol is given a meaningful allocation** because it provides diversification within the factor portfolio. Momentum strategies are known to crash during sharp market reversals — the low-vol factor tends to hold up better in those environments because the underlying stocks are less sensitive to broad market moves. Blending the two reduces the worst-case drawdown relative to pure momentum.

**Quality receives the smallest allocation** partly because it cannot be tested in the backtest (for the look-ahead reasons above) and partly because quality tends to be a slower-moving, lower-turnover signal. Adding it in live mode is a judgment call: the academic literature supports it, and it provides an additional dimension of stock selection that is orthogonal to price-based signals.

These weights have not been optimised through a grid search over the backtest period. Doing so would introduce overfitting — the optimal in-sample weights are almost never the best out-of-sample weights. The sensitivity analysis confirms that modest changes to the weights (including equal-weighting, or eliminating one factor entirely) produce broadly similar results, which is the right property to have.

---

## Why Monthly Rebalance?

Monthly rebalancing is the standard for a momentum-oriented strategy. Momentum signals decay — the predictive power of the 12-1 return weakens after 3 to 12 months and reverses at longer horizons. Rebalancing monthly ensures the portfolio stays aligned with the current signal without excessive trading.

The sensitivity analysis shows that quarterly rebalancing delivers comparable alpha (5.5% vs 4.8% in the backtest). The difference is small and within sampling noise. Monthly is preferred because it stays closer to the signal horizon and because the transaction cost difference is modest for an equal-weight S&P 500 portfolio.

Daily or weekly rebalancing would not be appropriate for this strategy: momentum is a medium-frequency signal, and higher-frequency rebalancing would sharply increase turnover and costs without improving the signal.

---

## Why Top 50? Why Equal Weight?

**Portfolio size.** The sensitivity analysis tests top-30, top-50, and top-100. The differences in alpha are small — roughly 0.5 percentage points — suggesting the exact cutoff is not the key driver. Top-50 is a middle ground: concentrated enough to capture the strongest signal, diversified enough to avoid single-stock idiosyncratic risk dominating the portfolio.

**Equal weight.** Equal weighting is the simplest, most transparent weighting scheme. The sensitivity analysis tests score-weighted and inverse-volatility-weighted alternatives. Score-weighting shows higher in-sample alpha (10.2% vs 4.8%), but this result should be treated with scepticism: it concentrates the portfolio in the very highest-scoring stocks, which may reflect in-sample overfitting. The difference is not statistically significant over a 15-year sample, and equal-weighting is the more defensible default because it avoids introducing a secondary optimisation layer that could overfit to the same data used to build the signal.

---

## What the Backtest Proves (and Doesn't)

**What it shows.** The backtest provides evidence that, over the 2010–2025 period on current S&P 500 constituents, a rules-based strategy selecting high-momentum, low-volatility stocks delivered approximately 17.2% annualised returns (net of transaction costs), compared with 13.9% for SPY. The strategy had lower maximum drawdown (-21.6% vs -23.9%), a higher Sharpe ratio (1.15 vs 1.00), and positive alpha across every reasonable variation tested.

**What it doesn't prove.** The backtest cannot tell you what will happen going forward. Specifically:

- It overstates true historical performance due to survivorship bias. The degree of overstatement is hard to quantify without point-in-time data, but academic literature suggests survivorship bias in S&P 500 backtests is typically 1–3 percentage points per year.
- It does not include the quality factor in any form, because doing so honestly is impossible with free data. The live strategy includes quality; the backtest does not. Whether the live composite score outperforms or underperforms the two-factor backtest version is unknown.
- The 2010–2025 period was exceptionally favorable for momentum strategies. The U.S. equity market experienced a long, relatively smooth bull market punctuated by sharp but brief crashes (2020 COVID). Strategies that would have fared very differently — for example, a value-heavy strategy — might look poor in this period for reasons that say nothing about the next 15 years.
- All parameter choices (weights, portfolio size, lookback windows) were evaluated on the same data used to report results. Even without explicit optimisation, knowing that a reasonable-sounding configuration produced these results means there is an implicit selection effect at work.

---

## What Would Change With Better Data

A proper institutional-grade version of this strategy would differ in several important ways:

1. **Point-in-time fundamentals** from a commercial data provider (Compustat, FactSet, Bloomberg) would allow quality to be included in the backtest without look-ahead bias, and would produce a cleaner estimate of its contribution.

2. **Point-in-time index membership** (from Compustat or the Center for Research in Security Prices, CRSP) would eliminate survivorship bias. The universe at each rebalance date would reflect only the stocks that were actually in the S&P 500 at that time.

3. **Higher-quality price data** with independently verified corporate action adjustments would reduce the risk of pricing errors contaminating the momentum signal.

4. **Longer history** — ideally back to the 1960s or 1970s — would provide more statistical power to estimate true factor premia and would cover multiple full market cycles, including the 1970s inflation shock, the 1987 crash, the 2000–2002 tech bust, and the 2008 financial crisis.

5. **More granular transaction cost modelling** using actual bid-ask spreads and volume data would produce a more realistic net-of-cost return estimate, particularly for smaller-cap holdings near the bottom of the selection threshold.

None of these limitations make the current backtest misleading — they simply mean it should be read as directional evidence rather than a precise forecast of live performance.

---

## Summary

This strategy is a disciplined, evidence-based implementation of two of the most replicated factor premia in academic finance. The factor choices, weights, and construction details are grounded in published literature and informed by the sensitivity analysis in this repository. The backtest is intentionally conservative: it applies realistic transaction costs, excludes the quality factor to avoid look-ahead bias, and clearly documents its limitations. The robustness of positive alpha across all 10 parameter variants tested is the most meaningful finding — it suggests the outperformance is not an artifact of one particular parameter choice.

The live strategy, beginning June 5, 2026, will provide an out-of-sample test under real market conditions with a time-stamped, publicly auditable record.

---

*References*

- Jegadeesh, N. and Titman, S. (1993). "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency." *Journal of Finance*, 48(1), 65–91.
- Frazzini, A. and Pedersen, L.H. (2014). "Betting Against Beta." *Journal of Financial Economics*, 111(1), 1–23.
- Asness, C.S., Frazzini, A., and Pedersen, L.H. (2019). "Quality Minus Junk." *Review of Accounting Studies*, 24(1), 34–112.
- Novy-Marx, R. (2013). "The Other Side of Value: The Gross Profitability Premium." *Journal of Financial Economics*, 108(1), 1–28.
