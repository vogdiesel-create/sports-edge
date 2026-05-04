# Apr 18 Post-Game Review

## Summary: 8W-8L, -$44.46

Mixed day. Game model totals carried (+$386.48 on 4W-1L), but moneyline losses (-$227.91) and a rough K prop night (-$203.03) wiped out the gains.

## Game Model (4W-3L, +$158.57)

**Totals: 4W-1L, +$386.48** - Strong night.
- BAL @ CLE UNDER 8.0: WIN (total 6). Model nailed this, 3rd straight win on this game.
- MIL @ MIA UNDER 8.0: WIN (total 7). After losing this line at 8.5 yesterday, 8.0 cashed.
- LAD @ COL UNDER 9.5: WIN (total 7). Coors under is unusual but model found value.
- SD @ LAA UNDER 8.0: WIN (total 5). CLV +2.94% - best CLV of the night.
- CIN @ MIN UNDER 8.5: LOSS (total 9). Game went over, Reds won 5-4.

**Moneyline: 0W-2L, -$227.91** - Both ML bets lost. ML is now DISABLED.
- OTT @ CAR away: Lost
- LAD @ COL away: Lost despite Dodgers winning 4-3 (wait - need to check this)

## K Props (4W-5L, -$203.03)

**First losing day for K props.** Previous: 6W-3L (+$148.55), 7W-2L (+$221.19).

**What went wrong:**
1. **Tarik Skubal Under 7.5: LOSS (actual 10 Ks)** - Model expected under, Skubal dealt. Model needs to respect elite K rates better.
2. **Luis Severino 7+ and 8+ Ks: Both LOSS (actual 3)** - Double exposure to same pitcher, both lost. Should cap at 1 bet per pitcher.
3. **Ryan Feltner 6+ Ks: LOSS (actual 5)** - Close miss.
4. **Noah Cameron 6+ Ks: LOSS (actual 3)** - Unknown pitcher, model had no data.

**What went right:**
- Paul Skenes Under 6.5: WIN (5 Ks). Elite pitcher, model correctly called under.
- Chris Sale Under 7.5: WIN (7 Ks). Squeaker - exactly hit the line, under cashed.
- Andre Pallante Over 3.5: WIN (5 Ks). Strong OVER hit.

**Key Learning: Double-betting same pitcher (Severino 7+ AND 8+) amplifies losses. Consider capping exposure to 1 bet per pitcher per game.**

## Cumulative Performance

| Model | Record | PnL | Bankroll | ROI |
|-------|--------|-----|----------|-----|
| Game (totals only) | 19W-13L-1P | +$725.19 | - | 16.1% |
| Game (w/ ML) | 21W-19L-1P | +$257.31 | $5,257.31 | 5.0% |
| K Props | 17W-10L | +$166.71 | $3,166.71 | 7.0% |
| **Combined** | **38W-29L-1P** | **+$424.02** | **$8,424.02** | - |

## CLV Check
- Avg CLV: -0.42% across 33 graded bets
- Only 39% of bets have positive CLV
- This is concerning - model may be slightly behind the market
- Need to hit 50 bets for proper CLV gate evaluation

## Issues Found
1. K prop bankroll was stale (showed $3369.74 instead of $3166.71) - FIXED
2. 4 game model bets had missing `date` field - FIXED
3. Severino double-exposure pattern needs addressing

## Morning Session Priorities
1. Grade Apr 19 bets after games complete
2. Investigate Severino double-bet issue - add 1-bet-per-pitcher cap
3. CLV approaching 50-bet gate (at 33 now)
4. Monitor batter prop model picks (first batch today)
5. NHL season winding down - focus shifting to MLB-only
