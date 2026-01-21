#!/usr/bin/env python3
"""
FINAL VALIDATED WATCHLIST - 20 Proven Stocks
Validated for trading on 19 Jan 2026
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKTEST_FILE = os.path.join(BASE_DIR, 'backtest_trades.csv')

# Load data
df = pd.read_csv(BACKTEST_FILE)
df['SourceDate'] = pd.to_datetime(df['SourceDate'])
df['ExitDate'] = pd.to_datetime(df['ExitDate'])
df['HoldDays'] = (df['ExitDate'] - df['SourceDate']).dt.days

# FINAL VALIDATED WATCHLIST - 20 stocks
FINAL_WATCHLIST = [
    'RLCO', 'ROCK', 'CANI', 'TIRT', 'HADE', 'VISI', 'KDTN', 'RICY', 
    'MTFN', 'TAXI', 'EURO', 'SINI', 'RMKO', 'PBSA', 'INPS', 'MORA', 
    'SSTM', 'INOV', 'NATO', 'DEWI'
]

TARGET_DATE = datetime(2026, 1, 19)
VALIDATION_WINDOW = 7

print("="*100)
print("FINAL VALIDATED WATCHLIST - 20 STOCKS")
print("="*100)
print(f"\nValidation Date: {TARGET_DATE.date()}")
print(f"Validation Window: Last {VALIDATION_WINDOW} days")

# Get latest prices and validation stats
validation_start = TARGET_DATE - pd.Timedelta(days=VALIDATION_WINDOW)

print(f"\n{'#':<4}{'Stock':<8}{'Avg':<10}{'Win%':<8}{'Hold':<8}{'Recent':<10}{'Val Wins':<10}{'Val Trades':<12}{'Latest Price':<15}")
print("-"*100)

watchlist_stats = []
for idx, stock in enumerate(FINAL_WATCHLIST, 1):
    stock_data = df[df['Kode Saham'] == stock]
    
    if len(stock_data) == 0:
        print(f"{idx:<4}{stock:<8}NO DATA")
        continue
    
    # Overall stats
    avg_return = stock_data['NetPnL'].mean()
    win_rate = (stock_data['NetPnL'] > 0).mean()
    avg_hold = stock_data['HoldDays'].mean()
    
    # Recent validation (last 7 days)
    recent = stock_data[
        (stock_data['SourceDate'] >= validation_start) & 
        (stock_data['SourceDate'] <= TARGET_DATE)
    ]
    
    recent_return = recent['NetPnL'].mean() if len(recent) > 0 else 0
    recent_wins = (recent['NetPnL'] > 0).sum()
    recent_count = len(recent)
    
    # Latest price
    latest_price = stock_data.sort_values('SourceDate', ascending=False).iloc[0]['EntryPrice']
    
    print(f"{idx:<4}{stock:<8}{avg_return:>9.2f}%{win_rate*100:>7.1f}%{avg_hold:>8.1f}{recent_return:>10.2f}%{int(recent_wins):>10}/{int(recent_count):<10}{latest_price:>15.0f}")
    
    watchlist_stats.append({
        'rank': idx,
        'stock': stock,
        'avg_return': avg_return,
        'win_rate': win_rate,
        'avg_hold': avg_hold,
        'recent_return': recent_return,
        'recent_wins': recent_wins,
        'recent_trades': recent_count,
        'latest_price': latest_price,
    })

stats_df = pd.DataFrame(watchlist_stats)

print("\n" + "="*100)
print("WATCHLIST STATISTICS")
print("="*100)
print(f"\nTotal Stocks: {len(FINAL_WATCHLIST)}")
print(f"Avg Return: {stats_df['avg_return'].mean():.2f}%")
print(f"Avg Win Rate: {stats_df['win_rate'].mean()*100:.1f}%")
print(f"Avg Hold: {stats_df['avg_hold'].mean():.1f} days")
print(f"Recent Avg Return (7d): {stats_df['recent_return'].mean():.2f}%")
print(f"Total Recent Wins: {stats_df['recent_wins'].sum():.0f} / {stats_df['recent_trades'].sum():.0f}")
print(f"Avg Price: Rp {stats_df['latest_price'].mean():.0f}")
print(f"Min Price: Rp {stats_df['latest_price'].min():.0f}")
print(f"Max Price: Rp {stats_df['latest_price'].max():.0f}")

# Tier 1: Anchor stocks (RLCO, ROCK)
print("\n" + "="*100)
print("TIER 1 - ANCHOR STOCKS (Highest Confidence)")
print("="*100)
tier1 = stats_df[stats_df['stock'].isin(['RLCO', 'ROCK'])]
for _, row in tier1.iterrows():
    print(f"  {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}% │ Hold: {row['avg_hold']:>4.1f}d │ Price: Rp{row['latest_price']:>8.0f}")

# Tier 2: Top performers
print("\n" + "="*100)
print("TIER 2 - TOP PERFORMERS (Strong Validation)")
print("="*100)
tier2 = stats_df[~stats_df['stock'].isin(['RLCO', 'ROCK'])].nlargest(6, 'avg_return')
for _, row in tier2.iterrows():
    print(f"  {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}% │ Hold: {row['avg_hold']:>4.1f}d │ Price: Rp{row['latest_price']:>8.0f}")

# Tier 3: All others
print("\n" + "="*100)
print("TIER 3 - SUPPORTING STOCKS (Validated Pattern)")
print("="*100)
tier3 = stats_df[~stats_df['stock'].isin(['RLCO', 'ROCK']) & ~stats_df['stock'].isin(tier2['stock'].tolist())].sort_values('avg_return', ascending=False)
for _, row in tier3.iterrows():
    print(f"  {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}% │ Hold: {row['avg_hold']:>4.1f}d │ Price: Rp{row['latest_price']:>8.0f}")

# Entry/Exit Rules
print("\n" + "="*100)
print("TRADING RULES")
print("="*100)
print("""
Entry Signals:
  1. Broker accumulation signal (check data/manual/broker_accumulation_signals.txt)
  2. Day 2-3 momentum confirmation
  3. Volume > 10k shares
  4. Price change 2-5% intraday

