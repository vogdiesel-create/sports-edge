# Post-Game Review: Apr 26, 2026

## Game Model: 3W-1L, +$183.25

Strong day. Back-to-back winning sessions (Apr 25: +$244, Apr 26: +$183).

| Game | Side | Line | Actual | Edge | CLV | PnL |
|------|------|------|--------|------|-----|-----|
| DET @ CIN | UNDER | 9.5 | 11 | 8.8% | -0.4% | -$115.76 |
| LAA @ KC | OVER | 9.0 | 20 | 8.8% | +5.1% | +$107.21 |
| MIN @ TB | UNDER | 8.5 | 6 | 8.6% | 0.0% | +$100.26 |
| PHI @ ATL | UNDER | 9.0 | 8 | 8.3% | -7.4% | +$91.54 |

### Key Observations

**LAA @ KC OVER 9.0 actual=20**: Massive blowout. +5.1% CLV confirms we had sharp line read. This is the profile of our OVER edge - when we see it, it's real.

**PHI @ ATL UNDER 9.0 actual=8**: Won the bet but CLV was -7.4%. The market moved hard against us. We got lucky here - the line closed at +106 (under 50%) from our -127. The market was right that this was a high-scoring game profile. We won on variance, not edge.

**DET @ CIN UNDER 9.5 actual=11**: Only loss. 11 runs on a 9.5 line. CIN is a high-scoring environment this year.

## Cumulative Update

| Model | Record | PnL | ROI |
|-------|--------|-----|-----|
| Game Model | 26W-25L-1P | +$109.06 | ~2% |
| K-Props | 38W-25L | +$910.63 | ~18% |
| OddsTrader Sim | 63W-54L | +$263.01 | ~9% |
| **Combined** | **127W-104L-1P** | **+$1,282.70** | |

232 of 300 target graded (77.3%).

## Edge Bucket Reality Check

The 8-12% bucket is carrying everything:
- **5-8%**: 7W-11L, -$265 (39% WR) - LOSING MONEY
- **8-12%**: 14W-7L-1P, +$773 (64% WR) - ALL THE ALPHA
- **12%+**: 5W-7L, -$399 (42% WR) - model overconfident at high edges

**Action**: Raise minimum game model edge threshold from 5% to 8%. The 5-8% bucket has negative expected value.

## CLV Split Deepening

- OVER CLV: +1.16% avg (71% positive rate, n=7) - WE ARE SHARP ON OVERS
- UNDER CLV: -0.86% avg (36% positive rate, n=28) - MARKET IS SHARPER ON UNDERS

This is now undeniable. Our OVER model finds genuine closing line value. Our UNDER model does not.

## Priorities for Morning Session

1. **IMPLEMENT: Raise game model threshold to 8%** - Kill the 5-8% bucket bleeding
2. **IMPLEMENT: Disable game model UNDERs** - 18W-17L-1P, -0.86% CLV, barely breakeven. The market is better at pricing unders.
3. **K-prop data quality**: Many K-prop bets missing game_date and line fields. Fix the logging.
4. **OddsTrader TB analysis**: 36W-15L (71%), +$532. This needs formal significance testing with updated sample.
5. **Approach 300-bet mark**: 68 more graded bets to reach analysis target.
