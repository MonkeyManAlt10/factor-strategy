"""
dashboard/app.py -- Streamlit dashboard for the Quality-Momentum Factor Strategy.

Launch: double-click launch_dashboard.bat at the repo root.
All performance numbers are labeled SIMULATED or BACKTESTED.
Nothing here implies real money.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# ── Paths & constants ──────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
RESULTS   = ROOT / "results"
PICKS_DIR = ROOT / "picks"

LAUNCH_DATE = date(2026, 6, 5)

# Color palette
CLR_50  = "#3b82f6"   # blue   -- top-50
CLR_10  = "#f59e0b"   # amber  -- top-10
CLR_SPY = "#6b7280"   # gray   -- SPY
CLR_POS = "#10b981"   # green
CLR_NEG = "#ef4444"   # red
CLR_BG  = "#0a0e1a"
CLR_BG2 = "#141925"
CLR_BDR = "#1e2d4d"

# ── Page config (MUST be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="Factor Strategy",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS injection ──────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ---------- hide streamlit chrome ---------- */
header[data-testid="stHeader"]  {{ display:none !important; }}
#MainMenu                        {{ display:none !important; }}
footer                           {{ display:none !important; }}
.stDeployButton                  {{ display:none !important; }}
[data-testid="stToolbar"]        {{ display:none !important; }}
[data-testid="stDecoration"]     {{ display:none !important; }}

/* ---------- base spacing ---------- */
.block-container {{
    padding-top: 0.6rem !important;
    padding-bottom: 1rem !important;
    max-width: 1500px;
}}
div[data-testid="stVerticalBlock"] > div {{ gap: 0.35rem; }}
.element-container {{ margin-bottom: 0 !important; }}

/* ---------- top header bar ---------- */
.top-hdr {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.35rem 0 0.55rem 0;
    border-bottom: 1px solid {CLR_BDR};
    margin-bottom: 0.65rem;
}}
.top-hdr-title {{
    font-size: 1.25rem;
    font-weight: 700;
    color: #e5e7eb;
    letter-spacing: -0.015em;
}}
.top-hdr-sub {{
    font-size: 0.78rem;
    color: #6b7280;
    text-align: right;
    line-height: 1.5;
}}

/* ---------- section headers ---------- */
.sec-hdr {{
    font-size: 0.95rem;
    font-weight: 600;
    color: #cbd5e1;
    margin: 0.6rem 0 0 0;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.sec-bar {{
    height: 2px;
    width: 2.2rem;
    background: {CLR_50};
    margin: 0.15rem 0 0.4rem 0;
    border-radius: 2px;
}}

/* ---------- metric cards ---------- */
[data-testid="metric-container"] {{
    background: {CLR_BG2};
    border: 1px solid {CLR_BDR};
    border-radius: 7px;
    padding: 0.5rem 0.8rem !important;
}}
[data-testid="metric-container"] label {{
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #9ca3af !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    font-family: 'Courier New', monospace !important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    font-size: 0.78rem !important;
}}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] {{
    background: {CLR_BG2} !important;
    border-right: 1px solid {CLR_BDR} !important;
}}

/* ---------- tables ---------- */
.stDataFrame {{ border: 1px solid {CLR_BDR}; border-radius: 6px; overflow: hidden; }}

/* ---------- dividers ---------- */
hr {{ border-color: {CLR_BDR} !important; margin: 0.4rem 0 !important; }}

/* ---------- info/warning/success boxes tighter ---------- */
.stAlert {{ padding: 0.4rem 0.75rem !important; }}

/* ---------- button ---------- */
.stButton > button {{
    background: {CLR_BG2};
    border: 1px solid {CLR_BDR};
    color: #e5e7eb;
    border-radius: 5px;
    font-size: 0.82rem;
}}
.stButton > button:hover {{
    border-color: {CLR_50};
    color: {CLR_50};
}}

/* ---------- selectbox / dropdown ---------- */
[data-testid="stSelectbox"] label {{
    font-size: 0.8rem;
    color: #9ca3af;
}}
</style>
""", unsafe_allow_html=True)

