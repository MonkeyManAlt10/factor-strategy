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

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
RESULTS   = ROOT / "results"
PICKS_DIR = ROOT / "picks"

LAUNCH_DATE = date(2026, 6, 5)

# ══════════════════════════════════════════════════════════════════════════════
# Design system constants
# ══════════════════════════════════════════════════════════════════════════════
BG_PRIMARY     = "#0a0e1a"
BG_SECONDARY   = "#111827"
BG_TERTIARY    = "#1f2937"
BORDER         = "#1f2937"
BORDER_STRONG  = "#374151"
TEXT_PRIMARY   = "#f9fafb"
TEXT_SECONDARY = "#9ca3af"
TEXT_TERTIARY  = "#6b7280"
ACCENT         = "#3b82f6"
ACCENT_HOVER   = "#2563eb"
ACCENT_AMBER   = "#f59e0b"
ACCENT_GRAY    = "#6b7280"
SUCCESS        = "#10b981"
DANGER         = "#ef4444"

# Legacy aliases used throughout helper functions
CLR_50  = ACCENT
CLR_10  = ACCENT_AMBER
CLR_SPY = ACCENT_GRAY
CLR_POS = SUCCESS
CLR_NEG = DANGER
CLR_BG  = BG_PRIMARY
CLR_BG2 = BG_SECONDARY
CLR_BDR = BORDER_STRONG

# ── Page config (MUST be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="factor-strategy",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS injection — Stripe/Linear-inspired design system
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── base ── */
html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background-color: {BG_PRIMARY} !important;
    color: {TEXT_PRIMARY} !important;
    -webkit-font-smoothing: antialiased;
}}

/* ── hide streamlit chrome ── */
header[data-testid="stHeader"]   {{ display: none !important; }}
#MainMenu                         {{ display: none !important; }}
footer                            {{ display: none !important; }}
.stDeployButton                   {{ display: none !important; }}
[data-testid="stToolbar"]         {{ display: none !important; }}
[data-testid="stDecoration"]      {{ display: none !important; }}
[data-testid="stSidebarNav"]      {{ display: none !important; }}
section[data-testid="stSidebar"]  {{ display: none !important; }}
[data-testid="collapsedControl"]  {{ display: none !important; }}

/* ── container ── */
.block-container {{
    padding-top: 0 !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1440px !important;
}}
div[data-testid="stVerticalBlock"] > div {{ gap: 0.5rem; }}
.element-container {{ margin-bottom: 0 !important; }}

/* ── scrollbar ── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG_PRIMARY}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_STRONG}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #4b5563; }}

/* ── top navigation bar ── */
.topbar {{
    background: {BG_SECONDARY};
    padding: 0 0 0 0;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0;
}}
.topbar-brand {{
    display: flex;
    align-items: center;
    gap: 8px;
}}
.topbar-logo {{
    width: 14px;
    height: 14px;
    background: {ACCENT};
    border-radius: 2px;
    flex-shrink: 0;
    display: inline-block;
}}
.topbar-name {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
    font-weight: 500;
    color: {TEXT_SECONDARY};
    letter-spacing: -0.01em;
}}
.topbar-right {{
    display: flex;
    align-items: center;
    gap: 16px;
    text-align: right;
}}
.topbar-timestamp {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    color: {TEXT_TERTIARY};
    display: flex;
    align-items: center;
    gap: 6px;
}}
.topbar-user {{
    font-family: 'Inter', sans-serif;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4b5563;
}}
.status-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: {SUCCESS};
    display: inline-block;
    flex-shrink: 0;
    animation: pulse-dot 2.5s ease-in-out infinite;
}}
.status-dot.amber {{ background: {ACCENT_AMBER}; }}
@keyframes pulse-dot {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.35; }}
}}

/* ── tabs (styled as Linear-style top nav) ── */
[data-testid="stTabs"] > div:first-child {{
    background: {BG_SECONDARY};
    border-bottom: 1px solid {BORDER_STRONG};
    gap: 0;
    padding: 0;
}}
[data-testid="stTabs"] button[role="tab"] {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: {TEXT_SECONDARY} !important;
    padding: 14px 18px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    background: transparent !important;
    transition: color 150ms ease-out, border-color 150ms ease-out !important;
    margin-right: 2px !important;
    white-space: nowrap !important;
}}
[data-testid="stTabs"] button[role="tab"]:hover {{
    color: {TEXT_PRIMARY} !important;
    background: rgba(255,255,255,0.03) !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: {TEXT_PRIMARY} !important;
    border-bottom: 2px solid {ACCENT} !important;
    background: transparent !important;
    font-weight: 600 !important;
}}
/* Remove Streamlit's default indicator div */
[data-testid="stTabs"] > div:first-child > div:last-child {{
    display: none !important;
}}

/* ── tab content fade in ── */
[data-testid="stTabsContent"] {{
    animation: fadeIn 200ms ease-out;
    padding-top: 24px;
}}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(3px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

/* ── metric cards (native st.metric override for non-custom usage) ── */
[data-testid="metric-container"] {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BORDER_STRONG} !important;
    border-radius: 8px !important;
    padding: 18px 20px 14px 20px !important;
    transition: border-color 150ms ease-out;
}}
[data-testid="metric-container"]:hover {{ border-color: #4b5563 !important; }}
[data-testid="metric-container"] label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: {TEXT_TERTIARY} !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    font-size: 26px !important;
    font-weight: 600 !important;
    color: {TEXT_PRIMARY} !important;
    line-height: 1.15 !important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    font-size: 12px !important;
    font-weight: 400 !important;
}}

