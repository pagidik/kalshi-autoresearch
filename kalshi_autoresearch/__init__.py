"""
kalshi-autoresearch: Self-improving signal detection for Kalshi prediction markets.

A Python library that applies autoresearch methodology to find, evaluate,
and continuously improve trading signals on Kalshi.
"""

from .monitor import Monitor
from .autoresearch import Autoresearch
from .memory import Memory
from .swarm import Swarm
from .backtest import backtest

__version__ = "0.1.0"
__all__ = ["Monitor", "Autoresearch", "Memory", "Swarm", "backtest"]
