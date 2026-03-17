"""Multi-agent consensus voting for trade decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Vote:
    """A single agent's vote on a signal."""

    agent_name: str
    should_trade: bool
    reason: str


@dataclass
class SwarmResult:
    """Result of a swarm consensus vote."""

    should_trade: bool
    yes_votes: int
    total_agents: int
    reason: str
    votes: list[Vote] = field(default_factory=list)


class _Agent:
    """Base class for swarm agents."""

    name: str = "BaseAgent"

    def vote(self, signal: dict[str, Any], config: dict[str, Any]) -> Vote:
        raise NotImplementedError


class _WhaleChaser(_Agent):
    """Follows large-dollar trades."""

    name = "WhaleChaser"

    def vote(self, signal: dict[str, Any], config: dict[str, Any]) -> Vote:
        dollar = signal.get("dollar_observed", 0)
        threshold = config.get("min_trade_usd", 500) * 2
        if dollar >= threshold:
            return Vote(self.name, True, f"Whale trade: ${dollar:.0f} >= ${threshold:.0f}")
        return Vote(self.name, False, f"Trade too small: ${dollar:.0f} < ${threshold:.0f}")


class _MomentumRider(_Agent):
    """Bets on high-implied-probability signals."""

    name = "MomentumRider"

    def vote(self, signal: dict[str, Any], config: dict[str, Any]) -> Vote:
        implied = signal.get("implied_pct", 0)
        if implied >= 0.80:
            return Vote(self.name, True, f"Strong momentum: {implied:.0%}")
        return Vote(self.name, False, f"Weak momentum: {implied:.0%}")


class _Contrarian(_Agent):
    """Bets against the crowd on overpriced signals."""

    name = "Contrarian"

    def vote(self, signal: dict[str, Any], config: dict[str, Any]) -> Vote:
        implied = signal.get("implied_pct", 0)
        if implied >= 0.90:
            return Vote(self.name, False, "Too expensive, contrarian pass")
        if 0.65 <= implied <= 0.80:
            return Vote(self.name, True, f"Value zone: {implied:.0%}")
        return Vote(self.name, False, f"Outside contrarian range: {implied:.0%}")


class _Conservative(_Agent):
    """Only trades when all conditions align."""

    name = "Conservative"

    def vote(self, signal: dict[str, Any], config: dict[str, Any]) -> Vote:
        implied = signal.get("implied_pct", 0)
        dollar = signal.get("dollar_observed", 0)
        min_usd = config.get("min_trade_usd", 500)
        if implied >= 0.75 and dollar >= min_usd * 1.5:
            return Vote(self.name, True, "Conditions aligned for conservative entry")
        return Vote(self.name, False, "Conditions not strong enough for conservative entry")


class _ValueHunter(_Agent):
    """Looks for edge based on category performance."""

    name = "ValueHunter"

    def vote(self, signal: dict[str, Any], config: dict[str, Any]) -> Vote:
        category = signal.get("category", "other")
        implied = signal.get("implied_pct", 0)
        # Heuristic: politics/crypto tend to have more mispricing
        high_value_cats = {"politics", "crypto"}
        if category in high_value_cats and implied >= 0.70:
            return Vote(self.name, True, f"Value found in {category} at {implied:.0%}")
        if implied >= 0.85:
            return Vote(self.name, True, f"High implied value at {implied:.0%}")
        return Vote(self.name, False, f"No value edge detected in {category}")


class Swarm:
    """Multi-agent consensus voting system for trade decisions.

    Builds 5 internal agents with different strategies and requires
    a 3-of-5 consensus to approve a trade.

    Args:
        base_config: Configuration dict passed to each agent for thresholds.
    """

    CONSENSUS_THRESHOLD = 3

    def __init__(self, base_config: dict[str, Any] | None = None) -> None:
        self.config = base_config or {}
        self._agents: list[_Agent] = [
            _WhaleChaser(),
            _MomentumRider(),
            _Contrarian(),
            _Conservative(),
            _ValueHunter(),
        ]

    def vote(self, signal: dict[str, Any]) -> SwarmResult:
        """Run all agents and return consensus result.

        Args:
            signal: A signal dict with implied_pct, dollar_observed, category.

        Returns:
            SwarmResult with vote tally and decision.
        """
        votes = [agent.vote(signal, self.config) for agent in self._agents]
        yes_votes = sum(1 for v in votes if v.should_trade)
        should_trade = yes_votes >= self.CONSENSUS_THRESHOLD

        if should_trade:
            reasons = [v.reason for v in votes if v.should_trade]
            reason = f"Consensus ({yes_votes}/5): " + "; ".join(reasons)
        else:
            reasons = [v.reason for v in votes if not v.should_trade]
            reason = f"No consensus ({yes_votes}/5): " + "; ".join(reasons)

        return SwarmResult(
            should_trade=should_trade,
            yes_votes=yes_votes,
            total_agents=len(self._agents),
            reason=reason,
            votes=votes,
        )
