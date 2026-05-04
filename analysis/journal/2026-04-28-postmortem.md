# Apr 28 Postmortem

## Summary
Worst day since system corrections. K-props 4W-7L (-$429), game model 0W-1L (-$127), OT +$240. Net: -$316.

## What Happened

### K-Props: 4W-7L (-$429.02)
The elite pitcher regression flaw struck hard. Ohtani expected 4.16 Ks, got 9. Chase Burns expected 5.6, got 9. Bibee expected 3.3, got 6.

ALL 11 bets were UNDERs. The model's systematic underestimation of high-K pitchers caused 7 losses.

**Edge cap would have helped only slightly:** The 20% cap (added Apr 28 but logged before) would have filtered Ohtani and Bibee, saving $190. But the remaining 9 bets still went 4W-5L (-$239). This suggests a broader model problem on Apr 28, not just extreme outliers.

### Key Pattern: 15-20% Edge is Degrading
All-time edge buckets tell the story:
- <10%: 5W-0L (+$309) -- too few, but perfect
- 10-15%: 24W-14L, 63% (+$657) -- THE sweet spot
- 15-20%: 13W-10L, 57% (+$110) -- marginal and declining
- 20%+: 7W-10L, 41% (-$346) -- confirmed losing

**Action: Consider tightening cap from 20% to 15%.** The 15-20% bucket is barely profitable and declining. But need more data -- current 23-bet sample is small.

### Game Model: MIA @ LAD OVER 8.5 Lost
CLV was +3.97% (line moved from -104 to -122). This is the right side of the market -- sometimes right bets lose. Game model record now 26W-26L-2P, effectively breakeven. Only OVERs are active (6W-3L now).

### OddsTrader: 14W-6L (+$240.48)
TB continues to dominate: 21W-6L (78%) overall. Real-money bets only: 29W-18L, +$425, 9.4% ROI.

**Data quality issue:** 98 of 145 graded OT bets have $0 wager (phantom bets). Record should be reported as real-money only.

## Updated Totals
| Model | Record | PnL | ROI |
|-------|--------|-----|-----|
| Game Model | 26W-26L-2P | -$18.16 | -0.3% |
| K-Props | 49W-34L | +$730.62 | ~12% |
| OT Sim (real $) | 29W-18L | +$425.09 | 9.4% |
| **Combined** | | **+$1,137.55** | |

## Critical Findings

1. **K-prop edge cap validated but may need tightening.** 20%+ is 7W-10L. 15-20% is 13W-10L. The 10-15% bucket is where the real alpha lives (24W-14L, 63%).

2. **Prior-season K/9 regression fix is URGENT.** Ohtani, Burns, Bibee all had model expectations way below their talent. This is the #1 priority for model improvement.

3. **OddsTrader TB is by far the strongest signal.** 78% win rate, 30.7% ROI on real money. Should increase sizing.

4. **Game model is breakeven.** 26W-26L-2P after 54 bets. Consider whether to keep running or fold into K-props/OT exclusively.

## Morning Session Priorities
1. Implement prior-season K/9 regression (fixes the root cause of today's K-prop losses)
2. Evaluate tightening K-prop edge cap to 15%
3. Increase OT TB bet sizing
4. Decide game model fate -- breakeven after 54 bets is not alpha
