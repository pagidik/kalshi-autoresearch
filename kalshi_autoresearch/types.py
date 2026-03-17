"""Shared type definitions for kalshi-autoresearch."""

from __future__ import annotations

from typing import TypedDict


class Prediction(TypedDict, total=False):
    """A prediction dict with outcome data for backtesting."""

    implied_pct: float
    outcome: int
    dollar_observed: float
    category: str


class SignalDict(TypedDict, total=False):
    """A signal dict for swarm voting and memory decisions."""

    implied_pct: float
    dollar_observed: float
    category: str
