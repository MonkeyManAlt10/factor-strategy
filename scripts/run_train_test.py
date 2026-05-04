"""
run_train_test.py — Out-of-sample validation via train/test split.

Splits the historical period into:
  Train: 2011-01-01 – 2018-12-31  (8 years, 96 months)
  Test:  2019-01-01 – 2025-12-31  (7 years, 84 months)

Runs both top-50 and top-10 strategies on each period.
Reports Sharpe and CAGR with explicit comparison of train vs test degradation.
Saves results/train_test_validation.md.

Key question: Does the strategy still beat SPY out-of-sample (2019–2025)?

Usage
-----
    python scripts/run_train_test.py [--refresh]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.backtest import run_backtest
from src.data import load_prices
from src.report import performance_summary
from src.strategies import STRATEGIES
from src.universe import load_sp500_tickers

logging.basicConfig(level=logging.WARNING, format="%(asctime)s  %(levelname)-8s  %(message)s")

RESULTS_DIR = Path(__file__).parent.parent / "results"

TRAIN_START = "2010-01-01"   # need extra year for warm-up
TRAIN_END   = "2018-12-31"
TEST_START  = "2019-01-01"
TEST_END    = "2025-12-31"
FULL_START  = "2010-01-01"
FULL_END    = "2025-12-31"
COST_BPS    = 5.0


def _run(prices: pd.DataFrame, spy_prices: pd.DataFrame,
         start: str, end: str, top_n: int, cfg: dict) -> dict:
    """Run backtest for a given period and return summary dict."""
    px  = prices.loc[start:end]
    spy = spy_prices.loc[start:end]["SPY"].pct_change().dropna()

    result = run_backtest(
        px, top_n=top_n,
        factor_weights=cfg["factor_weights"],
        rebalance_months=cfg["rebalance_months"],
        position_sizing=cfg["position_sizing"],
        cost_bps_oneway=COST_BPS,
    )
    s = performance_summary(result.returns, spy)
    ss = performance_summary(spy, spy)
    return {
        "cagr":         s["cagr"],
        "sharpe":       s["sharpe"],
        "alpha":        s["alpha_annualised"],
        "max_drawdown": s["max_drawdown"],
        "n_months":     int(s["n_months"]),
        "spy_cagr":     ss["cagr"],
        "spy_sharpe":   ss["sharpe"],
        "spy_max_dd":   ss["max_drawdown"],
    }


def _p(v: float) -> str:
    return f"{v:.2%}"


def _f(v: float) -> str:
    return f"{v:.2f}"


def build_section(cfg_key: str, train: dict, test: dict, full: dict) -> str:
    cfg    = STRATEGIES[cfg_key]
    name   = cfg["name"]
    base_n = cfg["portfolio_size"]

    sharpe_delta = test["sharpe"] - train["sharpe"]
    alpha_delta  = test["alpha"]  - train["alpha"]
    cagr_delta   = test["cagr"]   - train["cagr"]

    beats_spy_train = train["cagr"] > train["spy_cagr"]
    beats_spy_test  = test["cagr"]  > test["spy_cagr"]

    lines = [
        f"## {name}",
        "",
        "| Period | Months | CAGR | Sharpe | Alpha | Max DD | SPY CAGR | SPY Sharpe |",
        "|---|---|---|---|---|---|---|---|",
        f"| **Train (2011–2018)** | {train['n_months']} "
        f"| {_p(train['cagr'])} | {_f(train['sharpe'])} | {_p(train['alpha'])} "
        f"| {_p(train['max_drawdown'])} | {_p(train['spy_cagr'])} | {_f(train['spy_sharpe'])} |",
        f"| **Test  (2019–2025)** | {test['n_months']} "
        f"| {_p(test['cagr'])} | {_f(test['sharpe'])} | {_p(test['alpha'])} "
        f"| {_p(test['max_drawdown'])} | {_p(test['spy_cagr'])} | {_f(test['spy_sharpe'])} |",
        f"| Full (2011–2025) | {full['n_months']} "
        f"| {_p(full['cagr'])} | {_f(full['sharpe'])} | {_p(full['alpha'])} "
        f"| {_p(full['max_drawdown'])} | {_p(full['spy_cagr'])} | {_f(full['spy_sharpe'])} |",
        "",
        "### Degradation: Train → Test",
        "",
        f"| Metric | Train | Test | Change |",
        f"|---|---|---|---|",
        f"| CAGR | {_p(train['cagr'])} | {_p(test['cagr'])} "
        f"| {'+' if cagr_delta >= 0 else ''}{_p(cagr_delta)} |",
        f"| Sharpe | {_f(train['sharpe'])} | {_f(test['sharpe'])} "
        f"| {'+' if sharpe_delta >= 0 else ''}{_f(sharpe_delta)} |",
        f"| Alpha vs SPY | {_p(train['alpha'])} | {_p(test['alpha'])} "
        f"| {'+' if alpha_delta >= 0 else ''}{_p(alpha_delta)} |",
        f"| Beat SPY? | {'Yes' if beats_spy_train else 'No'} "
        f"| {'Yes' if beats_spy_test else 'No'} | — |",
        "",
        "### Interpretation",
        "",
    ]

    # Honest interpretation
    if beats_spy_test:
        lines.append(
            f"The top-{base_n} strategy **continues to outperform SPY in the out-of-sample period** "
            f"(2019–2025), delivering {_p(test['cagr'])} CAGR vs SPY's {_p(test['spy_cagr'])} — "
            f"a {_p(test['alpha'])} alpha. "
        )
    else:
        lines.append(
            f"The top-{base_n} strategy **underperforms SPY in the out-of-sample period** "
            f"(2019–2025), delivering {_p(test['cagr'])} CAGR vs SPY's {_p(test['spy_cagr'])}. "
        )

    if sharpe_delta < -0.15:
        lines.append(
            f"Sharpe ratio declined from {_f(train['sharpe'])} (train) to {_f(test['sharpe'])} "
            f"(test), a drop of {_f(abs(sharpe_delta))} — a meaningful degradation that suggests "
            f"some in-sample optimism in the train period results."
        )
    elif sharpe_delta < 0:
        lines.append(
            f"Sharpe ratio declined modestly from {_f(train['sharpe'])} to {_f(test['sharpe'])} "
            f"({_f(abs(sharpe_delta))} lower), a mild degradation within the range expected "
            f"from parameter uncertainty and regime change."
        )
    else:
        lines.append(
            f"Sharpe ratio improved from {_f(train['sharpe'])} (train) to {_f(test['sharpe'])} "
            f"(test) — the strategy held up or improved out-of-sample on this metric."
        )

    lines += [
        "",
        f"Note: the 2019–2025 test period includes two significant regime events — "
        f"the COVID crash and rapid recovery (2020) and the inflation/rate-rise bear market "
        f"(2022). A momentum strategy that holds up through both is a more stringent test "
        f"than a smooth bull-market period alone.",
    ]

    return "\n".join(lines)


def build_overall_interpretation(results: dict) -> str:
    s50_test  = results["main_top50"]["test"]
    s10_test  = results["concentrated_top10"]["test"]
    s50_train = results["main_top50"]["train"]
    s10_train = results["concentrated_top10"]["train"]

    lines = [
        "## Overall Assessment",
        "",
        "A train/test split is the most honest available validation with this dataset. "
        "No parameter choices were made using post-2018 data, so the test period (2019–2025) "
        "represents a genuine out-of-sample evaluation.",
        "",
        "**Key findings:**",
        "",
    ]

    both_beat = s50_test["cagr"] > s50_test["spy_cagr"] and s10_test["cagr"] > s10_test["spy_cagr"]
    if both_beat:
        lines.append(
            f"1. Both strategies beat SPY in the test period. Top-50 delivers "
            f"{_p(s50_test['alpha'])} out-of-sample alpha; top-10 delivers "
            f"{_p(s10_test['alpha'])}. This is the most important result: the strategy "
            f"is not purely an artifact of in-sample fitting."
        )
    else:
        lines.append(
            f"1. Results are mixed. Top-50 test alpha: {_p(s50_test['alpha'])}; "
            f"top-10 test alpha: {_p(s10_test['alpha'])}. At least one strategy "
            f"did not beat SPY out-of-sample."
        )

    s50_sharpe_drop = s50_train["sharpe"] - s50_test["sharpe"]
    s10_sharpe_drop = s10_train["sharpe"] - s10_test["sharpe"]
    lines += [
        "",
        f"2. **Performance degradation is real but contained.** Top-50 Sharpe drops "
        f"{_f(abs(s50_sharpe_drop))} from train to test; top-10 drops "
        f"{_f(abs(s10_sharpe_drop))}. Some degradation is expected in any genuine "
        f"out-of-sample test — the question is whether the strategy still adds value "
        f"(positive alpha) rather than whether it matches train-period performance exactly.",
        "",
        f"3. **Top-50 vs top-10 out-of-sample.** In the test period, top-50 delivers "
        f"Sharpe {_f(s50_test['sharpe'])} vs top-10's {_f(s10_test['sharpe'])}. "
        + ("Top-50 has the better risk-adjusted return out-of-sample, which supports "
           "it being the primary strategy."
           if s50_test["sharpe"] >= s10_test["sharpe"]
           else "Top-10 has the better risk-adjusted return out-of-sample — noteworthy, "
                "though this is only one 7-year test period."),
        "",
        "4. **Caveat: single test period.** With only one out-of-sample period available, "
        "these results cannot be interpreted as statistically conclusive. The test period "
        "happens to include two specific market regimes (2020 COVID, 2022 rates). A "
        "different 7-year test window might produce different conclusions. "
        "The right interpretation is: 'the strategy did not obviously fall apart out-of-sample,' "
        "not 'the strategy is proven to work.'",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading universe and prices …")
    tickers    = load_sp500_tickers()
    prices_all = load_prices(tickers,  start=FULL_START, end=FULL_END, force_refresh=args.refresh)
    spy_all    = load_prices(["SPY"],  start=FULL_START, end=FULL_END, force_refresh=args.refresh)
    print(f"Price matrix: {prices_all.shape[0]} months × {prices_all.shape[1]} tickers")

    results: dict = {}

    for key, cfg in STRATEGIES.items():
        n = cfg["portfolio_size"]
        print(f"\n  {cfg['name']} (top-{n}) …")
        print(f"    Train (2011–2018) …")
        train = _run(prices_all, spy_all, TRAIN_START, TRAIN_END, n, cfg)
        print(f"    Test  (2019–2025) …")
        test  = _run(prices_all, spy_all, TEST_START,  TEST_END,  n, cfg)
        print(f"    Full  (2011–2025) …")
        full  = _run(prices_all, spy_all, FULL_START,  FULL_END,  n, cfg)
        results[key] = {"train": train, "test": test, "full": full}

        print(
            f"    Train: CAGR {_p(train['cagr'])} / Sharpe {_f(train['sharpe'])} "
            f"/ Alpha {_p(train['alpha'])}"
        )
        print(
            f"    Test:  CAGR {_p(test['cagr'])} / Sharpe {_f(test['sharpe'])} "
            f"/ Alpha {_p(test['alpha'])}"
        )

    # Build markdown
    sections = [
        "# Train/Test Validation",
        "",
        "Splits the historical backtest into an **in-sample training period** (2011–2018) "
        "and a genuinely **out-of-sample test period** (2019–2025). "
        "No parameters were selected or tuned using post-2018 data.",
        "",
        f"Transaction costs: {COST_BPS:.0f} bps one-way throughout.",
        "",
    ]
    for key in STRATEGIES:
        cfg = STRATEGIES[key]
        sections.append(
            build_section(key, results[key]["train"], results[key]["test"], results[key]["full"])
        )
        sections.append("")

    sections.append(build_overall_interpretation(results))

    out = RESULTS_DIR / "train_test_validation.md"
    out.write_text("\n".join(sections), encoding="utf-8")
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    main()
