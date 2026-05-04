#!/bin/bash
# Sports Edge - Daily Pipeline Runner with logging
# Runs edge detector, grades bets, logs output
cd /home/aiciv/sports-edge
LOG_DIR="data/daily_runs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date -u +%Y%m%d_%H%M)
LOG_FILE="$LOG_DIR/cron_${TIMESTAMP}.log"

echo "=== Sports Edge Daily Run: $(date -u) ===" > "$LOG_FILE"
python3 run_daily.py >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo "=== K-Prop Model: DISABLED (51W-47L, -\$363, systematic failure) ===" >> "$LOG_FILE"
# python3 prop_model.py >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo "=== Run Complete: $(date -u) ===" >> "$LOG_FILE"
