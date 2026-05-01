"""
backtest.py — Vectorized monthly-rebalance backtest engine.

Strategy
--------
At each month-end rebalance date:
  1. Compute factor z-scores for all tickers with sufficient history.
  2. Build composite score (price-only factors in backtest mode).
  3. Select top-N tickers; assign equal weight (1/N each).
  4. Hold until the next rebalance date, then repeat.

Transaction costs are not modelled (results/ README notes this).

Returns a ``BacktestResult`` named-tuple with the strategy return series
and the per-date portfolio holdings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.factors import lowvol_zscore, momentum_zscore
from src.screen import composite_score, select_top_n

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Container for backtest outputs."""

    returns: pd.Series          # Monthly strategy returns (index = date)
    holdings: pd.DataFrame      # Columns = tickers, rows = rebalance dates, values = weights
    rebalance_dates: list[pd.Timestamp] = field(default_factory=list)


def run_backtest(
    prices: pd.DataFrame,
    top_n: int = 50,
    momentum_lookback: int = 12,
    vol_lookback: int = 12,
    min_history_months: int = 13,
) -> BacktestResult:
    """Run a monthly equal-weight quality-momentum backtest on *prices*.

    Uses price-only factors (momentum + low-vol) to avoid look-ahead bias.
    No quality factor is used here — see module docstring and README.

    Parameters
    ----------
    prices:
        Monthly adjusted-close prices.  Columns = tickers, index = month-end
        dates.  Output of ``data.load_prices()`` resampled to month-end.
    top_n:
        Number of names to hold each month.
    momentum_lookback, vol_lookback:
        Look-back windows in months.
    min_history_months:
        Minimum months of price history required before a ticker is eligible.
        Default 13 covers the 12+1 momentum window.

    Returns
    -------
    BacktestResult
    """
    dates = prices.index.sort_values()
    min_start_idx = max(momentum_lookback, vol_lookback, min_history_months)

    rebalance_dates: list[pd.Timestamp] = []
    holdings_list: list[pd.Series] = []
    strategy_returns: list[float] = []
    return_dates: list[pd.Timestamp] = []

    for i in range(min_start_idx, len(dates)):
        as_of = dates[i]
        prev_date = dates[i - 1]

        # --- Build factor scores at prev_date (avoid using today's close) ---
        mom = momentum_zscore(prices, prev_date, momentum_lookback)
        vol = lowvol_zscore(prices, prev_date, vol_lookback)

        if mom.empty or vol.empty:
            continue

        score = composite_score(mom, vol, mode="backtest")
        if score.empty:
            continue

        selected = select_top_n(score, n=top_n)
        if not selected:
            continue

        weight = 1.0 / len(selected)
        weights = pd.Series(weight, index=selected)

        # --- Compute portfolio return from prev_date to as_of ---
        available = [t for t in selected if t in prices.columns]
        period_ret = (
            prices.loc[as_of, available] / prices.loc[prev_date, available] - 1.0
        ).dropna()

        port_return = (weights.reindex(period_ret.index).fillna(0) * period_ret).sum()

        rebalance_dates.append(prev_date)
        holdings_list.append(weights)
        strategy_returns.append(port_return)
        return_dates.append(as_of)

        if i % 12 == 0:
            logger.info("Backtest progress: %s  portfolio return this month: %.2f%%", as_of.date(), port_return * 100)

    returns = pd.Series(strategy_returns, index=return_dates, name="strategy")
    holdings = pd.DataFrame(holdings_list, index=rebalance_dates).fillna(0.0)

    return BacktestResult(
        returns=returns,
        holdings=holdings,
        rebalance_dates=rebalance_dates,
    )
