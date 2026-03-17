"""Configuration management for kalshi-autoresearch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "min_trade_usd": 500,
    "implied_range": [0.65, 1.0],
    "skip_categories": [],
    "lookback_days": 30,
    "ewma_decay": 0.94,
    "kelly_fraction": 0.25,
    "bet_size": 100,
}


def load_config(path: str | Path) -> dict[str, Any]:
    """Load config from a JSON file, falling back to defaults for missing keys.

    Args:
        path: Path to the JSON config file.

    Returns:
        Merged config dict with defaults filled in.
    """
    p = Path(path)
    if not p.exists():
        return dict(DEFAULT_CONFIG)
    with open(p, "r") as f:
        user_cfg = json.load(f)
    merged = dict(DEFAULT_CONFIG)
    merged.update(user_cfg)
    return merged


def save_config(config: dict[str, Any], path: str | Path) -> None:
    """Save config dict to a JSON file.

    Args:
        config: Configuration dictionary.
        path: Destination file path.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(config, f, indent=2)
