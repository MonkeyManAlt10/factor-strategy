# Quality-Momentum Factor Strategy

> **Live tracking begins June 5, 2026 (first Friday of June).** The `picks/_dry_runs/` folder contains pre-launch test runs used to validate the pipeline.

A systematic long-only equity strategy that screens the S&P 500 using
price momentum, low volatility, and (in live mode) quality / return-on-assets.
Built as a recruiting project with the goal of producing a 12+ month
time-stamped live track record by sophomore year.

---

## Strategies

Two strategies are tracked in parallel as a live comparison experiment.

| | **Top-50 (primary)** | **Top-10 (concentrated)** |
|---|---|---|
| Holdings | Top-50 names | Top-10 names |
| Weighting | Equal weight (2%) | Equal weight (10%) |
| Rebalance | Monthly | Monthly |
| Factors | Same composite | Same composite |
| Status | Primary strategy | Concentrated comparison |

> **Top-10 disclosure:** The concentrated portfolio is included as a parallel experiment to compare live performance. It has not been validated out-of-sample. Higher concentration implies higher volatility and drawdown. Do not treat the top-10 backtest result as evidence that it outperforms top-50; in-sample CAGR differences are expected due to size effects and will be tested going forward.

### Composite Score

```
Composite = 0.50 × momentum_z + 0.50 × lowvol_z  (backtest, price-only)
Composite = 0.50 × momentum_z + 0.30 × lowvol_z + 0.20 × quality_z  (live)
```

| Factor | Definition | Direction |
|---|---|---|
| **Momentum** | 12-1 month total return z-score | Higher = better |
| **Low-vol** | Trailing 12-month annualised vol z-score | Lower = better (inverted) |
| **Quality** | Return on assets (ROA) z-score — live only | Higher = better |

---

## Important Data Caveat: Point-in-Time Fundamentals

**yfinance returns current fundamental values (ROA, margins, etc.) — not
historical point-in-time values.**

Using today's ROA at past rebalance dates would introduce look-ahead bias into
the backtest, inflating historical performance.

To keep the backtest honest:

- **Backtest (2010–2025):** uses **price-derived factors only** (momentum + low-vol,
  re-weighted to sum to 1).  No quality factor.
- **Live strategy (June 2026 onward):** uses the **full composite** including ROA,
  because picks are recorded in real time and there is no look-ahead risk.

This limitation is documented in `src/data.py` and `src/factors.py`.

---

## Backtest Results

Backtest period: January 2010 – December 2025 (179 monthly observations).  
Universe: 503 current S&P 500 constituents.  Transaction costs: 5 bps one-way.

*Results below are updated after each backtest run. See `results/summary_top50.json` and `results/summary_top10.json` for full details.*

| Metric | Top-50 (net) | Top-10 (net) | SPY |
|---|---|---|---|
| CAGR | 17.20% | 24.01% | 14.41% |
| Volatility (ann.) | 14.82% | 22.06% | 14.32% |
| Sharpe Ratio | 1.15 | 1.09 | 1.02 |
| Max Drawdown | -21.57% | -32.68% | -23.93% |
| Alpha (ann.) | 4.77% | 8.90% | — |
| Beta | 0.88 | 1.10 | — |
| Information Ratio | 0.36 | 0.63 | — |

> **Top-10 disclaimer:** Higher CAGR comes with materially higher drawdown (-32.7% vs -21.6%) and vol (22% vs 15%). The top-10 is an in-sample result; its outperformance has not been validated out-of-sample.

Charts saved to `results/` after running `python scripts/run_backtest.py`.

### Sensitivity and Validation

Robustness tests across factor weights, rebalance frequency, and position sizing — all net of 5 bps one-way costs. Full tables: [`results/sensitivity_top50.md`](results/sensitivity_top50.md) and [`results/sensitivity_top10.md`](results/sensitivity_top10.md).

Alpha is positive in every variant tested for both strategies, across all parameter perturbations — the direction of outperformance is structurally robust.

### Train/Test Out-of-Sample Validation

| | Train 2011–2018 | Test 2019–2025 |
|---|---|---|
| **Top-50 CAGR** | 16.5% | 16.3% |
| **Top-50 Sharpe** | 1.30 | 0.92 |
| **Top-50 Alpha** | 6.4% | 2.1% |
| **Top-10 CAGR** | 19.3% | 32.3% |
| **Top-10 Sharpe** | 1.04 | 1.17 |
| **Top-10 Alpha** | 7.8% | 13.6% |
| SPY CAGR (reference) | ~14% | ~17% |

Top-50 shows mild Sharpe degradation (1.30 → 0.92) but retains positive out-of-sample alpha (+2.1%). Top-10's test outperformance reflects the mega-cap momentum period (NVDA, META, etc. in 2023–2025) — strong but concentrated in one regime. Full analysis: [`results/train_test_validation.md`](results/train_test_validation.md).

