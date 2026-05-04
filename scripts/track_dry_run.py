#!/usr/bin/env python3
"""
Dry-run portfolio tracker for 2026-05-01 picks.
Re-run any day to refresh with latest closing prices.
"""

import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

PICKS_FILE = Path(__file__).parent.parent / "picks" / "_dry_runs" / "2026-05-01.md"
OUTPUT_CSV = Path(__file__).parent.parent / "results" / "dry_run_tracker.csv"
START_DATE = "2026-05-01"
PORTFOLIO_START = 50.0


def parse_tickers(md_path: Path) -> list[str]:
    tickers = []
    for line in md_path.read_text().splitlines():
        m = re.match(r"\|\s*\d+\s*\|\s*(\w+)\s*\|", line)
        if m:
            tickers.append(m.group(1))
    return tickers


def main():
    tickers = parse_tickers(PICKS_FILE)
    if len(tickers) != 50:
        print(f"ERROR: expected 50 tickers, parsed {len(tickers)}")
        sys.exit(1)

    today = date.today()
    end = (today + timedelta(days=1)).isoformat()   # yfinance end is exclusive

    all_symbols = tickers + ["SPY"]
    print(f"Fetching prices for {len(tickers)} holdings + SPY  ({START_DATE} to {today}) ...")

    raw = yf.download(all_symbols, start=START_DATE, end=end, auto_adjust=True, progress=False)
    closes: pd.DataFrame = raw["Close"]

    # Keep only trading days; forward-fill intra-period halts
    closes = closes.dropna(how="all").ffill()

    if closes.empty:
        print("No price data available yet (market may not have closed).")
        sys.exit(0)

    base = closes.iloc[0]
    excluded = [t for t in tickers if pd.isna(base.get(t))]
    if excluded:
        print(f"Warning: no base price for {excluded!r} — excluded from portfolio.")
    active = [t for t in tickers if not pd.isna(base.get(t))]

    per_stock = PORTFOLIO_START / len(active)
    shares = {t: per_stock / base[t] for t in active}
    spy_shares = PORTFOLIO_START / base["SPY"]

    records = []
    for dt, row in closes.iterrows():
        port_val = sum(shares[t] * row[t] for t in active if not pd.isna(row.get(t)))
        spy_val = spy_shares * row["SPY"]
        port_ret = (port_val / PORTFOLIO_START - 1) * 100
        spy_ret  = (spy_val  / PORTFOLIO_START - 1) * 100
        records.append({
            "date":                   dt.date().isoformat(),
            "portfolio_value":        round(port_val, 4),
            "spy_value":              round(spy_val,  4),
            "portfolio_return_pct":   round(port_ret, 4),
            "spy_return_pct":         round(spy_ret,  4),
            "alpha_pct":              round(port_ret - spy_ret, 4),
        })

    df = pd.DataFrame(records)
    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved -> {OUTPUT_CSV}\n")

    first = df.iloc[0]
    last  = df.iloc[-1]
    sep = "-" * 62
    print(sep)
    print("  Dry-Run Portfolio Summary (2026-05-01 picks)")
    print(sep)
    print(f"  Start date  : {first['date']}  (${PORTFOLIO_START:.2f} invested, {len(active)} holdings)")
    print(f"  Latest date : {last['date']}")
    print(f"  Portfolio   : ${last['portfolio_value']:.2f}  ({last['portfolio_return_pct']:+.2f}%)")
    print(f"  SPY         : ${last['spy_value']:.2f}  ({last['spy_return_pct']:+.2f}%)")
    print(f"  Alpha       : {last['alpha_pct']:+.2f}%")
    print(sep)


if __name__ == "__main__":
    main()
