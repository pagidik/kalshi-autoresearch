/**
 * kalshi-autoresearch.mjs Ã¢â‚¬â€ Autoresearch Orchestrator
 *
 * Applies Karpathy's autoresearch methodology to the Kalshi signal filter.
 * Spawns an AI research agent that:
 *   1. Reads kalshi-program.md for instructions
 *   2. Runs experiments via kalshi-backtest.mjs
 *   3. Keeps improvements, discards failures
 *   4. Logs everything to kalshi-experiment-log.jsonl
 *   5. Saves best config to kalshi-config.json
 *
 * Run manually: node kalshi-autoresearch.mjs
 * Or via nightly cron (replaces kalshi-learner.mjs on the daily midnight run)
 *
 * The agent is given program.md + current state and told to run Ã¢â€°Â¥25 experiments.
 * Typical runtime: 5-15 minutes (limited by LLM calls, not compute).
 */

import { readFile, writeFile, appendFile } from 'fs/promises'
import { execSync } from 'child_process'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const FILES = {
  predictions: join(__dirname, 'kalshi-predictions.json'),
  config:      join(__dirname, 'kalshi-config.json'),
  program:     join(__dirname, 'kalshi-program.md'),
  log:         join(__dirname, 'kalshi-experiment-log.jsonl'),
  summary:     join(__dirname, 'kalshi-research-summary.md'),
}

// Ã¢â€â‚¬Ã¢â€â‚¬ Experiment log helpers Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

async function logExperiment(entry) {
  await appendFile(FILES.log, JSON.stringify(entry) + '\n')
}

async function readLog() {
  try {
    const raw = await readFile(FILES.log, 'utf8')
    return raw.trim().split('\n').filter(Boolean).map(l => JSON.parse(l))
  } catch {
    return []
  }
}

// Ã¢â€â‚¬Ã¢â€â‚¬ Backtest runner Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

function runBacktest(params) {
  try {
    const out = execSync(
      `node "${join(__dirname, 'kalshi-backtest.mjs')}"`,
      { cwd: __dirname, encoding: 'utf8', timeout: 15000,
        env: { ...process.env, BACKTEST_CONFIG: JSON.stringify(params) } }
    ).trim()

    if (out.startsWith('BACKTEST_RESULT')) {
      const parts = Object.fromEntries(
        out.split('|').slice(1).map(p => {
          const idx = p.indexOf(':')
          return [p.slice(0, idx), p.slice(idx + 1)]
        })
      )
      return {
        status: 'ok',
        brierScore: parseFloat(parts.brierScore),
        winRate: parseFloat(parts.winRate),
        nSignals: parseInt(parts.nSignals),
        totalPnL: parseFloat(parts.totalPnL),
        sharpe: parseFloat(parts.sharpe),
      }
    } else if (out.startsWith('BACKTEST_INSUFFICIENT')) {
      return { status: 'insufficient' }
    }
    return { status: 'error', raw: out }
  } catch (e) {
    return { status: 'error', raw: e.message }
  }
}

// Ã¢â€â‚¬Ã¢â€â‚¬ Parameter perturbation engine Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
// OPTIMIZATION TARGET: totalPnL (profit) Ã¢â‚¬â€ NOT Brier score
// We know from data that 80%+ implied = 100% win rate + positive PnL
// Search is focused on high-confidence zone + trade size combos

