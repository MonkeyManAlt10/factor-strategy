"""
run_backtest.py — Full historical backtest entry point.

Runs both registered strategies (top-50 and top-10) in a single pass and
saves separate summary files for each.

Usage
-----
    python scripts/run_backtest.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]
                                   [--refresh]

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
from src.strategies import STRATEGIES
from src.universe import load_sp500_tickers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run quality-momentum factor backtest for all strategies.")
    p.add_argument("--start", default="2010-01-01")
    p.add_argument("--end", default="2025-12-31")
    p.add_argument("--refresh", action="store_true")
    return p.parse_args()


def run_strategy(key: str, cfg: dict, prices: pd.DataFrame, spy_returns: pd.Series) -> dict:
    """Run backtest for one strategy config; return (net_returns, gross_returns, summary_dict)."""
    cost_bps = cfg["cost_bps_oneway"]
    logger.info(
        "Running %s (top-%d, %.0f bps one-way) …",
        cfg["name"], cfg["portfolio_size"], cost_bps,
    )
    result = run_backtest(
        prices,
        top_n=cfg["portfolio_size"],
        cost_bps_oneway=cost_bps,
        factor_weights=cfg["factor_weights"],
        rebalance_months=cfg["rebalance_months"],
        position_sizing=cfg["position_sizing"],
    )
    logger.info("  %d monthly observations", len(result.returns))

    gross_summary = performance_summary(result.gross_returns, spy_returns)
    net_summary = performance_summary(result.returns, spy_returns)

    short = cfg["short_name"]

    result.returns.to_csv(RESULTS_DIR / f"strategy_returns_{short}.csv", header=True)
    result.gross_returns.to_csv(RESULTS_DIR / f"strategy_returns_{short}_gross.csv", header=True)
    result.holdings.to_csv(RESULTS_DIR / f"holdings_{short}.csv")

    combined = {
        "strategy_key": key,
        "strategy_name": cfg["name"],
        "gross": {k: (float(v) if v is not None else None) for k, v in gross_summary.items()},
        "net": {k: (float(v) if v is not None else None) for k, v in net_summary.items()},
        "cost_bps_oneway": cost_bps,
    }
    summary_path = RESULTS_DIR / f"summary_{short}.json"
    with open(summary_path, "w") as f:
        json.dump(combined, f, indent=2)
    logger.info("  Saved %s", summary_path)

    return {"key": key, "cfg": cfg, "result": result, "net": net_summary, "gross": gross_summary}


def main() -> None:
    args = parse_args()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading S&P 500 universe …")
    tickers = load_sp500_tickers()
    logger.info("Universe: %d tickers", len(tickers))

    logger.info("Loading prices %s → %s …", args.start, args.end)
    prices = load_prices(tickers, start=args.start, end=args.end, force_refresh=args.refresh)
    logger.info("Price matrix: %d months × %d tickers", *prices.shape)

    logger.info("Loading SPY benchmark …")
    spy_prices = load_prices(["SPY"], start=args.start, end=args.end, force_refresh=args.refresh)
    spy_returns = spy_prices["SPY"].pct_change().dropna()

    # --- Run all strategies ---
    results = {}
    for key, cfg in STRATEGIES.items():
        results[key] = run_strategy(key, cfg, prices, spy_returns)

    # --- Print side-by-side comparison ---
    print("\n" + "=" * 60)
    print("  BACKTEST COMPARISON — NET OF TRANSACTION COSTS")
    print("=" * 60)
    headers = ["Metric", "Top-50", "Top-10", "SPY"]
    rows = [
        ("CAGR", "cagr"),
        ("Volatility", "volatility"),
        ("Sharpe Ratio", "sharpe"),
        ("Max Drawdown", "max_drawdown"),
        ("Alpha (ann.)", "alpha_annualised"),
        ("Beta", "beta"),
        ("Info Ratio", "information_ratio"),
    ]
    spy_s = performance_summary(spy_returns, spy_returns)

    fmt = "{:<22} {:>10} {:>10} {:>10}"
    print(fmt.format(*headers))
    print("-" * 56)
    for label, key in rows:
        v50 = results["main_top50"]["net"].get(key)
        v10 = results["concentrated_top10"]["net"].get(key)
        vspy = spy_s.get(key)
        def _f(v):
            if v is None:
                return "—"
            if key in ("sharpe", "beta", "information_ratio"):
                return f"{v:.2f}"
            return f"{v:.2%}"
        print(fmt.format(label, _f(v50), _f(v10), _f(vspy)))
    print("=" * 60)

    # --- Combined cumulative returns chart ---
    top50_ret = results["main_top50"]["result"].returns
    top10_ret = results["concentrated_top10"]["result"].returns
    plot_cumulative_returns(
        top50_ret, spy_returns,
        filename="cumulative_returns.png",
        extra_series=[(top10_ret, "Top-10 quality-momentum")],
    )
    plot_drawdown(top50_ret, spy_returns, filename="drawdown.png")
    plot_cumulative_returns(
        results["main_top50"]["result"].gross_returns, spy_returns,
        filename="cumulative_returns_gross.png",
        extra_series=[(results["concentrated_top10"]["result"].gross_returns, "Top-10 (gross)")],
    )

    # --- Keep legacy summary.json pointing to top-50 (backward compat) ---
    import shutil
    shutil.copy(RESULTS_DIR / "summary_top50.json", RESULTS_DIR / "summary.json")

    logger.info("All results saved to %s/", RESULTS_DIR)


if __name__ == "__main__":
    main()
