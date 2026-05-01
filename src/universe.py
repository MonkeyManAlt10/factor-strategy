"""
universe.py — S&P 500 constituent loader.

Scrapes the Wikipedia list of S&P 500 companies once and caches it locally
as data/sp500_constituents.parquet.  Subsequent calls read from cache.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).parent.parent / "data" / "sp500_constituents.parquet"
_WIKIPEDIA_URL = (
    "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
)


def load_sp500_tickers(force_refresh: bool = False) -> list[str]:
    """Return the current list of S&P 500 ticker symbols.

    Reads from a local parquet cache if available; otherwise scrapes Wikipedia
    and writes the cache.  Pass ``force_refresh=True`` to re-scrape.

    Returns
    -------
    list[str]
        Ticker symbols, upper-cased, with dots replaced by hyphens so they
        work with yfinance (e.g. ``BRK-B`` instead of ``BRK.B``).
    """
    if _CACHE_PATH.exists() and not force_refresh:
        logger.info("Loading S&P 500 constituents from cache: %s", _CACHE_PATH)
        df = pd.read_parquet(_CACHE_PATH)
        return df["ticker"].tolist()

    logger.info("Scraping S&P 500 constituents from Wikipedia …")
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # pandas.read_html uses urllib which gets a 403 from Wikipedia; use
    # requests with a browser User-Agent instead.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(_WIKIPEDIA_URL, headers=headers, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(io.StringIO(response.text))
    sp500_table = next(
        (t for t in tables if "Symbol" in t.columns),
        None,
    )
    if sp500_table is None:
        raise RuntimeError("Could not find the S&P 500 table on Wikipedia.")

    tickers: list[str] = (
        sp500_table["Symbol"]
        .str.upper()
        .str.replace(".", "-", regex=False)
        .tolist()
    )

    pd.DataFrame({"ticker": tickers}).to_parquet(_CACHE_PATH, index=False)
    logger.info("Cached %d tickers to %s", len(tickers), _CACHE_PATH)
    return tickers
