"""
kalshi-autoresearch: Self-improving signal detection for Kalshi prediction markets.

A Python library that applies autoresearch methodology to find, evaluate,
and continuously improve trading signals on Kalshi.
"""

from .backtest import backtest, BacktestResult
from .config import load_config, save_config, DEFAULT_CONFIG
from .monitor import Monitor, Signal
from .autoresearch import Autoresearch, AutoresearchResult
from .memory import Memory, Condition
from .swarm import Swarm, SwarmResult

__version__ = "0.1.0"
__all__ = [
    "Monitor", "Signal",
    "Autoresearch", "AutoresearchResult",
    "Memory", "Condition",
    "Swarm", "SwarmResult",
    "backtest", "BacktestResult",
    "load_config", "save_config", "DEFAULT_CONFIG",
]
