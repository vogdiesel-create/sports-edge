#!/usr/bin/env python3
"""Run prop grading for completed games. Call after games finish."""
import sys
sys.path.insert(0, '/home/aiciv/sports-edge')

from prop_grader import log_props, grade_props, show_summary
from auto_grader import grade_all

print("\n=== PROP GRADING ===")
log_props()
grade_props()
show_summary()

print("\n=== GAME LINE GRADING ===")
grade_all()
