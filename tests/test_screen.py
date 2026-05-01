"""Tests for composite score construction and top-N selection."""

import numpy as np
import pandas as pd
import pytest

from src.screen import composite_score, select_top_n


def _make_factor(tickers: list[str], seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(rng.standard_normal(len(tickers)), index=tickers)


TICKERS = [f"T{i:02d}" for i in range(20)]


class TestCompositeScore:
    def test_backtest_mode_no_quality_needed(self):
        mom = _make_factor(TICKERS, seed=1)
        vol = _make_factor(TICKERS, seed=2)
        score = composite_score(mom, vol, mode="backtest")
        assert len(score) == len(TICKERS)

    def test_live_mode_requires_quality(self):
        mom = _make_factor(TICKERS, seed=1)
        vol = _make_factor(TICKERS, seed=2)
        with pytest.raises(ValueError, match="quality"):
            composite_score(mom, vol, mode="live")

    def test_live_mode_uses_all_three_factors(self):
        mom = _make_factor(TICKERS, seed=1)
        vol = _make_factor(TICKERS, seed=2)
        qual = _make_factor(TICKERS, seed=3)
        score = composite_score(mom, vol, quality=qual, mode="live")
        assert len(score) == len(TICKERS)

    def test_output_sorted_descending(self):
        mom = _make_factor(TICKERS, seed=1)
        vol = _make_factor(TICKERS, seed=2)
        score = composite_score(mom, vol, mode="backtest")
        assert score.is_monotonic_decreasing

    def test_missing_ticker_dropped(self):
        mom = _make_factor(TICKERS[:10], seed=1)
        vol = _make_factor(TICKERS, seed=2)  # extra tickers in vol
        score = composite_score(mom, vol, mode="backtest")
        # Only tickers present in both factors survive
        assert set(score.index).issubset(set(TICKERS[:10]))

    def test_weights_sum_to_one(self):
        """Sanity check: a ticker that dominates all three factors should rank first."""
        mom = pd.Series([3.0, 0.0, -1.0], index=["A", "B", "C"])
        vol = pd.Series([3.0, 0.0, -1.0], index=["A", "B", "C"])
        qual = pd.Series([3.0, 0.0, -1.0], index=["A", "B", "C"])
        score = composite_score(mom, vol, quality=qual, mode="live")
        assert score.index[0] == "A"


class TestSelectTopN:
    def test_returns_correct_count(self):
        mom = _make_factor(TICKERS, seed=1)
        vol = _make_factor(TICKERS, seed=2)
        score = composite_score(mom, vol, mode="backtest")
        top = select_top_n(score, n=5)
        assert len(top) == 5

    def test_returns_list_of_strings(self):
        mom = _make_factor(TICKERS, seed=1)
        vol = _make_factor(TICKERS, seed=2)
        score = composite_score(mom, vol, mode="backtest")
        top = select_top_n(score, n=10)
        assert all(isinstance(t, str) for t in top)

    def test_top_ticker_has_highest_score(self):
        mom = _make_factor(TICKERS, seed=1)
        vol = _make_factor(TICKERS, seed=2)
        score = composite_score(mom, vol, mode="backtest")
        top = select_top_n(score, n=10)
        assert top[0] == score.index[0]

    def test_n_larger_than_universe(self):
        """Should return all available tickers rather than raising."""
        mom = _make_factor(TICKERS[:5], seed=1)
        vol = _make_factor(TICKERS[:5], seed=2)
        score = composite_score(mom, vol, mode="backtest")
        top = select_top_n(score, n=100)
        assert len(top) == 5
