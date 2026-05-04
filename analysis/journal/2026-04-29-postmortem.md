# Apr 29 Post-Game Review

## Results Summary
- **Game Model**: 1W-1L-2P (+$15.11) - Quiet day, OVERs only, BOS@TOR hit
- **K-Props**: 2W-7L (-$574.41) - CATASTROPHIC. Second straight terrible day.
- **OddsTrader**: 17W-8L (+$304.83) - Strong, TB carried the portfolio
- **Combined**: -$254.47

## The K-Prop Crisis

Two-day drawdown: **6W-14L (-$1,003.43)**. This is not variance.

### Updated All-Time Edge Buckets
| Bucket | Record | WR | PnL |
|--------|--------|----|-----|
| <10% | 5W-0L | 100% | +$309 |
| 10-15% | 24W-19L | 55.8% | +$127 |
| 15-20% | 15W-12L | 55.6% | +$66 |
| 20%+ | 7W-10L | 41.2% | -$346 |

The 10-15% bucket degraded from 63% to 55.8% WR. Still marginally profitable but barely.

### OVER vs UNDER - The Defining Split
| Direction | Record | WR | PnL |
|-----------|--------|----|-----|
| **OVER** | 20W-12L | 62.5% | +$486 |
| **UNDER** | 31W-29L | 51.7% | -$330 |

**K-prop UNDERs are a confirmed losing market.** 51.7% WR does not cover the vig. All remaining K-prop alpha is in OVERs.

### What Went Wrong Today
7 of 7 losing bets were UNDERs where pitchers threw 6+ Ks:
- Cavalli: expected under 4.5, threw 10 Ks
- Fedde: expected under 3.5, threw 6 Ks
- Rasmussen, Taillon, Bradley, Chandler: all blew through under lines

The model systematically underestimates K upside for pitchers having "on" days. UNDER bets have asymmetric risk: the downside (pitcher gets hot, throws 8+ Ks) wipes out multiple small wins.

Lambert OVER 6+ Ks got 0 Ks (model expected 5.61). The OVER model isn't perfect either, but the overall direction is clearly better.

## OddsTrader Bright Spot
Total Bases continues to be the best signal in the system. 13W-6L today. All-time real-money TB still the strongest by far.

## Mandatory Action Items for Morning Session

### URGENT: Disable K-Prop UNDERs
K-prop UNDERs must be disabled immediately. 51.7% WR, -$330 PnL. Every UNDER bet placed is negative expected value.

Only allow K-prop OVERs going forward (62.5% WR, +$486).

### Updated Bankroll
- Game Model: $4,996.95 (was $4,981.84 + $15.11)
- K-Props: $3,156.21 (was $3,730.62 - $574.41)
- OT Sim: $5,729.92 (was $5,425.09 + $304.83)
- **Combined PnL**: +$883.08 (was $1,137.55 - $254.47)

### Priority Stack for Morning
1. **DISABLE K-prop UNDERs in prop_model.py** - only allow OVERs
2. Update state/core.json with new bankroll and records
3. Recalculate: with UNDER removal, what would historical performance look like?
4. Consider reducing K-prop OVER sizing until model proves stable
5. Increase OT TB sizing (still the best signal)
