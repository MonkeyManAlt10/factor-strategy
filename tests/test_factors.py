"""Tests for factor calculation correctness."""

import numpy as np
import pandas as pd
import pytest

from src.factors import _zscore, lowvol_zscore, momentum_zscore, quality_zscore


def _make_prices(n_months: int = 24, n_tickers: int = 10, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-31", periods=n_months, freq="ME")
    data = 100 * np.exp(np.cumsum(rng.normal(0.005, 0.04, size=(n_months, n_tickers)), axis=0))
    tickers = [f"T{i:02d}" for i in range(n_tickers)]
    return pd.DataFrame(data, index=dates, columns=tickers)


def _make_fundamentals(n_tickers: int = 10, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    tickers = [f"T{i:02d}" for i in range(n_tickers)]
    return pd.DataFrame(
        {"return_on_assets": rng.uniform(0.01, 0.25, size=n_tickers)},
        index=tickers,
    )


class TestZscore:
    def test_mean_zero(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        z = _zscore(s)
        assert abs(z.mean()) < 1e-10

    def test_std_one(self):
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        z = _zscore(s)
        assert abs(z.std(ddof=1) - 1.0) < 1e-10

    def test_constant_returns_zeros(self):
        s = pd.Series([5.0, 5.0, 5.0])
        z = _zscore(s)
        assert (z == 0).all()

    def test_nans_ignored(self):
        s = pd.Series([1.0, 2.0, np.nan, 4.0])
        z = _zscore(s)
        # NaN input should produce NaN output; non-NaN entries should be z-scored
        assert z.dropna().shape[0] == 3


class TestMomentumZscore:
    def test_returns_series_indexed_by_ticker(self):
        prices = _make_prices()
        as_of = prices.index[-1]
        mom = momentum_zscore(prices, as_of)
        assert isinstance(mom, pd.Series)
        assert set(mom.index).issubset(set(prices.columns))

    def test_insufficient_history_returns_empty(self):
        prices = _make_prices(n_months=5)
        as_of = prices.index[-1]
        mom = momentum_zscore(prices, as_of, lookback_months=12)
        assert mom.empty

    def test_values_are_zscored(self):
        prices = _make_prices()
        as_of = prices.index[-1]
        mom = momentum_zscore(prices, as_of).dropna()
        assert abs(mom.mean()) < 0.1  # roughly centred
        assert abs(mom.std(ddof=1) - 1.0) < 0.2


class TestLowvolZscore:
    def test_returns_series(self):
        prices = _make_prices()
        as_of = prices.index[-1]
        vol = lowvol_zscore(prices, as_of)
        assert isinstance(vol, pd.Series)
        assert len(vol) > 0

    def test_higher_vol_gets_lower_score(self):
        """The highest-vol ticker should have the lowest z-score (inverted)."""
        prices = _make_prices(n_tickers=5)
        # Replace T04 with a high-volatility path (10× the return std)
        rng = np.random.default_rng(99)
        high_vol_returns = rng.normal(0.005, 0.40, size=len(prices))
        prices["T04"] = 100 * np.exp(np.cumsum(high_vol_returns))
        as_of = prices.index[-1]
        vol = lowvol_zscore(prices, as_of).dropna()
        assert vol.idxmin() == "T04"

    def test_insufficient_history_returns_empty(self):
        prices = _make_prices(n_months=3)
        as_of = prices.index[-1]
        vol = lowvol_zscore(prices, as_of, lookback_months=12)
        assert vol.empty


class TestQualityZscore:
    def test_returns_series(self):
        fund = _make_fundamentals()
        qual = quality_zscore(fund)
        assert isinstance(qual, pd.Series)
        assert len(qual) == 10

    def test_higher_roa_gets_higher_score(self):
        fund = pd.DataFrame(
            {"return_on_assets": [0.01, 0.05, 0.20]},
            index=["LOW", "MID", "HIGH"],
        )
        qual = quality_zscore(fund)
        assert qual["HIGH"] > qual["MID"] > qual["LOW"]

    def test_missing_roa_excluded(self):
        fund = pd.DataFrame(
            {"return_on_assets": [0.10, None, 0.15]},
            index=["A", "B", "C"],
        )
        qual = quality_zscore(fund)
        assert "B" not in qual.index