function generateCandidates(current, alreadyTried) {
  const tried = new Set(alreadyTried.map(e => JSON.stringify(e.params)))
  const candidates = []

  const add = (params, hypothesis) => {
    const key = JSON.stringify(params)
    if (!tried.has(key)) candidates.push({ params, hypothesis })
  }

  // 1. HIGH-CONFIDENCE ZONE Ã¢â‚¬â€ primary focus (data shows 80%+ = 100% WR)
  // Sweep lower bound from 0.75 to 0.95, upper always 1.0
  for (const newLo of [0.75, 0.78, 0.80, 0.82, 0.84, 0.85, 0.87, 0.88, 0.90, 0.92, 0.95]) {
    add({ ...current, impliedRange: [newLo, 1.0] },
      `HIGH-CONF: impliedRange [${newLo}Ã¢â‚¬â€œ1.0] Ã¢â‚¬â€ focus on whale-certainty signals`)
  }

  // 2. HIGH-CONFIDENCE + trade size combos (bigger trades = smarter money?)
  for (const newLo of [0.80, 0.85, 0.90]) {
    for (const usd of [200, 300, 500, 750, 1000, 1500]) {
      add({ ...current, impliedRange: [newLo, 1.0], minTradeUSD: usd },
        `COMBO: range [${newLo}Ã¢â‚¬â€œ1.0] + minTrade $${usd}`)
    }
  }

  // 3. HIGH-CONFIDENCE + sports-only (NCAAB/NCAAW is our best category)
  for (const newLo of [0.80, 0.85, 0.90]) {
    add({ ...current, impliedRange: [newLo, 1.0], skipCategories: ['crypto', 'politics', 'other'] },
      `SPORTS-ONLY high-conf: [${newLo}Ã¢â‚¬â€œ1.0], skip all non-sports`)
  }

  // 4. HIGH-CONFIDENCE + lookback (shorter = more recent data, less stale)
  for (const newLo of [0.80, 0.85]) {
    for (const days of [7, 14, 21]) {
      add({ ...current, impliedRange: [newLo, 1.0], lookbackDays: days },
        `RECENCY: [${newLo}Ã¢â‚¬â€œ1.0] + lookback ${days}d`)
    }
  }

  // 5. HIGH-CONFIDENCE + contract size (big contracts = institutional money)
  for (const newLo of [0.80, 0.85, 0.90]) {
    for (const mc of [500, 750, 1000, 1500]) {
      add({ ...current, impliedRange: [newLo, 1.0], minContracts: mc },
        `INSTITUTIONAL: [${newLo}Ã¢â‚¬â€œ1.0] + minContracts ${mc}`)
    }
  }

  // 6. BROADER RANGE Ã¢â‚¬â€ test if 70-80% bucket adds or subtracts value
  for (const newLo of [0.70, 0.72, 0.75]) {
    add({ ...current, impliedRange: [newLo, 1.0] },
      `WIDER: does including [${newLo}Ã¢â‚¬â€œ0.80] zone help or hurt PnL?`)
  }

  // 7. DIP FILTER Ã¢â‚¬â€ the key new hypothesis from spike analysis
  // Data shows dip>=10Ã‚Â¢ + cluster = 100% WR. Explore this space.
  for (const dip of [0.05, 0.08, 0.10, 0.12, 0.15]) {
    add({ ...current, minDip: dip, maxDip: 0.18 },
      `DIP: minDip=${dip} maxDip=0.18 Ã¢â‚¬â€ conviction during wobble, not collapse`)
  }
  // Just dip, no max cap
  for (const dip of [0.05, 0.10, 0.15]) {
    add({ ...current, minDip: dip },
      `DIP-ONLY: minDip=${dip} Ã¢â‚¬â€ any conviction dip`)
  }

  // 8. CLUSTER FILTER Ã¢â‚¬â€ spike bursts
  add({ ...current, requireCluster: true },
    'CLUSTER: only signals in 3+ burst within 5 min')
  add({ ...current, requireCluster: true, impliedRange: [0.70, 1.0] },
    'CLUSTER+WIDER: cluster + 70%+ implied')
  add({ ...current, requireCluster: true, impliedRange: [0.75, 1.0] },
    'CLUSTER+75: cluster + 75%+ implied')

  // 9. THE HOLY GRAIL COMBOS Ã¢â‚¬â€ dip + cluster (100% WR in backtest)
  add({ ...current, minDip: 0.10, maxDip: 0.18, requireCluster: true },
    'HOLY-GRAIL-A: dip 10-18Ã‚Â¢ + cluster Ã¢â‚¬â€ Ole Miss pattern')
  add({ ...current, minDip: 0.08, maxDip: 0.18, requireCluster: true },
    'HOLY-GRAIL-B: dip 8-18Ã‚Â¢ + cluster Ã¢â‚¬â€ slightly wider')
  add({ ...current, minDip: 0.10, maxDip: 0.18, requireCluster: true, impliedRange: [0.65, 1.0] },
    'HOLY-GRAIL-C: dip 10-18Ã‚Â¢ + cluster + wider implied range')
  add({ ...current, minDip: 0.10, maxDip: 0.18, requireCluster: true, minTradeUSD: 300 },
    'HOLY-GRAIL-D: dip 10-18Ã‚Â¢ + cluster + $300+ trade size')

  // 10. FULL combos
  add({ ...current, impliedRange: [0.75, 1.0], minTradeUSD: 200, minDip: 0.10, maxDip: 0.18, requireCluster: true },
    'FULL-OPTIMAL: 75%+ + dip 10-18Ã‚Â¢ + cluster + $200+')
  add({ ...current, impliedRange: [0.70, 1.0], minTradeUSD: 300, minDip: 0.08, requireCluster: true },
    'FULL-WIDE: 70%+ + dip 8Ã‚Â¢+ + cluster + $300+')


  // ===== WAVE 2 EXPERIMENTS (Mar 16, 2026) =====

  // 11. EWMA decay sweep
  for (const decay of [0.05, 0.10, 0.20, 0.25, 0.30, 0.40, 0.50]) {
    add({ ...current, ewmaDecay: decay },
      `EWMA: decay=${decay} -- weight recent vs historical`)
  }

  // 12. Kelly fraction sweep
  for (const kf of [0.25, 0.33, 0.40, 0.60, 0.75, 1.0]) {
    add({ ...current, kellyFraction: kf },
      `KELLY: fraction=${kf} -- bet sizing`)
  }

  // 13. Category combos
  add({ ...current, skipCategories: ['sports', 'other'] },
    'POLITICS+CRYPTO: skip sports only')
  add({ ...current, skipCategories: ['sports', 'crypto', 'other'] },
    'POLITICS-ONLY: pure political markets')

  // 14. High-value only
  for (const usd of [2000, 3000, 5000]) {
    add({ ...current, minTradeUSD: usd },
      `HIGH-VALUE: minTrade ${usd}`)
  }

  // 15. Cap top of range
  for (const hi of [0.92, 0.95, 0.97]) {
    add({ ...current, impliedRange: [0.65, hi] },
      `CAP-TOP: range 0.65-${hi}`)
  }
  for (const hi of [0.90, 0.85]) {
    add({ ...current, impliedRange: [0.75, hi] },
      `MIDDLE-BAND: range 0.75-${hi}`)
  }

  // 16. Ultra-recent lookback
  for (const days of [3, 5, 10]) {
    add({ ...current, lookbackDays: days },
      `ULTRA-RECENT: lookback ${days}d`)
  }

  // 17. Aggressive Kelly + high confidence
  for (const newLo of [0.80, 0.85, 0.90]) {
    for (const kf of [0.75, 1.0]) {
      add({ ...current, impliedRange: [newLo, 1.0], kellyFraction: kf },
        `AGGRESSIVE: range-${newLo}-kelly-${kf}`)
    }
  }

  // 18. EWMA combos
  for (const newLo of [0.80, 0.85]) {
    add({ ...current, impliedRange: [newLo, 1.0], ewmaDecay: 0.05 },
      `STABLE-HIST: range-${newLo}-ewma-0.05`)
    add({ ...current, impliedRange: [newLo, 1.0], ewmaDecay: 0.40 },
      `ADAPTIVE: range-${newLo}-ewma-0.40`)
  }

  // 19. Liquidity filter
  for (const mc of [50, 100, 200]) {
    add({ ...current, minContracts: mc },
      `CONTRACT-MIN: ${mc} contracts`)
  }

  // 20. Wildcards
  add({ ...current, impliedRange: [0.60, 1.0], minTradeUSD: 500, ewmaDecay: 0.20 },
    'WILDCARD-A: wide-range-med-trade-fast-ewma')
  add({ ...current, impliedRange: [0.85, 1.0], kellyFraction: 0.75, ewmaDecay: 0.10 },
    'WILDCARD-B: high-conf-aggressive-kelly-stable-history')
  add({ ...current, impliedRange: [0.80, 1.0], minTradeUSD: 300, kellyFraction: 0.50, ewmaDecay: 0.15, lookbackDays: 14 },
    'WILDCARD-C: recent-2wk-balanced-params')
  add({ ...current, impliedRange: [0.90, 1.0], minTradeUSD: 200, skipCategories: ['other'] },
    'WILDCARD-D: near-certainty-no-junk-low-entry')
  return candidates
}