/* ── custom metric card (render_metric HTML) ── */
.mc {{
    background: {BG_SECONDARY};
    border: 1px solid {BORDER_STRONG};
    border-radius: 8px;
    padding: 20px 20px 16px 20px;
    height: 100%;
    transition: border-color 150ms ease-out;
    box-sizing: border-box;
}}
.mc:hover {{ border-color: #4b5563; }}
.mc-label {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: {TEXT_TERTIARY};
    margin-bottom: 10px;
}}
.mc-value {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 28px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    line-height: 1.1;
    margin-bottom: 8px;
    letter-spacing: -0.02em;
}}
.mc-delta {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 13px;
    font-weight: 400;
    display: inline-flex;
    align-items: center;
    gap: 2px;
}}
.mc-delta.pos {{ color: {SUCCESS}; }}
.mc-delta.neg {{ color: {DANGER}; }}
.mc-delta.neu {{ color: {TEXT_SECONDARY}; }}
.mc-compare {{
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: {TEXT_SECONDARY};
    margin-top: 5px;
}}

/* ── section headers ── */
.sec-hdr {{
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: {TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding-bottom: 10px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 14px;
    margin-top: 4px;
}}

/* ── status badges ── */
.badge {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px 3px 8px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 10px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.badge-dry {{
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.25);
    color: {ACCENT_AMBER};
}}
.badge-live {{
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.25);
    color: {SUCCESS};
}}
.badge-hist {{
    background: rgba(107,114,128,0.1);
    border: 1px solid rgba(107,114,128,0.25);
    color: {TEXT_SECONDARY};
}}
.badge-dot {{
    width: 5px;
    height: 5px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}}

/* ── hero ── */
.hero {{ padding: 28px 0 8px 0; }}
.hero-title {{
    font-family: 'Inter', sans-serif;
    font-size: 28px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    letter-spacing: -0.025em;
    line-height: 1.2;
    margin-bottom: 8px;
}}
.hero-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    color: {TEXT_SECONDARY};
    line-height: 1.6;
    max-width: 580px;
}}

/* ── countdown card ── */
.countdown {{
    background: {BG_SECONDARY};
    border: 1px solid {BORDER_STRONG};
    border-radius: 8px;
    padding: 24px;
    text-align: center;
}}
.countdown-num {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 52px;
    font-weight: 600;
    color: {ACCENT};
    line-height: 1;
    letter-spacing: -0.04em;
    margin-bottom: 6px;
}}
.countdown-lbl {{
    font-family: 'Inter', sans-serif;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: {TEXT_TERTIARY};
    margin-bottom: 4px;
}}
.countdown-date {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}

/* ── buttons ── */
.stButton > button {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    background: {ACCENT} !important;
    color: #ffffff !important;
    border: 1px solid {ACCENT} !important;
    border-radius: 6px !important;
    padding: 8px 20px !important;
    transition: background 150ms ease-out, border-color 150ms ease-out !important;
    letter-spacing: 0 !important;
}}
.stButton > button:hover {{
    background: {ACCENT_HOVER} !important;
    border-color: {ACCENT_HOVER} !important;
}}
.stButton > button:active {{
    background: #1d4ed8 !important;
}}

/* ── selectbox ── */
[data-testid="stSelectbox"] label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: {TEXT_TERTIARY} !important;
}}
[data-testid="stSelectbox"] > div > div {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BORDER_STRONG} !important;
    border-radius: 6px !important;
    color: {TEXT_PRIMARY} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    min-height: 38px !important;
}}
[data-testid="stSelectbox"] > div > div:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
}}

/* ── dataframe containers ── */
.stDataFrame, [data-testid="stDataFrame"] {{
    border: 1px solid {BORDER_STRONG} !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}}

/* ── dividers ── */
hr {{
    border-color: {BORDER} !important;
    margin: 16px 0 !important;
}}

/* ── alerts ── */
.stAlert {{
    background: {BG_SECONDARY} !important;
    border: 1px solid {BORDER_STRONG} !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}}

/* ── expanders ── */
[data-testid="stExpander"] {{
    border: 1px solid {BORDER_STRONG} !important;
    border-radius: 6px !important;
    background: {BG_SECONDARY} !important;
}}
[data-testid="stExpander"] summary {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: {TEXT_SECONDARY} !important;
    padding: 10px 14px !important;
}}

/* ── spinner ── */
.stSpinner > div {{
    border-top-color: {ACCENT} !important;
}}

/* ── caption ── */
.stCaption, [data-testid="stCaptionContainer"] {{
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important;
    color: {TEXT_TERTIARY} !important;
}}

/* ── markdown body text ── */
[data-testid="stMarkdownContainer"] p {{
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
    color: #d1d5db !important;
}}

/* ── toggle ── */
[data-testid="stToggle"] label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    color: {TEXT_SECONDARY} !important;
}}

