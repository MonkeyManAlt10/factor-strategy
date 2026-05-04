"""
dashboard/app.py — Streamlit dashboard for the Quality-Momentum Factor Strategy.

Launch: double-click launch_dashboard.bat at the repo root.
All performance numbers are clearly labeled SIMULATED or BACKTESTED.
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

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
RESULTS   = ROOT / "results"
PICKS_DIR = ROOT / "picks"

LAUNCH_DATE = date(2026, 6, 5)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Factor Strategy Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Header ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("Quality-Momentum Factor Strategy")
    st.caption("Austin Krauskopf — Personal Project  |  " + datetime.now().strftime("%A %B %d, %Y"))
with col_h2:
    days_to_launch = (LAUNCH_DATE - date.today()).days
    if days_to_launch > 0:
        st.metric("Days to Live Launch", days_to_launch, help="Live tracking starts June 5, 2026")
    else:
        st.metric("Live Since", LAUNCH_DATE.strftime("%b %d, %Y"))

st.divider()

# ── Sidebar navigation ─────────────────────────────────────────────────────────
tab = st.sidebar.radio(
    "Navigate",
    ["Overview", "Top-50 (Primary)", "Top-10 (Concentrated)", "Performance Comparison", "Project Log"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption("**Disclaimer:** All results are simulated/backtested. Nothing here constitutes investment advice.")


# ── Data helpers ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_summary(short: str) -> dict:
    p = RESULTS / f"summary_{short}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


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
    monthly = px["Close"].resample("ME").last()
    return monthly.pct_change().dropna()


def get_latest_picks_file(short: str) -> Path | None:
    d = PICKS_DIR / short
    if not d.exists():
        return None
    files = sorted(d.glob("*.md"))
    return files[-1] if files else None


def parse_picks_md(path: Path) -> pd.DataFrame:
    """Parse a picks markdown table into a DataFrame."""
    text = path.read_text(encoding="utf-8")
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


def picks_date_from_path(path: Path) -> date:
    """Extract the pick date from YYYY-MM-DD.md filename."""
    try:
        return date.fromisoformat(path.stem)
    except ValueError:
        return date.today()


@st.cache_data(ttl=300)
def fetch_portfolio_data(tickers: tuple, entry_date: str, dollars_per_pick: float) -> pd.DataFrame:
    """
    For each ticker, fetch entry close price on entry_date and current price.
    Returns DataFrame with shares, entry_price, current_price, dollar pnl, pct pnl.
    """
    all_tickers = list(tickers) + ["SPY"]
    # Fetch from a few days before entry to a few days after (handles weekends/holidays)
    start = (date.fromisoformat(entry_date) - timedelta(days=5)).isoformat()
    end   = (date.today() + timedelta(days=1)).isoformat()

    raw = yf.download(all_tickers, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        return pd.DataFrame()

    closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw

    # Entry price = first close ON or AFTER entry_date
    entry_ts = pd.Timestamp(entry_date)
    future_closes = closes[closes.index >= entry_ts]
    if future_closes.empty:
        return pd.DataFrame()
    entry_row = future_closes.iloc[0]

    # Current price = latest close
    current_row = closes.iloc[-1]

    rows = []
    for t in tickers:
        ep = entry_row.get(t, None)
        cp = current_row.get(t, None)
        if ep is None or cp is None or pd.isna(ep) or pd.isna(cp) or ep <= 0:
            continue
        shares   = dollars_per_pick / float(ep)
        cur_val  = shares * float(cp)
        dollar_pnl = cur_val - dollars_per_pick
        pct_pnl    = (float(cp) / float(ep) - 1) * 100
        rows.append({
            "ticker":        t,
            "entry_price":   round(float(ep), 2),
            "current_price": round(float(cp), 2),
            "shares":        round(shares, 4),
            "entry_value":   round(dollars_per_pick, 2),
            "current_value": round(cur_val, 2),
            "dollar_pnl":    round(dollar_pnl, 2),
            "pct_pnl":       round(pct_pnl, 2),
        })

    # SPY comparison
    spy_ep = entry_row.get("SPY", None)
    spy_cp = current_row.get("SPY", None)
    if spy_ep and spy_cp and not pd.isna(spy_ep) and not pd.isna(spy_cp) and spy_ep > 0:
        n = len(rows)
        total_invested = n * dollars_per_pick
        spy_shares = total_invested / float(spy_ep)
        spy_pct = (float(spy_cp) / float(spy_ep) - 1) * 100
        return pd.DataFrame(rows), spy_pct, float(spy_cp)

    return pd.DataFrame(rows), None, None


def _pct_color(val: float) -> str:
    return "green" if val >= 0 else "red"


def render_portfolio_tab(short: str, dollars_per_pick: float, strategy_name: str) -> None:
    """Render the per-strategy picks + P&L tab."""
    picks_file = get_latest_picks_file(short)

    if picks_file is None:
        st.info(f"No picks files found yet in picks/{short}/. Run `python scripts/run_live.py` to generate picks.")
        if st.button(f"Generate {strategy_name} Picks Now", key=f"gen_{short}"):
            with st.spinner("Generating picks (downloading prices)..."):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "run_live.py")],
                    capture_output=True, text=True, cwd=str(ROOT),
                )
            if result.returncode == 0:
                st.success("Picks generated successfully! Refresh the page.")
                st.cache_data.clear()
            else:
                st.error("Error generating picks:")
                st.code(result.stderr[-2000:])
        return

    picks_df    = parse_picks_md(picks_file)
    entry_date  = picks_date_from_path(picks_file)

    col1, col2, col3 = st.columns(3)
    col1.metric("Picks Date", entry_date.strftime("%b %d, %Y"))
    col2.metric("Positions", len(picks_df))
    col3.metric("Simulated Per Position", f"${dollars_per_pick:.0f}")

    if not picks_df.empty:
        st.subheader("Current Holdings")
        st.caption("*SIMULATED — not real money*")
        display_cols = ["rank", "ticker", "composite_score", "momentum", "lowvol"]
        if "quality" in picks_df.columns and picks_df["quality"].notna().any():
            display_cols.append("quality")
        st.dataframe(
            picks_df[display_cols].rename(columns={
                "rank": "Rank", "ticker": "Ticker",
                "composite_score": "Score", "momentum": "Mom Z",
                "lowvol": "LowVol Z", "quality": "Quality Z"
            }),
            width="stretch", hide_index=True,
        )

    st.divider()
    st.subheader("Simulated P&L Since Last Rebalance")
    st.caption(f"*SIMULATED — assumes ${dollars_per_pick:.0f} invested in each position at close on {entry_date}. No real money.*")

    if picks_df.empty:
        st.warning("No picks loaded.")
        return

    tickers = tuple(picks_df["ticker"].tolist())

    with st.spinner("Fetching current prices..."):
        try:
            result = fetch_portfolio_data(tickers, entry_date.isoformat(), dollars_per_pick)
            if isinstance(result, tuple) and len(result) == 3:
                port_df, spy_pct, spy_price = result
            else:
                port_df = result
                spy_pct, spy_price = None, None
        except Exception as e:
            st.error(f"Error fetching prices: {e}")
            return

    if port_df.empty:
        st.warning("Could not fetch current prices.")
        return

    total_invested = port_df["entry_value"].sum()
    total_current  = port_df["current_value"].sum()
    total_pnl      = total_current - total_invested
    total_pct      = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Invested (Simulated)", f"${total_invested:,.0f}")
    m2.metric("Current Value (Simulated)", f"${total_current:,.0f}",
              delta=f"${total_pnl:+,.0f} ({total_pct:+.2f}%)")
    if spy_pct is not None:
        m3.metric("SPY Return (Same Period)", f"{spy_pct:+.2f}%")
        m4.metric("Alpha vs SPY", f"{total_pct - spy_pct:+.2f} pp")

    # Per-stock table with color
    def style_pnl(val):
        if isinstance(val, (int, float)):
            color = "#2e7d32" if val >= 0 else "#c62828"
            return f"color: {color}"
        return ""

    display = port_df[["ticker", "entry_price", "current_price", "shares", "dollar_pnl", "pct_pnl"]].rename(
        columns={"ticker": "Ticker", "entry_price": "Entry $",
                 "current_price": "Current $", "shares": "Shares",
                 "dollar_pnl": "P&L ($)", "pct_pnl": "P&L (%)"}
    ).sort_values("P&L (%)", ascending=False)

    st.dataframe(
        display.style.applymap(style_pnl, subset=["P&L ($)", "P&L (%)"]),
        width="stretch", hide_index=True,
    )

    st.divider()
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button(f"Refresh {strategy_name} Picks Now", key=f"refresh_{short}",
                     help="Downloads fresh prices and regenerates picks. Creates a new dated file."):
            with st.spinner("Running live picks (this may take 30-60 seconds)..."):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "run_live.py")],
                    capture_output=True, text=True, cwd=str(ROOT),
                )
            if result.returncode == 0:
                st.success("Picks refreshed! New dated file created. Refresh page to see updated data.")
                st.cache_data.clear()
            else:
                st.error("Error refreshing picks:")
                st.code(result.stderr[-2000:])


# ── TAB: OVERVIEW ──────────────────────────────────────────────────────────────
if tab == "Overview":
    st.header("Overview")

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("""
This project implements a **systematic, long-only equity strategy** that selects stocks from the S&P 500
using two quantitative signals: price momentum and low volatility. Every month, the strategy scores every
S&P 500 stock on both factors, ranks them, and holds the top names in an equal-weight portfolio.

