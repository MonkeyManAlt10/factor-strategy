"""
backtest.py — Vectorized monthly-rebalance backtest engine.

Strategy
--------
At each month-end rebalance date:
  1. Compute factor z-scores for all tickers with sufficient history.
  2. Build composite score (price-only factors in backtest mode).
  3. Select top-N tickers; assign equal weight (1/N each).
  4. Hold until the next rebalance date, then repeat.

Transaction costs are modelled as a configurable one-way basis-point charge
applied to the turnover fraction at each rebalance.

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

    returns: pd.Series          # Monthly net returns after transaction costs (index = date)
    gross_returns: pd.Series    # Monthly gross returns before transaction costs
    holdings: pd.DataFrame      # Columns = tickers, rows = rebalance dates, values = weights
    rebalance_dates: list[pd.Timestamp] = field(default_factory=list)
    cost_bps_oneway: float = 5.0


def run_backtest(
    prices: pd.DataFrame,
    top_n: int = 50,
    momentum_lookback: int = 12,
    vol_lookback: int = 12,
    min_history_months: int = 13,
    cost_bps_oneway: float = 5.0,
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
    cost_bps_oneway:
        One-way transaction cost in basis points applied to turnover.
        Round-trip cost on rebalanced names = 2 × cost_bps_oneway.
        Default 5 bps one-way (10 bps round-trip) is conservative for
        large-cap S&P 500 names.

    Returns
    -------
    BacktestResult
    """
    dates = prices.index.sort_values()
    min_start_idx = max(momentum_lookback, vol_lookback, min_history_months)

    rebalance_dates: list[pd.Timestamp] = []
    holdings_list: list[pd.Series] = []
    strategy_returns: list[float] = []
    gross_strategy_returns: list[float] = []
    return_dates: list[pd.Timestamp] = []

    prev_selected_set: set[str] = set()

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

        gross_return = (weights.reindex(period_ret.index).fillna(0) * period_ret).sum()

        # --- Transaction costs: one-way bps × turnover fraction ---
        # Turnover = fraction of portfolio that changes hands (buys or sells).
        # Names entering or leaving the portfolio each generate a one-way cost;
        # names staying but whose weight drifted generate no cost (equal-weight
        # rebalance resets drift, but we charge only for additions/removals).
        current_set = set(selected)
        names_added = current_set - prev_selected_set
        names_removed = prev_selected_set - current_set
        # Each added name is a buy (one-way); each removed name is a sell (one-way).
        # First period has no prior portfolio so full cost applies.
        turnover = (len(names_added) + len(names_removed)) / max(len(current_set), 1)
        cost = turnover * (cost_bps_oneway / 10_000)

        net_return = gross_return - cost

        rebalance_dates.append(prev_date)
        holdings_list.append(weights)
        strategy_returns.append(net_return)
        gross_strategy_returns.append(gross_return)
        return_dates.append(as_of)
        prev_selected_set = current_set

        if i % 12 == 0:
            logger.info(
                "Backtest progress: %s  gross: %.2f%%  cost: %.1f bps  net: %.2f%%",
                as_of.date(), gross_return * 100, cost * 10_000, net_return * 100,
            )

    returns = pd.Series(strategy_returns, index=return_dates, name="strategy")
    gross_returns = pd.Series(gross_strategy_returns, index=return_dates, name="strategy_gross")
    holdings = pd.DataFrame(holdings_list, index=rebalance_dates).fillna(0.0)

    return BacktestResult(
        returns=returns,
        gross_returns=gross_returns,
        holdings=holdings,
        rebalance_dates=rebalance_dates,
        cost_bps_oneway=cost_bps_oneway,
    )