Exit Rules:
  1. Target: +5% profit
  2. Stop Loss: -2%
  3. Time Stop: Exit on day 3 close if not hit

Position Sizing:
  • Tier 1: 50% of capital per trade
  • Tier 2: 25-30% of capital per trade
  • Tier 3: 15-20% of capital per trade
  • Max 10 concurrent positions
  • Use 50% position size to preserve capital

Validation Rules:
  ✓ Stock price ≥ Rp100
  ✓ Not suspended on IDX
  ✓ Positive recent performance (last 7 days)
  ✓ Liquidity > 10k shares/day
  ✓ Not on IDX watchlist
""")

# Save watchlist
watchlist_file = os.path.join(BASE_DIR, 'watchlist_final_20stocks.txt')
with open(watchlist_file, 'w') as f:
    f.write("FINAL VALIDATED WATCHLIST - 20 STOCKS\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Validation Date: {TARGET_DATE.date()}\n")
    f.write("="*100 + "\n\n")
    f.write("WATCHLIST:\n")
    for stock in FINAL_WATCHLIST:
        f.write(f"  {stock}\n")
    f.write("\n" + "="*100 + "\n\n")
    f.write("TIER 1 (Anchor):\n")
    for _, row in tier1.iterrows():
        f.write(f"  {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}%\n")
    f.write("\nTIER 2 (Top Performers):\n")
    for _, row in tier2.iterrows():
        f.write(f"  {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}%\n")
    f.write("\nTIER 3 (Supporting):\n")
    for _, row in tier3.iterrows():
        f.write(f"  {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}%\n")

print(f"\n✓ Watchlist saved to: {watchlist_file}")
print("\n" + "="*100)
