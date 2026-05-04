"""
run_backtest.py — Full historical backtest entry point.

Usage
-----
    python scripts/run_backtest.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                   [--top-n N] [--refresh]

Runs the price-only (momentum + low-vol) backtest from 2010 to 2025 by
default, saves results to results/, and prints the performance summary.

NOTE: Quality (ROA) factor is intentionally excluded from the backtest
because yfinance provides only current fundamentals, not point-in-time
historical values.  Including it would introduce look-ahead bias.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running as `python scripts/run_backtest.py` from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.backtest import run_backtest
from src.data import load_prices
from src.report import (
    performance_summary,
    plot_cumulative_returns,
    plot_drawdown,
    print_summary,
)
from src.universe import load_sp500_tickers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run quality-momentum factor backtest.")
    p.add_argument("--start", default="2010-01-01", help="Backtest start date (YYYY-MM-DD)")
    p.add_argument("--end", default="2025-12-31", help="Backtest end date (YYYY-MM-DD)")
    p.add_argument("--top-n", type=int, default=50, help="Number of holdings per period")
    p.add_argument("--refresh", action="store_true", help="Force re-download of cached data")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Universe ---
    logger.info("Loading S&P 500 universe …")
    tickers = load_sp500_tickers()
    logger.info("Universe: %d tickers", len(tickers))

    # --- Prices (strategy) ---
    logger.info("Loading prices %s → %s …", args.start, args.end)
    prices = load_prices(tickers, start=args.start, end=args.end, force_refresh=args.refresh)
    logger.info("Price matrix: %d months × %d tickers", *prices.shape)

    # --- Benchmark (SPY) ---
    logger.info("Loading SPY benchmark …")
    spy_prices = load_prices(["SPY"], start=args.start, end=args.end, force_refresh=args.refresh)
    spy_returns = spy_prices["SPY"].pct_change().dropna()

    # --- Backtest ---
    cost_bps = 5.0  # one-way basis points; 10 bps round-trip on rebalanced names
    logger.info("Running backtest (top-%d, price-only factors, %.0f bps one-way cost) …", args.top_n, cost_bps)
    result = run_backtest(prices, top_n=args.top_n, cost_bps_oneway=cost_bps)
    logger.info("Backtest complete: %d monthly observations", len(result.returns))

    # --- Analytics (gross and net) ---
    gross_summary = performance_summary(result.gross_returns, spy_returns)
    net_summary = performance_summary(result.returns, spy_returns)

    print("\n--- GROSS (before transaction costs) ---")
    print_summary(gross_summary)
    print("\n--- NET (after transaction costs: %.0f bps one-way) ---" % cost_bps)
    print_summary(net_summary)

    # --- Save outputs ---
    result.returns.to_csv(RESULTS_DIR / "strategy_returns.csv", header=True)
    result.gross_returns.to_csv(RESULTS_DIR / "strategy_returns_gross.csv", header=True)
    spy_returns.to_csv(RESULTS_DIR / "spy_returns.csv", header=True)
    result.holdings.to_csv(RESULTS_DIR / "holdings.csv")

    combined_summary = {
        "gross": {k: (float(v) if v is not None else None) for k, v in gross_summary.items()},
        "net": {k: (float(v) if v is not None else None) for k, v in net_summary.items()},
        "cost_bps_oneway": cost_bps,
    }
    summary_path = RESULTS_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(combined_summary, f, indent=2)
    logger.info("Saved summary (gross + net) to %s", summary_path)

    plot_cumulative_returns(result.returns, spy_returns)
    plot_drawdown(result.returns, spy_returns)
    plot_cumulative_returns(result.gross_returns, spy_returns, filename="cumulative_returns_gross.png")

    logger.info("All results saved to %s/", RESULTS_DIR)


if __name__ == "__main__":
    main()
