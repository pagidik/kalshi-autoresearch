"""Unit tests for the backtest engine using synthetic data."""

import pytest
from kalshi_autoresearch.backtest import backtest, BacktestResult


def _make_predictions(n: int, win_rate: float = 0.7, implied: float = 0.65) -> list[dict]:
    """Generate synthetic predictions for testing."""
    preds = []
    for i in range(n):
        outcome = 1 if (i % int(1 / win_rate) != 0) else 0
        preds.append({
            "implied_pct": implied,
            "outcome": outcome,
            "dollar_observed": 1000,
            "category": "politics",
        })
    return preds


class TestBacktest:
    def test_empty_predictions_returns_zero(self):
        result = backtest([], {})
        assert isinstance(result, BacktestResult)
        assert result.sharpe == 0.0
        assert result.n_signals == 0
        assert result.pnl == []

    def test_all_winners_positive_return(self):
        preds = [
            {"implied_pct": 0.70, "outcome": 1, "dollar_observed": 1000, "category": "politics"}
            for _ in range(20)
        ]
        result = backtest(preds, {"min_trade_usd": 500, "implied_range": [0.65, 1.0]})
        assert result.total_return > 0
        assert result.win_rate == 1.0
        assert result.n_signals == 20

    def test_all_losers_negative_return(self):
        preds = [
            {"implied_pct": 0.70, "outcome": 0, "dollar_observed": 1000, "category": "crypto"}
            for _ in range(20)
        ]
        result = backtest(preds, {"min_trade_usd": 500, "implied_range": [0.65, 1.0]})
        assert result.total_return < 0
        assert result.win_rate == 0.0

    def test_filter_excludes_small_trades(self):
        preds = [
            {"implied_pct": 0.75, "outcome": 1, "dollar_observed": 100, "category": "politics"},
            {"implied_pct": 0.75, "outcome": 1, "dollar_observed": 1000, "category": "politics"},
        ]
        result = backtest(preds, {"min_trade_usd": 500, "implied_range": [0.65, 1.0]})
        assert result.n_signals == 1

    def test_filter_excludes_skipped_categories(self):
        preds = [
            {"implied_pct": 0.75, "outcome": 1, "dollar_observed": 1000, "category": "sports"},
            {"implied_pct": 0.75, "outcome": 1, "dollar_observed": 1000, "category": "politics"},
        ]
        result = backtest(preds, {
            "min_trade_usd": 500,
            "implied_range": [0.65, 1.0],
            "skip_categories": ["sports"],
        })
        assert result.n_signals == 1

    def test_sharpe_is_finite(self):
        preds = _make_predictions(50)
        result = backtest(preds, {"min_trade_usd": 500, "implied_range": [0.60, 1.0]})
        assert result.sharpe != float("inf")
        assert result.sharpe != float("-inf")
        assert result.n_signals > 0
