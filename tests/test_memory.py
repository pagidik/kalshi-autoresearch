"""Tests for memory module."""

import pytest
from kalshi_autoresearch.memory import Memory, Condition, _classify_implied_bucket


class TestClassifyImpliedBucket:
    def test_very_high(self):
        assert _classify_implied_bucket(0.90) == "very_high_implied"
        assert _classify_implied_bucket(0.85) == "very_high_implied"

    def test_high(self):
        assert _classify_implied_bucket(0.75) == "high_implied"
        assert _classify_implied_bucket(0.70) == "high_implied"

    def test_moderate(self):
        assert _classify_implied_bucket(0.65) == "moderate_implied"
        assert _classify_implied_bucket(0.50) == "moderate_implied"


def _sample_predictions():
    return [
        {"category": "politics", "implied_pct": 0.75, "outcome": 1, "dollar_observed": 1000},
        {"category": "politics", "implied_pct": 0.80, "outcome": 1, "dollar_observed": 500},
        {"category": "politics", "implied_pct": 0.70, "outcome": 0, "dollar_observed": 800},
        {"category": "crypto", "implied_pct": 0.90, "outcome": 1, "dollar_observed": 2000},
        {"category": "crypto", "implied_pct": 0.85, "outcome": 0, "dollar_observed": 1500},
    ]


class TestMemory:
    def test_from_predictions_populates_l0(self):
        mem = Memory.from_predictions(_sample_predictions())
        assert "politics" in mem._l0
        assert "crypto" in mem._l0
        assert mem._l0["politics"]["total"] == 3

    def test_from_predictions_populates_l1(self):
        mem = Memory.from_predictions(_sample_predictions())
        assert len(mem._l1) > 0
        labels = [c.label for c in mem._l1]
        assert any("politics" in label for label in labels)

    def test_top_conditions_returns_sorted(self):
        mem = Memory.from_predictions(_sample_predictions())
        top = mem.top_conditions(3)
        assert len(top) <= 3
        if len(top) >= 2:
            assert top[0].edge >= top[1].edge

    def test_should_trade_default_allows(self):
        mem = Memory()
        should, reason = mem.should_trade({"category": "other", "implied_pct": 0.75})
        assert should is True

    def test_should_trade_negative_edge_blocks(self):
        mem = Memory()
        mem._l0["bad_cat"] = {"win_rate": 0.3, "total": 10, "pnl": -2.0, "edge": -0.2}
        should, reason = mem.should_trade({"category": "bad_cat", "implied_pct": 0.75})
        assert should is False

    def test_empty_predictions(self):
        mem = Memory.from_predictions([])
        assert mem._l0 == {}
        assert mem._l1 == []
        assert mem.top_conditions() == []
