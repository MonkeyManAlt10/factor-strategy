"""
live.py — Generate this week's live strategy picks.

Called weekly from scripts/run_live.py starting June 2026.  Picks are
time-stamped and appended to results/live_picks.csv so that a running
track record accumulates over time.

This module uses the full quality-momentum composite (momentum + low-vol +
quality / ROA) because picks are recorded at the time of calculation —
there is no look-ahead bias when the fundamental data is current.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import pandas as pd

from src.data import load_fundamentals, load_prices
from src.factors import lowvol_zscore, momentum_zscore, quality_zscore
from src.screen import composite_score, select_top_n
from src.universe import load_sp500_tickers

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"
LIVE_PICKS_PATH = RESULTS_DIR / "live_picks.csv"

# Price history needed to compute trailing factors
_PRICE_HISTORY_MONTHS = 14


def generate_picks(
    top_n: int = 50,
    force_data_refresh: bool = False,
) -> pd.DataFrame:
    """Compute today's composite scores and return the top-N picks.

    Appends the picks (with today's date) to results/live_picks.csv.

    Parameters
    ----------
    top_n:
        Number of names to select.
    force_data_refresh:
        Re-download prices and fundamentals even if cached.

    Returns
    -------
    pd.DataFrame
        Columns: ``date``, ``ticker``, ``rank``, ``composite_score``,
        ``momentum``, ``lowvol``, ``quality``.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    tickers = load_sp500_tickers()

    # Pull ~14 months of price history so we have enough for 12-1 momentum
    end = pd.Timestamp.today().normalize()
    start = (end - pd.DateOffset(months=_PRICE_HISTORY_MONTHS)).strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    prices = load_prices(tickers, start=start, end=end_str, force_refresh=force_data_refresh)
    fundamentals = load_fundamentals(tickers, force_refresh=force_data_refresh)

    if prices.empty:
        raise RuntimeError("No price data returned — check your internet connection.")

    as_of = prices.index[-1]
    logger.info("Computing live picks as of %s", as_of.date())

    mom = momentum_zscore(prices, as_of)
    vol = lowvol_zscore(prices, as_of)
    qual = quality_zscore(fundamentals)

    score = composite_score(mom, vol, quality=qual, mode="live")
    selected = select_top_n(score, n=top_n)

    rows = []
    for rank, ticker in enumerate(selected, start=1):
        rows.append(
            {
                "date": as_of.date(),
                "ticker": ticker,
                "rank": rank,
                "composite_score": round(score.get(ticker, float("nan")), 4),
                "momentum": round(mom.get(ticker, float("nan")), 4),
                "lowvol": round(vol.get(ticker, float("nan")), 4),
                "quality": round(qual.get(ticker, float("nan")), 4),
            }
        )

    picks_df = pd.DataFrame(rows)

    # Append to running track record
    if LIVE_PICKS_PATH.exists() and LIVE_PICKS_PATH.stat().st_size > 0:
        existing = pd.read_csv(LIVE_PICKS_PATH)
        # Avoid duplicate entries for the same date
        existing = existing[existing["date"] != str(as_of.date())]
        combined = pd.concat([existing, picks_df], ignore_index=True)
    else:
        combined = picks_df

    combined.to_csv(LIVE_PICKS_PATH, index=False)
    logger.info("Saved %d picks to %s", len(picks_df), LIVE_PICKS_PATH)

    return picks_df
