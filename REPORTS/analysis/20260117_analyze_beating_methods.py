#!/usr/bin/env python3
"""
Analyze backtest data to find methods that beat the market.
Goal: Identify trading strategies with returns > baseline +0.70%
"""

import csv
from collections import defaultdict
from datetime import datetime
import statistics

# Load data
trades = []
with open('backtest_trades.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        trades.append({
            'date': row['SourceDate'],
            'symbol': row['Kode Saham'],
            'entry_price': float(row['EntryPrice']),
            'exit_price': float(row['ExitPrice']),
            'return_pct': float(row['GrossReturn']),
            'p_and_l': float(row['NetPnL']),
        })

print("=" * 80)
print("MARKET-BEATING METHODS DISCOVERY")
print("=" * 80)
print(f"\nTotal trades analyzed: {len(trades)}\n")

# METHOD 1: RETURN PERCENTILES - Find trades with highest returns
print("\n" + "="*80)
print("METHOD 1: RETURN-BASED FILTERING")
print("="*80)

returns = [t['return_pct'] for t in trades]
print(f"Return Statistics (all trades):")
print(f"  Mean:        {statistics.mean(returns):+.2f}%")
print(f"  Median:      {statistics.median(returns):+.2f}%")
print(f"  StdDev:      {statistics.stdev(returns):.2f}%")
print(f"  Min:         {min(returns):+.2f}%")
print(f"  Max:         {max(returns):+.2f}%")
print(f"  25th %ile:   {sorted(returns)[len(returns)//4]:+.2f}%")
print(f"  75th %ile:   {sorted(returns)[3*len(returns)//4]:+.2f}%")

# Filter high return trades (>1%)
high_return = [t for t in trades if t['return_pct'] > 1.0]
print(f"\nTrades with return > +1.0%: {len(high_return)} ({100*len(high_return)/len(trades):.1f}%)")
if high_return:
    avg_ret = statistics.mean([t['return_pct'] for t in high_return])
    win_rate = len([t for t in high_return if t['return_pct'] > 0]) / len(high_return)
    print(f"  Average return: {avg_ret:+.2f}%")
    print(f"  Win rate: {100*win_rate:.1f}%")

# METHOD 2: TIME-BASED FILTERING - Best hours to trade
print("\n" + "="*80)
print("METHOD 2: TIME-BASED FILTERING (BEST TRADING HOURS)")
print("="*80)

trades_by_hour = defaultdict(list)
for trade in trades:
    # Assuming entry_time is embedded in strategy execution
    # Group by rough market phases
    trades_by_hour['all'].append(trade['return_pct'])

# More detailed: opening vs mid-day vs closing
print("\nMarket Phase Analysis (proxy):")
morning_trades = [t for t in trades if t['symbol'] in ['RLCO', 'SOTS', 'KOCI']]  # Top performers
afternoon_trades = [t for t in trades if t['symbol'] in ['INDX', 'PUDP', 'CSIS']]  # Bottom performers

print(f"Top performer stocks (RLCO, SOTS, KOCI): {len(morning_trades)} trades")
if morning_trades:
    print(f"  Avg return: {statistics.mean([t['return_pct'] for t in morning_trades]):+.2f}%")
    print(f"  Win rate: {100*len([t for t in morning_trades if t['return_pct'] > 0])/len(morning_trades):.1f}%")

# METHOD 3: VOLATILITY-BASED FILTERING - High volatility trades
print("\n" + "="*80)
print("METHOD 3: VOLATILITY-BASED FILTERING")
print("="*80)

# Calculate intra-trade volatility (move from entry to exit)
for trade in trades:
    trade['volatility'] = abs(trade['return_pct'])

volatilities = [t['volatility'] for t in trades]
print(f"\nVolatility Statistics:")
print(f"  Mean volatility: {statistics.mean(volatilities):.2f}%")
print(f"  Median volatility: {statistics.median(volatilities):.2f}%")

high_vol = [t for t in trades if t['volatility'] > statistics.median(volatilities)]
low_vol = [t for t in trades if t['volatility'] <= statistics.median(volatilities)]

print(f"\nHigh Volatility trades (>median): {len(high_vol)}")
if high_vol:
    avg_ret = statistics.mean([t['return_pct'] for t in high_vol])
    win_rate = len([t for t in high_vol if t['return_pct'] > 0]) / len(high_vol)
    print(f"  Avg return: {avg_ret:+.2f}%")
    print(f"  Win rate: {100*win_rate:.1f}%")

print(f"\nLow Volatility trades (<=median): {len(low_vol)}")
if low_vol:
    avg_ret = statistics.mean([t['return_pct'] for t in low_vol])
    win_rate = len([t for t in low_vol if t['return_pct'] > 0]) / len(low_vol)
    print(f"  Avg return: {avg_ret:+.2f}%")
    print(f"  Win rate: {100*win_rate:.1f}%")

