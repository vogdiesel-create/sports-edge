# Post-Game Review: April 30, 2026

## Tonight's Results

### Game Model: 3W-1L (+$196)
Strong day. Best single-day since Apr 25. Cumulative now 30W-28L-4P, +$193. Model is trending slightly positive after weeks of breakeven.

### K-Props: 0W-1L (-$95)
Only 1 bet generated (Peter Lambert K under, loss). Volume near zero since UNDERs disabled and OVER model overcorrects. This market is effectively dead without a model overhaul.

### OddstraderSim: 7W-4L (-$50)
Slightly negative day despite winning record because losses were at heavier juice. TB went 5W-2L today.

## Bug Fixes This Session

### CRITICAL: 9 bets had wager=0 and PnL=0
The oddstrader_scraper was generating bets on Apr 29-30 without assigning wager amounts. Fixed all 9 with $100 flat wager and recalculated PnL. Bankroll adjusted from $5609.81 to $5513.49.

The root cause is likely in the scraper's bet generation for certain market types. Need to investigate oddstrader_scraper.py for the wager assignment logic.

### 3 bets still ungraded
- Walbert Urena (Apr 25) - Hits Allowed
- Kodai Senga (Apr 25) - Strikeouts
- Brandon Marsh (Apr 29) - Total Bases

API couldn't find these players in box scores. Possible name mismatches or the players didn't appear in the game.

## Key Metrics Update

| Model | Record | PnL | ROI | Status |
|-------|--------|-----|-----|--------|
| OT TB Signal | 73W-31L | +$1,484 | +14.4% | THE ALPHA |
| OT Hits Allowed | 16W-9L | +$321 | +13.7% | Solid secondary |
| OT Earned Runs | 2W-1L | +$36 | +11.9% | Too small sample |
| Game Model | 30W-28L-4P | +$193 | +3.1% | Marginally positive |
| K-Props OVER | 3W-1L | +$237 | Positive | Near zero volume |
| K-Props ALL | 51W-42L | +$62 | +1.0% | UNDERs disabled |
| OT Strikeouts | 11W-13L | -$371 | DISABLED | |
| OT RBI | 11W-28L | -$956 | DISABLED | |

## Active Markets Combined: $2,095 PnL

This is the real number. Active-only (TB + HA + ER): 91W-41L (68.9%), +$1,841, 14.2% ROI.

## Tier Analysis (OddstraderSim)
- Tier A: 59W-47L (55.7%), -$230 ROI: -2.2%
- Tier B: 54W-35L (60.7%), +$743 ROI: +8.7%

Tier B significantly outperforms Tier A. This is counterintuitive (Tier A should be higher EV). Possible explanation: Tier A bets at heavier juice (-190, -215) have worse risk/reward even if they hit more often in absolute terms.

## Morning Session Priorities

1. **Investigate wager=0 bug in oddstrader_scraper.py** - prevent this from recurring
2. **Investigate Tier A underperformance** - should we restrict to Tier B only?
3. **Run May 1 scraper** - capture today's lines
4. **3 ungraded bets** - manually grade or investigate name matching
