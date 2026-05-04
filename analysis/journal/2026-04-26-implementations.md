# Implementation Log - April 26, 2026

## Changes Made (Post-Weekly Deep Dive)

### 1. Game Model UNDERs DISABLED (EXP-006)
**File**: `edge_detector.py` line 84
**Change**: `PREFERRED_SIDE["MLB"] = "OVER"`
**Why**: 10W-12L-1P, -$170, CLV -0.49%. OVERs 5W-0L +$642, CLV +0.44%. No ambiguity.

### 2. K-Prop Bias Correction Strengthened
**File**: `prop_model.py` line 327
**Change**: Multiplier 0.91 -> 0.86 (~0.9 K reduction at avg 6.4 expected)
**Why**: Previous correction was based on N=27 (0.58 overestimation). N=54 shows 0.9 overestimation. UNDER bias -0.84, OVER bias -0.96.

### 3. Pitcher Blacklist Added
**File**: `prop_model.py` lines 62-68 (config), lines 600-602 + 1163-1164 (enforcement)
**Change**: Ragans, Skubal, Sasaki, Misiorowski blacklisted from all K-prop picks.
**Why**: These 4 pitchers cause 47% of all K-prop losses. Model can't price their K variance.

### 4. K-Prop OVERs Re-enabled
**File**: `prop_model.py` line 59
**Change**: `DISABLE_OVER_BETS = False`
**Why**: Was disabled Apr 22 based on early data. Now 16W-11L +$196 (59% WR). With stronger bias correction, should improve further.

## Expected Impact
- Game model: Cuts ~$170 of drag per 23 bets. Only OVERs now.
- K-props: Fewer losing bets from blacklisted pitchers. Better calibration from stronger bias correction. Both OVER and UNDER active.
- Net: Should push combined ROI from current levels toward 15%+ target.

## What's Left
- SwStr%/CSW% integration (P0 from research, biggest accuracy gain)
- MLB_OVERDISPERSION 1.8 -> 2.1
- Remove NHL from pipeline