/* ── project log timeline ── */
.log-wrap {{
    padding: 4px 0;
}}
.log-entry {{
    display: flex;
    gap: 16px;
    padding: 16px 0;
    border-bottom: 1px solid {BORDER};
    position: relative;
}}
.log-left {{
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 130px;
    padding-top: 2px;
}}
.log-time {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
    color: {TEXT_TERTIARY};
    white-space: nowrap;
    text-align: right;
    width: 100%;
}}
.log-rail {{
    width: 1px;
    background: {BORDER_STRONG};
    flex: 1;
    min-height: 24px;
    margin-top: 6px;
}}
.log-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: {BORDER_STRONG};
    border: 2px solid {BG_PRIMARY};
    margin-top: 6px;
    flex-shrink: 0;
    align-self: flex-start;
}}
.log-body {{
    flex: 1;
    min-width: 0;
}}
.log-title {{
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
    margin-bottom: 6px;
    line-height: 1.4;
}}
.log-meta {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
}}
.log-commit {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11px;
    color: {TEXT_SECONDARY};
    background: {BG_TERTIARY};
    border: 1px solid {BORDER_STRONG};
    border-radius: 4px;
    padding: 1px 7px;
}}
.log-chip {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 10px;
    color: {TEXT_TERTIARY};
    background: {BG_TERTIARY};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 1px 6px;
}}
.log-notes {{
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: {TEXT_SECONDARY};
    line-height: 1.65;
}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Top bar
# ══════════════════════════════════════════════════════════════════════════════
_now_str   = datetime.now().strftime("%b %d, %Y  %H:%M")
_days_left = (LAUNCH_DATE - date.today()).days
_dot_cls   = "amber" if _days_left > 0 else ""

st.markdown(f"""
<div class="topbar">
  <div class="topbar-brand">
    <span class="topbar-logo"></span>
    <span class="topbar-name">factor-strategy</span>
  </div>
  <div class="topbar-right">
    <div class="topbar-timestamp">
      <span class="status-dot {_dot_cls}"></span>
      Updated: {_now_str} ET
    </div>
    <span class="topbar-user">Austin Krauskopf</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# Helper functions  (logic unchanged)
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
    """Fetch prices from entry_date to exit_date. Returns (pnl_df, spy_pct)."""
    all_tickers = list(tickers) + ["SPY"]
    start = (date.fromisoformat(entry_date) - timedelta(days=5)).isoformat()
    end   = (date.fromisoformat(exit_date)  + timedelta(days=3)).isoformat()

    raw = yf.download(all_tickers, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        return pd.DataFrame(), None

    closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw

    entry_ts    = pd.Timestamp(entry_date)
    future_rows = closes[closes.index >= entry_ts]
    if future_rows.empty:
        return pd.DataFrame(), None
    entry_row = future_rows.iloc[0]

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


# ══════════════════════════════════════════════════════════════════════════════
# UI component helpers
# ══════════════════════════════════════════════════════════════════════════════

def render_metric(
    label: str,
    value: str,
    delta: str | None = None,
    positive: bool | None = None,
    compare: str | None = None,
) -> str:
    """Return custom metric card HTML."""
    if delta is None:
        delta_html = ""
    else:
        if positive is None:
            cls, arrow = "neu", ""
        elif positive:
            cls, arrow = "pos", "▲ "
        else:
            cls, arrow = "neg", "▼ "
        delta_html = f'<div class="mc-delta {cls}">{arrow}{delta}</div>'

    compare_html = (
        f'<div class="mc-compare">{compare}</div>' if compare else ""
    )

    return f"""<div class="mc">
  <div class="mc-label">{label}</div>
  <div class="mc-value">{value}</div>
  {delta_html}{compare_html}
</div>"""


def section_header(title: str) -> None:
    st.markdown(f'<div class="sec-hdr">{title}</div>', unsafe_allow_html=True)


def _fmt_pct(val: float | None, decimals: int = 2) -> str:
    if val is None:
        return "—"
    return f"{val:+.{decimals}f}%"


def _fmt_dollar(val: float | None) -> str:
    if val is None:
        return "—"
    return f"${val:+,.0f}"


def style_chart(fig: go.Figure, height: int = 400) -> go.Figure:
    """Apply factor_dark design system to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, -apple-system, sans-serif",
            size=12,
            color=TEXT_SECONDARY,
        ),
        height=height,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=BG_TERTIARY,
            bordercolor=BORDER_STRONG,
            font=dict(
                family="'JetBrains Mono', 'Courier New', monospace",
                size=12,
                color=TEXT_PRIMARY,
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(family="Inter, sans-serif", size=12, color=TEXT_SECONDARY),
            tracegroupgap=8,
        ),
        margin=dict(l=54, r=20, t=48, b=72),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        tickfont=dict(
            family="'JetBrains Mono', 'Courier New', monospace",
            size=11,
            color=TEXT_TERTIARY,
        ),
        tickcolor=BORDER_STRONG,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(55,65,81,0.35)",
        zeroline=False,
        showline=False,
        tickfont=dict(
            family="'JetBrains Mono', 'Courier New', monospace",
            size=11,
            color=TEXT_TERTIARY,
        ),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# Portfolio tab renderer
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

    # ── Header row: month selector + status badge ──────────────────────────────
    hdr_l, hdr_r = st.columns([4, 1])

    def _month_label(idx: int, d: date, is_dry: bool) -> str:
        s = d.strftime("%B %Y")
        if idx == 0:
            return s + ("  [DRY RUN · CURRENT]" if is_dry else "  [CURRENT]")
        return s + ("  [DRY RUN]" if is_dry else "  [HISTORICAL]")

    labels = [_month_label(i, d, dr) for i, (d, _, dr) in enumerate(all_files)]

    with hdr_l:
        if len(all_files) > 1:
            sel_idx = st.selectbox(
                "View month",
                options=range(len(all_files)),
                format_func=lambda i: labels[i],
                key=f"sel_{short}",
            )
        else:
            sel_idx = 0

    sel_date, picks_file, is_dry = all_files[sel_idx]
    is_current = (sel_idx == 0)

    with hdr_r:
        if is_dry:
            badge = '<span class="badge badge-dry"><span class="badge-dot" style="background:#f59e0b"></span>DRY RUN</span>'
        elif is_current and date.today() >= LAUNCH_DATE:
            badge = '<span class="badge badge-live"><span class="badge-dot" style="background:#10b981"></span>LIVE</span>'
        else:
            badge = '<span class="badge badge-hist"><span class="badge-dot" style="background:#6b7280"></span>HISTORICAL</span>'
        st.markdown(f'<div style="padding-top:28px;text-align:right">{badge}</div>',
                    unsafe_allow_html=True)

    # Status note
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

    # ── Parse picks ────────────────────────────────────────────────────────────
    picks_df = parse_picks_md(picks_file)
    if picks_df.empty:
        st.warning("No picks data found in this file.")
        return

    exit_date_str = (
        date.today().isoformat()
        if is_current
        else (
            all_files[sel_idx - 1][0].isoformat()
            if sel_idx - 1 >= 0
            else date.today().isoformat()
        )
    )

    # ── Refresh button (above table, full-width) ───────────────────────────────
    if st.button(f"↻  Refresh {strategy_name} Data", key=f"refresh_{short}", use_container_width=True):
        with st.spinner("Running run_live.py..."):
            res = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "run_live.py")],
                capture_output=True, text=True, cwd=str(ROOT),
            )
        if res.returncode == 0:
            st.toast("Picks refreshed successfully.", icon="✓")
            st.cache_data.clear()
        else:
            st.error("Error:"); st.code(res.stderr[-2000:])

    # ── Fetch P&L ──────────────────────────────────────────────────────────────
    tickers = tuple(picks_df["ticker"].tolist())
    with st.spinner("Fetching prices..."):
        try:
            port_df, spy_pct = fetch_portfolio_data(
                tickers, sel_date.isoformat(), exit_date_str, dollars_per_pick
            )
        except Exception as exc:
            st.error(f"Price fetch error: {exc}")
            port_df, spy_pct = pd.DataFrame(), None

    # ── 4-column custom metric cards ──────────────────────────────────────────
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
    with m1:
        pnl_str = f"${total_pnl:+,.0f}" if not port_df.empty else None
        st.markdown(render_metric(
            "Portfolio Value",
            f"${total_cur:,.0f}" if not port_df.empty else "—",
            delta=pnl_str,
            positive=(total_pnl >= 0) if not port_df.empty else None,
        ), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric(
            f"P&L  ·  {period_label}",
            _fmt_dollar(total_pnl if not port_df.empty else None),
            delta=None,
        ), unsafe_allow_html=True)
    with m3:
        pct_val = total_pct if not port_df.empty else None
        st.markdown(render_metric(
            "Return %",
            _fmt_pct(pct_val),
            delta=None,
            compare="SIMULATED",
        ), unsafe_allow_html=True)
    with m4:
        st.markdown(render_metric(
            "Alpha vs SPY",
            _fmt_pct(alpha_pp),
            positive=(alpha_pp >= 0) if alpha_pp is not None else None,
            compare=f"SPY: {_fmt_pct(spy_pct)}" if spy_pct is not None else None,
        ), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 65/35 split: holdings table | summary panel ────────────────────────────
    col_l, col_r = st.columns([13, 7])

    with col_l:
        section_header(f"Holdings — {sel_date.strftime('%b %d, %Y')}  ·  {len(picks_df)} names")
        st.caption(f"${dollars_per_pick:.0f}/position simulated  ·  SIMULATED")

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
            use_container_width=True,
            hide_index=True,
            height=min(560, 44 + 35 * len(picks_df)),
        )

    with col_r:
        # Score distribution histogram
        if "composite_score" in picks_df.columns:
            scores = picks_df["composite_score"].dropna().sort_values()
            if not scores.empty:
                section_header("Score Distribution")
                fig_hist = go.Figure(go.Bar(
                    x=list(range(len(scores))),
                    y=scores.values,
                    marker=dict(
                        color=scores.values,
                        colorscale=[[0, ACCENT_GRAY], [1, ACCENT]],
                        showscale=False,
                    ),
                    hovertemplate="Rank %{x}: %{y:.4f}<extra></extra>",
                ))
                fig_hist = style_chart(fig_hist, height=160)
                fig_hist.update_layout(
                    margin=dict(l=30, r=10, t=8, b=30),
                    showlegend=False,
                    bargap=0.08,
                    xaxis=dict(showticklabels=False, showgrid=False),
                )
                st.plotly_chart(fig_hist, use_container_width=True,
                                config={"displayModeBar": False})

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
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
            st.caption("*Backtest 2010-2025, net of 5 bps one-way costs*")

        ott = RESULTS / "train_test_validation.md"
        if ott.exists():
            with st.expander("OOS validation", expanded=False):
                text = read_text_safe(ott)
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
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        section_header(f"Position P&L  ·  {period_label}  ·  SIMULATED")

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
            use_container_width=True,
            hide_index=True,
        )

    # ── Compare to other strategy ──────────────────────────────────────────────
    other_short = "top10" if short == "top50" else "top50"
    other_name  = "Top-10" if short == "top50" else "Top-50"
    other_dpp   = 100.0 if other_short == "top10" else 50.0
    other_files = get_all_picks_files(other_short)

    if other_files:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        compare_on = st.toggle(
            f"Compare {other_name} same-month performance",
            key=f"cmp_{short}",
        )
        if compare_on:
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
                    with c1:
                        st.markdown(render_metric(
                            strategy_name, _fmt_pct(this_pp),
                            positive=(this_pp >= 0) if this_pp is not None else None,
                        ), unsafe_allow_html=True)
                    with c2:
                        st.markdown(render_metric(
                            other_name, _fmt_pct(opp),
                            positive=(opp >= 0),
                        ), unsafe_allow_html=True)
                    diff = (opp - this_pp) if this_pp is not None else None
                    with c3:
                        st.markdown(render_metric(
                            f"{other_name} − {strategy_name}", _fmt_pct(diff),
                            positive=(diff >= 0) if diff is not None else None,
                        ), unsafe_allow_html=True)
                    st.caption(f"*Period: {period_label}  ·  SIMULATED*")


