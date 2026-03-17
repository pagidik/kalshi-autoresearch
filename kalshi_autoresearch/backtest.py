"""Fast backtesting engine for prediction market signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import DEFAULT_CONFIG
from .types import Prediction


@dataclass
class BacktestResult:
    """Results from a backtest run."""

    sharpe: float
    total_return: float
    win_rate: float
    max_dd: float
    n_signals: int
    pnl: list[float]


def _passes_filter(pred: Prediction, config: dict[str, Any]) -> bool:
    """Check if a prediction passes the config filters."""
    dollar = pred.get("dollar_observed", 0)
    if dollar < config.get("min_trade_usd", 0):
        return False

    implied = pred.get("implied_pct", 0)
    implied_range = config.get("implied_range", [0, 1])
    range_low, range_high = implied_range[0], implied_range[1]
    if not (range_low <= implied <= range_high):
        return False

    category = pred.get("category", "other")
    skip = config.get("skip_categories", [])
    if category in skip:
        return False

    return True


def backtest(predictions: list[Prediction], config: dict[str, Any] | None = None) -> BacktestResult:
    """Run a backtest over a list of prediction dicts.

    Each prediction dict should contain:
        - implied_pct: float, the implied probability at entry
        - outcome: int, 1 for win, 0 for loss
        - dollar_observed: float, dollar volume observed
        - category: str, market category

    Args:
        predictions: List of prediction dicts with outcomes.
        config: Backtest configuration. Uses DEFAULT_CONFIG if None.

    Returns:
        BacktestResult with performance metrics.
    """
    cfg = dict(DEFAULT_CONFIG)
    if config:
        cfg.update(config)

    bet_size = cfg["bet_size"]
    kelly_fraction = cfg["kelly_fraction"]

    filtered = [p for p in predictions if _passes_filter(p, cfg)]

    if not filtered:
        return BacktestResult(
            sharpe=0.0,
            total_return=0.0,
            win_rate=0.0,
            max_dd=0.0,
            n_signals=0,
            pnl=[],
        )

    pnl: list[float] = []

    for pred in filtered:
        implied = pred.get("implied_pct", 0.5)
        outcome = pred.get("outcome", 0)

        # Kelly-sized bet: edge = outcome - implied, sized by kelly_fraction
        raw_pnl = (outcome - implied) * bet_size * kelly_fraction
        pnl.append(raw_pnl)

    pnl_arr = np.array(pnl)
    total_return = float(np.sum(pnl_arr))
    wins = sum(1 for p in pnl_arr if p > 0)
    win_rate = wins / len(pnl_arr) if len(pnl_arr) > 0 else 0.0

    # Sharpe ratio (annualized assuming daily signals)
    if len(pnl_arr) > 1 and np.std(pnl_arr) > 0:
        sharpe = float(np.mean(pnl_arr) / np.std(pnl_arr) * np.sqrt(252))
    else:
        sharpe = 0.0

    # Max drawdown
    cumulative = np.cumsum(pnl_arr)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = running_max - cumulative
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    return BacktestResult(
        sharpe=sharpe,
        total_return=total_return,
        win_rate=win_rate,
        max_dd=max_dd,
        n_signals=len(filtered),
        pnl=pnl_arr.tolist(),
    )
