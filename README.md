# kalshi-autoresearch

**Self-improving signal detection for Kalshi prediction markets.**

A Python library that applies Karpathy-style autoresearch to find, evaluate, and continuously improve trading signals on Kalshi -- the regulated US prediction market.

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Results](https://img.shields.io/badge/win_rate-72.3%25-brightgreen.svg)](results/)

## What It Does

Most prediction market bots use fixed rules. This one improves its own rules every night.

```
Wave 1: test 50 parameter configs → find best Sharpe
Wave 2: generate new configs based on what worked → test again  
Wave 3: perturb winners ±20% → explore nearby space
...
Wave N: converge on optimal signal filter for current market conditions
```

After 372 real predictions tracked:
- **72.3% win rate** (random = 50%)
- **Brier score: 0.1367** (perfect = 0, random = 0.25)
- **Best signal type**: Sports markets, 90%+ implied probability, $500+ trade size

## How It Works

### The Signal

Kalshi shows real-time trade data. When someone places a large trade on a high-probability outcome, it usually means they know something. We track these "whale signals."

```python
# A signal looks like this
{
  "market": "NCAA Men's Basketball - Duke vs. UNC",
  "side": "YES",
  "implied_probability": 0.87,  # 87% likely
  "trade_size_usd": 750,
  "signal_type": "whale_conviction"
}
```

### The Autoresearch Loop

Every night, the loop generates new hypotheses and tests them against historical signal data:

```python
# Wave 1: broad search
configs = generate_base_hypotheses()  # ~240 configs

# Wave 2+: focused search based on winners  
winners = [c for c in results if c.sharpe > best_sharpe]
configs = perturb_winners(winners) + explore_new_space()

# Each config is evaluated on historical data
for config in configs:
    result = backtest(config, historical_signals)
    if result.sharpe > best_sharpe:
        save_config(config)  # this is now the new baseline
```

### Memory System (L0/L1/L2)

Inspired by ByteDance's OpenViking hierarchical memory:

- **L0**: Category stats (sports 73% WR, other 33% WR)
- **L1**: Condition patterns (sports + 90-100% implied = 100% WR across 92 bets)
- **L2**: Raw trade log (every signal with outcome)

```python
from kalshi_autoresearch import Memory

memory = Memory.load("kalshi-memory.json")
print(memory.best_conditions[:3])
# sports|90-100|nodip: 100.0% WR (92 bets)
# sports|70-80|dip-10-15: 100.0% WR (17 bets)  
# sports|70-80|dip-15+: 100.0% WR (11 bets)
```

### Swarm Consensus

5 agents with different personalities vote on each signal. Trade only when 3+ agree:

| Agent | Strategy |
|-------|----------|
| Whale Chaser | Only $1000+ trades |
| Momentum Rider | Fast-moving markets |
| Contrarian | Mid-range overlooked signals |
| Conservative | 85%+ certainty only |
| Value Hunter | Best autoresearch config |

## Installation

```bash
pip install kalshi-autoresearch
```

## Quick Start

```python
from kalshi_autoresearch import Monitor, Autoresearch, Memory

# Run signal monitor (reads Kalshi public trade API)
monitor = Monitor(min_trade_usd=500, implied_range=(0.65, 1.0))
signals = monitor.scan()

# Run overnight research loop (improves the config)
researcher = Autoresearch(waves=5, per_wave=40)
result = researcher.run()
print(f"Best config: Sharpe {result.best_sharpe:.3f}")

# Check memory patterns
memory = Memory.from_predictions("predictions.json")
print(memory.top_conditions(n=5))
```

## Results

Live tracked predictions (not backtesting):

| Metric | Value |
|--------|-------|
| Total predictions | 372 |
| Win rate | 72.3% |
| Brier score | 0.1367 |
| Best category | Sports (73% WR) |
| Best single pattern | Sports 90-100% implied (100% WR, 92 bets) |

Full results in [results/](results/).

## Architecture

```
kalshi_autoresearch/
  monitor.py        # Watches Kalshi API for whale signals
  autoresearch.py   # Self-improving parameter search loop
  memory.py         # L0/L1/L2 hierarchical memory
  swarm.py          # Multi-agent consensus voting
  backtest.py       # Fast backtesting engine
  config.py         # Config management
```

## Why Open Source

Prediction markets are a research-grade testbed for signal detection algorithms. The self-improving loop, memory architecture, and swarm voting are general techniques applicable far beyond Kalshi. Making this open helps researchers and developers build better signal detection systems.

## License

MIT -- do whatever you want with it.

## Author

Built by [Kishore Reddy Pagidi](https://linkedin.com/in/kishore005/) -- AI PM at SOLIDWORKS, founder of [Akira Data](https://akiradata.ai), CoRL 2023 paper author.
