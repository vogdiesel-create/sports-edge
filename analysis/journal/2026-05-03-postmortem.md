# Post-Game Review: May 3, 2026

## Results Summary

**OddsTr: 3W-1L (+$216.49)**
**Game Model: 0W-1L (-$104.51)**
**Net: +$111.98**

## OddsTr Picks

| Player | Market | Line | Odds | Result | PnL | Actual |
|--------|--------|------|------|--------|-----|--------|
| Michael Busch | TB | u1.5 | -135 | LOSS | -$180.05 | 5 |
| Luis Rengifo | TB | u1.5 | -160 | WIN | +$112.53 | 0 |
| Michael Harris | TB | u1.5 | -105 | WIN | +$171.48 | 0 |
| Steven Matz | HA | u5.5 | -160 | WIN | +$112.53 | 4 |

## Analysis

### The Busch Blowup (5 TB)
Model had 78% probability of staying under 1.5 TB. Busch went 3-for-4 with a double (5 total bases) against the Cubs. This is a ~22% event that happened — within expected variance for a single pick. No model fix needed for this kind of miss.

### Matz HA Filter Violation
The HA line filter (EXP-012) was implemented May 3 to skip u5.5+ lines. Matz was u5.5 — this pick should NOT have been generated under the new filter. It won anyway (4 HA vs 5.5 line), but the filter exists because u5.5+ has only 50% WR historically. Need to verify the filter is actually active in the scraper.

### Game Model (KC @ SEA OVER)
Game model continues to be a coin flip. 33W-33L now. Not contributing edge. This model needs either major improvement or permanent disabling.

## Calibration Check

TB model: 80W-33L (70.8%) on picks where we estimated ~65-78% fair probability. Model is well-calibrated or slightly conservative.

Active markets overall: 100W-46L (68.5%). The edge is real and sustained.

## Key Numbers Update

| Metric | Value |
|--------|-------|
| OddsTr bankroll | $6,043.96 |
| OddsTr total PnL | +$1,043.96 |
| Active markets PnL | +$2,278.90 |
| TB PnL | +$2,102.97 |
| TB within juice cap | 38W-12L (76.0%) |

## Action Items for Morning Session

1. **Verify HA line filter is active** — Matz u5.5 should have been filtered. Check oddstrader_scraper.py for EXP-012 implementation.
2. **No May 4 picks** — Investigate whether morning scan ran or if there were simply no qualifying picks today.
3. **Game model decision** — At 33W-33L, this is a provably zero-edge model. Consider disabling to reduce noise.
4. **TB continues dominant** — 80W-33L. No changes needed to core TB logic.
