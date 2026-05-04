# Apr 17 Post-Game Analysis

## Results Summary
- **Game Model**: 1W-4L-1P, -$335.61 (worst single day)
- **K-Props**: 7W-2L, +$221.19 (best single day)
- **Combined**: -$114.42

## Cumulative State
- Game Model: 17W-16L-1P, $5,098.74 (+$98.74)
- K-Props: 13W-5L, $3,369.74 (+$369.74)
- Combined PnL: +$468.48

## Critical Finding: Moneyline AWAY Bets Are Destroying Value

The backtest said AWAY moneylines have +4.1% ROI. Live results (n=6):
- HOME: 2-0, +$212.44
- AWAY: 0-4, -$452.41

The PREFERRED_ML_SIDE config is set to AWAY only, but somehow HOME bets slipped through on Apr 16 (and won). The AWAY-only filter is correct per backtest, but 0-4 live is painful.

**Without moneylines**: Game model totals are 15W-12L, +$338.71. The model IS profitable on totals.

**With moneylines**: 17W-16L-1P, +$98.74. Moneylines added -$240 of drag.

## Decision: Pause Moneylines

At n=6, we can't conclude the backtest is wrong. But the purpose of paper trading is to validate. Moneylines have not validated yet and are consuming bankroll that could fund more totals volume.

**Recommendation for morning session**: Disable moneyline scanning until we reach 50+ graded totals bets. Focus the edge detector on what's working (totals + K-props). Revisit moneylines after we have a statistically meaningful totals sample.

## K-Props Analysis

K-props continue to be the star: 13-5 (72.2% win rate), +$369.74 (+12.3% ROI on $3K bankroll).

Key observations:
- Under picks: 10-2 (83.3% WR) - our core edge
- Over picks: 3-3 (50% WR) - breaking even
- The model's expected K estimates are highly accurate for unders

Tonight's 2 losses were OVER bets (Williamson 7+, Lauer 6+). Both pitchers significantly underperformed. Consider tightening OVER criteria or increasing edge threshold for OVERs.

## CLV Status

Average CLV: -0.35%. Only 39% of bets have positive CLV. This is concerning - we're generally not beating closing lines. However, positive CLV bets are generating $651 in profit vs -$312 for negative CLV. The model may be finding edges that the market eventually agrees with (some lag), but we need to monitor this.

## Morning Session Priorities

1. **Disable moneyline scanning** - focus on validated markets (totals + K-props)
2. **Run Apr 18 scans** - MLB games today
3. **K-prop OVER tightening** - consider raising edge threshold for K OVERs from 5% to 8%
4. **CLV deep-dive** - are we consistently getting worse odds than close? If so, timing issue.
