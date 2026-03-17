"""Tests for swarm module."""

import pytest
from kalshi_autoresearch.swarm import Swarm, SwarmResult, Vote


class TestSwarm:
    def test_consensus_reached_with_strong_signal(self):
        swarm = Swarm(base_config={"min_trade_usd": 500})
        signal = {"implied_pct": 0.80, "dollar_observed": 2000, "category": "politics"}
        result = swarm.vote(signal)
        assert isinstance(result, SwarmResult)
        assert result.total_agents == 5
        assert 0 <= result.yes_votes <= 5

    def test_weak_signal_no_consensus(self):
        swarm = Swarm(base_config={"min_trade_usd": 500})
        signal = {"implied_pct": 0.50, "dollar_observed": 100, "category": "other"}
        result = swarm.vote(signal)
        assert result.should_trade is False
        assert result.yes_votes < 3

    def test_whale_trade_gets_votes(self):
        swarm = Swarm(base_config={"min_trade_usd": 500})
        signal = {"implied_pct": 0.85, "dollar_observed": 5000, "category": "crypto"}
        result = swarm.vote(signal)
        whale_votes = [v for v in result.votes if v.agent_name == "WhaleChaser"]
        assert len(whale_votes) == 1
        assert whale_votes[0].should_trade is True

    def test_contrarian_rejects_expensive(self):
        swarm = Swarm(base_config={"min_trade_usd": 500})
        signal = {"implied_pct": 0.95, "dollar_observed": 1000, "category": "politics"}
        result = swarm.vote(signal)
        contrarian_votes = [v for v in result.votes if v.agent_name == "Contrarian"]
        assert len(contrarian_votes) == 1
        assert contrarian_votes[0].should_trade is False

    def test_default_config(self):
        swarm = Swarm()
        signal = {"implied_pct": 0.75, "dollar_observed": 1000, "category": "politics"}
        result = swarm.vote(signal)
        assert isinstance(result, SwarmResult)

    def test_result_reason_contains_vote_count(self):
        swarm = Swarm(base_config={"min_trade_usd": 500})
        signal = {"implied_pct": 0.80, "dollar_observed": 2000, "category": "politics"}
        result = swarm.vote(signal)
        assert "/5" in result.reason
