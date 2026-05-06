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

## 2026-05-03 23:57  Phase 1: sensitivity tests for top-50 and top-10 (run_sensitivity.py), train/test validation (run_train_test.py), updated README and METHODOLOGY.md with dual-strategy framing and OOS results; Phase 2: remove stale single-strategy result files
- **Files:** `scripts/run_sensitivity.py`, `scripts/run_train_test.py`, `results/sensitivity_top50.md`, `results/sensitivity_top10.md`, `results/train_test_validation.md`, `METHODOLOGY.md`, `README.md`
- **Commit:** (uncommitted)

## 2026-05-04 00:30  Phase 3: Add Streamlit dashboard for live tracking and project review
- **Files:** `dashboard/app.py`, `launch_dashboard.bat`, `requirements.txt`
- **Commit:** `1795725`
- **Notes:** 5-tab Streamlit dashboard (Overview, Top-50, Top-10, Performance Comparison, Project Log). Double-click launch_dashboard.bat to open in browser. Tabs show live portfolio P&L from picks files, backtest summary stats, interactive Plotly cumulative return charts, and PROJECT_LOG entries most-recent-first.

## 2026-05-04 00:33  Phase 4: End-to-end verification -- fix live.py EmptyDataError, generate May 2026 picks for both strategies, confirm 36 tests passing
- **Files:** `src/live.py`, `picks/top50/2026-05-04.md`, `picks/top10/2026-05-04.md`, `results/live_picks.csv`
- **Commit:** `6ce6b08`
- **Notes:** Fixed EmptyDataError when live_picks.csv was empty (added try/except around pd.read_csv). Force-refreshed price cache to populate 2026 data (previous cache had NaN rows for Jan-Apr 2026). Top-50 picks: 50 names as of 2026-04-30 (SNDK #1, NVDA #4). Top-10 picks: same top 10. 36/36 tests passing. Dashboard installs and loads cleanly.

## 2026-05-04  Fix UTF-8 encoding bug in picks file reading and writing
- **Files:** `scripts/run_live.py`, `tests/test_picks_encoding.py`, `picks/top50/2026-05-04.md`, `picks/top10/2026-05-04.md`, `picks/_dry_runs/2026-05-01.md`
- **Commit:** `1b27b13`
- **Notes:** run_live.py now writes with encoding="utf-8" and replaces em-dash with ASCII dash in title line. All existing picks files re-encoded as UTF-8. Added 3-test test_picks_encoding.py (all passing). 39/39 tests passing.

## 2026-05-04  Redesign dashboard: dark theme, professional UI, monthly history dropdown
- **Files:** `dashboard/app.py`, `.streamlit/config.toml`
- **Commit:** (uncommitted)
- **Notes:** Dark theme via config.toml (navy/blue). CSS injection hides streamlit chrome, adds persistent header bar (strategy name + Austin Krauskopf attribution), tighter spacing, styled metric cards. Plotly charts use plotly_dark template with consistent color palette (blue/amber/gray). Portfolio tabs: 4-col metrics row, 2-col picks+stats layout, position P&L table with green/red coloring. Monthly dropdown (Task 3): select any historical month, shows picks + P&L for that period, "Compare to other strategy" toggle. read_text_safe() helper handles UTF-8/CP1252/latin-1 fallback.

## 2026-05-05  Stripe/Linear-inspired full visual redesign of dashboard
- **Files:** `dashboard/app.py`, `.streamlit/config.toml`, `requirements.txt`
- **Commit:** (uncommitted)
- **Notes:** Complete visual overhaul. Design system constants (BG_PRIMARY #0a0e1a, BG_SECONDARY #111827, ACCENT #3b82f6 etc.) defined at top of app.py. Single comprehensive CSS block injects Inter + JetBrains Mono from Google Fonts, hides all Streamlit chrome, styles tabs as Linear-style top nav (2px blue active indicator, no default underline), custom metric cards via render_metric() helper (28px JetBrains Mono values, uppercase labels, colored deltas), custom scrollbar, 200ms fade-in animation on tab content. Sidebar navigation replaced with st.tabs(). Top bar HTML shows brand logo + "factor-strategy" in JetBrains Mono with pulsing status dot and timestamp. style_chart() helper applies factor_dark design to all Plotly figures (transparent bg, horizontal grid only, JetBrains Mono tick labels, bottom legend, dark hover tooltips). Cumulative return charts have 8% opacity area fill; new interactive drawdown chart added with soft red fill. Overview tab gets hero section, 4-column headline metrics, 60/40 chart+stats layout, countdown card. Portfolio tabs get status badges (DRY RUN / LIVE / HISTORICAL), composite score histogram in right panel, full-width refresh button. Project Log renders as HTML timeline with commit badges and file chips. Added streamlit-extras to requirements.txt. config.toml secondaryBackgroundColor updated to #111827. Limitation noted: sector breakdown chart omitted (fundamentals.parquet has no sector column; only ROA/ROE/margins). 39/39 tests still passing.
