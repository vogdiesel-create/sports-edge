#!/bin/bash
# Sports Edge Autonomous Analyst - Session Launcher
# Usage: ./run-session.sh [morning|pregame|postmortem|weekly]

SESSION_TYPE="${1:-morning}"
cd /home/aiciv/sports-edge
mkdir -p logs/sessions

PROMPT_FILE="sessions/prompts/${SESSION_TYPE}.md"
if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: No prompt file for session type: $SESSION_TYPE"
    echo "Available: morning, pregame, postmortem, weekly"
    exit 1
fi

echo "=== Sports Edge Analyst Session: ${SESSION_TYPE} ==="
echo "=== $(date -u '+%Y-%m-%d %H:%M UTC') ==="
echo ""

PROMPT=$(cat "$PROMPT_FILE")

claude -p "$PROMPT" \
    --allowedTools "Read,Write,Edit,Bash,Grep,Glob" \
    --max-turns 50 \
    2>&1

echo ""
echo "=== Session Complete: $(date -u '+%Y-%m-%d %H:%M UTC') ==="
