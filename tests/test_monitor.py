"""Tests for monitor module (non-network logic)."""

import pytest
from kalshi_autoresearch.monitor import Monitor


class TestDetectCategory:
    def test_sports(self):
        assert Monitor.detect_category("NFL-SUPERBOWL-2025") == "sports"
        assert Monitor.detect_category("NBA-MVP-LEBRON") == "sports"

    def test_crypto(self):
        assert Monitor.detect_category("BTC-100K-2025") == "crypto"
        assert Monitor.detect_category("ETHEREUM-PRICE") == "crypto"

    def test_politics(self):
        assert Monitor.detect_category("TRUMP-WIN-2024") == "politics"
        assert Monitor.detect_category("SENATE-GA-RUNOFF") == "politics"

    def test_other(self):
        assert Monitor.detect_category("WEATHER-TEMP-NYC") == "other"
        assert Monitor.detect_category("OSCARS-BEST-PICTURE") == "other"

    def test_case_insensitive(self):
        assert Monitor.detect_category("nfl-game") == "sports"
        assert Monitor.detect_category("NFL-GAME") == "sports"


class TestMonitorInit:
    def test_defaults(self):
        monitor = Monitor()
        assert monitor.min_trade_usd == 500
        assert monitor.implied_range == (0.65, 1.0)
        assert monitor.skip_categories == []

    def test_custom_params(self):
        monitor = Monitor(min_trade_usd=1000, implied_range=(0.7, 0.9), skip_categories=["sports"])
        assert monitor.min_trade_usd == 1000
        assert monitor.implied_range == (0.7, 0.9)
        assert monitor.skip_categories == ["sports"]
