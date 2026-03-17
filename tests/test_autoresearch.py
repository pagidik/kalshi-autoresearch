"""Tests for autoresearch optimization module."""

import json
from pathlib import Path

import pytest
from kalshi_autoresearch.autoresearch import Autoresearch, AutoresearchResult, _random_config, _perturb_config


def _sample_predictions():
    """Generate small sample prediction dataset."""
    return [
        {"implied_pct": 0.70, "outcome": 1, "dollar_observed": 1000, "category": "politics"},
        {"implied_pct": 0.75, "outcome": 1, "dollar_observed": 800, "category": "politics"},
        {"implied_pct": 0.80, "outcome": 0, "dollar_observed": 1200, "category": "crypto"},
        {"implied_pct": 0.65, "outcome": 1, "dollar_observed": 600, "category": "sports"},
        {"implied_pct": 0.90, "outcome": 0, "dollar_observed": 2000, "category": "politics"},
        {"implied_pct": 0.70, "outcome": 1, "dollar_observed": 900, "category": "crypto"},
        {"implied_pct": 0.85, "outcome": 1, "dollar_observed": 1500, "category": "politics"},
        {"implied_pct": 0.72, "outcome": 0, "dollar_observed": 700, "category": "other"},
    ]


class TestRandomConfig:
    def test_returns_required_keys(self):
        cfg = _random_config()
        assert "min_trade_usd" in cfg
        assert "implied_range" in cfg
        assert "kelly_fraction" in cfg
        assert "ewma_decay" in cfg

    def test_implied_range_valid(self):
        for _ in range(20):
            cfg = _random_config()
            lo, hi = cfg["implied_range"]
            assert lo < hi
            assert 0.5 <= lo <= 0.8
            assert 0.75 <= hi <= 1.0


class TestPerturbConfig:
    def test_returns_modified_config(self):
        base = _random_config()
        perturbed = _perturb_config(base)
        assert set(perturbed.keys()) >= {"min_trade_usd", "implied_range", "ewma_decay", "kelly_fraction"}

    def test_implied_range_stays_valid(self):
        base = {"min_trade_usd": 500, "implied_range": [0.65, 1.0], "ewma_decay": 0.94, "kelly_fraction": 0.25}
        for _ in range(20):
            perturbed = _perturb_config(base)
            lo, hi = perturbed["implied_range"]
            assert lo < hi


class TestAutoresearch:
    def test_run_returns_result(self, tmp_path):
        ar = Autoresearch(waves=1, per_wave=3, log_file=tmp_path / "log.jsonl", output_config_path=tmp_path / "best.json")
        result = ar.run(_sample_predictions())
        assert isinstance(result, AutoresearchResult)
        assert result.total_experiments == 3
        assert result.best_config is not None

    def test_saves_best_config(self, tmp_path):
        output_path = tmp_path / "best.json"
        ar = Autoresearch(waves=1, per_wave=2, log_file=tmp_path / "log.jsonl", output_config_path=output_path)
        ar.run(_sample_predictions())
        assert output_path.exists()
        cfg = json.loads(output_path.read_text())
        assert "min_trade_usd" in cfg

    def test_writes_log_file(self, tmp_path):
        log_path = tmp_path / "log.jsonl"
        ar = Autoresearch(waves=1, per_wave=2, log_file=log_path, output_config_path=tmp_path / "best.json")
        ar.run(_sample_predictions())
        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_multi_wave_improves(self, tmp_path):
        ar = Autoresearch(waves=2, per_wave=5, log_file=tmp_path / "log.jsonl", output_config_path=tmp_path / "best.json")
        result = ar.run(_sample_predictions())
        assert result.total_experiments == 10
        assert result.improvements >= 1
