# Quality-Momentum Factor Strategy

> **Live tracking begins June 5, 2026 (first Friday of June).** The `picks/_dry_runs/` folder contains pre-launch test runs used to validate the pipeline.

A systematic long-only equity strategy that screens the S&P 500 using
price momentum, low volatility, and (in live mode) quality / return-on-assets.
Built as a recruiting project with the goal of producing a 12+ month
time-stamped live track record by sophomore year.

---

## Strategy Overview

| Parameter | Value |
|---|---|
| Universe | S&P 500 (current constituents via Wikipedia) |
| Holdings | Top 50 names by composite score |
| Weighting | Equal weight (2% each) |
| Rebalance | Monthly |
| Benchmark | SPY |

### Composite Score

```
Composite = 0.50 × momentum_z + 0.30 × lowvol_z + 0.20 × quality_z
```

| Factor | Definition | Direction |
|---|---|---|
| **Momentum** | 12-1 month total return z-score | Higher = better |
| **Low-vol** | Trailing 12-month annualised vol z-score | Lower = better (inverted) |
| **Quality** | Return on assets (ROA) z-score | Higher = better |

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

| Metric | Gross | Net (5 bps) | SPY |
|---|---|---|---|
| CAGR | 17.60% | 17.20% | 13.91% |
| Volatility (ann.) | 14.82% | 14.82% | 14.06% |
| Sharpe Ratio | 1.18 | 1.15 | 1.00 |
| Max Drawdown | -21.52% | -21.57% | -23.93% |
| Alpha (ann.) | 5.12% | 4.77% | — |
| Beta | 0.88 | 0.88 | — |
| Information Ratio | 0.40 | 0.36 | — |

Charts saved to `results/` after running `python scripts/run_backtest.py`.

### Sensitivity Range (10 variants tested)

Robustness tests across portfolio size (30/50/100), factor weights, rebalance frequency, and position sizing — all net of 5 bps one-way costs:

| Variant | CAGR | Sharpe | Alpha |
|---|---|---|---|
| Score-weighted positions *(in-sample high — treat with caution)* | 25.36% | 1.18 | 10.20% |
| Momentum-only factor weights | 22.85% | 1.22 | 6.93% |
| Quarterly rebalance | 18.30% | 1.22 | 5.53% |
| **Baseline (top-50, monthly, equal-weight)** | **17.20%** | **1.15** | **4.77%** |
| Top-100 portfolio | 16.26% | 1.21 | 4.48% |
| Inverse-vol-weighted positions | 15.26% | 1.09 | 3.94% |
| Low-vol-only factor weights | 12.25% | 0.98 | 2.63% |

Alpha is positive in every variant tested. Full table and interpretation in `results/sensitivity.md`.

---

## Project Structure

```
factor-strategy/
  src/
    universe.py      # S&P 500 constituent loader (Wikipedia → parquet cache)
    data.py          # Price + fundamentals loader with parquet cache
    factors.py       # Factor z-score calculations
    screen.py        # Composite score + top-N selection
    backtest.py      # Vectorized monthly-rebalance backtest engine
    report.py        # Performance analytics and charts
    live.py          # Live pick generation (appends to results/live_picks.csv)
  scripts/
    run_backtest.py  # Entry point: full historical backtest
    run_live.py      # Entry point: generate weekly live picks
  tests/             # pytest test suite
  data/              # Parquet cache (git-ignored)
  results/           # Backtest outputs, charts, live_picks.csv
  reports/           # Monthly write-ups and commentary
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
# Optional flags:
#   --start 2010-01-01
#   --end   2025-12-31
#   --top-n 50
#   --refresh        (force re-download)
```

## Generating Live Picks

```bash
python scripts/run_live.py
# Appends picks to results/live_picks.csv with today's date
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
