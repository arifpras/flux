#!/usr/bin/env python3
"""Backtest day-trading pump strategy on historical data"""

import pandas as pd
from pathlib import Path

# Step 1: Load data
print("Loading data files...")
df = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
watchlist = pd.read_csv('data/IHSGstockdata/alerts/manipulation_watchlist.csv')
print(f"✓ Loaded {len(df)} rows from combined CSV")
print(f"✓ Loaded {len(watchlist)} flagged rows from watchlist")

# Step 2: Parse dates
df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

# Step 3: Parse numeric columns
for col in ['Penutupan', 'Sebelumnya', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"\n✓ Data parsed successfully")

# Step 4: Get trading dates
unique_dates = sorted(df['SourceDate'].unique())
print(f"✓ Trading dates: {len(unique_dates)} days from {unique_dates[0].date()} to {unique_dates[-1].date()}")

# Step 5: Backtest loop
print("\nRunning backtest...")
trades = []
trade_count = 0

for i in range(len(unique_dates) - 1):
    current_date = unique_dates[i]
    next_date = unique_dates[i + 1]
    
    # Get flagged stocks for this date
    flagged_today = watchlist[watchlist['SourceDate'] == current_date]
    
    for _, flag_row in flagged_today.iterrows():
        ticker = flag_row['Kode Saham']
        
        # Entry: close price on flagged date
        entry_candidates = df[(df['SourceDate'] == current_date) & (df['Kode Saham'] == ticker)]
        if entry_candidates.empty:
            continue
            
        entry_price = float(entry_candidates.iloc[0]['Penutupan'])
        
        # Exit: close price on next date
        exit_candidates = df[(df['SourceDate'] == next_date) & (df['Kode Saham'] == ticker)]
        if exit_candidates.empty:
            continue
            
        exit_price = float(exit_candidates.iloc[0]['Penutupan'])
        
        # Calculate P&L with slippage
        pnl_pct = ((exit_price - entry_price) / entry_price * 100) - 0.2
        
        trades.append({
            'ticker': ticker,
            'entry_date': current_date,
            'exit_date': next_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return_gross': (exit_price - entry_price) / entry_price * 100,
            'pnl_pct': pnl_pct
        })
        
        trade_count += 1

print(f"✓ Generated {trade_count} trades")

# Step 6: Analyze results
if trade_count == 0:
    print("\n❌ ERROR: No trades generated!")
    exit(1)

trades_df = pd.DataFrame(trades)

wins = len(trades_df[trades_df['pnl_pct'] > 0])
losses = len(trades_df[trades_df['pnl_pct'] <= 0])
win_rate = 100 * wins / len(trades_df)
avg_pnl = trades_df['pnl_pct'].mean()
median_pnl = trades_df['pnl_pct'].median()
max_gain = trades_df['pnl_pct'].max()
max_loss = trades_df['pnl_pct'].min()
total_cumulative = trades_df['pnl_pct'].sum()

# Step 7: Display results
print(f"\n{'='*80}")
print(f"BACKTEST RESULTS: Day-Trading Pump Strategy")
print(f"Period: {unique_dates[0].date()} to {unique_dates[-1].date()}")
print(f"{'='*80}\n")

print(f"Total trades:              {len(trades_df)}")
print(f"Winning trades:            {wins}")
print(f"Losing trades:             {losses}")
print(f"Win rate:                  {win_rate:.1f}%\n")

print(f"Average P&L per trade:     {avg_pnl:+.4f}%")
print(f"Median P&L:                {median_pnl:+.4f}%")
print(f"Best trade:                {max_gain:+.4f}%")
print(f"Worst trade:               {max_loss:+.4f}%")
print(f"Std deviation:             {trades_df['pnl_pct'].std():.4f}%\n")

if wins > 0:
    avg_win = trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean()
    print(f"Average winning trade:     {avg_win:+.4f}%")
if losses > 0:
    avg_loss = trades_df[trades_df['pnl_pct'] < 0]['pnl_pct'].mean()
    print(f"Average losing trade:      {avg_loss:+.4f}%")

print(f"\nTotal cumulative P&L:      {total_cumulative:+.2f}%")

print(f"\n{'='*80}")
if avg_pnl > 0.5:
    print(f"✅ STRATEGY IS PROFITABLE")
    print(f"   Avg P&L: +{avg_pnl:.4f}% per trade | Win Rate: {win_rate:.1f}%")
elif avg_pnl > 0:
    print(f"⚠️  MARGINAL PROFITABILITY")
    print(f"   Avg P&L: +{avg_pnl:.4f}% per trade | Win Rate: {win_rate:.1f}%")
else:
    print(f"❌ STRATEGY IS NOT PROFITABLE")
    print(f"   Avg P&L: {avg_pnl:.4f}% per trade | Win Rate: {win_rate:.1f}%")
print(f"{'='*80}\n")

# Export results
trades_df.to_csv('backtest_trades_detail.csv', index=False)
print(f"✓ Detailed trades saved to backtest_trades_detail.csv")

# Create summary
summary = {
    'total_trades': len(trades_df),
    'wins': wins,
    'losses': losses,
    'win_rate_pct': win_rate,
    'avg_pnl_pct': avg_pnl,
    'median_pnl_pct': median_pnl,
    'best_trade_pct': max_gain,
    'worst_trade_pct': max_loss,
    'std_dev_pct': trades_df['pnl_pct'].std(),
    'total_cumulative_pct': total_cumulative
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv('backtest_summary.csv', index=False)
print(f"✓ Summary stats saved to backtest_summary.csv")

print(f"\nBacktest complete.")
