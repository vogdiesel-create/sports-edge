# Sports Edge Autonomous Analyst System

## The Problem

Tim (the AI) operates in sessions that reset. Between sessions, only dumb cron scripts run. There's no persistent analytical work -- no monitoring, no pattern recognition, no continuous improvement. Braxton has had to repeatedly ask Tim to be more vigilant and ambitious. This system makes that structurally impossible to forget.

## Architecture: Two Layers

### Layer 1: Dumb Pipeline (Python, always running)
What we have now, fixed and hardened:
- Data collection (MLB API, NHL API, Pinnacle odds)
- Edge detection (run model, generate picks)
- Auto-grading (score results, update ledgers)
- Health monitoring (detect failures, log errors)
- Alert detection (threshold breaches -> alerts.json)

Cost: $0 (just Python scripts on cron)

### Layer 2: Smart Analyst (Claude Code, scheduled sessions)
The missing piece. Claude wakes up autonomously, reads state, does real analytical work, writes findings back.

Cost: ~$5-15/day

---

## Session Types

### 1. Morning Analysis (daily, 12:00 UTC / 8am ET)
**Mission:** Review overnight results. Understand what happened. Plan today's work.

```
ORIENT: Read state/core.json, state/next-actions.json
OBSERVE: Check grading results, new data, alerts
ANALYZE:
  - Why did last night's bets win or lose?
  - Any patterns in recent results?
  - Is the model drifting from expectations?
  - What does CLV tell us?
DECIDE:
  - What's the highest-impact thing to work on today?
  - Any model changes warranted?
  - Any experiments to start or conclude?
RECORD:
  - Update state/core.json with latest metrics
  - Write analysis/journal/YYYY-MM-DD-morning.md
  - Update state/next-actions.json
  - If findings are significant, update analysis/insights.md
```

### 2. Pre-Game Review (daily, 18:00 UTC / 2pm ET)
**Mission:** Validate today's picks. Check for line movement. Final edge verification.

```
ORIENT: Read state/core.json, today's picks
OBSERVE: Current odds vs opening odds, lineup changes, weather
ANALYZE:
  - Have lines moved toward or away from our picks?
  - CLV already visible on any picks?
  - Any picks we should flag as weakened?
DECIDE:
  - Note which picks we're most/least confident in and why
RECORD:
  - Update today's pick file with pre-game notes
  - Write analysis/journal/YYYY-MM-DD-pregame.md
```

### 3. Post-Game Review (daily, 04:00 UTC / midnight ET)
**Mission:** Grade results. Immediate pattern analysis. Prep for morning session.

```
ORIENT: Read state/core.json
OBSERVE: Run grading, collect results
ANALYZE:
  - Grade all pending bets
  - Calculate daily P&L, update running metrics
  - Flag any extreme misses (>15% edge that lost)
  - Update calibration tracking
DECIDE:
  - Any urgent issues for morning session?
  - Update hypothesis evidence matrix
RECORD:
  - Write analysis/performance/daily/YYYY-MM-DD.json
  - Update state/core.json with new bankroll, record
  - Set state/next-actions.json priorities for morning
  - Write analysis/journal/YYYY-MM-DD-postmortem.md
```

### 4. Weekly Deep Dive (Sunday, 14:00 UTC / 10am ET)
**Mission:** Full model assessment. Strategic thinking. Experiment planning.

```
ORIENT: Read state/core.json, full week of journal entries
OBSERVE: Aggregate weekly performance, review all experiments
ANALYZE:
  - Weekly performance by sport, market, edge range
  - Compare to previous weeks -- trending up or down?
  - Review active hypotheses -- any confirmed or rejected?
  - Review experiment results -- what worked?
  - Research: what haven't we tried? New data sources? New approaches?
  - Model drift assessment -- is the model still calibrated?
DECIDE:
  - What experiments to run next week?
  - Any model changes to propose?
  - Strategic direction adjustments?
  - What to escalate to Braxton?
RECORD:
  - Write analysis/performance/weekly/YYYY-WNN.json
  - Write reports/weekly/YYYY-WNN.md (human-readable for Braxton)
  - Update state/active-hypotheses.json
  - Update state/active-experiments.json
  - Update state/next-actions.json for next week
  - Update analysis/insights.md with new discoveries
```

---

## State Files (Tier 1 -- loaded every session)