# ══════════════════════════════════════════════════════════════════════════════
# Tab navigation
# ══════════════════════════════════════════════════════════════════════════════
tab_overview, tab_top50, tab_top10, tab_perf, tab_log = st.tabs([
    "Overview",
    "Top-50  ·  Primary",
    "Top-10  ·  Concentrated",
    "Performance",
    "Project Log",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    # Hero
    st.markdown("""
<div class="hero">
  <div class="hero-title">Quality-Momentum Factor Strategy</div>
  <div class="hero-sub">
    Systematic, long-only equity strategy selecting S&amp;P 500 stocks via momentum
    and low volatility. Two parallel portfolios — Top-50 (primary) and Top-10 (concentrated
    comparison) — rebalanced monthly with equal weighting.
  </div>
</div>
""", unsafe_allow_html=True)

    # 4-metric headline row
    s50 = load_summary("top50")
    s10 = load_summary("top10")

    if s50:
        net50 = s50.get("net", {})
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            v = net50.get("cagr")
            st.markdown(render_metric(
                "CAGR (Top-50)",
                f"{v:.2%}" if v else "—",
                compare="Backtest 2010-2025",
            ), unsafe_allow_html=True)
        with m2:
            v = net50.get("sharpe")
            spy_s = net50.get("benchmark_sharpe")
            st.markdown(render_metric(
                "Sharpe Ratio",
                f"{v:.2f}" if v else "—",
                compare=f"SPY: {spy_s:.2f}" if spy_s else None,
            ), unsafe_allow_html=True)
        with m3:
            v = net50.get("max_drawdown")
            spy_dd = net50.get("benchmark_max_drawdown")
            st.markdown(render_metric(
                "Max Drawdown",
                f"{v:.2%}" if v else "—",
                positive=(v > spy_dd) if (v and spy_dd) else None,
                compare=f"SPY: {spy_dd:.2%}" if spy_dd else None,
            ), unsafe_allow_html=True)
        with m4:
            v = net50.get("alpha_annualised")
            st.markdown(render_metric(
                "Alpha vs SPY",
                f"{v:.2%}" if v else "—",
                positive=(v >= 0) if v is not None else None,
                compare="Annualised",
            ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # 60/40 split: chart | comparison stats table
    chart_col, stats_col = st.columns([3, 2])

    with chart_col:
        section_header("Cumulative Returns — SIMULATED BACKTEST 2010-2025")
        r50 = load_returns("top50")
        r10 = load_returns("top10")
        if not r50.empty:
            try:
                spy_ret = load_spy_returns(
                    str(r50.index[0].date()), str(r50.index[-1].date())
                )
            except Exception:
                spy_ret = pd.Series(dtype=float)

            w50 = (1 + r50).cumprod()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=w50.index, y=w50.values,
                name="Top-50 (Primary)",
                line=dict(color=CLR_50, width=2),
                fill="tozeroy",
                fillcolor=f"rgba(59,130,246,0.06)",
                hovertemplate="Top-50: $%{y:.2f}<extra></extra>",
            ))
            if not r10.empty:
                w10 = (1 + r10).cumprod()
                fig.add_trace(go.Scatter(
                    x=w10.index, y=w10.values,
                    name="Top-10 (Concentrated)",
                    line=dict(color=CLR_10, width=2),
                    fill="tozeroy",
                    fillcolor=f"rgba(245,158,11,0.05)",
                    hovertemplate="Top-10: $%{y:.2f}<extra></extra>",
                ))
            if not spy_ret.empty:
                common = spy_ret.index.intersection(r50.index)
                w_spy  = (1 + spy_ret.loc[common]).cumprod()
                fig.add_trace(go.Scatter(
                    x=w_spy.index, y=w_spy.values,
                    name="SPY",
                    line=dict(color=CLR_SPY, width=1.5, dash="dash"),
                    hovertemplate="SPY: $%{y:.2f}<extra></extra>",
                ))

            fig.update_layout(
                title=dict(text="Growth of $1  ·  Log scale", font=dict(size=13)),
                yaxis_type="log",
                yaxis_title="Growth of $1",
            )
            fig = style_chart(fig, height=340)
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.caption("Run `python scripts/run_backtest.py` to generate returns data.")

    with stats_col:
        section_header("Strategy Comparison — SIMULATED")
        if s50 and s10:
            rows_def = [
                ("CAGR",              "cagr",              "{:.2%}"),
                ("Volatility",        "volatility",        "{:.2%}"),
                ("Sharpe Ratio",      "sharpe",             "{:.2f}"),
                ("Max Drawdown",      "max_drawdown",       "{:.2%}"),
                ("Alpha vs SPY",      "alpha_annualised",   "{:.2%}"),
                ("Beta",              "beta",               "{:.2f}"),
                ("Info Ratio",        "information_ratio",  "{:.2f}"),
            ]
            spy_map = {
                "cagr": "benchmark_cagr",
                "volatility": "benchmark_volatility",
                "sharpe": "benchmark_sharpe",
                "max_drawdown": "benchmark_max_drawdown",
            }
            tbl: dict[str, list] = {
                "Metric": [],
                "Top-50 · Primary": [],
                "Top-10 · Comparison (Experimental)": [],
                "SPY": [],
            }
            for lbl, key, fmt in rows_def:
                tbl["Metric"].append(lbl)
                v50 = s50.get("net", {}).get(key)
                v10 = s10.get("net", {}).get(key)
                spy = s50.get("net", {}).get(spy_map.get(key, ""))
                tbl["Top-50 · Primary"].append(fmt.format(v50) if v50 is not None else "—")
                tbl["Top-10 · Comparison (Experimental)"].append(fmt.format(v10) if v10 is not None else "—")
                tbl["SPY"].append(fmt.format(spy)    if spy is not None else "—")

            st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)
            st.caption("*Net of 5 bps one-way transaction costs*")
        else:
            st.warning("Run `python scripts/run_backtest.py` to generate summary files.")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Countdown + methodology row
    cd_col, meth_col = st.columns([1, 2])

    with cd_col:
        if _days_left > 0:
            st.markdown(f"""
<div class="countdown">
  <div class="countdown-lbl">Live tracking begins</div>
  <div class="countdown-num">{_days_left}</div>
  <div class="countdown-lbl">days remaining</div>
  <div class="countdown-date">June 5, 2026</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="countdown">
  <div class="countdown-lbl">Status</div>
  <div class="countdown-num" style="font-size:32px;color:{SUCCESS}">LIVE</div>
  <div class="countdown-date">Tracking active since Jun 5, 2026</div>
</div>
""", unsafe_allow_html=True)

    with meth_col:
        section_header("Methodology")
        st.markdown("""
Every month, all S&P 500 constituents are scored on two factors: **price momentum**
(12-1 month return, z-scored) and **low volatility** (inverse of trailing realized
volatility, z-scored). Scores combine at equal weight into a composite rank.

The **Top-50** portfolio holds the top 50 names at 2% each — a diversified, risk-aware
construction with Sharpe 1.15 vs SPY 1.02. The **Top-10** portfolio is a concentrated
experimental comparison tracking whether extra concentration earns its risk premium.

A quality overlay (ROA / ROE / gross margin) was tested but excluded from the primary
strategy after sensitivity analysis showed marginal incremental alpha vs added turnover.
Out-of-sample validation (train 2011-2018, test 2019-2025) confirms positive alpha in
the holdout period. All results are **simulated** and subject to survivorship bias.
""")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
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
with tab_top50:
    section_header("Top-50 Strategy — Primary Portfolio")
    st.caption("Equal weight · 2% per position · monthly rebalance · SIMULATED / DRY RUN")
    render_portfolio_tab("top50", 50.0, "Top-50")


# ══════════════════════════════════════════════════════════════════════════════
# TAB: TOP-10
# ══════════════════════════════════════════════════════════════════════════════
with tab_top10:
    section_header("Top-10 Strategy — Concentrated Comparison")
    st.caption("Equal weight · 10% per position · monthly rebalance · SIMULATED / DRY RUN")
    st.markdown(f"""
<div style="
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.35);
    border-left: 3px solid {ACCENT_AMBER};
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 16px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    line-height: 1.55;
    color: {TEXT_PRIMARY};
">
  <div style="
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.12em;
      color: {ACCENT_AMBER};
      text-transform: uppercase;
      margin-bottom: 6px;
  ">EXPERIMENTAL — NOT A VALIDATED STRATEGY</div>
  Top-10 is a concentrated <b>comparison</b> portfolio, not a validated strategy.
  Out-of-sample testing showed alpha <b>increasing</b> from training to testing
  periods (7.8% → 13.6%), which almost certainly reflects regime-dependent
  exposure to the 2023–2025 mega-cap momentum rally rather than a robust signal.
  Top-10 has worse Sharpe (1.09 vs 1.15) and materially worse drawdown
  (-32.7% vs -21.6%) than the primary top-50 strategy. Tracked for learning and
  live comparison only.
</div>
""", unsafe_allow_html=True)
    render_portfolio_tab("top10", 100.0, "Top-10")


# ══════════════════════════════════════════════════════════════════════════════
# TAB: PERFORMANCE COMPARISON
# ══════════════════════════════════════════════════════════════════════════════
with tab_perf:
    section_header("Performance Comparison")

    if date.today() < LAUNCH_DATE:
        st.caption(
            f"Live tracking begins {LAUNCH_DATE}. "
            f"Showing **backtested** returns (2010-2025). SIMULATED."
        )
    else:
        st.caption("Live cumulative returns since June 5, 2026.")

    r50 = load_returns("top50")
    r10 = load_returns("top10")

    if not r50.empty:
        try:
            spy_ret = load_spy_returns(
                str(r50.index[0].date()), str(r50.index[-1].date())
            )
        except Exception:
            spy_ret = pd.Series(dtype=float)

        # ── Cumulative returns chart (full-width, 400px) ───────────────────────
        w50 = (1 + r50).cumprod()
        fig_cum = go.Figure()

        fig_cum.add_trace(go.Scatter(
            x=w50.index, y=w50.values,
            name="Top-50 (Primary)",
            line=dict(color=CLR_50, width=2),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.07)",
            hovertemplate="Top-50: $%{y:.2f}<extra></extra>",
        ))
        if not r10.empty:
            w10 = (1 + r10).cumprod()
            fig_cum.add_trace(go.Scatter(
                x=w10.index, y=w10.values,
                name="Top-10 (Concentrated)",
                line=dict(color=CLR_10, width=2),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.06)",
                hovertemplate="Top-10: $%{y:.2f}<extra></extra>",
            ))
        if not spy_ret.empty:
            common = spy_ret.index.intersection(r50.index)
            w_spy  = (1 + spy_ret.loc[common]).cumprod()
            fig_cum.add_trace(go.Scatter(
                x=w_spy.index, y=w_spy.values,
                name="SPY",
                line=dict(color=CLR_SPY, width=1.5, dash="dash"),
                hovertemplate="SPY: $%{y:.2f}<extra></extra>",
            ))

        fig_cum.update_layout(
            title=dict(text="Growth of $1 — SIMULATED BACKTEST 2010-2025", font=dict(size=14)),
            yaxis_type="log",
            yaxis_title="Growth of $1 (log)",
        )
        fig_cum = style_chart(fig_cum, height=400)
        st.plotly_chart(fig_cum, use_container_width=True,
                        config={"displayModeBar": False})

        # ── Drawdown chart (full-width, 300px) ────────────────────────────────
        def _compute_drawdown(r: pd.Series) -> pd.Series:
            cumulative = (1 + r).cumprod()
            rolling_max = cumulative.cummax()
            return (cumulative / rolling_max) - 1

        fig_dd = go.Figure()

        dd50 = _compute_drawdown(r50)
        fig_dd.add_trace(go.Scatter(
            x=dd50.index, y=dd50.values * 100,
            name="Top-50 (Primary)",
            line=dict(color=CLR_50, width=1.5),
            fill="tozeroy",
            fillcolor="rgba(239,68,68,0.12)",
            hovertemplate="Top-50 DD: %{y:.1f}%<extra></extra>",
        ))
        if not r10.empty:
            dd10 = _compute_drawdown(r10)
            fig_dd.add_trace(go.Scatter(
                x=dd10.index, y=dd10.values * 100,
                name="Top-10 (Concentrated)",
                line=dict(color=CLR_10, width=1.5),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.08)",
                hovertemplate="Top-10 DD: %{y:.1f}%<extra></extra>",
            ))
        if not spy_ret.empty:
            dd_spy = _compute_drawdown(spy_ret.loc[spy_ret.index.intersection(r50.index)])
            fig_dd.add_trace(go.Scatter(
                x=dd_spy.index, y=dd_spy.values * 100,
                name="SPY",
                line=dict(color=CLR_SPY, width=1, dash="dash"),
                hovertemplate="SPY DD: %{y:.1f}%<extra></extra>",
            ))

        fig_dd.update_layout(
            title=dict(text="Drawdown from Peak — SIMULATED", font=dict(size=14)),
            yaxis_title="Drawdown %",
        )
        fig_dd.update_yaxes(ticksuffix="%")
        fig_dd = style_chart(fig_dd, height=300)
        st.plotly_chart(fig_dd, use_container_width=True,
                        config={"displayModeBar": False})

        # ── Static PNG exports (reference) ────────────────────────────────────
        cp = RESULTS / "cumulative_returns.png"
        dp = RESULTS / "drawdown.png"
        if cp.exists() or dp.exists():
            with st.expander("Static chart exports (matplotlib)"):
                chart_cols = st.columns(2)
                if cp.exists():
                    chart_cols[0].image(str(cp), caption="Cumulative returns — static export")
                if dp.exists():
                    chart_cols[1].image(str(dp), caption="Drawdown — static export")

        # ── Rolling period stats ───────────────────────────────────────────────
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        section_header("Rolling Annualised CAGR — SIMULATED  ·  Net of 5 bps costs")

        def rolling_cagr(r: pd.Series, w: int) -> pd.Series:
            return (1 + r).rolling(w).apply(
                lambda x: x.prod() ** (12 / w) - 1, raw=True
            )

        windows = [("3-month", 3), ("6-month", 6), ("12-month", 12)]
        for label, w in windows:
            c1, c2, c3 = st.columns(3)
            for col_ui, (s_key, color) in zip([c1, c2], [("top50", CLR_50), ("top10", CLR_10)]):
                r = load_returns(s_key)
                if r.empty:
                    continue
                rc     = rolling_cagr(r, w)
                latest = rc.dropna().iloc[-1] if not rc.dropna().empty else None
                name   = "Top-50" if s_key == "top50" else "Top-10"
                spy_rc = rolling_cagr(spy_ret, w) if not spy_ret.empty else None
                spy_l  = spy_rc.dropna().iloc[-1] if spy_rc is not None and not spy_rc.dropna().empty else None
                if latest is not None:
                    delta_str = f"{latest - spy_l:+.2%} vs SPY" if spy_l else None
                    col_ui.metric(f"{label} {name}", f"{latest:.2%}", delta_str)
            if not spy_ret.empty:
                spy_rc2 = rolling_cagr(spy_ret, w)
                spy_l2  = spy_rc2.dropna().iloc[-1] if not spy_rc2.dropna().empty else None
                if spy_l2 is not None:
                    c3.metric(f"{label} SPY", f"{spy_l2:.2%}")
    else:
        st.warning("Run `python scripts/run_backtest.py` to generate returns data.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB: PROJECT LOG
# ══════════════════════════════════════════════════════════════════════════════
with tab_log:
    section_header("Project Log")
    st.caption("Append-only record of all meaningful changes. Most recent first.")

    log_path = ROOT / "PROJECT_LOG.md"
    if not log_path.exists():
        st.warning("PROJECT_LOG.md not found.")
    else:
        text  = read_text_safe(log_path)
        parts = re.split(r"\n(?=## )", text)
        entries = [p for p in parts if p.startswith("## ")]

        def _parse_log_entry(raw: str) -> dict:
            lines = raw.strip().splitlines()
            title_line = lines[0].replace("## ", "").strip()
            commit, files_str, notes = "", "", ""
            for ln in lines[1:]:
                ln = ln.strip()
                if ln.startswith("- **Commit:**"):
                    m = re.search(r"`([a-f0-9]+)`", ln)
                    commit = m.group(1) if m else ""
                elif ln.startswith("- **Files:**"):
                    files_str = ln.replace("- **Files:**", "").strip()
                elif ln.startswith("- **Notes:**"):
                    notes = ln.replace("- **Notes:**", "").strip()
            return {
                "title": title_line,
                "commit": commit,
                "files": files_str,
                "notes": notes,
            }

        def _files_chips(files_str: str) -> str:
            if not files_str:
                return ""
            raw = re.sub(r"`([^`]+)`", r"\1", files_str)
            chips = [f.strip().strip("()").strip()
                     for f in re.split(r"[,;]", raw) if f.strip()]
            return "".join(
                f'<span class="log-chip">{c}</span>'
                for c in chips[:8]
            )

        entries_reversed = list(reversed(entries))
        log_html_parts = ['<div class="log-wrap">']

        for i, raw in enumerate(entries_reversed):
            info = _parse_log_entry(raw)
            title = info["title"]

            # Extract timestamp from title (first word group matching date pattern)
            ts_match = re.match(r"^(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)\s+(.*)", title)
            if ts_match:
                ts_display = ts_match.group(1)
                title_display = ts_match.group(2)
            else:
                ts_display = ""
                title_display = title

            commit_html = (
                f'<span class="log-commit">{info["commit"][:7]}</span>'
                if info["commit"] else ""
            )
            chips_html  = _files_chips(info["files"])
            notes_html  = (
                f'<div class="log-notes">{info["notes"]}</div>'
                if info["notes"] else ""
            )
            meta_html = ""
            if commit_html or chips_html:
                meta_html = f'<div class="log-meta">{commit_html}{chips_html}</div>'

            log_html_parts.append(f"""
<div class="log-entry">
  <div class="log-left">
    <div class="log-time">{ts_display}</div>
    {"<div class='log-rail'></div>" if i < len(entries_reversed) - 1 else ""}
  </div>
  <div style="display:flex;align-items:flex-start;gap:10px;padding-top:2px">
    <div class="log-dot"></div>
    <div class="log-body">
      <div class="log-title">{title_display}</div>
      {meta_html}
      {notes_html}
    </div>
  </div>
</div>""")

        log_html_parts.append("</div>")
        st.markdown("".join(log_html_parts), unsafe_allow_html=True)
