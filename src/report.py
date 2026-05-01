"""
report.py — Performance analytics and charting.

Provides:
  - ``performance_summary()`` — CAGR, Sharpe, max drawdown, vs-benchmark stats
  - ``plot_cumulative_returns()`` — cumulative wealth chart saved to results/
  - ``plot_drawdown()`` — underwater chart saved to results/
  - ``print_summary()`` — pretty-print the summary dict to stdout
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"


def _drawdown_series(returns: pd.Series) -> pd.Series:
    wealth = (1 + returns).cumprod()
    peak = wealth.cummax()
    return (wealth - peak) / peak


def performance_summary(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    rf_annual: float = 0.0,
) -> dict:
    """Compute standard performance metrics.

    Parameters
    ----------
    strategy_returns, benchmark_returns:
        Monthly return series.  Must overlap in time.
    rf_annual:
        Annual risk-free rate (default 0 for simplicity).

    Returns
    -------
    dict with keys: cagr, volatility, sharpe, max_drawdown, benchmark_cagr,
    benchmark_volatility, benchmark_sharpe, benchmark_max_drawdown,
    information_ratio, alpha_annualised, beta, n_months.
    """
    rf_monthly = (1 + rf_annual) ** (1 / 12) - 1

    common = strategy_returns.index.intersection(benchmark_returns.index)
    s = strategy_returns.loc[common]
    b = benchmark_returns.loc[common]
    n = len(s)

    def _cagr(r: pd.Series) -> float:
        total = (1 + r).prod()
        years = n / 12
        return float(total ** (1 / years) - 1) if years > 0 else np.nan

    def _sharpe(r: pd.Series) -> float:
        excess = r - rf_monthly
        if excess.std() == 0:
            return np.nan
        return float(excess.mean() / excess.std() * np.sqrt(12))

    def _max_dd(r: pd.Series) -> float:
        return float(_drawdown_series(r).min())

    cov_matrix = np.cov(s, b)
    beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] != 0 else np.nan
    alpha_monthly = (s - rf_monthly).mean() - beta * (b - rf_monthly).mean()
    alpha_annual = float((1 + alpha_monthly) ** 12 - 1)

    active = s - b
    ir = float(active.mean() / active.std() * np.sqrt(12)) if active.std() > 0 else np.nan

    return {
        "cagr": _cagr(s),
        "volatility": float(s.std() * np.sqrt(12)),
        "sharpe": _sharpe(s),
        "max_drawdown": _max_dd(s),
        "benchmark_cagr": _cagr(b),
        "benchmark_volatility": float(b.std() * np.sqrt(12)),
        "benchmark_sharpe": _sharpe(b),
        "benchmark_max_drawdown": _max_dd(b),
        "information_ratio": ir,
        "alpha_annualised": alpha_annual,
        "beta": float(beta),
        "n_months": n,
    }


def print_summary(summary: dict) -> None:
    """Pretty-print a performance summary dict."""
    width = 48
    print("=" * width)
    print("  QUALITY-MOMENTUM FACTOR STRATEGY  —  BACKTEST")
    print("=" * width)
    print(f"  Period (months)        : {summary['n_months']}")
    print()
    print("  STRATEGY")
    print(f"    CAGR                 : {summary['cagr']:.2%}")
    print(f"    Volatility (ann.)    : {summary['volatility']:.2%}")
    print(f"    Sharpe Ratio         : {summary['sharpe']:.2f}")
    print(f"    Max Drawdown         : {summary['max_drawdown']:.2%}")
    print()
    print("  BENCHMARK (SPY)")
    print(f"    CAGR                 : {summary['benchmark_cagr']:.2%}")
    print(f"    Volatility (ann.)    : {summary['benchmark_volatility']:.2%}")
    print(f"    Sharpe Ratio         : {summary['benchmark_sharpe']:.2f}")
    print(f"    Max Drawdown         : {summary['benchmark_max_drawdown']:.2%}")
    print()
    print("  VS. BENCHMARK")
    print(f"    Alpha (ann.)         : {summary['alpha_annualised']:.2%}")
    print(f"    Beta                 : {summary['beta']:.2f}")
    print(f"    Information Ratio    : {summary['information_ratio']:.2f}")
    print("=" * width)


def plot_cumulative_returns(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    filename: str = "cumulative_returns.png",
) -> Path:
    """Save a cumulative-wealth chart to results/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    common = strategy_returns.index.intersection(benchmark_returns.index)
    s = (1 + strategy_returns.loc[common]).cumprod()
    b = (1 + benchmark_returns.loc[common]).cumprod()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(s.index, s.values, label="Strategy (top-50 quality-momentum)", linewidth=2)
    ax.plot(b.index, b.values, label="SPY (benchmark)", linewidth=2, linestyle="--", alpha=0.8)
    ax.set_title("Cumulative Returns: Quality-Momentum Strategy vs SPY", fontsize=14)
    ax.set_ylabel("Growth of $1")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out = RESULTS_DIR / filename
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Saved cumulative returns chart: %s", out)
    return out


def plot_drawdown(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    filename: str = "drawdown.png",
) -> Path:
    """Save an underwater (drawdown) chart to results/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    common = strategy_returns.index.intersection(benchmark_returns.index)
    s_dd = _drawdown_series(strategy_returns.loc[common])
    b_dd = _drawdown_series(benchmark_returns.loc[common])

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.fill_between(s_dd.index, s_dd.values, 0, alpha=0.4, label="Strategy drawdown")
    ax.fill_between(b_dd.index, b_dd.values, 0, alpha=0.3, label="SPY drawdown", color="orange")
    ax.set_title("Drawdown: Quality-Momentum Strategy vs SPY", fontsize=14)
    ax.set_ylabel("Drawdown")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out = RESULTS_DIR / filename
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Saved drawdown chart: %s", out)
    return out
