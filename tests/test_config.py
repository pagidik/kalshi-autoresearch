"""Tests for config module."""

import json
from pathlib import Path

import pytest
from kalshi_autoresearch.config import load_config, save_config, DEFAULT_CONFIG


class TestLoadConfig:
    def test_missing_file_returns_defaults(self, tmp_path):
        result = load_config(tmp_path / "nonexistent.json")
        assert result == DEFAULT_CONFIG

    def test_valid_file_merges_with_defaults(self, tmp_path):
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text(json.dumps({"min_trade_usd": 1000}))
        result = load_config(cfg_path)
        assert result["min_trade_usd"] == 1000
        assert result["kelly_fraction"] == DEFAULT_CONFIG["kelly_fraction"]

    def test_returns_copy_not_reference(self, tmp_path):
        result = load_config(tmp_path / "nonexistent.json")
        result["min_trade_usd"] = 9999
        assert DEFAULT_CONFIG["min_trade_usd"] != 9999


class TestSaveConfig:
    def test_creates_file(self, tmp_path):
        path = tmp_path / "out.json"
        save_config({"min_trade_usd": 500}, path)
        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["min_trade_usd"] == 500

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "config.json"
        save_config(DEFAULT_CONFIG, path)
        assert path.exists()
