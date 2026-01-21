#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import sys

# Load data
combined_path = Path('data/histories/ringkasan_histories_combined.csv')
watchlist_path = Path('data/IHSGstockdata/alerts/manipulation_watchlist.csv')

print("Loading data...")
df = pd.read_csv(combined_path)
watchlist = pd.read_csv(watchlist_path)

df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

for col in ['Penutupan', 'Sebelumnya', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Get unique dates sorted
unique_dates = sorted(df['SourceDate'].unique())
print(f"Date range: {unique_dates[0]} to {unique_dates[-1]}")
print(f"Total trading days: {len(unique_dates)}")

trades = []

# Backtest logic
for i in range(len(unique_dates) - 1):
    current_date = unique_dates[i]
    next_date = unique_dates[i + 1]
    
    # Get flagged stocks on current date
    flagged_today = watchlist[watchlist['SourceDate'] == current_date]
    flagged_tickers = flagged_today['Kode Saham'].unique()
    
    for ticker in flagged_tickers:
        # Get entry price (close on current date)
        entry_row = df[(df['SourceDate'] == current_date) & (df['Kode Saham'] == ticker)]
        if entry_row.empty:
            continue
        
        entry_price = entry_row.iloc[0]['Penutupan']
        
        # Get exit price (close on next date)
        exit_row = df[(df['SourceDate'] == next_date) & (df['Kode Saham'] == ticker)]
        if exit_row.empty:
            continue
        
        exit_price = exit_row.iloc[0]['Penutupan']
        
        # Calculate return with 0.2% slippage
        pnl_pct = ((exit_price - entry_price) / entry_price * 100) - 0.2
        trades.append({
            'ticker': ticker,
            'entry_date': current_date,
            'exit_date': next_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_pct': pnl_pct
        })

trades_df = pd.DataFrame(trades)

if len(trades_df) == 0:
    print("ERROR: No trades generated")
    sys.exit(1)

wins = len(trades_df[trades_df['pnl_pct'] > 0])
losses = len(trades_df[trades_df['pnl_pct'] <= 0])
avg_pnl = trades_df['pnl_pct'].mean()
median_pnl = trades_df['pnl_pct'].median()
max_gain = trades_df['pnl_pct'].max()
max_loss = trades_df['pnl_pct'].min()

print(f"\n{'='*80}")
print(f"BACKTEST RESULTS: Day-Trading Pump Strategy")
print(f"{'='*80}\n")
print(f"Total trades:          {len(trades_df)}")
print(f"Wins:                  {wins}")
print(f"Losses:                {losses}")
print(f"Win rate:              {100 * wins / len(trades_df):.1f}%")
print(f"\nAvg P&L per trade:     {avg_pnl:+.3f}%")
print(f"Median P&L:            {median_pnl:+.3f}%")
print(f"Max gain:              {max_gain:+.3f}%")
print(f"Max loss:              {max_loss:+.3f}%")
print(f"Std Dev:               {trades_df['pnl_pct'].std():.3f}%")

if len(trades_df) > 0:
    avg_win = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean() if wins > 0 else 0
    avg_loss_amt = abs(trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].mean()) if losses > 0 else 0
    print(f"Avg win:               {avg_win:+.3f}%")
    print(f"Avg loss:              {avg_loss_amt:+.3f}%")

print(f"\nTotal cumulative P&L:  {trades_df['pnl_pct'].sum():+.3f}%")

print(f"\n{'='*80}")
if avg_pnl > 0.3:
    print(f"✅ STRATEGY IS PROFITABLE: +{avg_pnl:.3f}% avg per trade")
elif avg_pnl > 0:
    print(f"⚠️  MARGINAL: {avg_pnl:+.3f}% avg per trade (positive but low edge)")
else:
    print(f"❌ STRATEGY IS UNPROFITABLE: {avg_pnl:.3f}% avg per trade")
print(f"{'='*80}\n")

# Export detailed results
trades_df.to_csv('backtest_trades.csv', index=False)
print(f"Detailed trades exported to backtest_trades.csv")
