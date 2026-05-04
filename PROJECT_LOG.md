# Project Log — Quality-Momentum Factor Strategy

Append-only record of all meaningful changes to this project.
Entries from before this file was created are marked **[reconstructed from git history]**.
Going-forward entries are live timestamps written before each commit.

---

## 2026-05-01 15:07  Initial project scaffold and first live picks  [reconstructed from git history]
- **Files:** (entire project — initial commit)
- **Commit:** `96e555d`
- **Notes:** Quality-momentum factor strategy: top-50 S&P 500, monthly rebalance, equal weight. Backtest 2011–2025 gross: CAGR 17.60%, Sharpe 1.18, alpha +5.12% vs SPY. First live picks run as of 2026-04-30 (50 names, full quality-momentum composite including ROA quality factor). 36 unit tests, all passing.

## 2026-05-01 15:55  Reclassify May 1 picks as dry run, push official launch to June 5  [reconstructed from git history]
- **Files:** `picks/`, `results/`, `README.md`
- **Commit:** `60a09a1`
- **Notes:** Moved 2026-05-01 picks and live_picks.csv into _dry_runs/ subdirectories. README updated to state live tracking begins June 5, 2026.

## 2026-05-01 19:45  Add .gitignore entry for .claude/ session directory  [reconstructed from git history]
- **Files:** `.gitignore`
- **Commit:** `0ce875b`

## 2026-05-03 20:29  Add daily tracker CSV for May 1 dry-run picks  [reconstructed from git history]
- **Files:** `results/dry_run_tracker.csv`, `scripts/track_dry_run.py`
- **Commit:** `9651577`

## 2026-05-03 20:33  Add transaction costs to backtest  [reconstructed from git history]
- **Files:** `src/backtest.py`, `scripts/run_backtest.py`, `results/summary.json`
- **Commit:** `0604730`
- **Notes:** 5 bps one-way (10 bps round-trip) on rebalanced names. Gross CAGR 17.60% → Net CAGR 17.20%; cost drag ~40 bps/yr. BacktestResult now carries both gross_returns and returns (net) fields.

## 2026-05-03 20:38  Add sensitivity analysis across parameter space  [reconstructed from git history]
- **Files:** `scripts/run_sensitivity.py`, `results/sensitivity.md`
- **Commit:** `0b0304b`
- **Notes:** 10 variants tested across portfolio size (30/50/100), factor weights (mom-only, vol-only, 0.5/0.5, 0.625/0.375), rebalance frequency (monthly/quarterly), position sizing (equal/score/inverse-vol). Alpha positive across all variants (2.63%–10.20%). Score-weighting flagged as in-sample overfitting risk.

## 2026-05-03 20:40  Document strategy limitations in README and summary.json  [reconstructed from git history]
- **Files:** `README.md`, `results/summary.json`
- **Commit:** `1cc0806`
- **Notes:** Added Limitations section to README covering survivorship bias, transaction costs, yfinance data quality, and point-in-time fundamentals.

## 2026-05-03 20:41  Add METHODOLOGY.md  [reconstructed from git history]
- **Files:** `METHODOLOGY.md`
- **Commit:** `983c57b`
- **Notes:** Plain-English strategy explanation with academic citations: Jegadeesh-Titman (1993), Frazzini-Pedersen (2014), Novy-Marx (2013). Covers what the backtest proves/doesn't and what would improve with better data.

## 2026-05-03 20:44  Update README with sensitivity range table  [reconstructed from git history]
- **Files:** `README.md`
- **Commit:** `2aeb9cf`
- **Notes:** Shows alpha range (2.63%–10.20%) across 10 variants. Links to sensitivity.md.

## 2026-05-03 23:15  Add PROJECT_LOG.md and reconstruct full git history
- **Files:** `PROJECT_LOG.md`, `scripts/log_change.py`
- **Commit:** `7d54b69`

## 2026-05-03 23:15  Add parallel top-10 monthly strategy alongside top-50 baseline. Backtest net results: top-50 CAGR 17.20% / Sharpe 1.15 / max DD -21.6%; top-10 CAGR 24.01% / Sharpe 1.09 / max DD -32.7%.
- **Files:** `src/strategies.py`, `scripts/run_backtest.py`, `scripts/run_live.py`, `src/report.py`, `METHODOLOGY.md`, `README.md`, `results/summary_top50.json`, `results/summary_top10.json`
- **Commit:** `2830401`
