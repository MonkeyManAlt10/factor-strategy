"""
data.py — Price and fundamentals loader with parquet cache.

All network calls go through yfinance.  Results are cached in data/ as
parquet files so repeat runs are fast and offline-friendly.

NOTE ON FUNDAMENTALS LOOK-AHEAD BIAS
--------------------------------------
yfinance returns *current* fundamentals (ROA, etc.), not point-in-time
historical values.  Using them in a historical backtest would introduce
look-ahead bias.  Therefore:

  - Backtest (2010–2025): price-derived factors only (momentum, low-vol).
  - Live strategy (June 2026+): full quality-momentum composite, because
    picks are recorded in real time and there is no look-ahead risk.

This distinction is enforced in factors.py and screen.py.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
PRICES_CACHE = DATA_DIR / "prices.parquet"
FUNDAMENTALS_CACHE = DATA_DIR / "fundamentals.parquet"


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

def load_prices(
    tickers: list[str],
    start: str,
    end: str,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Return monthly adjusted-close prices for *tickers*.

    Pulls from yfinance and resamples to month-end.  Results are appended to
    (or replaced in) the local parquet cache keyed on ticker × date.

    Parameters
    ----------
    tickers:
        List of ticker symbols understood by yfinance.
    start, end:
        Date strings ``"YYYY-MM-DD"`` passed to yfinance.
    force_refresh:
        Ignore the local cache and re-download everything.

    Returns
    -------
    pd.DataFrame
        Columns = tickers, index = month-end dates (``pd.Timestamp``).
        Missing values are NaN.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if PRICES_CACHE.exists() and not force_refresh:
        cached = pd.read_parquet(PRICES_CACHE)
        cached_tickers = set(cached.columns)
        need = [t for t in tickers if t not in cached_tickers]
        cache_min = cached.index.min()
        cache_max = cached.index.max()
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        # Price data is monthly so the first entry is the month-end on or after
        # start.  Allow up to 31 days of lead-in before the requested start.
        start_covered = cache_min <= start_ts + pd.DateOffset(months=1)
        # Allow up to 7 calendar days of gap at the end (weekends, holidays)
        end_covered = (end_ts - cache_max).days <= 7
        date_range_ok = start_covered and end_covered
        if not need and date_range_ok:
            logger.info("Prices fully served from cache.")
            return cached.loc[start:end, [t for t in tickers if t in cached.columns]]
        # Cache is stale (date range not covered) — re-download all tickers
        if not date_range_ok:
            logger.info("Cache date range stale (max=%s, need=%s) — re-downloading.",
                        cache_max.date(), end)
            need = tickers
    else:
        cached = pd.DataFrame()
        need = tickers

    if need:
        logger.info("Downloading daily prices for %d tickers …", len(need))
        raw = yf.download(
            need,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if isinstance(raw.columns, pd.MultiIndex):
            daily = raw["Close"]
        else:
            daily = raw[["Close"]] if "Close" in raw.columns else raw

        monthly = daily.resample("ME").last()

        if not cached.empty:
            monthly = pd.concat([cached, monthly], axis=1)
            # remove duplicate columns (prefer freshly downloaded)
            monthly = monthly.loc[:, ~monthly.columns.duplicated(keep="last")]

        monthly.to_parquet(PRICES_CACHE)
        logger.info("Prices cached to %s", PRICES_CACHE)
    else:
        monthly = cached

    cols = [t for t in tickers if t in monthly.columns]
    return monthly.loc[start:end, cols]


# ---------------------------------------------------------------------------
# Fundamentals
# ---------------------------------------------------------------------------

def load_fundamentals(
    tickers: list[str],
    force_refresh: bool = False,
) -> pd.DataFrame:
    """Return current fundamental data for *tickers* from yfinance.

    Cached in data/fundamentals.parquet.  Because yfinance fundamentals are
    point-in-time only for the *current* date, this data must NOT be used in
    historical backtests.  It is intended solely for the live strategy.

    Returns
    -------
    pd.DataFrame
        Index = ticker.  Columns include ``return_on_assets`` and others
        pulled from ``yf.Ticker.info``.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if FUNDAMENTALS_CACHE.exists() and not force_refresh:
        cached = pd.read_parquet(FUNDAMENTALS_CACHE)
        cached_tickers = set(cached.index)
        need = [t for t in tickers if t not in cached_tickers]
    else:
        cached = pd.DataFrame()
        need = tickers

    if need:
        logger.info("Fetching fundamentals for %d tickers …", len(need))
        records: list[dict] = []
        for i, ticker in enumerate(need):
            if i % 50 == 0:
                logger.info("  … %d / %d", i, len(need))
            try:
                info = yf.Ticker(ticker).info
                records.append(
                    {
                        "ticker": ticker,
                        "return_on_assets": info.get("returnOnAssets"),
                        "return_on_equity": info.get("returnOnEquity"),
                        "gross_margins": info.get("grossMargins"),
                        "operating_margins": info.get("operatingMargins"),
                    }
                )
            except Exception as exc:
                logger.warning("Could not fetch fundamentals for %s: %s", ticker, exc)
                records.append({"ticker": ticker})

        new_df = pd.DataFrame(records).set_index("ticker")

        if not cached.empty:
            new_df = pd.concat([cached, new_df])
            new_df = new_df[~new_df.index.duplicated(keep="last")]

        new_df.to_parquet(FUNDAMENTALS_CACHE)
        logger.info("Fundamentals cached to %s", FUNDAMENTALS_CACHE)
    else:
        new_df = cached

    available = [t for t in tickers if t in new_df.index]
    return new_df.loc[available]
