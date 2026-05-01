"""
run_live.py — Generate this week's live strategy picks.

Usage
-----
    python scripts/run_live.py [--top-n N] [--refresh]

Fetches current prices and fundamentals, computes the full quality-momentum
composite score, selects the top-N names, and appends them (with today's
date) to results/live_picks.csv.

Run this every week (or monthly at rebalance) starting June 2026 to build
a time-stamped live track record.

NOTE: This uses current yfinance fundamentals (ROA).  There is no look-ahead
bias because picks are recorded in real time as of today's date.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.live import generate_picks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate live quality-momentum picks.")
    p.add_argument("--top-n", type=int, default=50, help="Number of holdings to select")
    p.add_argument("--refresh", action="store_true", help="Force re-download of cached data")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    picks = generate_picks(top_n=args.top_n, force_data_refresh=args.refresh)
    print(picks.to_string(index=False))


if __name__ == "__main__":
    main()