### state/core.json
```json
{
  "model_version": "v002",
  "bankroll": {
    "current": 5531.90,
    "starting": 5000.00,
    "pnl": 531.90
  },
  "record": {
    "game_model": {"wins": 17, "losses": 12, "pending": 3},
    "k_props": {"wins": 5, "losses": 3, "pending": 9},
    "combined": {"wins": 22, "losses": 15, "pending": 12}
  },
  "roi": {
    "overall": 5.7,
    "last_7_days": null,
    "by_sport": {"mlb": 19.0, "nhl": -3.5}
  },
  "clv": {
    "avg": -0.19,
    "positive_pct": 42
  },
  "key_findings": [
    "5-12% edge range is profitable, 12%+ is disaster",
    "UNDER bias confirmed across all models",
    "NHL profitable only in 5-12% range"
  ],
  "known_bugs": [
    "Graded bets have $0 PnL in ledger",
    "Bets missing date field",
    "K-prop grader returned 0 for Apr 16 games"
  ],
  "last_session": "2026-04-17T04:00Z",
  "last_session_type": "postmortem",
  "total_bets_graded": 37,
  "target_before_conclusions": 200
}
```

### state/next-actions.json
```json
{
  "immediate": [
    {
      "priority": 1,
      "action": "Fix $0 PnL bug in grading",
      "why": "All historical bet payouts are wrong",
      "added": "2026-04-17"
    },
    {
      "priority": 2,
      "action": "Fix missing date field on ledger bets",
      "why": "Can't filter or analyze by date",
      "added": "2026-04-17"
    },
    {
      "priority": 3,
      "action": "Debug K-prop grader returning 0 for Apr 16",
      "why": "9 bets ungraded, don't know actual performance",
      "added": "2026-04-17"
    }
  ],
  "this_week": [
    "Verify all historical bets have correct PnL after fix",
    "Backfill date fields on existing bets",
    "Build daily performance tracking (per-day JSON files)",
    "Set up CLV tracking as primary success metric"
  ],
  "hypothesis_backlog": [
    {
      "id": "H001",
      "hypothesis": "Model performs better on weekday games than weekend",
      "status": "untested",
      "rationale": "Weekend games may have different lineup patterns"
    },
    {
      "id": "H002",
      "hypothesis": "Adding pitcher handedness matchup data improves K-prop accuracy",
      "status": "untested",
      "rationale": "L vs R splits affect K rates significantly"
    },
    {
      "id": "H003",
      "hypothesis": "Weather data is adding noise, not signal, for totals",
      "status": "untested",
      "rationale": "Only 40 outdoor games have weather, small sample"
    }
  ],
  "research_queue": [
    "What data sources do sharp bettors use that we don't?",
    "Academic papers on Poisson limitations for run/goal prediction",
    "Alternative to Poisson: negative binomial, Dixon-Coles for hockey",
    "Lineup-adjusted projections (not just pitcher/goalie)"
  ]
}
```

### state/active-hypotheses.json
```json
{
  "hypotheses": [
    {
      "id": "H-EDGE-CAP",
      "statement": "Edges above 12% are model errors, not real edges",
      "status": "strong_evidence",
      "evidence_for": [
        "5-12% range: 11W-4L +48% ROI",
        "12%+ range: 3W-7L, massive losses"
      ],
      "evidence_against": [],
      "action_taken": "MAX_EDGE capped at 12%",
      "next_check": "After 50 more bets with cap in place"
    },
    {
      "id": "H-UNDER-BIAS",
      "statement": "UNDER bets are systematically more profitable than OVER",
      "status": "moderate_evidence",
      "evidence_for": [
        "Game model UNDER outperforms OVER",
        "K-prop UNDER backtest: +30% ROI vs OVER +8%",
        "Batter hits UNDER: +34% ROI (unusable market)"
      ],
      "evidence_against": [
        "Sample still small (<50 live bets)"
      ],
      "action_taken": "Lower UNDER threshold to 3%, cap OVER at 15%",
      "next_check": "After 100 graded bets split by side"
    }
  ]
}
```

