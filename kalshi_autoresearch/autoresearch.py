"""Self-improving parameter search loop for trading signal optimization."""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .backtest import backtest
from .config import DEFAULT_CONFIG, save_config

logger = logging.getLogger(__name__)


@dataclass
class AutoresearchResult:
    """Results from an autoresearch optimization run."""

    best_sharpe: float
    best_config: dict[str, Any]
    total_experiments: int
    improvements: int
    top_configs: list[dict[str, Any]]


def _random_config() -> dict[str, Any]:
    """Generate a random parameter configuration."""
    lo = round(random.uniform(0.50, 0.80), 2)
    hi = round(random.uniform(max(lo + 0.05, 0.75), 1.0), 2)
    return {
        "min_trade_usd": random.choice([100, 200, 500, 750, 1000, 2000]),
        "implied_range": [lo, hi],
        "skip_categories": random.choice([[], ["sports"], ["other"], ["sports", "other"]]),
        "lookback_days": random.choice([7, 14, 30, 60, 90]),
        "ewma_decay": round(random.uniform(0.85, 0.99), 2),
        "kelly_fraction": round(random.uniform(0.05, 0.50), 2),
        "bet_size": random.choice([50, 100, 200]),
    }


def _perturb_config(config: dict[str, Any]) -> dict[str, Any]:
    """Perturb a winning config to explore nearby parameter space."""
    new = dict(config)

    # Perturb min_trade_usd
    new["min_trade_usd"] = max(50, new.get("min_trade_usd", 500) + random.choice([-200, -100, 0, 100, 200]))

    # Perturb implied_range
    lo, hi = new.get("implied_range", [0.65, 1.0])
    lo = round(max(0.50, min(0.90, lo + random.uniform(-0.05, 0.05))), 2)
    hi = round(max(lo + 0.05, min(1.0, hi + random.uniform(-0.05, 0.05))), 2)
    new["implied_range"] = [lo, hi]

    # Perturb EWMA decay
    new["ewma_decay"] = round(
        max(0.80, min(0.99, new.get("ewma_decay", 0.94) + random.uniform(-0.03, 0.03))), 2
    )

    # Perturb kelly_fraction
    new["kelly_fraction"] = round(
        max(0.05, min(0.50, new.get("kelly_fraction", 0.25) + random.uniform(-0.05, 0.05))), 2
    )

    return new


class Autoresearch:
    """Self-improving parameter search loop.

    Generates parameter candidates, backtests each, and keeps improvements.
    Later waves perturb winners from earlier waves for focused search.

    Args:
        waves: Number of optimization waves to run.
        per_wave: Number of experiments per wave.
        log_file: Path to JSONL log file for experiment results.
    """

    def __init__(
        self,
        waves: int = 5,
        per_wave: int = 40,
        log_file: str | Path = "autoresearch-log.jsonl",
    ) -> None:
        self.waves = waves
        self.per_wave = per_wave
        self.log_file = Path(log_file)

    def run(self, predictions: list[dict[str, Any]]) -> AutoresearchResult:
        """Run the autoresearch optimization loop.

        Args:
            predictions: List of prediction dicts with outcomes for backtesting.

        Returns:
            AutoresearchResult with best config found.
        """
        best_sharpe = float("-inf")
        best_config: dict[str, Any] = dict(DEFAULT_CONFIG)
        total_experiments = 0
        improvements = 0
        all_results: list[tuple[float, dict[str, Any]]] = []
        winners: list[dict[str, Any]] = []

        for wave in range(self.waves):
            wave_configs: list[dict[str, Any]] = []

            if wave == 0 or not winners:
                # Wave 1: pure random exploration
                wave_configs = [_random_config() for _ in range(self.per_wave)]
            else:
                # Later waves: mix of perturbations and random
                n_perturb = int(self.per_wave * 0.7)
                n_random = self.per_wave - n_perturb
                for _ in range(n_perturb):
                    parent = random.choice(winners)
                    wave_configs.append(_perturb_config(parent))
                for _ in range(n_random):
                    wave_configs.append(_random_config())

            for cfg in wave_configs:
                result = backtest(predictions, cfg)
                total_experiments += 1

                all_results.append((result.sharpe, cfg))

                if result.sharpe > best_sharpe:
                    best_sharpe = result.sharpe
                    best_config = dict(cfg)
                    improvements += 1
                    logger.info(
                        "Wave %d: new best Sharpe %.4f (experiment %d)",
                        wave + 1, best_sharpe, total_experiments,
                    )

                self._log_experiment(wave, cfg, result.sharpe, result.win_rate)

            # Select top configs as winners for next wave
            all_results.sort(key=lambda x: x[0], reverse=True)
            winners = [cfg for _, cfg in all_results[:5]]

        # Save best config
        save_config(best_config, "best_config.json")

        # Top configs
        all_results.sort(key=lambda x: x[0], reverse=True)
        top_configs = [
            {"sharpe": s, **cfg} for s, cfg in all_results[:10]
        ]

        return AutoresearchResult(
            best_sharpe=best_sharpe,
            best_config=best_config,
            total_experiments=total_experiments,
            improvements=improvements,
            top_configs=top_configs,
        )

    def _log_experiment(
        self, wave: int, config: dict[str, Any], sharpe: float, win_rate: float
    ) -> None:
        """Append experiment result to JSONL log."""
        entry = {
            "wave": wave,
            "config": config,
            "sharpe": sharpe,
            "win_rate": win_rate,
        }
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as exc:
            logger.warning("Failed to write experiment log: %s", exc)


def _cli_main() -> None:
    """CLI entry point for kalshi-research command."""
    import argparse

    parser = argparse.ArgumentParser(description="Run kalshi-autoresearch parameter optimization")
    parser.add_argument("predictions", help="Path to predictions JSON file")
    parser.add_argument("--waves", type=int, default=5, help="Number of optimization waves")
    parser.add_argument("--per-wave", type=int, default=40, help="Experiments per wave")
    parser.add_argument("--log-file", default="autoresearch-log.jsonl", help="JSONL log file path")
    args = parser.parse_args()

    predictions = json.loads(Path(args.predictions).read_text())
    ar = Autoresearch(waves=args.waves, per_wave=args.per_wave, log_file=args.log_file)
    result = ar.run(predictions)

    print(f"Best Sharpe: {result.best_sharpe:.4f}")
    print(f"Best config: {json.dumps(result.best_config, indent=2)}")
    print(f"Total experiments: {result.total_experiments}")
    print(f"Improvements: {result.improvements}")


if __name__ == "__main__":
    _cli_main()
