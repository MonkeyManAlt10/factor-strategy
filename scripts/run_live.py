"""
run_live.py — Generate this month's live strategy picks for all strategies.

Usage
-----
    python scripts/run_live.py [--refresh]

Fetches current prices and fundamentals, computes the full quality-momentum
composite score, and saves picks for each registered strategy to:
    picks/top50/YYYY-MM-DD.md
    picks/top10/YYYY-MM-DD.md

Run monthly on the last trading day starting June 2026.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.live import generate_picks
from src.strategies import STRATEGIES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PICKS_DIR = Path(__file__).parent.parent / "picks"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate live picks for all strategies.")
    p.add_argument("--refresh", action="store_true")
    return p.parse_args()


def write_picks_md(picks, strategy_cfg: dict, out_path: Path) -> None:
    """Write picks to a dated markdown file."""
    today = date.today().isoformat()
    lines = [
        f"# {strategy_cfg['name']} — Live Picks {today}",
        "",
        f"*{strategy_cfg['description']}*",
        "",
        f"| Rank | Ticker | Composite Score | Momentum | Low-Vol | Quality |",
        f"|------|--------|-----------------|----------|---------|---------|",
    ]
    for _, row in picks.iterrows():
        lines.append(
            f"| {row['rank']} | {row['ticker']} | {row['composite_score']:.4f} "
            f"| {row['momentum']:.4f} | {row['lowvol']:.4f} | {row.get('quality', float('nan')):.4f} |"
        )
    lines += ["", f"*Generated: {today}*", ""]
    out_path.write_text("\n".join(lines))
    logger.info("  Saved %s", out_path)


def main() -> None:
    args = parse_args()
    today = date.today().isoformat()

    for key, cfg in STRATEGIES.items():
        short = cfg["short_name"]
        top_n = cfg["portfolio_size"]
        logger.info("Generating picks for %s (top-%d) …", cfg["name"], top_n)

        picks = generate_picks(top_n=top_n, force_data_refresh=args.refresh)

        out_dir = PICKS_DIR / short
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{today}.md"
        write_picks_md(picks, cfg, out_path)

        print(f"\n--- {cfg['name']} (top-{top_n}) ---")
        print(picks.to_string(index=False))

    logger.info("Done — picks saved to picks/top50/ and picks/top10/")


if __name__ == "__main__":
    main()