---

## Project Structure

```
factor-strategy/
  src/
    universe.py        # S&P 500 constituent loader (Wikipedia → parquet cache)
    data.py            # Price + fundamentals loader with parquet cache
    factors.py         # Factor z-score calculations
    screen.py          # Composite score + top-N selection
    backtest.py        # Vectorized monthly-rebalance backtest engine
    report.py          # Performance analytics and charts
    live.py            # Live pick generation
    strategies.py      # Strategy config registry (top-50, top-10)
  scripts/
    run_backtest.py    # Run both strategies, save summary_top50.json + summary_top10.json
    run_live.py        # Generate picks for both strategies → picks/top50/ picks/top10/
    run_sensitivity.py # Robustness tests across parameter space → sensitivity_top50/top10.md
    run_train_test.py  # Train/test out-of-sample split → train_test_validation.md
    log_change.py      # Append timestamped entry to PROJECT_LOG.md
  dashboard/
    app.py             # Streamlit dashboard (launch via launch_dashboard.bat)
  tests/               # pytest test suite (36 tests)
  data/                # Parquet cache (git-ignored)
  results/             # Backtest outputs, charts, validation reports
  picks/               # Time-stamped live picks (top50/ top10/ _dry_runs/)
  reports/             # Monthly write-ups and commentary
  PROJECT_LOG.md       # Append-only change log
  METHODOLOGY.md       # Plain-English strategy explanation (recruiter-facing)
```

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Running the Backtest

```bash
python scripts/run_backtest.py
# Runs top-50 and top-10 in one pass.
# Saves results/summary_top50.json and results/summary_top10.json.
# Optional flags:
#   --start 2010-01-01
#   --end   2025-12-31
#   --refresh        (force re-download)
```

## Generating Live Picks

```bash
python scripts/run_live.py
# Generates picks for both strategies.
# Saves to picks/top50/YYYY-MM-DD.md and picks/top10/YYYY-MM-DD.md.
```

## Running Tests

```bash
pytest tests/ -v
```

---

## Methodology Notes

- **Momentum** skips the most recent month (12-1) to avoid short-term reversal.
- **Low-vol** uses annualised monthly return standard deviation, then inverts
  so that quieter stocks score higher.
- **Transaction costs** are modelled at 5 bps one-way (10 bps round-trip) on
  rebalanced names.  Cost drag is approximately 40 bps per year given typical
  monthly turnover.  See `results/summary.json` for gross and net figures.
- **Survivorship bias**: the universe uses *current* S&P 500 constituents.
  Historical backtests therefore have mild survivorship bias (excludes companies
  that were removed from the index).  This is disclosed, not corrected.

---

## Limitations

A candid assessment of what this backtest does and does not prove:

### 1. Survivorship Bias
The universe is built from the *current* S&P 500 constituent list (sourced from Wikipedia). Companies that were delisted, went bankrupt, were acquired, or were removed from the index between 2010 and 2025 are absent from the backtest entirely. This is a well-known source of upward bias in historical performance: survivors are, by definition, companies that did well enough to remain in the index. The true gross alpha is likely lower than the 5.12% reported. This is standard for most public backtests using freely available data; correcting it requires a point-in-time index membership database (e.g., from Compustat or a data vendor).

### 2. Transaction Costs
The 5 bps one-way (10 bps round-trip) assumption is conservative for large-cap S&P 500 names but does not capture market impact for larger position sizes, bid-ask spread variation during stress periods, or short-term price impact from the buy/sell itself. A real institutional strategy would also incur borrow costs for any hedging and potentially higher slippage during low-liquidity periods.

### 3. yfinance Data Quality
All prices are sourced from Yahoo Finance via `yfinance`. The data is adjusted for splits and dividends using Yahoo's corporate action records, which occasionally contain errors (dividend adjustment reversals, incorrect split factors). No independent data validation or cross-referencing against a commercial data provider was performed. A small number of tickers may have stale or missing price observations that affect their factor scores.

### 4. Point-in-Time Fundamentals
The quality factor (return on assets) uses `yfinance` data that returns current balance sheet figures rather than the values that would have been available at each historical rebalance date. Reporting lags, restatements, and the look-ahead embedded in current fundamental data mean the quality factor cannot be included in the backtest without inflating historical performance. The backtest uses only momentum and low-vol (price-derived factors) for this reason. The live strategy uses current ROA in real time, where there is no look-ahead risk, but the backtest cannot fully replicate the live composite score.

---

## Live Track Record

Picks start June 2026.  All picks are appended to `results/live_picks.csv`
with a timestamp at the time of calculation, creating an auditable record.

---

## Disclaimer

This project is for educational and recruiting purposes only.  Nothing here
constitutes investment advice.
