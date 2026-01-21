import pandas as pd
from pathlib import Path

combined_path = Path('data/histories/ringkasan_histories_combined.csv')
watchlist_path = Path('data/IHSGstockdata/alerts/manipulation_watchlist.csv')

df = pd.read_csv(combined_path)
watchlist = pd.read_csv(watchlist_path)

df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

for col in ['Penutupan', 'Sebelumnya', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

trades = []
unique_dates = sorted(df['SourceDate'].unique())

for date_idx in range(len(unique_dates) - 1):
    current_date = unique_dates[date_idx]
    next_date = unique_dates[date_idx + 1] if date_idx + 1 < len(unique_dates) else None
    
    if next_date is None:
        break
    
    today_flagged = watchlist[watchlist['SourceDate'] == current_date]
    
    for ticker in today_flagged['Kode Saham'].unique():
        entry_cand = df[(df['SourceDate'] == current_date) & (df['Kode Saham'] == ticker)]
        exit_cand = df[(df['SourceDate'] == next_date) & (df['Kode Saham'] == ticker)]
        
        if len(entry_cand) == 0 or len(exit_cand) == 0:
            continue
        
        entry_price = entry_cand.iloc[0]['Penutupan']
        exit_price = exit_cand.iloc[0]['Penutupan']
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100 - 0.2
        trades.append(pnl_pct)

trades_df = pd.DataFrame(trades, columns=['pnl_pct'])
wins = len(trades_df[trades_df['pnl_pct'] > 0])

print(f"\n{'='*100}")
print(f"BACKTEST RESULTS: Day-Trading Pump Strategy (Dec 1 - Jan 15)")
print(f"{'='*100}\n")
print(f"Total trades:         {len(trades)}")
print(f"Win rate:             {wins}/{len(trades)} ({100*wins/len(trades):.1f}%)")
print(f"Avg P&L per trade:    {trades_df['pnl_pct'].mean():+.2f}%")
print(f"Median P&L:           {trades_df['pnl_pct'].median():+.2f}%")
print(f"Max gain:             {trades_df['pnl_pct'].max():+.2f}%")
print(f"Max loss:             {trades_df['pnl_pct'].min():+.2f}%")
print(f"Std Dev:              {trades_df['pnl_pct'].std():.2f}%")
print(f"Total P&L if 1 trade: {trades_df['pnl_pct'].sum():+.2f}%")
print(f"Cumulative P&L:       {trades_df['pnl_pct'].cumsum().iloc[-1]:+.2f}%")

print(f"\nWins:  {trades_df[trades_df['pnl_pct'] > 0]['pnl_pct'].mean():+.2f}% avg")
print(f"Losses:{trades_df[trades_df['pnl_pct'] <= 0]['pnl_pct'].mean():+.2f}% avg")

if trades_df['pnl_pct'].mean() > 0:
    print(f"\n✅ STRATEGY IS PROFITABLE: +{trades_df['pnl_pct'].mean():.2f}% avg per trade")
else:
    print(f"\n❌ STRATEGY IS UNPROFITABLE: {trades_df['pnl_pct'].mean():.2f}% avg per trade")

print(f"{'='*100}\n")
