#!/bin/bash
# Run Pinnacle gap backfill after API quota resets at midnight UTC.
# Logs to data/backfill_gaps.log
#
# Usage:
#   ./run_backfill.sh          # Run immediately
#   ./run_backfill.sh schedule  # Wait until 00:05 UTC then run
#
# Schedule via: nohup ./run_backfill.sh schedule &

set -e
cd "$(dirname "$0")"
LOG="data/backfill_gaps.log"

if [ "$1" = "schedule" ]; then
    # Calculate seconds until 00:05 UTC
    TARGET=$(date -u -d "tomorrow 00:05:00" +%s 2>/dev/null || date -u -d "00:05:00 tomorrow" +%s)
    NOW=$(date -u +%s)
    WAIT=$((TARGET - NOW))
    if [ "$WAIT" -lt 0 ]; then
        WAIT=$((WAIT + 86400))
    fi
    echo "$(date -u): Waiting ${WAIT}s until 00:05 UTC to start backfill..." | tee -a "$LOG"
    sleep "$WAIT"
fi

echo "$(date -u): Starting Pinnacle gap backfill" | tee -a "$LOG"
python3 backfill_pinnacle_gaps.py 2>&1 | tee -a "$LOG"
echo "$(date -u): Backfill complete" | tee -a "$LOG"

# Show final status
python3 backfill_pinnacle_gaps.py --status 2>&1 | tee -a "$LOG"
