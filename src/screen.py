"""
screen.py — Composite score construction and top-N selection.

Two scoring modes are supported:

  ``"backtest"``
      Uses only momentum (50%) and low-vol (50%), scaled to sum to 1.
      Safe for historical backtests because no fundamental data is required.

  ``"live"``
      Uses momentum (50%) + low-vol (30%) + quality (20%).
      Requires current fundamentals from yfinance.  Valid only for the live
      strategy (June 2026 onward) where there is no look-ahead bias.

Weights are re-normalised over the factors actually present so that the
composite always sums to 1.0.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

# Default composite weights per the strategy spec
_WEIGHTS_LIVE = {
    "momentum": 0.50,
    "lowvol": 0.30,
    "quality": 0.20,
}

_WEIGHTS_BACKTEST = {
    "momentum": 0.50,
    "lowvol": 0.50,
}

Mode = Literal["backtest", "live"]


def composite_score(
    momentum: pd.Series,
    lowvol: pd.Series,
    quality: pd.Series | None = None,
    mode: Mode = "live",
) -> pd.Series:
    """Combine factor z-scores into a single composite ranking score.

    Parameters
    ----------
    momentum, lowvol:
        Cross-sectional z-scores from ``factors.py``.  Must share the same
        ticker index.
    quality:
        Cross-sectional z-score from ``factors.quality_zscore()``.  Required
        when ``mode="live"``, ignored when ``mode="backtest"``.
    mode:
        ``"backtest"`` uses momentum + low-vol only.
        ``"live"`` uses momentum + low-vol + quality.

    Returns
    -------
    pd.Series
        Composite score indexed by ticker, descending = more attractive.
    """
    if mode == "backtest":
        weights = _WEIGHTS_BACKTEST
        factors = {"momentum": momentum, "lowvol": lowvol}
    else:
        if quality is None:
            raise ValueError("quality factor is required for mode='live'.")
        weights = _WEIGHTS_LIVE
        factors = {"momentum": momentum, "lowvol": lowvol, "quality": quality}

    # Align on common index, drop rows missing any factor
    frame = pd.DataFrame(factors).dropna()

    # Re-normalise weights over present factors (should always be full set,
    # but guards against empty series edge cases)
    present = [k for k in weights if k in frame.columns]
    w = {k: weights[k] for k in present}
    total = sum(w.values())
    w = {k: v / total for k, v in w.items()}

    score = sum(frame[k] * v for k, v in w.items())
    return score.rename("composite_score").sort_values(ascending=False)


def select_top_n(
    score: pd.Series,
    n: int = 50,
) -> list[str]:
    """Return the top-*n* tickers by composite score.

    Parameters
    ----------
    score:
        Output of ``composite_score()``.
    n:
        Number of names to select.

    Returns
    -------
    list[str]
        Ticker symbols, ordered best-to-worst.
    """
    return score.nlargest(n).index.tolist()
