"""Quickstart example: load predictions and run autoresearch."""

import json
from pathlib import Path

from kalshi_autoresearch import Autoresearch

# Load your predictions (list of dicts with implied_pct, outcome, dollar_observed, category)
predictions = json.loads(Path("predictions.json").read_text())

# Run self-improving parameter search
ar = Autoresearch(waves=3, per_wave=20)
result = ar.run(predictions)

print(f"Best Sharpe: {result.best_sharpe:.4f}")
print(f"Best config: {result.best_config}")
print(f"Total experiments: {result.total_experiments}")
print(f"Improvements found: {result.improvements}")