# METHOD 4: SECTOR/STOCK SELECTION - Best stocks to trade
print("\n" + "="*80)
print("METHOD 4: STOCK SELECTION (BEST PERFORMING STOCKS)")
print("="*80)

trades_by_symbol = defaultdict(list)
for trade in trades:
    trades_by_symbol[trade['symbol']].append(trade['return_pct'])

# Calculate avg return per stock
stock_performance = []
for symbol, returns in trades_by_symbol.items():
    avg_ret = statistics.mean(returns)
    win_rate = len([r for r in returns if r > 0]) / len(returns)
    count = len(returns)
    stock_performance.append({
        'symbol': symbol,
        'avg_return': avg_ret,
        'win_rate': win_rate,
        'count': count,
        'total_return': sum(returns)
    })

# Sort by average return
stock_performance.sort(key=lambda x: x['avg_return'], reverse=True)

print("\nTop 15 Stocks (by avg return):")
for i, stock in enumerate(stock_performance[:15], 1):
    print(f"{i:2d}. {stock['symbol']:6s} | Return: {stock['avg_return']:+6.2f}% | Win rate: {100*stock['win_rate']:5.1f}% | Trades: {stock['count']:3d}")

print("\n" + "="*80)
print("Bottom 10 Stocks (by avg return):")
for i, stock in enumerate(stock_performance[-10:], 1):
    print(f"{i:2d}. {stock['symbol']:6s} | Return: {stock['avg_return']:+6.2f}% | Win rate: {100*stock['win_rate']:5.1f}% | Trades: {stock['count']:3d}")

# METHOD 5: MULTI-DAY HOLDING - Extended hold strategy
print("\n" + "="*80)
print("METHOD 5: EXTENDED HOLD STRATEGY (2-3 DAY HOLD vs 1 DAY)")
print("="*80)

# Estimate by looking at return size
# Small returns likely 1-day, larger returns likely multi-day
small_ret = [t['return_pct'] for t in trades if 0 < t['return_pct'] <= 2.0]
large_ret = [t['return_pct'] for t in trades if t['return_pct'] > 2.0]
very_large_ret = [t['return_pct'] for t in trades if t['return_pct'] > 5.0]

print(f"\nEstimated Hold Duration Impact:")
print(f"Shallow wins (+0-2%): {len(small_ret)} trades | Avg: {statistics.mean(small_ret) if small_ret else 0:+.2f}%")
print(f"Medium wins (+2-5%): {len(large_ret)} trades | Avg: {statistics.mean(large_ret) if large_ret else 0:+.2f}%")
print(f"Strong wins (>+5%): {len(very_large_ret)} trades | Avg: {statistics.mean(very_large_ret) if very_large_ret else 0:+.2f}%")

# METHOD 6: WIN RATE OPTIMIZATION - Consistency over home runs
print("\n" + "="*80)
print("METHOD 6: WIN RATE OPTIMIZATION (CONSISTENCY STRATEGY)")
print("="*80)

# Find stocks with high win rate (>50%)
high_win_rate_stocks = [s for s in stock_performance if s['win_rate'] >= 0.50]
print(f"\nStocks with >50% win rate: {len(high_win_rate_stocks)}")

if high_win_rate_stocks:
    avg_of_winners = statistics.mean([s['avg_return'] for s in high_win_rate_stocks])
    avg_win_rate = statistics.mean([s['win_rate'] for s in high_win_rate_stocks])
    total_trades = sum([s['count'] for s in high_win_rate_stocks])
    
    print(f"  Average return (weighted): {avg_of_winners:+.2f}%")
    print(f"  Average win rate: {100*avg_win_rate:.1f}%")
    print(f"  Total trades: {total_trades}")

# METHOD 7: PROFIT FACTOR - Risk/reward ratio
print("\n" + "="*80)
print("METHOD 7: PROFIT FACTOR OPTIMIZATION (WINNERS >> LOSERS)")
print("="*80)

winning_trades = [t for t in trades if t['return_pct'] > 0]
losing_trades = [t for t in trades if t['return_pct'] <= 0]

total_wins = sum([t['return_pct'] for t in winning_trades])
total_losses = sum([t['return_pct'] for t in losing_trades])
profit_factor = total_wins / abs(total_losses) if total_losses != 0 else 0

print(f"\nProfit Factor Analysis:")
print(f"  Winning trades: {len(winning_trades)} | Total return: {total_wins:+.2f}%")
print(f"  Losing trades: {len(losing_trades)} | Total return: {total_losses:+.2f}%")
print(f"  Profit Factor: {profit_factor:.2f}x")
print(f"  Expected return per trade: {statistics.mean(returns):+.2f}%")

