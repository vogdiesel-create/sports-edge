# Post-Game Review: Apr 25, 2026

## Results Summary

| Model | Record | PnL | Notes |
|-------|--------|-----|-------|
| Game Model | 2W-0L | +$243.65 | Both OVER picks won |
| K-Props | 6W-3L | +$143.98 | 67% WR, under-heavy |
| OddsTrader Sim | 26W-12L | +$419.31 | TB market crushing |
| **Day Total** | | **+$387.63** | Best day since Apr 14 |

## Running Totals (All Time)

| Model | Record | PnL | ROI |
|-------|--------|-----|-----|
| Game Model | 23W-24L-1P | -$74.19 | -1.5% |
| K-Props | 33W-21L | +$647.22 | 12.6% |
| OddsTrader Sim | 51W-46L | +$246.54 | 10.9% |
| **Combined** | | **+$573.03** | |

## What Hit

**Game Model:**
- Two OVER picks both cashed. The model's OVER accuracy continues to be strong (now 5W-2L overall on overs, +$342 combined).
- The unlocking of MLB OVERs (removing UNDER-only restriction) is paying off.

**K-Props:**
- Robbie Ray under 6+ (4 Ks) - comfortable win, $+112
- Garrett Crochet under 8+ (7 Ks) - just squeaked under, $+86
- Bryan Woo under 6+ (1 K) - crushed it
- Jack Flaherty under 6+ (4 Ks) - comfortable
- Jake Irvin over 4+ (9 Ks) - rare OVER pick, big hit
- Kevin Gausman under 6+ (3 Ks) - comfortable

## What Missed

**K-Props (3 losses):**
1. **Cole Ragans under 7+ (actual: 11 Ks)** - Massive overshoot. Ragans is a high-K arm; 11 Ks is an extreme outcome but he's capable. Model may underestimate his ceiling. Worth tracking if he's a consistent miss.
2. **Zack Wheeler under 6+ (actual: 6 Ks)** - Lost by exactly hitting the line (push rules as loss here). Tight miss.
3. **Jacob Misiorowski under 8+ (actual: 9 Ks)** - Rookie with high K upside. Just above the line. Acceptable variance.

## Key Observations

1. **K-Props remain the alpha source.** 33W-21L (+$647) is no longer a small sample. At 54 graded bets, the signal is real.

2. **OddsTrader sim TB market is extraordinary.** 27W-10L (73% WR) on Total Bases with +$616. This is the strongest single market across all models.

3. **Game model OVER picks are profitable.** 5W-2L lifetime. The model finds genuine edges on overs, especially in the 8-12% edge bucket.

4. **Game model UNDER CLV is still bad.** Average CLV -0.51% overall, with 34% positive CLV rate. We're still generally buying worse than closing. But the model is now barely negative (-1.5% ROI) - much improved from -5.9% last recorded.

5. **No Apr 26 picks were generated.** The pick generation pipeline didn't produce any picks for today. Need to investigate whether the cron for pick generation ran.

## Calibration Check

- K-Props: 33/54 = 61.1% win rate. For bets with model edge, this is reasonable.
- Game Model totals: 23/47 = 48.9% win rate. Below 50% but ROI recovering due to favorable odds on winners.
- OddsTrader TB: 73% WR at average odds around -130 to -150. Very profitable.

## Issues

1. **1 pending game bet (unknown matchup)** - Still unresolved from previous days. Not blocking.
2. **VGK @ UTA still pending** - NHL playoff game, may need manual check.
3. **No picks generated for Apr 26** - Pipeline gap. The grading cron runs but where is the pick generation cron?

## Morning Session Priorities

1. Investigate why no picks were generated for Apr 26 (pick pipeline may be broken or not scheduled)
2. Generate today's (Apr 27) picks early
3. Consider: K-prop sample now at 54. Start analyzing by pitcher type/matchup quality for refinement
4. Cole Ragans specific review - is this a pitcher the model consistently misrates?
5. SwStr% integration still outstanding from prior action items
