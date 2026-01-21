#!/usr/bin/env python3
"""
Daily IDX Suspension Checker
=============================
Run this daily to track suspension status and get alerts.
"""

import sys
import os

# Add scripts to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'stockscraper', 'scripts', 'utilities'))

# Import suspension tracker
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'scripts', 'utilities'))
from suspension_tracker import SuspensionTracker
from suspension_tracker import SuspensionTracker

print('='*80)
print('IDX SUSPENSION TRACKER - DAILY CHECK')
print('='*80)

# Initialize tracker (will fetch fresh data or use cache)
print('\n📡 Checking IDX suspension status...\n')
tracker = SuspensionTracker(use_cache=True, cache_age_hours=6)

# Print full report
tracker.print_suspensions()

# Get suspended stocks
suspended = tracker.get_suspended_stocks()
reopened = tracker.get_reopened_stocks()

# Check recommended stocks
recommended_stocks = ['RLCO', 'SOTS', 'KOCI', 'ROCK', 'INDS', 'MKAP', 'ATAP', 'GOLF', 'MDRN', 'DPUM']

print('\n\n📊 RECOMMENDED STOCKS STATUS')
print('='*80)

safe_to_trade = []
has_issues = []

for stock in recommended_stocks:
    is_suspended, reason = tracker.is_suspended(stock)
    info = tracker.get_suspension_info(stock)
    
    if is_suspended:
        status = "🚫 SUSPENDED"
        has_issues.append((stock, reason))
    elif stock in reopened:
        status = "⚠️ RECENTLY REOPENED"
        has_issues.append((stock, f"Reopened {info['reopening_date']} - Monitor closely"))
    else:
        status = "✓ SAFE TO TRADE"
        safe_to_trade.append(stock)
    
    print(f"{stock:<10} {status:<30}", end="")
    if info:
        print(f"  Last event: {info['last_event_date']}")
    else:
        print()

print('\n\n' + '='*80)
print(f'✓ SAFE TO TRADE: {len(safe_to_trade)} stocks')
print(f'⚠ HAS ISSUES: {len(has_issues)} stocks')
print('='*80)

if safe_to_trade:
    print(f"\nTrade Focus: {', '.join(safe_to_trade)}")

if has_issues:
    print(f"\n⚠ Avoid or Monitor:")
    for stock, reason in has_issues:
        print(f"  • {stock}: {reason}")

print('\n' + '='*80)
print('Run this script daily to stay updated on suspension status')
print('='*80)