**Two portfolios run in parallel.** The top-50 is the **primary strategy** — 50 names at 2% each,
designed for robustness and diversification. It has the better risk-adjusted backtest performance
(Sharpe 1.15 vs SPY's 1.02) and the shallower max drawdown (-21.6% vs -23.9%). The top-10 is a
**concentrated comparison portfolio** — 10 names at 10% each — tracked to test whether extra
concentration earns its extra risk. Both strategies are tracked transparently from launch.

**Live tracking begins June 5, 2026.** Until then, picks are recorded as dry runs to validate the
pipeline. The backtest results below are simulated on historical data from 2010–2025.
All results are clearly labeled. See METHODOLOGY.md for the full academic foundation.
        """)

    with col_r:
        days_left = (LAUNCH_DATE - date.today()).days
        if days_left > 0:
            st.info(f"**Live launch in {days_left} day{'s' if days_left != 1 else ''}**\n\n"
                    f"Official start: **June 5, 2026**")
        else:
            st.success("**LIVE** — tracking active")

    st.subheader("Backtest Summary (Net of 5 bps one-way costs) — SIMULATED")
    st.caption("Period: Jan 2010 – Dec 2025 | Universe: 503 current S&P 500 constituents")

    s50  = load_summary("top50")
    s10  = load_summary("top10")

    if s50 and s10:
        rows = [
            ("CAGR",             "cagr",            "{:.2%}"),
            ("Volatility (ann)", "volatility",       "{:.2%}"),
            ("Sharpe Ratio",     "sharpe",           "{:.2f}"),
            ("Max Drawdown",     "max_drawdown",     "{:.2%}"),
            ("Alpha vs SPY",     "alpha_annualised", "{:.2%}"),
            ("Beta",             "beta",             "{:.2f}"),
            ("Info Ratio",       "information_ratio","{:.2f}"),
        ]
        table_data = {"Metric": [], "Top-50 (Primary)": [], "Top-10 (Concentrated)": [], "SPY": []}
        for label, key, fmt in rows:
            table_data["Metric"].append(label)
            v50  = s50.get("net", {}).get(key)
            v10  = s10.get("net", {}).get(key)
            vsm  = s50.get("net", {}).get("benchmark_" + key.replace("alpha_annualised", "").replace("information_ratio", "").replace("beta",""))
            # SPY values
            spy_key = key.replace("alpha_annualised", "").replace("information_ratio", "")
            spy_val = s50.get("net", {}).get("benchmark_cagr") if key == "cagr" else \
                      s50.get("net", {}).get("benchmark_volatility") if key == "volatility" else \
                      s50.get("net", {}).get("benchmark_sharpe") if key == "sharpe" else \
                      s50.get("net", {}).get("benchmark_max_drawdown") if key == "max_drawdown" else None
            table_data["Top-50 (Primary)"].append(fmt.format(v50) if v50 is not None else "—")
            table_data["Top-10 (Concentrated)"].append(fmt.format(v10) if v10 is not None else "—")
            table_data["SPY"].append(fmt.format(spy_val) if spy_val is not None else "—")
        st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)
    else:
        st.warning("Run `python scripts/run_backtest.py` to generate summary files.")

    st.divider()
    st.subheader("Out-of-Sample Validation (Train 2011–2018 / Test 2019–2025)")
    st.caption("SIMULATED — no future data used in train period")

    ott = RESULTS / "train_test_validation.md"
    if ott.exists():
        text = ott.read_text(encoding="utf-8")
        # Show just the tables section
        lines = text.splitlines()
        in_section = False
        snippet = []
        for line in lines:
            if "| Period |" in line or "| **Train" in line or "| **Test" in line or "| Full" in line:
                snippet.append(line)
            elif "### Degradation" in line or "### Interpretation" in line or "## Overall" in line:
                if snippet:
                    snippet.append("")
                break
        st.markdown("\n".join(snippet[:20]))
        with st.expander("Full validation report"):
            st.markdown(text)


# ── TAB: TOP-50 ────────────────────────────────────────────────────────────────
elif tab == "Top-50 (Primary)":
    st.header("Top-50 Strategy — Primary Portfolio")
    st.caption("Equal weight, 2% per position, monthly rebalance | SIMULATED / DRY RUN")
    render_portfolio_tab("top50", 50.0, "Top-50")


# ── TAB: TOP-10 ────────────────────────────────────────────────────────────────
elif tab == "Top-10 (Concentrated)":
    st.header("Top-10 Strategy — Concentrated Comparison")
    st.caption("Equal weight, 10% per position, monthly rebalance | SIMULATED / DRY RUN")
    st.warning(
        "Top-10 is a **concentrated comparison portfolio**, not the primary strategy. "
        "It has higher in-sample backtest returns but also higher drawdown (-32.7% vs -21.6%) "
        "and has not been validated out-of-sample separately from the top-50. "
        "It is tracked to compare live performance, not as a recommendation."
    )
    render_portfolio_tab("top10", 100.0, "Top-10")


# ── TAB: PERFORMANCE COMPARISON ────────────────────────────────────────────────
elif tab == "Performance Comparison":
    st.header("Performance Comparison")

    live_mode = date.today() >= LAUNCH_DATE
    if live_mode:
        st.caption("Showing live cumulative returns since June 5, 2026")
    else:
        st.caption(f"Live tracking begins {LAUNCH_DATE}. Showing **backtested** returns (2010–2025). SIMULATED.")

    # Cumulative returns chart from results/
    chart_path = RESULTS / "cumulative_returns.png"
    if chart_path.exists():
        st.image(str(chart_path), caption="SIMULATED backtest: Quality-Momentum vs SPY (2010–2025)")

    drawdown_path = RESULTS / "drawdown.png"
    if drawdown_path.exists():
        st.image(str(drawdown_path), caption="SIMULATED drawdown comparison")

    st.divider()
    st.subheader("Interactive Cumulative Returns (Backtest) — SIMULATED")

    r50 = load_returns("top50")
    r10 = load_returns("top10")

    if not r50.empty:
        try:
            spy_ret = load_spy_returns(str(r50.index[0].date()), str(r50.index[-1].date()))
        except Exception:
            spy_ret = pd.Series(dtype=float)

        wealth50  = (1 + r50).cumprod()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=wealth50.index, y=wealth50.values,
                                  name="Top-50 (Primary)", line=dict(color="steelblue", width=2.5)))
        if not r10.empty:
            wealth10 = (1 + r10).cumprod()
            fig.add_trace(go.Scatter(x=wealth10.index, y=wealth10.values,
                                      name="Top-10 (Concentrated)", line=dict(color="darkorange", width=2)))
        if not spy_ret.empty:
            common = spy_ret.index.intersection(r50.index)
            wealth_spy = (1 + spy_ret.loc[common]).cumprod()
            fig.add_trace(go.Scatter(x=wealth_spy.index, y=wealth_spy.values,
                                      name="SPY", line=dict(color="black", width=1.5, dash="dash")))

        fig.update_layout(
            title="Growth of $1 — SIMULATED BACKTEST",
            xaxis_title="Date", yaxis_title="Growth of $1",
            yaxis_type="log",
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.8)"),
            height=500,
        )
        st.plotly_chart(fig, width="stretch")

    st.divider()
    st.subheader("Rolling Performance — SIMULATED")
    st.caption("Net of 5 bps one-way transaction costs")

    if not r50.empty:
        windows = {"30-day (2.5 mo)": 3, "60-day (5 mo)": 5, "90-day (7.5 mo)": 8}

        def rolling_cagr(r: pd.Series, w: int) -> pd.Series:
            return (1 + r).rolling(w).apply(lambda x: x.prod() ** (12 / w) - 1, raw=True)

        for label, w in windows.items():
            cols = st.columns(3)
            for i, (short, color) in enumerate([("top50", "steelblue"), ("top10", "darkorange")]):
                r = load_returns(short)
                if r.empty:
                    continue
                rc = rolling_cagr(r, w)
                latest = rc.dropna().iloc[-1] if not rc.dropna().empty else None
                spy_rc = rolling_cagr(spy_ret, w) if not spy_ret.empty else None
                spy_latest = spy_rc.dropna().iloc[-1] if spy_rc is not None and not spy_rc.dropna().empty else None
                name = "Top-50" if short == "top50" else "Top-10"
                if latest is not None:
                    delta = f"{latest - spy_latest:+.2%} vs SPY" if spy_latest else None
                    cols[i].metric(f"{label} — {name}", f"{latest:.2%}", delta)
            if spy_latest is not None:
                cols[2].metric(f"{label} — SPY", f"{spy_latest:.2%}")


# ── TAB: PROJECT LOG ───────────────────────────────────────────────────────────
elif tab == "Project Log":
    st.header("Project Log")
    st.caption("Append-only record of all meaningful changes. Most recent first.")

    log_path = ROOT / "PROJECT_LOG.md"
    if log_path.exists():
        text = log_path.read_text(encoding="utf-8")
        # Reverse entries so most recent appears first
        sections = re.split(r"\n(?=## )", text)
        header = sections[0]
        entries = sections[1:]
        st.markdown(header)
        for entry in reversed(entries):
            with st.expander(entry.splitlines()[0].replace("## ", ""), expanded=False):
                st.markdown(entry)
    else:
        st.warning("PROJECT_LOG.md not found.")
