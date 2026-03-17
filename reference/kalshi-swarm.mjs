/**
 * kalshi-swarm.mjs â€” MiroFish-inspired Multi-Config Consensus Voting
 *
 * Concept from MiroFish: only act when multiple independent agents agree.
 * Here: run N config variants simultaneously, trade only when M of N agree.
 * 
 * Instead of one config deciding, a SWARM of parameter variants votes.
 * Consensus threshold: at least 3 out of 5 configs must pass the signal.
 *
 * Run: node kalshi-swarm.mjs
 * Used by: kalshi-trader.mjs (replace single-config filter with swarm vote)
 */

import { readFile, writeFile } from 'fs/promises'
import { existsSync } from 'fs'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const CONFIG_FILE  = join(process.cwd(), 'kalshi-config.json')
const MEMORY_FILE  = join(process.cwd(), 'kalshi-memory.json')
const SWARM_FILE   = join(process.cwd(), 'kalshi-swarm-config.json')

// =============================================
// SWARM: 5 independent agents with different personalities
// (inspired by MiroFish agent archetypes)
// =============================================
function buildSwarm(baseConfig) {
  return [
    {
      name: 'Whale-Chaser',
      // Only follows big institutional money
      ...baseConfig,
      minTradeUSD: Math.max(baseConfig.minTradeUSD, 1000),
      impliedRange: [0.75, 1.0],
    },
    {
      name: 'Momentum-Rider',
      // Follows fast-moving markets with high confidence
      ...baseConfig,
      impliedRange: [0.70, 1.0],
      ewmaDecay: 0.30, // faster decay = more reactive
    },
    {
      name: 'Contrarian',
      // Slightly wider range to catch 65-75% implied edge cases
      ...baseConfig,
      impliedRange: [0.65, 0.85],
      minTradeUSD: Math.max(baseConfig.minTradeUSD, 500),
    },
    {
      name: 'Conservative',
      // Only near-certainty signals
      ...baseConfig,
      impliedRange: [0.85, 1.0],
      minTradeUSD: baseConfig.minTradeUSD,
    },
    {
      name: 'Value-Hunter',
      // Best PnL config from autoresearch + memory L1 insights
      ...baseConfig,
      impliedRange: baseConfig.impliedRange || [0.60, 1.0],
      ewmaDecay: baseConfig.ewmaDecay || 0.20,
    },
  ]
}

// Check if a prediction record passes a given config
function passesConfig(record, config) {
  if (record.dollarObserved < (config.minTradeUSD || 0)) return false
  const [lo, hi] = config.impliedRange || [0, 1]
  if (record.price < lo || record.price > hi) return false
  if ((config.skipCategories || []).includes(record.category)) return false
  return true
}

export async function swarmVote(record) {
  const raw = await readFile(CONFIG_FILE, 'utf8')
  const baseConfig = JSON.parse(raw)
  const swarm = buildSwarm(baseConfig)

  const votes = swarm.map(agent => ({
    agent: agent.name,
    vote: passesConfig(record, agent)
  }))

  const yesVotes = votes.filter(v => v.vote).length
  const consensus = yesVotes >= 3 // majority rule: 3 of 5

  // Load memory for L1 context
  let memoryBoost = false
  if (existsSync(MEMORY_FILE)) {
    try {
      const mem = JSON.parse(await readFile(MEMORY_FILE, 'utf8'))
      // Check if L0 category has good win rate
      const catMem = mem.L0_categories?.[record.category]
      if (catMem && catMem.winRate >= 0.65) memoryBoost = true
    } catch {}
  }

  return {
    signal: record.market,
    ticker: record.ticker,
    impliedPct: record.impliedPct,
    category: record.category,
    votes,
    yesVotes,
    totalAgents: swarm.length,
    consensus,
    memoryBoost,
    // Final decision: consensus OR (memory-boosted + 2+ votes)
    shouldTrade: consensus || (memoryBoost && yesVotes >= 2),
    reason: consensus
      ? `Consensus: ${yesVotes}/5 agents agree`
      : memoryBoost && yesVotes >= 2
        ? `Memory-boosted: ${record.category} category WR >= 65%, ${yesVotes}/5 agents agree`
        : `No consensus: only ${yesVotes}/5 agents agree`
  }
}

// CLI test mode
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const raw = await readFile(CONFIG_FILE, 'utf8')
  const baseConfig = JSON.parse(raw)
  const swarm = buildSwarm(baseConfig)

  await writeFile(SWARM_FILE, JSON.stringify({ agents: swarm, consensusThreshold: 3 }, null, 2))
  console.log('SWARM_BUILT|' + swarm.length + ' agents configured')
  swarm.forEach(a => console.log(`  [${a.name}] range=[${a.impliedRange}] minTrade=$${a.minTradeUSD}`))

  // Test with a sample record
  const testRecord = {
    market: 'TEST: Team A vs Team B',
    ticker: 'KXNCAAMBGAME_TEST',
    price: 0.82,
    impliedPct: 82,
    dollarObserved: 750,
    category: 'sports',
    dipFromOpen: 0.05,
  }
  const result = await swarmVote(testRecord)
  console.log('\nSWARM_VOTE test result:')
  console.log(JSON.stringify(result, null, 2))
  console.log('\nSWARM_OK')
}
