# Apr 27 Post-Game Review

## Results: 8W-5L, +$138.92

### K-Props: 5W-2L, +$167.46
Strong day. The model continues to print money on K unders.

**Winners:**
- Cease U7.5 (+$73) - 5 Ks, model nailed it
- Leiter U5.5 (+$105) - 4 Ks, clean win
- Fried U5.5 (+$86) - 5 Ks, right on the edge
- Matz U4.5 (+$64) - 2 Ks, dominated
- May U4.5 (+$29) - 2 Ks, low K pitcher did low K things

**Losers (both BLOWOUTS):**
- Messick U4.5: 9 Ks (expected 3.61, delta +5.39)
  - Young pitcher, limited sample. Model had him at 3.61 expected but he struck out 9. Career game. Random variance likely, but flag for investigation.
- Suarez U4.5: 10 Ks (expected 3.18, delta +6.82)
  - This is the biggest miss I've seen. Model had him at 3.18 expected Ks and he got 10. That's a 3x miss. Suarez is historically a contact pitcher. If he's changed his approach, model needs to adapt.

**Action:** Investigate Ranger Suarez's recent K rate trends. If his season K/9 has spiked above his career norm, he may need blacklisting or a manual adjustment.

### OddsTrader Sim: 3W-3L, -$28.54
Flat day. TB model continues to be the best market (38W-18L all-time) but today was coin-flip.

**Winners:** Matz HA (+$116), Ozuna TB (+$57), Grisham TB (+$62)
**Losers:** Mangum TB (-$105), Clemens TB (-$105), Jeffers TB (-$53)

### Game Model: No new graded bets
1 pending: VGK @ UTA (NHL, Apr 25). Score not found by grading script. Bug or data lag.

## Cumulative Update
| Model | Record | PnL | ROI |
|-------|--------|-----|-----|
| K-Props | 43W-27L | $1,078 | 17.5% |
| OT Sim | 66W-57L | $234 | 3.7% |
| Game Model | 26W-25L-1P | $109 | 1.7% |
| **Combined** | **135W-109L** | **$1,422** | **7.1%** |

Progress to 300-bet milestone: 245/300 (81.7%)

## Key Observations

1. **K-Props remain the alpha generator.** 17.5% ROI on 70 bets. This is the model to scale.

2. **Extreme misses are happening on UNDER bets where the pitcher has a breakout game.** Messick (9) and Suarez (10) both massively exceeded expectations. The model can't predict career games, but we should ask: are there predictive signals for "breakout K games"?

3. **OT TB is strong (38W-18L) but volatile per-day.** The 3W-3L today is noise.

4. **VGK @ UTA grading bug** - NHL playoff game from Apr 25 still ungraded. Check score API.

## Morning Session Priorities

1. Grade VGK @ UTA (fix NHL score lookup if needed)
2. Investigate Ranger Suarez K rate trend (blacklist candidate?)
3. Check for Apr 28 games to generate picks
4. 55 more bets to 300-bet milestone - push toward formal report