# ── Persistent header bar ──────────────────────────────────────────────────────
_now_str      = datetime.now().strftime("%b %d, %Y  %H:%M")
_days_left    = (LAUNCH_DATE - date.today()).days
_status_str   = (
    f"{_days_left}d to live launch (Jun 5)"
    if _days_left > 0 else "LIVE"
)
st.markdown(f"""
<div class="top-hdr">
  <span class="top-hdr-title">Quality-Momentum Factor Strategy</span>
  <span class="top-hdr-sub">
    Austin Krauskopf &mdash; Personal Project<br>
    As of: {_now_str} ET &nbsp;|&nbsp; {_status_str}
  </span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar navigation ─────────────────────────────────────────────────────────
tab = st.sidebar.radio(
    "Navigate",
    ["Overview", "Top-50 (Primary)", "Top-10 (Concentrated)",
     "Performance Comparison", "Project Log"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption(
    "**Disclaimer:** All results are simulated / backtested. "
    "Nothing here constitutes investment advice."
)


# ══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════════════════════

def read_text_safe(path: Path) -> str:
    """Try UTF-8 first; fall back to cp1252 then latin-1."""
    for enc in ("utf-8", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1", errors="replace")


@st.cache_data(ttl=300)
def load_summary(short: str) -> dict:
    p = RESULTS / f"summary_{short}.json"
    return json.loads(p.read_text()) if p.exists() else {}


@st.cache_data(ttl=300)
def load_returns(short: str) -> pd.Series:
    p = RESULTS / f"strategy_returns_{short}.csv"
    if not p.exists():
        return pd.Series(dtype=float)
    s = pd.read_csv(p, index_col=0, parse_dates=True).squeeze()
    s.name = short
    return s


@st.cache_data(ttl=3600)
def load_spy_returns(start: str, end: str) -> pd.Series:
    px = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)
    if px.empty:
        return pd.Series(dtype=float)
    return px["Close"].resample("ME").last().pct_change().dropna()


def get_all_picks_files(short: str) -> list[tuple[date, Path, bool]]:
    """Return (date, path, is_before_launch) sorted newest-first."""
    d = PICKS_DIR / short
    if not d.exists():
        return []
    result = []
    for f in sorted(d.glob("*.md"), reverse=True):
        try:
            fd = date.fromisoformat(f.stem)
            result.append((fd, f, fd < LAUNCH_DATE))
        except ValueError:
            continue
    return result


def parse_picks_md(path: Path) -> pd.DataFrame:
    text = read_text_safe(path)
    rows = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Rank") or line.startswith("|---"):
            in_table = True
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 2:
                try:
                    rows.append({
                        "rank":            int(parts[0]),
                        "ticker":          parts[1],
                        "composite_score": float(parts[2]) if len(parts) > 2 else None,
                        "momentum":        float(parts[3]) if len(parts) > 3 else None,
                        "lowvol":          float(parts[4]) if len(parts) > 4 else None,
                        "quality":         float(parts[5]) if len(parts) > 5 else None,
                    })
                except (ValueError, IndexError):
                    continue
        elif in_table and not line.startswith("|"):
            break
    return pd.DataFrame(rows) if rows else pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_portfolio_data(
    tickers: tuple[str, ...],
    entry_date: str,
    exit_date: str,
    dollars_per_pick: float,
) -> tuple[pd.DataFrame, float | None]:
    """
    Fetch prices from entry_date to exit_date for each ticker.
    Returns (pnl_df, spy_pct).
    """
    all_tickers = list(tickers) + ["SPY"]
    start = (date.fromisoformat(entry_date) - timedelta(days=5)).isoformat()
    end   = (date.fromisoformat(exit_date)  + timedelta(days=3)).isoformat()

    raw = yf.download(all_tickers, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        return pd.DataFrame(), None

    closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw

    # Entry: first close ON or AFTER entry_date
    entry_ts    = pd.Timestamp(entry_date)
    future_rows = closes[closes.index >= entry_ts]
    if future_rows.empty:
        return pd.DataFrame(), None
    entry_row = future_rows.iloc[0]

    # Exit: last close ON or BEFORE exit_date
    exit_ts   = pd.Timestamp(exit_date)
    past_rows = closes[closes.index <= exit_ts]
    if past_rows.empty:
        return pd.DataFrame(), None
    exit_row = past_rows.iloc[-1]

    rows = []
    for t in tickers:
        ep = entry_row.get(t)
        cp = exit_row.get(t)
        if ep is None or cp is None or pd.isna(ep) or pd.isna(cp) or float(ep) <= 0:
            continue
        ep, cp   = float(ep), float(cp)
        shares   = dollars_per_pick / ep
        cur_val  = shares * cp
        rows.append({
            "ticker":        t,
            "entry_price":   round(ep, 2),
            "current_price": round(cp, 2),
            "shares":        round(shares, 4),
            "entry_value":   round(dollars_per_pick, 2),
            "current_value": round(cur_val, 2),
            "dollar_pnl":    round(cur_val - dollars_per_pick, 2),
            "pct_pnl":       round((cp / ep - 1) * 100, 2),
        })

    spy_pct = None
    sep, scp = entry_row.get("SPY"), exit_row.get("SPY")
    if sep and scp and not pd.isna(sep) and not pd.isna(scp) and float(sep) > 0:
        spy_pct = (float(scp) / float(sep) - 1) * 100

    return pd.DataFrame(rows), spy_pct


def section_header(title: str) -> None:
    st.markdown(
        f'<div class="sec-hdr">{title}</div><div class="sec-bar"></div>',
        unsafe_allow_html=True,
    )


def _fmt_pct(val: float | None, decimals: int = 2) -> str:
    if val is None:
        return "—"
    return f"{val:+.{decimals}f}%"


def _fmt_dollar(val: float | None) -> str:
    if val is None:
        return "—"
    return f"${val:+,.0f}"


# ══════════════════════════════════════════════════════════════════════════════
# Portfolio tab renderer (Tasks 2 + 3)
# ══════════════════════════════════════════════════════════════════════════════

def render_portfolio_tab(short: str, dollars_per_pick: float, strategy_name: str) -> None:
    all_files = get_all_picks_files(short)

    if not all_files:
        st.info(f"No picks files in picks/{short}/. Run `python scripts/run_live.py`.")
        if st.button(f"Generate {strategy_name} Picks Now", key=f"gen_{short}"):
            with st.spinner("Generating picks..."):
                res = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "run_live.py")],
                    capture_output=True, text=True, cwd=str(ROOT),
                )
            if res.returncode == 0:
                st.success("Done. Refresh the page.")
                st.cache_data.clear()
            else:
                st.error("Error:"); st.code(res.stderr[-2000:])
        return

    # ── Month dropdown (Task 3) ────────────────────────────────────────────────
    def _month_label(idx: int, d: date, is_dry: bool) -> str:
        s = d.strftime("%B %Y")
        if idx == 0:
            return s + ("  [DRY RUN - CURRENT]" if is_dry else "  [CURRENT]")
        return s + ("  [DRY RUN]" if is_dry else "  [HISTORICAL]")

    labels = [_month_label(i, d, dr) for i, (d, _, dr) in enumerate(all_files)]

    if len(all_files) > 1:
        sel_idx = st.selectbox(
            "View month:",
            options=range(len(all_files)),
            format_func=lambda i: labels[i],
            key=f"sel_{short}",
        )
    else:
        sel_idx = 0

    sel_date, picks_file, is_dry = all_files[sel_idx]
    is_current = (sel_idx == 0)

    # Status banner
    if is_dry:
        st.warning(
            f"**DRY RUN** — {sel_date.strftime('%B %Y')} picks recorded before the "
            f"June 5, 2026 official launch. Not part of the live track record."
        )
    elif is_current and date.today() < LAUNCH_DATE:
        st.info(
            f"**CURRENT MONTH (pre-launch)** — picks are being logged "
            f"but live tracking starts June 5, 2026."
        )

    # Parse picks
    picks_df = parse_picks_md(picks_file)
    if picks_df.empty:
        st.warning("No picks data found in this file.")
        return

    # Exit date: next file's entry date, or today for current month
    if is_current:
        exit_date_str = date.today().isoformat()
    else:
        next_idx = sel_idx - 1   # files are newest-first; previous in list = next month
        exit_date_str = (
            all_files[next_idx][0].isoformat()
            if next_idx >= 0
            else date.today().isoformat()
        )

    # Fetch P&L
    tickers = tuple(picks_df["ticker"].tolist())
    with st.spinner("Fetching prices..."):
        try:
            port_df, spy_pct = fetch_portfolio_data(
                tickers, sel_date.isoformat(), exit_date_str, dollars_per_pick
            )
        except Exception as exc:
            st.error(f"Price fetch error: {exc}")
            port_df, spy_pct = pd.DataFrame(), None

    # ── 4-column metric row ────────────────────────────────────────────────────
    if not port_df.empty:
        total_inv  = port_df["entry_value"].sum()
        total_cur  = port_df["current_value"].sum()
        total_pnl  = total_cur - total_inv
        total_pct  = (total_pnl / total_inv * 100) if total_inv > 0 else 0
        alpha_pp   = (total_pct - spy_pct) if spy_pct is not None else None
    else:
        total_inv = total_cur = total_pnl = total_pct = 0.0
        alpha_pp = None

    period_label = (
        f"{sel_date.strftime('%b %d')} → today"
        if is_current
        else f"{sel_date.strftime('%b %d')} → {date.fromisoformat(exit_date_str).strftime('%b %d')}"
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value (Sim)",  f"${total_cur:,.0f}",
              delta=f"${total_pnl:+,.0f}" if not port_df.empty else None)
    m2.metric(f"P&L $ · {period_label}", _fmt_dollar(total_pnl if not port_df.empty else None))
    m3.metric("P&L %",                  _fmt_pct(total_pct if not port_df.empty else None))
    m4.metric("vs SPY (alpha pp)",      _fmt_pct(alpha_pp), delta_color="off")

    st.markdown("---")

    # ── 2-column layout: picks table | strategy stats ──────────────────────────
    col_l, col_r = st.columns([3, 2])

    with col_l:
        section_header("Holdings")
        st.caption(
            f"*{sel_date.strftime('%b %d, %Y')} — {len(picks_df)} names | "
            f"${dollars_per_pick:.0f}/position simulated | SIMULATED*"
        )
        display_cols = ["rank", "ticker", "composite_score", "momentum", "lowvol"]
        if "quality" in picks_df.columns and picks_df["quality"].notna().any():
            display_cols.append("quality")

        col_cfg = {
            "rank":            st.column_config.NumberColumn("Rk",     format="%d",     width="small"),
            "ticker":          st.column_config.TextColumn("Ticker",                    width="small"),
            "composite_score": st.column_config.NumberColumn("Score",  format="%.4f"),
            "momentum":        st.column_config.NumberColumn("Mom Z",  format="%.4f"),
            "lowvol":          st.column_config.NumberColumn("LV Z",   format="%.4f"),
            "quality":         st.column_config.NumberColumn("Qual Z", format="%.4f"),
        }
        st.dataframe(
            picks_df[display_cols],
            column_config={k: v for k, v in col_cfg.items() if k in display_cols},
            width="stretch", hide_index=True,
            height=min(560, 44 + 35 * len(picks_df)),
        )

    with col_r:
        section_header("Strategy Stats")
        s = load_summary(short)
        if s:
            net = s.get("net", {})
            stats_rows = [
                ("CAGR (backtest)",  net.get("cagr"),              "{:.2%}"),
                ("Volatility",       net.get("volatility"),         "{:.2%}"),
                ("Sharpe",           net.get("sharpe"),             "{:.2f}"),
                ("Max Drawdown",     net.get("max_drawdown"),       "{:.2%}"),
                ("Alpha vs SPY",     net.get("alpha_annualised"),   "{:.2%}"),
                ("Beta",             net.get("beta"),               "{:.2f}"),
                ("Info Ratio",       net.get("information_ratio"),  "{:.2f}"),
            ]
            df_stats = pd.DataFrame([
                {"Metric": lbl, "Value": fmt.format(v) if v is not None else "—"}
                for lbl, v, fmt in stats_rows
            ])
            st.dataframe(df_stats, width="stretch", hide_index=True)
            st.caption("*Backtest 2010-2025, net of 5 bps one-way costs*")

        # OOS summary callout
        ott = RESULTS / "train_test_validation.md"
        if ott.exists():
            with st.expander("OOS validation", expanded=False):
                text = read_text_safe(ott)
                # Find the table for this strategy
                upper = strategy_name.upper()
                lines = text.splitlines()
                capture = False
                snippet = []
                for ln in lines:
                    if short in ln.lower() or strategy_name.lower() in ln.lower():
                        capture = True
                    if capture and (ln.startswith("| ") or ln.startswith("|---")):
                        snippet.append(ln)
                    elif capture and snippet and not ln.startswith("|"):
                        break
                if snippet:
                    st.markdown("\n".join(snippet[:15]))

    # ── P&L table ──────────────────────────────────────────────────────────────
    if not port_df.empty:
        st.markdown("---")
        section_header("Position P&L")
        st.caption(f"*SIMULATED — ${dollars_per_pick:.0f}/position at {sel_date.strftime('%b %d')} close*")

        display = (
            port_df[["ticker", "entry_price", "current_price", "dollar_pnl", "pct_pnl"]]
            .copy()
            .sort_values("pct_pnl", ascending=False)
        )

        def _style_pnl(val):
            if isinstance(val, (int, float)):
                c = CLR_POS if val >= 0 else CLR_NEG
                return f"color: {c}; font-weight: 600"
            return ""

        st.dataframe(
            display.style.map(_style_pnl, subset=["dollar_pnl", "pct_pnl"]),
            column_config={
                "ticker":        st.column_config.TextColumn("Ticker"),
                "entry_price":   st.column_config.NumberColumn("Entry",   format="$%.2f"),
                "current_price": st.column_config.NumberColumn("Current", format="$%.2f"),
                "dollar_pnl":    st.column_config.NumberColumn("P&L $",   format="$%+.2f"),
                "pct_pnl":       st.column_config.NumberColumn("P&L %",   format="%+.2f%%"),
            },
            width="stretch", hide_index=True,
        )

    # ── Compare to other strategy (Task 3.5) ───────────────────────────────────
    other_short = "top10" if short == "top50" else "top50"
    other_name  = "Top-10" if short == "top50" else "Top-50"
    other_dpp   = 100.0 if other_short == "top10" else 50.0
    other_files = get_all_picks_files(other_short)

    if other_files:
        st.markdown("---")
        compare_on = st.toggle(
            f"Compare {other_name} same-month performance",
            key=f"cmp_{short}",
        )
        if compare_on:
            # Find other strategy's picks for same month
            other_match = None
            for od, of, _ in other_files:
                if od.year == sel_date.year and od.month == sel_date.month:
                    other_match = (od, of)
                    break

            if other_match is None:
                st.info(f"No {other_name} picks found for {sel_date.strftime('%B %Y')}.")
            else:
                other_date, other_file = other_match
                other_picks = parse_picks_md(other_file)
                other_tickers = tuple(other_picks["ticker"].tolist())
                with st.spinner(f"Fetching {other_name} prices..."):
                    try:
                        other_df, _ = fetch_portfolio_data(
                            other_tickers, other_date.isoformat(),
                            exit_date_str, other_dpp,
                        )
                    except Exception:
                        other_df = pd.DataFrame()

                section_header(f"Same-Month Comparison: {strategy_name} vs {other_name}")
                if not other_df.empty:
                    oi  = other_df["entry_value"].sum()
                    oc  = other_df["current_value"].sum()
                    opp = (oc - oi) / oi * 100 if oi > 0 else 0

                    this_pp = total_pct if not port_df.empty else None
                    c1, c2, c3 = st.columns(3)
                    c1.metric(f"{strategy_name}",  _fmt_pct(this_pp))
                    c2.metric(f"{other_name}",     _fmt_pct(opp))
                    diff = (opp - this_pp) if this_pp is not None else None
                    c3.metric(f"{other_name} - {strategy_name}", _fmt_pct(diff),
                              delta_color="off")
                    st.caption(f"*Period: {period_label}  |  SIMULATED*")

    # ── Refresh button ──────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button(f"Refresh {strategy_name} Picks Now", key=f"refresh_{short}"):
        with st.spinner("Running run_live.py..."):
            res = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "run_live.py")],
                capture_output=True, text=True, cwd=str(ROOT),
            )
        if res.returncode == 0:
            st.success("Picks refreshed. Reload the page to see new data.")
            st.cache_data.clear()
        else:
            st.error("Error:"); st.code(res.stderr[-2000:])


# ══════════════════════════════════════════════════════════════════════════════
# TAB: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if tab == "Overview":
    col_l, col_r = st.columns([5, 2])
    with col_l:
        section_header("Strategy Summary")
        st.markdown("""
This project implements a **systematic, long-only equity strategy** selecting S&P 500 stocks via
price momentum and low volatility. Every month the strategy scores all S&P 500 names on both
factors, ranks them, and holds the top names in an equal-weight portfolio.

**Two portfolios run in parallel.** Top-50 is the **primary** — 50 names at 2% each, better
risk-adjusted returns (Sharpe 1.15 vs SPY 1.02), shallower drawdown (-21.6% vs -23.9%).
Top-10 is a **concentrated comparison** — 10 names at 10% each — tracking whether extra
concentration earns its extra risk. Live tracking begins **June 5, 2026.**
        """)

    with col_r:
        if _days_left > 0:
            st.info(f"**Live launch in {_days_left} day{'s' if _days_left != 1 else ''}**\n\n"
                    f"Official start: **June 5, 2026**")
        else:
            st.success("**LIVE** — tracking active")

    st.markdown("---")
    section_header("Backtest Summary — SIMULATED (2010-2025, net of 5 bps costs)")

    s50 = load_summary("top50")
    s10 = load_summary("top10")

    if s50 and s10:
        rows_def = [
            ("CAGR",              "cagr",              "{:.2%}"),
            ("Volatility (ann.)", "volatility",        "{:.2%}"),
            ("Sharpe Ratio",      "sharpe",             "{:.2f}"),
            ("Max Drawdown",      "max_drawdown",       "{:.2%}"),
            ("Alpha vs SPY",      "alpha_annualised",   "{:.2%}"),
            ("Beta",              "beta",               "{:.2f}"),
            ("Info Ratio",        "information_ratio",  "{:.2f}"),
        ]
        spy_map = {
            "cagr":       "benchmark_cagr",
            "volatility":  "benchmark_volatility",
            "sharpe":      "benchmark_sharpe",
            "max_drawdown":"benchmark_max_drawdown",
        }
        tbl = {"Metric": [], "Top-50 (Primary)": [], "Top-10 (Concentrated)": [], "SPY": []}
        for lbl, key, fmt in rows_def:
            tbl["Metric"].append(lbl)
            v50 = s50.get("net", {}).get(key)
            v10 = s10.get("net", {}).get(key)
            spy = s50.get("net", {}).get(spy_map.get(key))
            tbl["Top-50 (Primary)"].append(   fmt.format(v50) if v50 is not None else "—")
            tbl["Top-10 (Concentrated)"].append(fmt.format(v10) if v10 is not None else "—")
            tbl["SPY"].append(                 fmt.format(spy) if spy is not None else "—")

        st.dataframe(pd.DataFrame(tbl), width="stretch", hide_index=True)
    else:
        st.warning("Run `python scripts/run_backtest.py` to generate summary files.")

    st.markdown("---")
    section_header("Out-of-Sample Validation (Train 2011-2018 / Test 2019-2025)")
    st.caption("SIMULATED — no post-2018 data touched during model construction")

    ott = RESULTS / "train_test_validation.md"
    if ott.exists():
        text = read_text_safe(ott)
        lines = text.splitlines()
        snippet = [ln for ln in lines
                   if ln.startswith("| ") or ln.startswith("|---")][:20]
        st.markdown("\n".join(snippet))
        with st.expander("Full validation report"):
            st.markdown(text)
    else:
        st.warning("Run `python scripts/run_train_test.py` to generate validation report.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB: TOP-50
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Top-50 (Primary)":
    section_header("Top-50 Strategy — Primary Portfolio")
    st.caption("Equal weight · 2% per position · monthly rebalance · SIMULATED / DRY RUN")
    render_portfolio_tab("top50", 50.0, "Top-50")


# ══════════════════════════════════════════════════════════════════════════════
# TAB: TOP-10
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Top-10 (Concentrated)":
    section_header("Top-10 Strategy — Concentrated Comparison")
    st.caption("Equal weight · 10% per position · monthly rebalance · SIMULATED / DRY RUN")
    st.warning(
        "**Concentrated comparison portfolio** — not the primary strategy. "
        "Higher in-sample returns (24% CAGR) but materially higher drawdown "
        "(-32.7% vs -21.6%) and no separate OOS validation. Tracked for "
        "experimental comparison only."
    )
    render_portfolio_tab("top10", 100.0, "Top-10")


# ══════════════════════════════════════════════════════════════════════════════
# TAB: PERFORMANCE COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Performance Comparison":
    section_header("Performance Comparison")

    if date.today() < LAUNCH_DATE:
        st.caption(
            f"Live tracking begins {LAUNCH_DATE}. "
            f"Showing **backtested** returns (2010-2025). SIMULATED."
        )
    else:
        st.caption("Live cumulative returns since June 5, 2026.")

    # Static PNG charts
    chart_cols = st.columns(2)
    cp = RESULTS / "cumulative_returns.png"
    dp = RESULTS / "drawdown.png"
    if cp.exists():
        chart_cols[0].image(str(cp), caption="Cumulative returns — SIMULATED backtest")
    if dp.exists():
        chart_cols[1].image(str(dp), caption="Drawdown — SIMULATED backtest")

    st.markdown("---")
    section_header("Interactive Cumulative Returns — SIMULATED")

    r50 = load_returns("top50")
    r10 = load_returns("top10")

    if not r50.empty:
        try:
            spy_ret = load_spy_returns(
                str(r50.index[0].date()), str(r50.index[-1].date())
            )
        except Exception:
            spy_ret = pd.Series(dtype=float)

        fig = go.Figure()
        w50 = (1 + r50).cumprod()
        fig.add_trace(go.Scatter(
            x=w50.index, y=w50.values, name="Top-50 (Primary)",
            line=dict(color=CLR_50, width=2.5),
            hovertemplate="Top-50: $%{y:.2f}<extra></extra>",
        ))
        if not r10.empty:
            w10 = (1 + r10).cumprod()
            fig.add_trace(go.Scatter(
                x=w10.index, y=w10.values, name="Top-10 (Concentrated)",
                line=dict(color=CLR_10, width=2),
                hovertemplate="Top-10: $%{y:.2f}<extra></extra>",
            ))
        if not spy_ret.empty:
            common  = spy_ret.index.intersection(r50.index)
            w_spy   = (1 + spy_ret.loc[common]).cumprod()
            fig.add_trace(go.Scatter(
                x=w_spy.index, y=w_spy.values, name="SPY",
                line=dict(color=CLR_SPY, width=1.5, dash="dash"),
                hovertemplate="SPY: $%{y:.2f}<extra></extra>",
            ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=CLR_BG2,
            plot_bgcolor="#0f1520",
            title=dict(
                text="Growth of $1 — SIMULATED BACKTEST 2010-2025",
                font=dict(size=13, color="#9ca3af"),
            ),
            xaxis_title="", yaxis_title="Growth of $1",
            yaxis_type="log",
            legend=dict(
                x=0.01, y=0.99,
                bgcolor="rgba(20,25,37,0.85)",
                bordercolor=CLR_BDR,
                borderwidth=1,
                font=dict(size=11),
            ),
            height=480,
            margin=dict(l=50, r=20, t=45, b=40),
            hovermode="x unified",
        )
        fig.update_xaxes(gridcolor="#1e2d4d", showgrid=True)
        fig.update_yaxes(gridcolor="#1e2d4d", showgrid=True)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown("---")
    section_header("Rolling Annualised CAGR — SIMULATED")
    st.caption("Net of 5 bps one-way transaction costs")

    if not r50.empty:
        def rolling_cagr(r: pd.Series, w: int) -> pd.Series:
            return (1 + r).rolling(w).apply(
                lambda x: x.prod() ** (12 / w) - 1, raw=True
            )

        windows = [
            ("3-month",  3),
            ("6-month",  6),
            ("12-month", 12),
        ]
        for label, w in windows:
            c1, c2, c3 = st.columns(3)
            for col_ui, (s_key, color) in zip(
                [c1, c2], [("top50", CLR_50), ("top10", CLR_10)]
            ):
                r = load_returns(s_key)
                if r.empty:
                    continue
                rc     = rolling_cagr(r, w)
                latest = rc.dropna().iloc[-1] if not rc.dropna().empty else None
                name   = "Top-50" if s_key == "top50" else "Top-10"
                spy_rc = rolling_cagr(spy_ret, w) if not spy_ret.empty else None
                spy_l  = spy_rc.dropna().iloc[-1] if spy_rc is not None and not spy_rc.dropna().empty else None
                if latest is not None:
                    delta = f"{latest - spy_l:+.2%} vs SPY" if spy_l else None
                    col_ui.metric(f"{label} {name}", f"{latest:.2%}", delta)
            if spy_ret is not None and not spy_ret.empty:
                spy_rc2 = rolling_cagr(spy_ret, w)
                spy_l2  = spy_rc2.dropna().iloc[-1] if not spy_rc2.dropna().empty else None
                if spy_l2 is not None:
                    c3.metric(f"{label} SPY", f"{spy_l2:.2%}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB: PROJECT LOG
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Project Log":
    section_header("Project Log")
    st.caption("Append-only record of all meaningful changes. Most recent first.")

    log_path = ROOT / "PROJECT_LOG.md"
    if log_path.exists():
        text = read_text_safe(log_path)
        sections = re.split(r"\n(?=## )", text)
        header_md = sections[0]
        entries   = sections[1:]
        st.markdown(header_md)
        for entry in reversed(entries):
            title = entry.splitlines()[0].replace("## ", "").strip()
            with st.expander(title, expanded=False):
                st.markdown(entry)
    else:
        st.warning("PROJECT_LOG.md not found.")