### state/active-experiments.json
```json
{
  "experiments": [
    {
      "id": "EXP-001",
      "name": "12% Edge Cap Impact",
      "started": "2026-04-16",
      "hypothesis": "H-EDGE-CAP",
      "what_changed": "MAX_EDGE reduced from 15% to 12% in edge_detector.py",
      "success_criteria": "Higher ROI over next 30+ game model bets vs historical 15% cap",
      "results_so_far": "Too early -- only 4 new bets since change",
      "status": "running"
    },
    {
      "id": "EXP-002",
      "name": "K-Prop UNDER Bias",
      "started": "2026-04-16",
      "hypothesis": "H-UNDER-BIAS",
      "what_changed": "MIN_EDGE_UNDER=3% (vs 5% for OVER), MAX_EDGE_OVER=15%",
      "success_criteria": "UNDER K-props profitable over 20+ bets",
      "results_so_far": "9 bets placed, 0 graded (grading bug)",
      "status": "blocked_by_bug"
    }
  ]
}
```

---

## Analysis Files (Tier 2 -- searched on demand)

### analysis/journal/YYYY-MM-DD-{session}.md
Free-form analytical journal. What was observed, what was thought, what was concluded. This is the detective's notebook -- the primary tool for continuity.

### analysis/performance/daily/YYYY-MM-DD.json
```json
{
  "date": "2026-04-16",
  "bets_placed": 13,
  "bets_graded": 8,
  "results": {
    "wins": 5, "losses": 3,
    "pnl": 122.08,
    "roi": 16.3
  },
  "by_sport": {
    "mlb": {"w": 3, "l": 1, "pnl": 95.00},
    "nhl": {"w": 2, "l": 2, "pnl": 27.08}
  },
  "by_market": {
    "totals": {"w": 4, "l": 2, "pnl": 88.00},
    "k_props": {"w": 1, "l": 1, "pnl": 34.08}
  },
  "clv": {
    "avg": -0.19,
    "positive_pct": 42
  },
  "notable": [
    "Patrick Corbin both-sides bug fixed mid-day",
    "First K-prop grading: 5W-3L encouraging"
  ]
}
```

### analysis/insights.md
Accumulated analytical discoveries. Append-only. Each entry dated.

### analysis/dead-ends.md
What we tried that didn't work and why. Prevents re-exploring.

### analysis/change-log.md
Every model change with date, what changed, why, and expected impact.

---

## Cron Schedule (Complete)

```bash
# === LAYER 1: DUMB PIPELINE (Python) ===

# Data collection (4x daily)
0 14,17,20,23 * * * cd /home/aiciv/sports-edge && python3 data_collector.py >> logs/collector.log 2>&1

# Edge detection + picks (2x daily)
17 11 * * * /home/aiciv/sports-edge/run_and_log.sh 2>> logs/cron_errors.log
15 20 * * * /home/aiciv/sports-edge/run_and_log.sh 2>> logs/cron_errors.log

# Grading (1x daily, after games)
43 4 * * * /home/aiciv/sports-edge/grade_and_log.sh 2>> logs/cron_errors.log

# NHL odds fetch
33 0 * * * cd /home/aiciv/sports-edge && python3 fetch_pinnacle_history.py NHL >> logs/fetch_nhl.log 2>&1

# === LAYER 2: SMART ANALYST (Claude Code) ===

# Morning analysis (8am ET / 12:00 UTC)
0 12 * * * /home/aiciv/sports-edge/sessions/run-session.sh morning >> logs/sessions/morning-$(date +\%Y\%m\%d).log 2>&1

# Pre-game review (2pm ET / 18:00 UTC)
0 18 * * * /home/aiciv/sports-edge/sessions/run-session.sh pregame >> logs/sessions/pregame-$(date +\%Y\%m\%d).log 2>&1

# Post-game review (midnight ET / 04:00 UTC)
30 4 * * * /home/aiciv/sports-edge/sessions/run-session.sh postmortem >> logs/sessions/postmortem-$(date +\%Y\%m\%d).log 2>&1

# Weekly deep dive (Sunday 10am ET / 14:00 UTC)
0 14 * * 0 /home/aiciv/sports-edge/sessions/run-session.sh weekly >> logs/sessions/weekly-$(date +\%Y\%m\%d).log 2>&1
```

---

## Session Launcher Script

