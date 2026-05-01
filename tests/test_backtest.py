"""Sanity tests for the backtest engine."""

import numpy as np
import pandas as pd
import pytest

from src.backtest import run_backtest


def _make_prices(n_months: int = 36, n_tickers: int = 60, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-01-31", periods=n_months, freq="ME")
    data = 100 * np.exp(
        np.cumsum(rng.normal(0.005, 0.04, size=(n_months, n_tickers)), axis=0)
    )
    tickers = [f"TICK{i:03d}" for i in range(n_tickers)]
    return pd.DataFrame(data, index=dates, columns=tickers)


class TestRunBacktest:
    def test_returns_nonempty(self):
        prices = _make_prices()
        result = run_backtest(prices, top_n=10)
        assert not result.returns.empty

    def test_return_index_is_dates(self):
        prices = _make_prices()
        result = run_backtest(prices, top_n=10)
        assert isinstance(result.returns.index, pd.DatetimeIndex)

    def test_holdings_weights_sum_to_one(self):
        prices = _make_prices()
        result = run_backtest(prices, top_n=10)
        row_sums = result.holdings.sum(axis=1)
        # Each rebalance row should sum to ~1.0
        assert ((row_sums - 1.0).abs() < 1e-9).all()

    def test_fewer_months_than_lookback_handled(self):
        """Backtest with very short history should return empty rather than crash."""
        prices = _make_prices(n_months=5, n_tickers=10)
        result = run_backtest(prices, top_n=5)
        assert result.returns.empty or len(result.returns) == 0

    def test_no_nan_in_returns(self):
        prices = _make_prices()
        result = run_backtest(prices, top_n=10)
        assert not result.returns.isna().any()

    def test_top_n_respected(self):
        prices = _make_prices()
        result = run_backtest(prices, top_n=10)
        # Each holdings row should have at most top_n non-zero weights
        nonzero_counts = (result.holdings > 0).sum(axis=1)
        assert (nonzero_counts <= 10).all()
