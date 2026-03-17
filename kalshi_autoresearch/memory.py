"""L0/L1/L2 hierarchical memory system for trading signal patterns."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Condition:
    """A learned condition/pattern from historical predictions."""

    label: str
    win_rate: float
    total_bets: int
    pnl: float
    edge: float


class Memory:
    """Hierarchical memory for learning from prediction outcomes.

    Three levels:
        L0: Category-level aggregate stats (sports, crypto, politics, etc.)
        L1: Condition-level patterns (e.g., "high implied + crypto")
        L2: Raw prediction log reference
    """

    def __init__(self) -> None:
        self._l0: dict[str, dict[str, float]] = {}
        self._l1: list[Condition] = []
        self._l2: list[dict[str, Any]] = []

    @classmethod
    def from_predictions(cls, predictions: list[dict[str, Any]]) -> Memory:
        """Build a Memory from a list of prediction dicts.

        Each prediction should have: category, implied_pct, outcome, dollar_observed.

        Args:
            predictions: List of prediction dicts with outcomes.

        Returns:
            Populated Memory instance.
        """
        mem = cls()
        mem._l2 = list(predictions)

        # L0: category-level stats
        cat_wins: dict[str, int] = defaultdict(int)
        cat_total: dict[str, int] = defaultdict(int)
        cat_pnl: dict[str, float] = defaultdict(float)

        for pred in predictions:
            cat = pred.get("category", "other")
            outcome = pred.get("outcome", 0)
            implied = pred.get("implied_pct", 0.5)
            cat_total[cat] += 1
            cat_wins[cat] += outcome
            cat_pnl[cat] += outcome - implied

        for cat in cat_total:
            total = cat_total[cat]
            wins = cat_wins[cat]
            wr = wins / total if total > 0 else 0.0
            mem._l0[cat] = {
                "win_rate": wr,
                "total": total,
                "pnl": cat_pnl[cat],
                "edge": wr - 0.5,
            }

        # L1: condition-level patterns
        # Bin by (category, implied_bucket) for richer patterns
        cond_data: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"wins": 0, "total": 0, "pnl": 0.0}
        )

        for pred in predictions:
            cat = pred.get("category", "other")
            implied = pred.get("implied_pct", 0.5)
            outcome = pred.get("outcome", 0)

            if implied >= 0.85:
                bucket = "very_high_implied"
            elif implied >= 0.70:
                bucket = "high_implied"
            else:
                bucket = "moderate_implied"

            key = f"{cat}_{bucket}"
            cond_data[key]["wins"] += outcome
            cond_data[key]["total"] += 1
            cond_data[key]["pnl"] += outcome - implied

        for label, stats in cond_data.items():
            total = stats["total"]
            if total == 0:
                continue
            wr = stats["wins"] / total
            mem._l1.append(
                Condition(
                    label=label,
                    win_rate=wr,
                    total_bets=total,
                    pnl=stats["pnl"],
                    edge=wr - 0.5,
                )
            )

        mem._l1.sort(key=lambda c: c.edge, reverse=True)
        return mem

    def top_conditions(self, n: int = 5) -> list[Condition]:
        """Return the top N conditions by edge.

        Args:
            n: Number of top conditions to return.

        Returns:
            List of Condition objects sorted by edge descending.
        """
        return self._l1[:n]

    def should_trade(self, signal: dict[str, Any]) -> tuple[bool, str]:
        """Decide whether to trade a signal based on learned patterns.

        Args:
            signal: A signal dict with category, implied_pct.

        Returns:
            Tuple of (should_trade, reason).
        """
        cat = signal.get("category", "other")
        implied = signal.get("implied_pct", 0.5)

        # Check L0: category-level
        cat_stats = self._l0.get(cat)
        if cat_stats and cat_stats["edge"] < -0.1:
            return False, f"Category '{cat}' has negative edge ({cat_stats['edge']:.2f})"

        if cat_stats and cat_stats["total"] < 5:
            return True, f"Insufficient data for category '{cat}', allowing trade"

        # Check L1: condition-level
        if implied >= 0.85:
            bucket = "very_high_implied"
        elif implied >= 0.70:
            bucket = "high_implied"
        else:
            bucket = "moderate_implied"

        key = f"{cat}_{bucket}"
        for cond in self._l1:
            if cond.label == key:
                if cond.edge > 0 and cond.total_bets >= 3:
                    return True, f"Condition '{key}' has positive edge ({cond.edge:.2f})"
                elif cond.edge < -0.05 and cond.total_bets >= 5:
                    return False, f"Condition '{key}' has negative edge ({cond.edge:.2f})"
                break

        return True, "No strong signal from memory, defaulting to trade"
