/**
 * kalshi-memory.mjs â€” OpenViking-style Hierarchical Memory for Kalshi
 *
 * L0: Category-level summaries (sports / politics / crypto / other)
 * L1: Condition-level patterns (implied range bucket + dip + cluster)
 * L2: Raw trade log (already in kalshi-predictions.json)
 *
 * Run: node kalshi-memory.mjs
 * Outputs: kalshi-memory.json
 */

import { readFile, writeFile } from 'fs/promises'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PREDICTIONS_FILE = join(__dirname, 'kalshi-predictions.json')
const MEMORY_FILE = join(__dirname, 'kalshi-memory.json')

function bucket(impliedPct) {
  if (impliedPct >= 90) return '90-100'
  if (impliedPct >= 80) return '80-90'
  if (impliedPct >= 70) return '70-80'
  if (impliedPct >= 60) return '60-70'
  return 'below-60'
}

function dipBucket(dip) {
  if (dip >= 0.15) return 'dip-15+'
  if (dip >= 0.10) return 'dip-10-15'
  if (dip >= 0.05) return 'dip-5-10'
  return 'nodip'
}

async function main() {
  const raw = await readFile(PREDICTIONS_FILE, 'utf8')
  const predictions = JSON.parse(raw)
  const settled = predictions.filter(p => ['won','lost'].includes(p.status))

  // =============================================
  // L0 â€” CATEGORY LEVEL MEMORY
  // =============================================
  const L0 = {}
  for (const p of settled) {
    const cat = p.category || 'other'
    if (!L0[cat]) L0[cat] = { wins: 0, losses: 0, pnl: 0, totalBets: 0 }
    const won = p.status === 'won'
    L0[cat].wins += won ? 1 : 0
    L0[cat].losses += won ? 0 : 1
    L0[cat].pnl += p.pnl || 0
    L0[cat].totalBets++
  }
  for (const cat of Object.keys(L0)) {
    const m = L0[cat]
    m.winRate = m.totalBets > 0 ? +(m.wins / m.totalBets).toFixed(3) : null
    m.avgPnl = m.totalBets > 0 ? +(m.pnl / m.totalBets).toFixed(2) : null
    m.summary = `${cat}: ${m.wins}W/${m.losses}L (${(m.winRate*100).toFixed(1)}% WR, avg PnL $${m.avgPnl})`
  }

  // =============================================
  // L1 â€” CONDITION-LEVEL MEMORY (pattern matching)
  // =============================================
  const L1 = {}
  for (const p of settled) {
    const impliedB = bucket(p.impliedPct)
    const dipB = dipBucket(p.dipFromOpen || 0)
    const cat = p.category || 'other'
    const key = `${cat}|${impliedB}|${dipB}`

    if (!L1[key]) L1[key] = { wins: 0, losses: 0, pnl: 0, totalBets: 0, examples: [] }
    const won = p.status === 'won'
    L1[key].wins += won ? 1 : 0
    L1[key].losses += won ? 0 : 1
    L1[key].pnl += p.pnl || 0
    L1[key].totalBets++
    if (L1[key].examples.length < 3) L1[key].examples.push(p.market)
  }
  for (const key of Object.keys(L1)) {
    const m = L1[key]
    m.winRate = m.totalBets > 0 ? +(m.wins / m.totalBets).toFixed(3) : null
    m.avgPnl = m.totalBets > 0 ? +(m.pnl / m.totalBets).toFixed(2) : null
    m.edge = m.winRate !== null ? +(m.winRate - 0.5).toFixed(3) : null
  }

  // =============================================
  // BEST CONDITIONS (high-edge L1 patterns)
  // =============================================
  const bestConditions = Object.entries(L1)
    .filter(([, v]) => v.totalBets >= 3 && v.winRate !== null)
    .sort(([, a], [, b]) => b.winRate - a.winRate)
    .slice(0, 10)
    .map(([key, v]) => ({
      condition: key,
      winRate: v.winRate,
      totalBets: v.totalBets,
      pnl: +v.pnl.toFixed(2),
      edge: v.edge,
      examples: v.examples
    }))

  // =============================================
  // WORST CONDITIONS (avoid these)
  // =============================================
  const worstConditions = Object.entries(L1)
    .filter(([, v]) => v.totalBets >= 3 && v.winRate !== null)
    .sort(([, a], [, b]) => a.winRate - b.winRate)
    .slice(0, 5)
    .map(([key, v]) => ({
      condition: key,
      winRate: v.winRate,
      totalBets: v.totalBets,
      pnl: +v.pnl.toFixed(2),
    }))

  const memory = {
    generatedAt: new Date().toISOString(),
    settledTrades: settled.length,
    L0_categories: L0,
    L1_conditions: L1,
    insights: {
      bestConditions,
      worstConditions,
      totalEdge: bestConditions.reduce((s, c) => s + c.edge, 0).toFixed(3),
    }
  }

  await writeFile(MEMORY_FILE, JSON.stringify(memory, null, 2))

  console.log('MEMORY_BUILT|' + settled.length + ' trades analyzed')
  console.log('TOP CONDITIONS:')
  bestConditions.slice(0, 5).forEach(c =>
    console.log(`  ${c.condition}: ${(c.winRate*100).toFixed(1)}% WR (${c.totalBets} bets, $${c.pnl} PnL)`)
  )
  console.log('L0 SUMMARY:')
  Object.values(L0).forEach(c => console.log(' ', c.summary))
}

main().catch(err => {
  console.error('Memory error:', err.message)
  process.exit(1)
})
