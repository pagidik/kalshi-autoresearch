# AI Grant Application -- kalshi-autoresearch

**Target:** AI Grant (aigrant.org) -- $5,000-$50,000 for open source AI projects
**Applicant:** Kishore Reddy Pagidi
**Email:** kishorereddy097@gmail.com
**GitHub:** github.com/pagidik/kalshi-autoresearch (to be created)
**Amount requested:** $15,000

---

## What is the project?

**kalshi-autoresearch** is an open source Python library that applies Karpathy-style autoresearch to prediction market signal detection on Kalshi -- the regulated US prediction market.

Most prediction market trading systems use fixed rules. This one improves its own rules every night.

The core loop:
1. Scan Kalshi real-time trade data for large trades on high-probability outcomes ("whale signals")
2. Run a self-improving parameter search that generates hypotheses, backtests them, keeps winners, discards losers
3. Apply a hierarchical memory system (L0/L1/L2, inspired by ByteDance's OpenViking) to identify which signal patterns have the best track records
4. Use a 5-agent swarm voting system to filter signals -- only acts when 3+ independent configs agree

## Why does this matter?

Prediction markets are a research-grade testbed for signal detection algorithms. Kalshi is the only CFTC-regulated prediction market in the US, making it a uniquely clean environment: outcomes are binary, ground truth resolves quickly, and the market microstructure is transparent.

The self-improving loop, hierarchical memory architecture, and multi-agent consensus voting are general techniques applicable far beyond Kalshi. Making this open source helps researchers and developers apply these methods to:
- Other prediction markets
- Sports betting signal detection
- Financial market signal processing
- Any domain with observable signals and binary outcomes

## What have you built so far?

A working production system running live:
- 372 real predictions tracked (not backtesting)
- 72.3% win rate (random = 50%)
- Brier score: 0.1367 (perfect = 0, random = 0.25)
- Best discovered pattern: sports markets, 90%+ implied probability = 100% win rate across 92 bets
- Autoresearch loop ran 246+ experiments, improved simulated PnL from $245 to $1,315

The system runs daily on a personal server. The grant would fund:
1. Open sourcing and packaging as a proper Python library (pip installable)
2. Writing documentation and tutorials
3. Building a public leaderboard where researchers can share and compare signal configs
4. Adding support for additional prediction markets (Polymarket, Manifold)

## Why open source?

Prediction market research is mostly proprietary. There are no open source tools for systematic signal detection on regulated prediction markets. This fills that gap.

## About me

I'm an AI Product Manager at SOLIDWORKS (Dassault Systemes), managing AI features for 3.7M engineers. I have a CoRL 2023 paper on robot imitation learning (22 citations, co-authored with Google DeepMind researchers) and 4 UK patents from Mercedes-Benz R&D. I'm the founder of Akira Data (akiradata.ai), an AI consulting firm.

I built this system as a side project to learn systematic ML research methodology and apply it to a real domain with fast feedback loops. The open source release is about sharing what works.

---

## Where to apply

aigrant.org has no public application form -- applications are submitted via email or Twitter DM to Nat Friedman (@natfriedman) and Daniel Gross (@danielgross).

**Draft email (needs Kishore's approval before sending):**

Subject: Open source prediction market autoresearch library

Hi Nat and Daniel,

I built kalshi-autoresearch -- an open source Python library that applies Karpathy's autoresearch methodology to prediction market signal detection on Kalshi.

The short version: instead of fixed trading rules, the system generates and tests its own hypotheses nightly, keeps the winners, and improves continuously. After 372 live tracked predictions it's sitting at 72.3% win rate with a Brier score of 0.1367.

More interesting than the results: the techniques -- self-improving parameter search, hierarchical signal memory (L0/L1/L2), multi-agent consensus voting -- are general and should be useful to anyone working on signal detection or systematic ML research.

I'd like to open source the full implementation, write proper documentation, and build a public config leaderboard where researchers can share and benchmark signal strategies. Requesting $15,000 to fund the time to do this properly.

GitHub: github.com/pagidik/kalshi-autoresearch  
Demo: kalshi-dashboard-brown.vercel.app  
Background: linkedin.com/in/kishore005/

Thanks,
Kishore Reddy Pagidi
