"""
strategies.py — Strategy configuration registry.

Each entry defines a named strategy variant with its key parameters.
Both strategies use the same momentum + low-vol factors and monthly
rebalance schedule; they differ only in portfolio concentration.
"""

from __future__ import annotations

STRATEGIES: dict[str, dict] = {
    "main_top50": {
        "name": "Quality-Momentum Top-50",
        "short_name": "top50",
        "portfolio_size": 50,
        "factor_weights": {"momentum": 0.5, "lowvol": 0.5},
        "rebalance_months": 1,
        "position_sizing": "equal",
        "cost_bps_oneway": 5.0,
        "description": (
            "Primary strategy. Holds the top-50 S&P 500 stocks by composite "
            "quality-momentum score, rebalanced monthly, equal weight."
        ),
    },
    "concentrated_top10": {
        "name": "Quality-Momentum Top-10",
        "short_name": "top10",
        "portfolio_size": 10,
        "factor_weights": {"momentum": 0.5, "lowvol": 0.5},
        "rebalance_months": 1,
        "position_sizing": "equal",
        "cost_bps_oneway": 5.0,
        "description": (
            "Concentrated comparison portfolio. Holds the top-10 names by the "
            "same composite score. Included as a higher-conviction parallel "
            "experiment; it has not been validated out-of-sample."
        ),
    },
}