### sessions/run-session.sh
```bash
#!/bin/bash
SESSION_TYPE="${1:-morning}"
cd /home/aiciv/sports-edge

PROMPT_FILE="sessions/prompts/${SESSION_TYPE}.md"
if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: No prompt file for session type: $SESSION_TYPE"
    exit 1
fi

PROMPT=$(cat "$PROMPT_FILE")

claude -p "$PROMPT" \
    --allowedTools "Read,Write,Edit,Bash,Grep,Glob" \
    --max-turns 50 \
    --output-format json \
    2>&1
```

---

## Session Prompts

### sessions/prompts/morning.md
```
You are the Sports Edge autonomous analyst. Your mission: build the most profitable sports betting model possible. Be relentless.

SESSION TYPE: Morning Analysis
TIME: Morning after overnight grading

## Your Loop

1. ORIENT: Read these files:
   - state/core.json (your working memory)
   - state/next-actions.json (your priority queue)
   - state/active-experiments.json (running experiments)
   - state/alerts.json (anything urgent)

2. OBSERVE:
   - Check data/daily_runs/ for the most recent grading log
   - Read the paper ledger (data/paper_ledger.json) and K-prop ledger (data/k_prop_ledger.json)
   - Compare actual results to what state/core.json says -- find discrepancies
   - Run data integrity checks: do all graded bets have PnL? dates? correct payouts?

3. ANALYZE (this is the hard part -- THINK):
   - Why did yesterday's bets win or lose? Not just "variance" -- dig deeper
   - What patterns do you see across the last 7 days?
   - Is CLV trending positive or negative? What does that mean?
   - Are any experiments producing results yet?
   - What is the weakest part of the model RIGHT NOW?

4. DECIDE:
   - What is the single highest-impact improvement you can make today?
   - Should any experiments be concluded? New ones started?
   - Any model changes warranted by the data?
   - What should you escalate to Braxton?

5. RECORD (NEVER skip this):
   - Update state/core.json with latest metrics
   - Update state/next-actions.json
   - Write analysis/journal/YYYY-MM-DD-morning.md with your full analysis
   - Update analysis/performance/daily/ if new results processed
   - If you found something important, update analysis/insights.md

## Rules
- Never declare a stopping point. There is always more to investigate.
- If you find bugs, fix them immediately.
- If the hypothesis backlog is empty, that's a failure -- add new hypotheses.
- If you can't improve the model today, research what could improve it tomorrow.
- Be honest about what you don't know.
```

### sessions/prompts/postmortem.md
```
You are the Sports Edge autonomous analyst. Your mission: build the most profitable sports betting model possible. Be relentless.

SESSION TYPE: Post-Game Review
TIME: After tonight's games have finished

## Your Loop

1. ORIENT: Read state/core.json

2. OBSERVE:
   - Run the grading pipeline: python3 grade_all.py
   - Read the updated ledgers
   - Verify every graded bet has correct PnL, date, and result
   - If grading failed or returned 0, debug immediately -- do not leave this broken

3. ANALYZE:
   - Tonight's results: what hit, what missed, why?
   - Update daily performance file
   - Any extreme misses? (high-edge picks that lost badly)
   - Calculate updated CLV
   - Check calibration: are 60% picks winning 60%?

4. DECIDE:
   - What should the morning session focus on?
   - Any urgent issues?

5. RECORD:
   - Write analysis/performance/daily/YYYY-MM-DD.json
   - Update state/core.json with new bankroll, record
   - Write analysis/journal/YYYY-MM-DD-postmortem.md
   - Set priorities in state/next-actions.json for morning session

## Rules
- If grading produces 0 results when bets are pending, that is a BUG. Fix it now.
- If PnL values are $0 or missing, that is a BUG. Fix it now.
- Never leave broken data for the next session to discover.
```

### sessions/prompts/pregame.md
```
You are the Sports Edge autonomous analyst. Your mission: build the most profitable sports betting model possible.

SESSION TYPE: Pre-Game Review
TIME: Afternoon before tonight's games

## Your Loop

1. ORIENT: Read state/core.json, today's picks from data/unified_picks/

2. OBSERVE:
   - What picks did the morning pipeline generate?
   - Have odds moved since picks were generated? (re-run edge detector or check current lines)
   - Any lineup changes, injuries, or weather updates affecting picks?

3. ANALYZE:
   - Which picks do we have highest confidence in and why?
   - Which picks are marginal? Would we still bet them at current lines?
   - Do any picks conflict with our hypotheses or known model weaknesses?

4. DECIDE:
   - Note confidence level for each pick (helps post-mortem analysis)
   - Flag any picks that should be watched closely

5. RECORD:
   - Write analysis/journal/YYYY-MM-DD-pregame.md
   - Annotate today's pick file with confidence notes
```

