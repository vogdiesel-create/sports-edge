#!/bin/bash
# Sports Edge - Evening Grading with logging
cd /home/aiciv/sports-edge
LOG_DIR="data/daily_runs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date -u +%Y%m%d_%H%M)
LOG_FILE="$LOG_DIR/grade_${TIMESTAMP}.log"

echo "=== Evening Grade: $(date -u) ===" > "$LOG_FILE"
python3 paper_trader.py >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo "=== Multi-Book Prop Grading: $(date -u) ===" >> "$LOG_FILE"
python3 grade_all.py >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo "=== K-Prop Grading: $(date -u) ===" >> "$LOG_FILE"
python3 prop_model.py --grade >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo "=== Model Prop Pick Grading: $(date -u) ===" >> "$LOG_FILE"
python3 prop_pick_tracker.py grade >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo "=== OddsTrader Sim Grading: $(date -u) ===" >> "$LOG_FILE"
python3 grade_oddstrader.py >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
echo "=== Grade Complete: $(date -u) ===" >> "$LOG_FILE"
