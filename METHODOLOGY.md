# Strategy Methodology

## What This Strategy Does and Why

This project implements a systematic, long-only equity strategy that selects stocks from the S&P 500 universe using two quantitative signals: price momentum and low volatility. Once a month, the strategy scores every stock on those two factors, ranks them from best to worst, and holds the top 50 in an equal-weight portfolio until the next rebalance.

The motivation is straightforward. Academic finance has documented a handful of persistent return premia — patterns in stock returns that appear to compensate investors for bearing risk or exploiting behavioral inefficiencies. This strategy targets two of the most replicated: the momentum premium and the low-volatility anomaly. A third factor, quality, is used in the live strategy but excluded from the historical backtest for reasons explained below.

The goal is not to beat the market every month. It is to construct a process that, on average and over long horizons, tilts the portfolio toward characteristics that have historically been associated with above-benchmark returns, while keeping costs and complexity low enough that the alpha is not consumed by friction.

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

## Why These Weights?

The weights — 50% momentum, 30% low-vol, 20% quality — are informed by the factor literature but are, in the end, somewhat arbitrary. A few considerations:

**Momentum is given the most weight** because it is the strongest single factor in the backtest. The sensitivity analysis in `results/sensitivity.md` shows that momentum-only delivers approximately 6.9% annualised alpha versus SPY over 2010–2025, compared with 2.6% for low-vol-only. Giving momentum the largest share reflects this empirical signal.

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