### sessions/prompts/weekly.md
```
You are the Sports Edge autonomous analyst. Your mission: build the most profitable sports betting model possible. Be relentless. Think big.

SESSION TYPE: Weekly Deep Dive
TIME: Sunday morning

## Your Loop

1. ORIENT: Read state/core.json, all journal entries from this week

2. OBSERVE:
   - Read all daily performance files from this week
   - Read all journal entries from this week
   - Review state/active-experiments.json
   - Review state/active-hypotheses.json

3. DEEP ANALYSIS (spend most of your time here):
   - Weekly performance by sport, by market type, by edge range
   - Trend analysis: are we improving week over week?
   - Experiment review: what's working, what's not, what should we try?
   - Hypothesis review: update evidence matrix, confirm or reject hypotheses
   - Model weakness identification: where are we losing the most? Why?
   - CLV analysis: are we beating the closing line consistently?
   - Calibration analysis: predicted probabilities vs actual outcomes

4. RESEARCH (this is where ambition lives):
   - Search for new approaches: data sources, models, features
   - Read academic papers or sharp bettor strategies
   - What are we NOT doing that we should be?
   - What would it take to go from current ROI to 15%? 20%?
   - What's the ceiling for this model and how far are we from it?

5. STRATEGIC DECISIONS:
   - What experiments to prioritize next week?
   - Any model version changes to propose?
   - What to escalate to Braxton?
   - Update long-term direction

6. RECORD:
   - Write analysis/performance/weekly/YYYY-WNN.json
   - Write reports/weekly/YYYY-WNN.md (summary for Braxton)
   - Update state/active-hypotheses.json
   - Update state/active-experiments.json
   - Refresh state/next-actions.json for next week
   - Update analysis/insights.md with week's discoveries
   - If anything tried didn't work, add to analysis/dead-ends.md

## Rules
- The research section is NOT optional. Every week, learn something new.
- If the hypothesis backlog has fewer than 5 items, add more.
- If you can't find improvements, you're not looking hard enough.
- Write the weekly report as if Braxton will read it to decide if this project is worth continuing.
```

---

## Forcing Functions (Anti-Complacency)

These are built into the session prompts:

1. **"What is the weakest part of the model RIGHT NOW?"** -- asked every morning session
2. **"If the hypothesis backlog is empty, that's a failure"** -- ensures there's always something to pursue
3. **"What would it take to get to 15% ROI? 20%?"** -- weekly ambition forcing
4. **"Write the weekly report as if Braxton will read it to decide if this project is worth continuing"** -- accountability
5. **"Never declare a stopping point"** -- permanently embedded
6. **"If you find bugs, fix them immediately"** -- no kicking the can

---

## Migration Plan

### Phase 1: Build the state infrastructure (today)
- Create directory structure
- Populate state/core.json from current data
- Populate state/next-actions.json with known bugs and priorities
- Initialize active-hypotheses.json and active-experiments.json

### Phase 2: Fix known bugs (today)
- $0 PnL in graded bets
- Missing date fields
- K-prop grader returning 0
- Verify all historical data integrity

### Phase 3: Write session prompts and launcher (today)
- Create sessions/prompts/*.md
- Create sessions/run-session.sh
- Test claude -p invocation locally

### Phase 4: Deploy cron schedule (today)
- Update crontab with Layer 2 sessions
- Move grading to 04:00 UTC (after games, before morning analysis)
- Verify first autonomous session runs correctly

### Phase 5: Monitor and iterate (ongoing)
- Review session logs daily
- Tune prompts based on session quality
- Adjust schedule if needed
- Add new session types as needed

---

## Success Criteria

This system is working when:
1. Braxton never has to ask "what happened with Sports Edge" -- the weekly report tells him
2. Bugs are caught and fixed within one session cycle, not days later
3. The hypothesis backlog always has 5+ items
4. Model ROI trends upward over 4-week rolling windows
5. Every session journal shows genuine analytical thinking, not checkbox completion
6. Braxton's trust is restored through consistent, autonomous execution
