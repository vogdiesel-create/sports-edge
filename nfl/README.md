# Sports Edge - NFL Player Props

## Overview

This is the NFL arm of the Sports Edge betting model system. It focuses on finding systematically mispriced NFL player prop markets, using the same philosophy that produced a 76% win rate (38W-12L) on MLB Total Bases OVER props.

## Key Principle

**Completely separate bankroll and tracking from MLB.** Different sport, different dynamics, different edge profile. No cross-contamination of results or bankroll.

## Current Status: RESEARCH (May-Aug 2026)

We are in the pre-season research phase. No bets are being placed or simulated yet.

### Research Phase Goals (May - August 2026)

1. Download and analyze 3 seasons of NFL player game logs (2023-2025)
2. Identify which prop markets are most inefficient
3. Build baseline projections from historical averages
4. Study weather effects on passing/rushing splits
5. Build a game-script model (predict blowouts to exploit correlated props)
6. Backtest candidate strategies against historical lines
7. Confirm OddsTr covers NFL prop markets

### Target: Week 1 Ready (September 10, 2026)

Have a backtested model with demonstrated edge ready for paper trading when the 2026 NFL season opens.

## Philosophy

Same as MLB:
- Find systematically mispriced player props
- Paper trade first, prove the edge in simulation
- Only risk real money after the model has a verified track record
- Discipline over volume -- only bet when the model says there is genuine edge

## Directory Structure

```
nfl/
  research/       - Research notes, market analysis, findings
  data/           - Raw data (historical seasons + daily scrapes)
  models/         - Model code (projections, edge detection)
  tracking/       - Separate bankroll, sim ledger, grading
  analysis/       - Journal entries, insights, post-mortems
  state/          - Model state, experiment tracking
```

## Bankroll

- Starting: $5,000 (simulated)
- Unit size: $100
- Completely independent from MLB tracking
- Simulation only until edge is statistically proven

## Key Differences from MLB Model

| Factor | MLB | NFL |
|--------|-----|-----|
| Games per season | 162 | 17 |
| Games per week | Daily | 1 per team |
| Sample size per player | Large | Small |
| Line sharpening window | Hours | Days |
| Weather impact | Moderate | Major |
| Injury impact | Moderate | Massive |
| Game script correlation | Low | High |
| Prop market attention | Lower | Higher |
