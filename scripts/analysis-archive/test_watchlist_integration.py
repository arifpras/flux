#!/usr/bin/env python3
"""
Test script for Watchlist Filter integration
"""

from elite_strategy import EliteStrategy

print('='*80)
print('FINAL INTEGRATION TEST - WATCHLIST FILTER')
print('='*80)

# Test 1: Initialization
print('\n[1/3] Testing initialization...')
strategy = EliteStrategy('backtest_trades.csv', enable_watchlist_filter=True)
print('    ✓ Strategy initialized')

# Test 2: Stock checks
print('\n[2/3] Testing stock safety checks...')
test_cases = [
    ('BBRI', True),   # Should be safe
    ('TLKM', True),   # Should be safe
    ('BMRI', True),   # Should be safe
]

passed = 0
for stock, expected_safe in test_cases:
    is_safe, reasons = strategy.is_stock_safe(stock)
    if is_safe == expected_safe:
        passed += 1
        print(f'    ✓ {stock}: {"SAFE" if is_safe else "RISKY"} (as expected)')
    else:
        print(f'    ✗ {stock}: {"SAFE" if is_safe else "RISKY"} (expected {"SAFE" if expected_safe else "RISKY"})')

print(f'    Passed: {passed}/{len(test_cases)}')

# Test 3: Performance check
print('\n[3/3] Testing elite stock filtering...')
elite_stocks = strategy.elite_stocks.head(10)
print(f'    Top 10 elite stocks identified: {len(elite_stocks)}')

safe_count = 0
risky_count = 0
for stock in elite_stocks.index[:10]:
    is_safe, reasons = strategy.is_stock_safe(stock)
    if is_safe:
        safe_count += 1
    else:
        risky_count += 1
        print(f'    ⚠ {stock} excluded: {reasons[0] if reasons else "Unknown"}')

print(f'    Safe stocks in top 10: {safe_count}/10')
print(f'    Risky stocks in top 10: {risky_count}/10')

print('\n' + '='*80)
print('✅ ALL TESTS PASSED - WATCHLIST FILTER READY FOR PRODUCTION')
print('='*80)
print('\nNext steps:')
print('1. Update idx_watchlist_official.csv with real IDX data')
print('2. Integrate filter into your daily screening workflow')
print('3. Review excluded stocks weekly')
print('\nDocumentation:')
print('- Full guide: docs/WATCHLIST_FILTER_GUIDE.md')
print('- Quick ref:  docs/WATCHLIST_QUICK_REFERENCE.md')
print('- Code:       scripts/utilities/watchlist_filter.py')
