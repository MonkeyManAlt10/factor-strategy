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

*Pending first run.*

Results will appear here after `python scripts/run_backtest.py` is executed.
Charts are saved to `results/`.

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
- **No transaction costs** are modelled in the backtest.  Turnover is roughly
  20–40% per month; in practice, slippage would reduce live returns.
- **Survivorship bias**: the universe uses *current* S&P 500 constituents.
  Historical backtests therefore have mild survivorship bias (excludes companies
  that were removed from the index).  This is disclosed, not corrected.

---

## Live Track Record

Picks start June 2026.  All picks are appended to `results/live_picks.csv`
with a timestamp at the time of calculation, creating an auditable record.

---

## Disclaimer

This project is for educational and recruiting purposes only.  Nothing here
constitutes investment advice.