// Ã¢â€â‚¬Ã¢â€â‚¬ Main autoresearch loop Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

async function main() {
  const startTime = Date.now()
  console.log(`AUTORESEARCH_START|${new Date().toISOString()}`)

  // Load state
  const config = JSON.parse(await readFile(FILES.config, 'utf8'))
  const log = await readLog()

  // OPTIMIZATION TARGET: PnL Ã¢â‚¬â€ not Brier score
  // Start from high-confidence baseline (80%+) based on what data shows
  let bestConfig = {
    minTradeUSD:    config.minTradeUSD    ?? 300,
    impliedRange:   [0.75, 1.0],
    ewmaDecay:      0.15,
    kellyFraction:  0.5,
    skipCategories: config.skipCategories ?? [],
    minContracts:   0,
    lookbackDays:   30,
    minDip:         0,
    maxDip:         1.0,
    requireCluster: false,
  }

  // Seed bestPnL from a quick baseline run
  const baselineResult = runBacktest(bestConfig)
  let bestPnL = baselineResult.status === 'ok' ? baselineResult.totalPnL : -Infinity
  let improvements = 0
  let insufficient = 0
  let total = 0

  console.log(`AUTORESEARCH_BASELINE|pnl:${bestPnL}|config:${JSON.stringify(bestConfig)}`)

  // Generate experiment candidates
  const candidates = generateCandidates(bestConfig, log)
  console.log(`AUTORESEARCH_CANDIDATES|${candidates.length} experiments queued`)

  // Run experiments
  for (const { params, hypothesis } of candidates) {
    total++
    const result = runBacktest(params)
    const ts = new Date().toISOString()

    if (result.status === 'insufficient') {
      insufficient++
      await logExperiment({
        ts, params, result: 'INSUFFICIENT', hypothesis,
        note: 'Too few signals passed filter'
      })
      process.stdout.write(`[${total}] SKIP  ${hypothesis}\n`)
      continue
    }

    if (result.status === 'error') {
      await logExperiment({ ts, params, result: 'ERROR', hypothesis, note: result.raw })
      process.stdout.write(`[${total}] ERR   ${hypothesis}\n`)
      continue
    }

    // OPTIMIZE FOR PnL Ã¢â‚¬â€ improved if PnL is at least $1 better
    const improved = result.totalPnL > bestPnL + 1.0

    await logExperiment({
      ts, params,
      result: improved ? 'IMPROVED' : 'REJECTED',
      brierScore: result.brierScore,
      totalPnL: result.totalPnL,
      prevBestPnL: bestPnL,
      winRate: result.winRate,
      nSignals: result.nSignals,
      sharpe: result.sharpe,
      hypothesis,
      note: improved
        ? `PnL $${bestPnL} Ã¢â€ â€™ $${result.totalPnL} (ÃŽâ€$${(result.totalPnL - bestPnL).toFixed(0)})`
        : `No improvement: $${result.totalPnL} vs best $${bestPnL}`
    })

    process.stdout.write(
      `[${total}] ${improved ? 'Ã¢Å“â€œ IMPROVED' : '  reject '} ` +
      `pnl:$${result.totalPnL} (prev:$${bestPnL}) brier:${result.brierScore} n:${result.nSignals} | ${hypothesis}\n`
    )

    if (improved) {
      improvements++
      bestPnL = result.totalPnL
      bestConfig = { ...params }

      // Write to config immediately
      const newConfig = {
        ...config,
        ...bestConfig,
        bestPnL,
        autoresearchOptimizationTarget: 'pnl',
        autoresearchAt: ts,
        autoresearchExperiments: total,
        autoresearchImprovements: improvements,
      }
      await writeFile(FILES.config, JSON.stringify(newConfig, null, 2))
    }
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1)

  // Write research summary
  const summary = `# Research Session Ã¢â‚¬â€ ${new Date().toDateString()}

## Best config found
\`\`\`json
${JSON.stringify(bestConfig, null, 2)}
\`\`\`

## PnL improvement (optimization target)
Baseline $${baselineResult.status === 'ok' ? baselineResult.totalPnL : '?'} Ã¢â€ â€™ Best $${bestPnL}

## Stats
- Experiments run: ${total}
- Improvements: ${improvements}
- Insufficient (too few signals): ${insufficient}
- Rejected: ${total - improvements - insufficient}
- Time: ${elapsed}s

## Key findings
${(await readLog())
  .filter(e => e.result === 'IMPROVED')
  .map(e => `- **${e.hypothesis}**: Brier ${e.prevBest} Ã¢â€ â€™ ${e.brierScore}`)
  .join('\n') || '- No improvements found this session'}
`
  await writeFile(FILES.summary, summary)

  console.log(
    `AUTORESEARCH_DONE` +
    `|elapsed:${elapsed}s` +
    `|experiments:${total}` +
    `|improvements:${improvements}` +
    `|bestPnL:${bestPnL}` +
    `|optimizationTarget:pnl`
  )
}

main().catch(err => {
  console.error('Autoresearch error:', err.message)
  process.exit(1)
})
