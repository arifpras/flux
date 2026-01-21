#!/usr/bin/env python3
"""Ultra-fast vectorized backtest"""

import pandas as pd
import numpy as np

print("Loading data...")
df = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
watchlist = pd.read_csv('data/IHSGstockdata/alerts/manipulation_watchlist.csv')

df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

for col in ['Penutupan', 'Sebelumnya', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"✓ {len(df)} rows, {len(watchlist)} flags")

# Create exit dates for each entry (shift forward by 1 trading day)
dates_sorted = sorted(df['SourceDate'].unique())
date_map = {d: dates_sorted[i+1] if i < len(dates_sorted)-1 else None for i, d in enumerate(dates_sorted)}

# Add exit date to watchlist
watchlist['ExitDate'] = watchlist['SourceDate'].map(date_map)
watchlist = watchlist.dropna(subset=['ExitDate'])

print(f"✓ {len(watchlist)} trades with next day available")

# Merge entry prices
entry_df = df[['SourceDate', 'Kode Saham', 'Penutupan']].copy()
entry_df.columns = ['SourceDate', 'Kode Saham', 'EntryPrice']

watchlist = watchlist.merge(entry_df, on=['SourceDate', 'Kode Saham'], how='left')
watchlist = watchlist.dropna(subset=['EntryPrice'])

# Merge exit prices
exit_df = df[['SourceDate', 'Kode Saham', 'Penutupan']].copy()
exit_df.columns = ['ExitDate', 'Kode Saham', 'ExitPrice']

watchlist = watchlist.merge(exit_df, on=['ExitDate', 'Kode Saham'], how='left')
watchlist = watchlist.dropna(subset=['ExitPrice'])

print(f"✓ {len(watchlist)} complete entry/exit pairs")

# Calculate returns
watchlist['GrossReturn'] = (watchlist['ExitPrice'] - watchlist['EntryPrice']) / watchlist['EntryPrice'] * 100
watchlist['NetPnL'] = watchlist['GrossReturn'] - 0.2

# Stats
trades_df = watchlist[['Kode Saham', 'SourceDate', 'ExitDate', 'EntryPrice', 'ExitPrice', 'GrossReturn', 'NetPnL']].copy()

wins = (trades_df['NetPnL'] > 0).sum()
losses = (trades_df['NetPnL'] <= 0).sum()
total = len(trades_df)
win_rate = 100 * wins / total if total > 0 else 0
avg_pnl = trades_df['NetPnL'].mean()
median_pnl = trades_df['NetPnL'].median()
max_gain = trades_df['NetPnL'].max()
max_loss = trades_df['NetPnL'].min()
std_dev = trades_df['NetPnL'].std()
total_pnl = trades_df['NetPnL'].sum()

# Results
print(f"\n{'='*80}")
print(f"BACKTEST: Day-Trading Pump Strategy (Dec 1 - Jan 15, 2026)")
print(f"{'='*80}\n")

print(f"Total Trades:              {total}")
print(f"Wins:                      {wins} ({win_rate:.1f}%)")
print(f"Losses:                    {losses} ({100-win_rate:.1f}%)\n")

print(f"Average P&L:               {avg_pnl:+.4f}%")
print(f"Median P&L:                {median_pnl:+.4f}%")
print(f"Std Dev:                   {std_dev:.4f}%\n")

print(f"Best Trade:                {max_gain:+.4f}%")
print(f"Worst Trade:               {max_loss:+.4f}%\n")

print(f"Total Cumulative P&L:      {total_pnl:+.2f}%")

print(f"\n{'='*80}")
if avg_pnl > 0.5:
    verdict = "✅ PROFITABLE"
elif avg_pnl > 0:
    verdict = "⚠️  MARGINAL"
else:
    verdict = "❌ UNPROFITABLE"

print(f"{verdict}: {avg_pnl:+.4f}% per trade | Win Rate {win_rate:.1f}%")
print(f"{'='*80}\n")

# Save
trades_df.to_csv('backtest_trades.csv', index=False)
print("✓ Saved backtest_trades.csv")

stats_dict = {
    'total_trades': [total],
    'win_rate_%': [win_rate],
    'avg_pnl_%': [avg_pnl],
    'median_%': [median_pnl],
    'best_%': [max_gain],
    'worst_%': [max_loss],
    'std_dev_%': [std_dev],
    'total_pnl_%': [total_pnl]
}

pd.DataFrame(stats_dict).to_csv('backtest_summary.csv', index=False)
print("✓ Saved backtest_summary.csv\n")