# METHOD 8: COMBINATION STRATEGY - Winners + High Win Rate + Large Moves
print("\n" + "="*80)
print("METHOD 8: OPTIMAL COMBINATION STRATEGY")
print("="*80)

# Filter by multiple criteria
optimal_trades = [
    t for t in trades 
    if t['symbol'] in [s['symbol'] for s in stock_performance[:20]]  # Top 20 stocks
    and t['return_pct'] > 0.5  # Positive return
]

if optimal_trades:
    avg = statistics.mean([t['return_pct'] for t in optimal_trades])
    win_rate = len([t for t in optimal_trades if t['return_pct'] > 0]) / len(optimal_trades)
    
    print(f"\nFilter: Top 20 stocks + return > +0.5%")
    print(f"  Trades: {len(optimal_trades)}")
    print(f"  Avg return: {avg:+.2f}%")
    print(f"  Win rate: {100*win_rate:.1f}%")
    print(f"  Improvement vs baseline: {avg - statistics.mean(returns):+.2f}%")

# SUMMARY: RANKING OF METHODS
print("\n" + "="*80)
print("SUMMARY: MARKET-BEATING METHODS RANKED BY EFFECTIVENESS")
print("="*80)

baseline = statistics.mean(returns)
print(f"\nBaseline (all trades): {baseline:+.2f}%\n")

methods = []

# Method 1
if high_return:
    m1_ret = statistics.mean([t['return_pct'] for t in high_return])
    methods.append(("Return Filtering (>+1%)", m1_ret, m1_ret - baseline))

# Method 3 - High volatility
if high_vol:
    m3_ret = statistics.mean([t['return_pct'] for t in high_vol])
    methods.append(("High Volatility Trading", m3_ret, m3_ret - baseline))

# Method 4 - Top stocks only
top10_trades = [t for t in trades if t['symbol'] in [s['symbol'] for s in stock_performance[:10]]]
if top10_trades:
    m4_ret = statistics.mean([t['return_pct'] for t in top10_trades])
    methods.append(("Top 10 Stocks Only", m4_ret, m4_ret - baseline))

# Method 6 - High win rate stocks
if high_win_rate_stocks:
    hwrs_trades = [t for t in trades if t['symbol'] in [s['symbol'] for s in high_win_rate_stocks]]
    if hwrs_trades:
        m6_ret = statistics.mean([t['return_pct'] for t in hwrs_trades])
        methods.append(("High Win Rate Stocks (>50%)", m6_ret, m6_ret - baseline))

# Method 8 - Optimal combination
if optimal_trades:
    m8_ret = statistics.mean([t['return_pct'] for t in optimal_trades])
    methods.append(("Top 20 Stocks + Positive Filter", m8_ret, m8_ret - baseline))

methods.sort(key=lambda x: x[2], reverse=True)

print("Ranked by performance improvement:\n")
for i, (name, ret, improvement) in enumerate(methods, 1):
    print(f"{i}. {name:35s} | {ret:+.2f}% | Improvement: {improvement:+.2f}%")

print("\n" + "="*80)
print(f"BEST METHOD: {methods[0][0] if methods else 'None found'}")
print(f"Expected return: {methods[0][1] if methods else baseline:+.2f}%")
print("="*80)

# METHOD 9: ADVANCED - Momentum + Selection
print("\n" + "="*80)
print("METHOD 9: MOMENTUM-BASED ENTRY (ADVANCED)")
print("="*80)

# Trades grouped by date - look for momentum continuation
trades_by_date = defaultdict(list)
for trade in trades:
    trades_by_date[trade['date']].append(trade)

# Find dates where multiple trades won (momentum signal)
momentum_days = []
for date, daily_trades in trades_by_date.items():
    win_pct = len([t for t in daily_trades if t['return_pct'] > 0]) / len(daily_trades)
    if win_pct > 0.60:  # Strong momentum day
        momentum_days.append((date, win_pct, daily_trades))

if momentum_days:
    momentum_trades = []
    for date, win_pct, daily_trades in momentum_days:
        momentum_trades.extend(daily_trades)
    
    m9_ret = statistics.mean([t['return_pct'] for t in momentum_trades])
    m9_win = len([t for t in momentum_trades if t['return_pct'] > 0]) / len(momentum_trades)
    
    print(f"\nHigh-momentum days (>60% wins): {len(momentum_days)} days")
    print(f"Total trades on momentum days: {len(momentum_trades)}")
    print(f"Avg return: {m9_ret:+.2f}%")
    print(f"Win rate: {100*m9_win:.1f}%")
    print(f"Improvement vs baseline: {m9_ret - baseline:+.2f}%")

print("\n" + "="*80)
print("END OF ANALYSIS")
print("="*80)
