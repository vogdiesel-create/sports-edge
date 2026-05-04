# May 1, 2026 - Post-Game Review

## Tonight: 6W-2L, +$350.60

### OddStrader: 4W-1L (+$286.40)
All Total Bases plays tonight. The juice cap is doing its job — 4 of 5 bets within -160 cap.

**Winners:**
- Jorge Mateo TB u1.5 (-160, 26.1% EV) — +$103.38
- Jonah Heim TB u1.5 (-135, 18.0% EV) — +$122.52
- Will Smith TB u1.5 (-135, 17.5% EV) — +$122.52
- Luis Rengifo TB u1.5 (-160, 13.1% EV) — +$103.38

**Loser:**
- Jarren Duran TB u1.5 (-145, 17.4% EV) — -$165.40

Duran went 2-for-4 with a double (3 TB). The model had fair value at 70% under — close to correct but he ran into one. Normal variance.

### Game Model: 2W-1L (+$64.20)
- BAL @ NYY — WIN (+$118.96)
- ATL @ COL — WIN (+$101.03)
- MIL @ WSH — LOSS (-$155.79)

### Grading Housekeeping
- **Fixed accent matching bug** in grade_oddstrader.py — Walbert Ureña wasn't matching because ñ→n normalization was missing. Added unicodedata NFD normalization.
- **Graded Ureña** (Apr 25): Hits Allowed u5.5 — LOSS. Allowed 6+ hits.
- **Graded Senga** (Apr 25→26): Strikeouts u5.5 — WIN (+$92.10). Had 1 K in 2.2 IP before IL stint.
- **Voided Marsh** (Apr 29): Game postponed (weather). $0 PnL.

## Cumulative State

| Model | Record | PnL | ROI |
|-------|--------|-----|-----|
| OT Total Bases | 76W-32L (70.4%) | +$1,770 | +15.9% |
| OT Hits Allowed | 16W-10L (61.5%) | +$231 | +9.5% |
| OT Earned Runs | 2W-1L (66.7%) | +$36 | +11.9% |
| OT Strikeouts | 12W-13L (48.0%) | -$279 | DISABLED |
| OT RBI | 11W-28L (28.2%) | -$956 | DISABLED |
| Game Model | 32W-29L-4P | +$257 | +3.1% |
| K-Props | 51W-47L | -$363 | DEAD |

**Active-only PnL: +$2,293.83**
**All models PnL: +$695.78**

### TB Juice Analysis (Updated)
- Within -160 cap: **36W-12L (75.0%) +$1,542 ROI: 30.3%**
- Beyond -160 cap: 40W-20L (66.7%) +$229 ROI: 3.8%

The cap is the single best decision we've made. 30.3% ROI vs 3.8%.

## Key Observations

1. **TB within cap is absurd**: 75% WR at 30.3% ROI over 48 bets. This is the signal.
2. **K-Props are hemorrhaging**: 51W-47L, -$363. Five straight losses since Apr 28. Model is dead — needs complete overhaul with SwStr%/CSW% features or should be permanently disabled.
3. **HA market softening**: Was 16W-9L, now 16W-10L after Ureña loss. Still solid at 9.5% ROI.
4. **Ks market added 1 win** (Senga graded): 12W-13L. Still negative, still disabled.

## Morning Session Priorities

1. Check if Kwan bet from today grades
2. Run pregame scan for May 2 slate
3. Consider permanently killing K-Props model — it's been a drag since launch
4. Game model is 32W-29L — not statistically significant but directionally profitable
