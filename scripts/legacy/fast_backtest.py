#!/usr/bin/env python3
"""Fast backtest of day-trading pump strategy"""

import pandas as pd
import numpy as np
from datetime import timedelta

print("Loading data...")
df = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
watchlist = pd.read_csv('data/IHSGstockdata/alerts/manipulation_watchlist.csv')

df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

for col in ['Penutupan', 'Sebelumnya', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"✓ Loaded {len(df)} rows, {len(watchlist)} flagged trades")

# Create mapping of (date, ticker) -> close price
date_ticker_close = {}
for _, row in df.iterrows():
    key = (row['SourceDate'], row['Kode Saham'])
    date_ticker_close[key] = row['Penutupan']

print("✓ Built price lookup table")

# Backtest: for each flagged trade, match entry/exit
trades = []
print("\nMatching entry/exit prices...")

for _, flag_row in watchlist.iterrows():
    entry_date = flag_row['SourceDate']
    ticker = flag_row['Kode Saham']
    
    # Find next trading date
    all_dates = sorted(df['SourceDate'].unique())
    if entry_date not in all_dates:
        continue
    
    date_idx = list(all_dates).index(entry_date)
    if date_idx >= len(all_dates) - 1:
        continue  # No next day
    
    exit_date = all_dates[date_idx + 1]
    
    entry_key = (entry_date, ticker)
    exit_key = (exit_date, ticker)
    
    if entry_key not in date_ticker_close or exit_key not in date_ticker_close:
        continue
    
    entry_price = date_ticker_close[entry_key]
    exit_price = date_ticker_close[exit_key]
    
    # Calculate P&L with 0.2% slippage
    gross_return = (exit_price - entry_price) / entry_price * 100
    net_pnl = gross_return - 0.2
    
    trades.append({
        'ticker': ticker,
        'entry_date': entry_date.date(),
        'exit_date': exit_date.date(),
        'entry_price': entry_price,
        'exit_price': exit_price,
        'gross_return_pct': gross_return,
        'pnl_pct': net_pnl
    })

print(f"✓ Generated {len(trades)} valid trades")

if len(trades) == 0:
    print("❌ No trades!")
    exit(1)

trades_df = pd.DataFrame(trades)

# Statistics
wins = (trades_df['pnl_pct'] > 0).sum()
losses = (trades_df['pnl_pct'] <= 0).sum()
win_rate = 100 * wins / len(trades_df)
avg_pnl = trades_df['pnl_pct'].mean()
median_pnl = trades_df['pnl_pct'].median()
max_gain = trades_df['pnl_pct'].max()
max_loss = trades_df['pnl_pct'].min()
std_dev = trades_df['pnl_pct'].std()
total_pnl = trades_df['pnl_pct'].sum()

# Print results
print(f"\n{'='*80}")
print(f"BACKTEST RESULTS: Day-Trading Pump Strategy")
print(f"Period: Dec 1, 2025 - Jan 15, 2026 (29 trading days)")
print(f"{'='*80}\n")

print(f"Total trades:              {len(trades_df)}")
print(f"Winning trades:            {wins} ({win_rate:.1f}%)")
print(f"Losing trades:             {losses} ({100-win_rate:.1f}%)\n")

print(f"Average P&L:               {avg_pnl:+.4f}%")
print(f"Median P&L:                {median_pnl:+.4f}%")
print(f"Std Deviation:             {std_dev:.4f}%\n")

print(f"Best trade:                {max_gain:+.4f}%")
print(f"Worst trade:               {max_loss:+.4f}%\n")

print(f"Total cumulative P&L:      {total_pnl:+.2f}%")
print(f"Avg P&L per $1K risk:      ${total_pnl / len(trades_df):.2f}\n")

# Verdict
print(f"{'='*80}")
if avg_pnl > 0.5:
    print(f"✅ PROFITABLE STRATEGY")
    print(f"   Expected return: {avg_pnl:+.4f}% per trade")
elif avg_pnl > 0:
    print(f"⚠️  MARGINAL (Small positive edge)")
    print(f"   Expected return: {avg_pnl:+.4f}% per trade")
else:
    print(f"❌ UNPROFITABLE")
    print(f"   Expected loss: {avg_pnl:.4f}% per trade")
print(f"{'='*80}\n")

# Save results
trades_df.to_csv('backtest_trades.csv', index=False)
print("✓ Saved backtest_trades.csv")

# Summary stats
summary = pd.DataFrame({
    'metric': ['total_trades', 'win_rate_%', 'avg_pnl_%', 'median_pnl_%', 'best_%', 'worst_%', 'std_dev_%', 'total_pnl_%'],
    'value': [len(trades_df), win_rate, avg_pnl, median_pnl, max_gain, max_loss, std_dev, total_pnl]
})
summary.to_csv('backtest_summary.csv', index=False)
print("✓ Saved backtest_summary.csv")
print("\nDone.")
