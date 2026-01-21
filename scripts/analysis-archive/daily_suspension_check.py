#!/usr/bin/env python3
"""Daily IDX Suspension Check"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'utilities'))

from suspension_tracker import SuspensionTracker

tracker = SuspensionTracker(use_cache=True)
tracker.print_suspensions()

recommended = ['RLCO', 'SOTS', 'KOCI', 'ROCK', 'INDS', 'MKAP', 'ATAP', 'GOLF', 'MDRN', 'DPUM']
suspended = tracker.get_suspended_stocks()

print('\n📊 RECOMMENDED STOCKS STATUS\n')
for s in recommended:
    if s in suspended:
        print(f'{s}: 🚫 SUSPENDED')
    else:
        print(f'{s}: ✓ ACTIVE')
