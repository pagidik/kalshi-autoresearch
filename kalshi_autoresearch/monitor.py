"""Watch Kalshi public API for large trades and detect signals."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)

KALSHI_TRADES_URL = (
    "https://api.elections.kalshi.com/trade-api/v2/markets/trades"
)

# Simple keyword-based category detection
_CATEGORY_PATTERNS: dict[str, list[str]] = {
    "sports": ["nfl", "nba", "mlb", "nhl", "soccer", "tennis", "sports", "game", "match", "player"],
    "crypto": ["btc", "eth", "bitcoin", "ethereum", "crypto", "sol", "solana", "coin"],
    "politics": ["trump", "biden", "election", "senate", "house", "president", "gop", "dem", "vote", "governor"],
}


@dataclass
class Signal:
    """A detected trading signal from the Kalshi public feed."""

    market: str
    ticker: str
    side: str
    price: float
    implied_pct: float
    dollar_observed: float
    category: str
    fired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class Monitor:
    """Watches Kalshi public trades API for large-dollar signals.

    Args:
        min_trade_usd: Minimum dollar value to consider a trade significant.
        implied_range: Tuple of (min, max) implied probability to include.
        skip_categories: Categories to exclude from results.
    """

    def __init__(
        self,
        min_trade_usd: float = 500,
        implied_range: tuple[float, float] = (0.65, 1.0),
        skip_categories: Optional[list[str]] = None,
    ) -> None:
        self.min_trade_usd = min_trade_usd
        self.implied_range = implied_range
        self.skip_categories = skip_categories or []

    @staticmethod
    def detect_category(ticker: str) -> str:
        """Classify a ticker into a category based on keyword matching.

        Args:
            ticker: The Kalshi market ticker string.

        Returns:
            One of 'sports', 'crypto', 'politics', or 'other'.
        """
        lower = ticker.lower()
        for category, keywords in _CATEGORY_PATTERNS.items():
            for kw in keywords:
                if kw in lower:
                    return category
        return "other"

    def scan(self) -> list[Signal]:
        """Hit the Kalshi public trades endpoint and return qualifying signals.

        Returns:
            List of Signal objects that pass the configured filters.
            Returns empty list on API failure.
        """
        try:
            resp = requests.get(
                KALSHI_TRADES_URL,
                params={"limit": 100},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Kalshi API request failed: %s", exc)
            return []

        data = resp.json()
        trades = data.get("trades", [])
        signals: list[Signal] = []

        for trade in trades:
            ticker = trade.get("ticker", "")
            price_cents = trade.get("yes_price") or trade.get("no_price") or 0
            count = trade.get("count", 1)

            price = price_cents / 100.0 if price_cents > 1 else price_cents
            dollar_observed = price * count * 100  # contracts are $1 notional, price in cents

            # Recompute with raw cents for dollar calc
            dollar_observed = price_cents * count  # cents * contracts = total cents
            dollar_observed /= 100.0  # convert to dollars

            if dollar_observed < self.min_trade_usd:
                continue

            implied_pct = price
            if not (self.implied_range[0] <= implied_pct <= self.implied_range[1]):
                continue

            category = self.detect_category(ticker)
            if category in self.skip_categories:
                continue

            side = trade.get("taker_side", "unknown")

            signals.append(
                Signal(
                    market=trade.get("market_ticker", ticker),
                    ticker=ticker,
                    side=side,
                    price=price,
                    implied_pct=implied_pct,
                    dollar_observed=dollar_observed,
                    category=category,
                    fired_at=datetime.now(timezone.utc),
                )
            )

        return signals
