"""
factors.py — Factor calculations: momentum, low-volatility, and quality.

All factor functions return a pd.Series indexed by ticker, with z-scored
values (mean 0, std 1).  Higher z-score = more attractive for that factor
after sign conventions are applied.

Sign conventions
----------------
- Momentum:   high return  → high z-score  (no inversion)
- Low-vol:    low vol      → high z-score  (inverted: multiply by -1)
- Quality:    high ROA     → high z-score  (no inversion)

IMPORTANT: quality_zscore() uses current yfinance fundamentals and must
NOT be called inside a historical backtest loop.  It is only valid for
the live strategy (June 2026 onward).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _zscore(series: pd.Series) -> pd.Series:
    """Return cross-sectional z-score, ignoring NaN."""
    mu = series.mean()
    sigma = series.std(ddof=1)
    if sigma == 0 or np.isnan(sigma):
        return series - series  # all zeros
    return (series - mu) / sigma


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

def momentum_zscore(
    prices: pd.DataFrame,
    as_of: pd.Timestamp,
    lookback_months: int = 12,
    skip_months: int = 1,
) -> pd.Series:
    """12-1 month momentum z-score as of *as_of*.

    Computes the total return from ``as_of - lookback_months`` to
    ``as_of - skip_months``, skipping the most recent month to avoid the
    well-known short-term reversal effect.

    Parameters
    ----------
    prices:
        Monthly adjusted-close price DataFrame (index = month-end dates,
        columns = tickers).
    as_of:
        The rebalance date.  Must be a date present in ``prices.index``.
    lookback_months, skip_months:
        Standard momentum window parameters.

    Returns
    -------
    pd.Series
        Cross-sectional z-score, indexed by ticker.  NaN for tickers with
        insufficient history.
    """
    idx = prices.index.get_loc(as_of)
    if idx < lookback_months:
        return pd.Series(dtype=float)

    start_price = prices.iloc[idx - lookback_months]
    end_price = prices.iloc[idx - skip_months]

    ret = (end_price / start_price) - 1.0
    return _zscore(ret).rename("momentum")


# ---------------------------------------------------------------------------
# Low volatility
# ---------------------------------------------------------------------------

def lowvol_zscore(
    prices: pd.DataFrame,
    as_of: pd.Timestamp,
    lookback_months: int = 12,
) -> pd.Series:
    """Trailing volatility z-score (inverted) as of *as_of*.

    Computes annualised monthly return standard deviation over the trailing
    ``lookback_months`` window, then inverts so that *lower* volatility
    produces a *higher* z-score.

    Parameters
    ----------
    prices:
        Monthly adjusted-close price DataFrame.
    as_of:
        Rebalance date present in ``prices.index``.
    lookback_months:
        Number of monthly returns to include.

    Returns
    -------
    pd.Series
        Inverted cross-sectional z-score, indexed by ticker.
    """
    idx = prices.index.get_loc(as_of)
    if idx < lookback_months:
        return pd.Series(dtype=float)

    window = prices.iloc[idx - lookback_months : idx + 1]
    monthly_returns = window.pct_change().dropna(how="all")

    ann_vol = monthly_returns.std(ddof=1) * np.sqrt(12)
    return _zscore(-ann_vol).rename("lowvol")  # invert: low vol → high score


# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

def quality_zscore(fundamentals: pd.DataFrame) -> pd.Series:
    """Return-on-assets quality z-score.

    Uses current yfinance fundamentals.

    *** BACKTEST WARNING ***
    This function must NOT be used inside a historical backtest loop.
    yfinance provides only the *current* ROA value, so using it at past
    rebalance dates would introduce look-ahead bias.  It is valid only for
    the live strategy, where picks are recorded at the time of calculation.

    Parameters
    ----------
    fundamentals:
        DataFrame returned by ``data.load_fundamentals()``, indexed by ticker.

    Returns
    -------
    pd.Series
        Cross-sectional z-score of ``return_on_assets``, indexed by ticker.
    """
    roa = fundamentals["return_on_assets"].dropna().astype(float)
    return _zscore(roa).rename("quality")
