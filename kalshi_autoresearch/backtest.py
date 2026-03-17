"""Fast backtesting engine for prediction market signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import DEFAULT_CONFIG


@dataclass
class BacktestResult:
    """Results from a backtest run."""

    sharpe: float
    total_return: float
    win_rate: float
    max_dd: float
    n_signals: int
    pnl: list[float]


def _passes_filter(pred: dict[str, Any], config: dict[str, Any]) -> bool:
    """Check if a prediction passes the config filters."""
    dollar = pred.get("dollar_observed", 0)
    if dollar < config.get("min_trade_usd", 0):
        return False

    implied = pred.get("implied_pct", 0)
    lo, hi = config.get("implied_range", (0, 1))
    if isinstance(lo, list):
        lo, hi = lo[0], lo[1]
    if not (lo <= implied <= hi):
        return False

    category = pred.get("category", "other")
    skip = config.get("skip_categories", [])
    if category in skip:
        return False

    return True


def backtest(predictions: list[dict[str, Any]], config: dict[str, Any] | None = None) -> BacktestResult:
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

    bet_size = cfg.get("bet_size", 100)
    kelly_fraction = cfg.get("kelly_fraction", 0.25)
    ewma_decay = cfg.get("ewma_decay", 0.94)

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
    ewma_edge = 0.0

    for i, pred in enumerate(filtered):
        implied = pred.get("implied_pct", 0.5)
        outcome = pred.get("outcome", 0)

        # Kelly-sized bet: edge = outcome - implied, sized by kelly_fraction
        raw_pnl = (outcome - implied) * bet_size * kelly_fraction

        # Apply EWMA weighting: recent signals weighted more
        if i == 0:
            ewma_edge = raw_pnl
        else:
            ewma_edge = ewma_decay * ewma_edge + (1 - ewma_decay) * raw_pnl

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
