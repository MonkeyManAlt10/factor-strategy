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
- **Commit:** `c3d30bb`

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

## 2026-05-04  Redesign dashboard: dark theme, professional UI
- **Files:** `dashboard/app.py`, `.streamlit/config.toml`
- **Commit:** `1403229`
- **Notes:** Dark theme via config.toml (navy/blue). CSS injection hides streamlit chrome, adds persistent header bar (strategy name + Austin Krauskopf attribution), tighter spacing, styled metric cards. Plotly charts use plotly_dark template with consistent color palette (blue/amber/gray). Portfolio tabs: 4-col metrics row, 2-col picks+stats layout, position P&L table with green/red coloring. read_text_safe() helper handles UTF-8/CP1252/latin-1 fallback.

## 2026-05-04  Add monthly dropdown for historical picks view and full dashboard rewrite
- **Files:** `dashboard/app.py`
- **Commit:** `5605f3c`
- **Notes:** Monthly dropdown: select any historical month, shows picks + P&L for that period, "Compare to other strategy" toggle.

## 2026-05-05  Add Stripe/Linear-inspired design system to dashboard
- **Files:** `dashboard/app.py`, `.streamlit/config.toml`, `requirements.txt`
- **Commit:** `e775104`
- **Notes:** Design system constants (BG_PRIMARY #0a0e1a, BG_SECONDARY #111827, ACCENT #3b82f6, etc.) defined at top of app.py. Comprehensive CSS block injects Inter + JetBrains Mono from Google Fonts, hides Streamlit chrome, styles tabs as Linear-style top nav (2px blue active indicator), custom scrollbar, 200ms fade-in on tab content. Sidebar replaced with st.tabs(). Top bar HTML shows brand logo + "factor-strategy" in JetBrains Mono with pulsing status dot and timestamp. config.toml secondaryBackgroundColor updated to #111827.

## 2026-05-05  Replace metric and table components with custom polished versions
- **Files:** `dashboard/app.py`
- **Commit:** `a1957f8`
- **Notes:** Custom render_metric() HTML helper (28px JetBrains Mono values, uppercase labels, colored deltas). Portfolio tabs get status badges (DRY RUN / LIVE / HISTORICAL), composite score histogram in right panel, full-width refresh button. Project Log renders as HTML timeline with commit badges and file chips.

## 2026-05-05  Apply custom plotly template across all dashboard charts
- **Files:** `dashboard/app.py`
- **Commit:** `9e4ba21`
- **Notes:** style_chart() helper applies factor_dark design to all Plotly figures (transparent bg, horizontal grid only, JetBrains Mono tick labels, bottom legend, dark hover tooltips). Cumulative return charts get 8% opacity area fill; interactive drawdown chart with soft red fill. 39/39 tests still passing.

## 2026-05-12  Run comprehensive project audit
- **Files:** `PROJECT_AUDIT_2026-05-12.md`
- **Commit:** (uncommitted — local artifact, not tracked)
- **Notes:** Read-only audit of repo state, code, strategy results, docs, dashboard, infrastructure, and June 5 launch gaps. 39 tests passing; strategy work solid; biggest gaps are operational (no scheduled job, no deploy, no live tracker).

## 2026-05-12 18:52  Add honest framing for top-10 across docs and dashboard
- **Files:** `README.md`, `METHODOLOGY.md`, `dashboard/app.py`
- **Commit:** `0c2061e`
- **Notes:** Top-10 reframed as a concentrated *comparison* portfolio, not a validated strategy. OOS alpha increasing from 7.8% (train) to 13.6% (test) flagged as regime artifact from the 2023–2025 mega-cap rally. New METHODOLOGY section "On Running Two Strategies"; README result tables split into Primary / Comparison; dashboard top-10 tab gets prominent amber EXPERIMENTAL banner; Overview comparison table relabelled "Top-50 · Primary" / "Top-10 · Comparison (Experimental)".

## 2026-05-12 18:52  Document quality factor backtest/live divergence in methodology
- **Files:** `METHODOLOGY.md`, `README.md`
- **Commit:** `2386500`
- **Notes:** Plainly state that the backtest does not represent the strategy being run live: backtest uses momentum + low-vol only; live adds quality (ROA) at 20%. New METHODOLOGY section "The Quality Factor Caveat" makes this explicit. README limitations section promotes point-in-time fundamentals to limitation #1 and expands the plain-English explanation.

## 2026-05-12  Address minor findings from project audit
- **Files:** `README.md`, `requirements.txt`, `picks/_dry_runs/2026-05-01.md`, `picks/top10/`, `picks/top50/`, `PROJECT_LOG.md`
- **Commit:** (this entry)
- **Notes:** Fixed README test count (36 → 39); fixed README `summary.json` reference to `summary_top50.json` / `summary_top10.json`; removed unused deps `scipy` and `streamlit-extras` from requirements.txt; removed three byte-identical duplicate daily picks files (2026-05-05, 2026-05-06 in both top10/ and top50/) — only the May 4 monthly composite remains; cleaned mojibake `â€"` → `-` in `picks/_dry_runs/2026-05-01.md`; backfilled stale "(uncommitted)" markers in earlier PROJECT_LOG entries with their actual commit hashes (`c3d30bb`, `1403229`, `5605f3c`, `e775104`, `a1957f8`, `9e4ba21`).
