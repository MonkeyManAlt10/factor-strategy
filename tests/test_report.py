"""Tests for performance analytics."""

import numpy as np
import pandas as pd
import pytest

from src.report import _drawdown_series, performance_summary


def _monthly_returns(cagr: float, n: int = 60, noise: float = 0.02, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2019-01-31", periods=n, freq="ME")
    monthly_mu = (1 + cagr) ** (1 / 12) - 1
    returns = monthly_mu + rng.normal(0, noise, size=n)
    return pd.Series(returns, index=dates)


class TestDrawdownSeries:
    def test_starts_at_zero(self):
        r = _monthly_returns(0.10)
        dd = _drawdown_series(r)
        assert dd.iloc[0] == pytest.approx(0.0)

    def test_always_nonpositive(self):
        r = _monthly_returns(0.10)
        dd = _drawdown_series(r)
        assert (dd <= 0).all()

    def test_always_down_series_is_negative(self):
        r = pd.Series([-0.05] * 12, index=pd.date_range("2020-01-31", periods=12, freq="ME"))
        dd = _drawdown_series(r)
        assert dd.iloc[-1] < 0


class TestPerformanceSummary:
    def test_keys_present(self):
        s = _monthly_returns(0.12, seed=1)
        b = _monthly_returns(0.09, seed=2)
        summary = performance_summary(s, b)
        expected_keys = {
            "cagr", "volatility", "sharpe", "max_drawdown",
            "benchmark_cagr", "benchmark_volatility", "benchmark_sharpe",
            "benchmark_max_drawdown", "information_ratio",
            "alpha_annualised", "beta", "n_months",
        }
        assert expected_keys.issubset(summary.keys())

    def test_higher_return_strategy_has_higher_cagr(self):
        s = _monthly_returns(0.20, seed=1)
        b = _monthly_returns(0.08, seed=2)
        summary = performance_summary(s, b)
        assert summary["cagr"] > summary["benchmark_cagr"]

    def test_n_months_correct(self):
        s = _monthly_returns(0.10, n=60, seed=1)
        b = _monthly_returns(0.09, n=60, seed=2)
        summary = performance_summary(s, b)
        assert summary["n_months"] == 60

    def test_max_drawdown_nonpositive(self):
        s = _monthly_returns(0.10, seed=1)
        b = _monthly_returns(0.09, seed=2)
        summary = performance_summary(s, b)
        assert summary["max_drawdown"] <= 0
        assert summary["benchmark_max_drawdown"] <= 0
