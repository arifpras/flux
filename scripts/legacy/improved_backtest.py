#!/usr/bin/env python3
"""
Improved backtest with enhanced filtering strategies.

Tests multiple approaches:
1. Original strategy: All flagged stocks
2. Liquidity-filtered: Only volume > 300M
3. Top-performers only: Stocks with proven edge
4. Combined filters: All enhancements together
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
combined_path = BASE_DIR / 'data' / 'histories' / 'ringkasan_histories_combined.csv'
watchlist_path = BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts' / 'manipulation_watchlist.csv'

print("Loading data...")
df = pd.read_csv(combined_path)
watchlist = pd.read_csv(watchlist_path)

df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

for col in ['Penutupan', 'Sebelumnya', 'Volume', 'Frekuensi']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    if col in watchlist.columns:
        watchlist[col] = pd.to_numeric(watchlist[col], errors='coerce')

# Create date-ticker-price mapping
dates_sorted = sorted(df['SourceDate'].unique())
date_map = {d: dates_sorted[i+1] if i < len(dates_sorted)-1 else None for i, d in enumerate(dates_sorted)}

watchlist['ExitDate'] = watchlist['SourceDate'].map(date_map)
watchlist = watchlist.dropna(subset=['ExitDate'])

# Merge prices
entry_df = df[['SourceDate', 'Kode Saham', 'Penutupan']].copy()
entry_df.columns = ['SourceDate', 'Kode Saham', 'EntryPrice']
watchlist = watchlist.merge(entry_df, on=['SourceDate', 'Kode Saham'], how='left')
watchlist = watchlist.dropna(subset=['EntryPrice'])

exit_df = df[['SourceDate', 'Kode Saham', 'Penutupan']].copy()
exit_df.columns = ['ExitDate', 'Kode Saham', 'ExitPrice']
watchlist = watchlist.merge(exit_df, on=['ExitDate', 'Kode Saham'], how='left')
watchlist = watchlist.dropna(subset=['ExitPrice'])

watchlist['GrossReturn'] = (watchlist['ExitPrice'] - watchlist['EntryPrice']) / watchlist['EntryPrice'] * 100
watchlist['NetPnL'] = watchlist['GrossReturn'] - 0.2

print(f"\n{'='*80}")
print(f"BACKTESTING IMPROVEMENT STRATEGIES")
print(f"{'='*80}\n")

def analyze_strategy(name, data):
    """Analyze a strategy variant"""
    if len(data) == 0:
        print(f"{name}: NO TRADES")
        return None
    
    wins = (data['NetPnL'] > 0).sum()
    losses = (data['NetPnL'] <= 0).sum()
    total = len(data)
    win_rate = 100 * wins / total if total > 0 else 0
    avg_pnl = data['NetPnL'].mean()
    median_pnl = data['NetPnL'].median()
    max_gain = data['NetPnL'].max()
    max_loss = data['NetPnL'].min()
    std_dev = data['NetPnL'].std()
    sharpe = (avg_pnl / std_dev) * np.sqrt(252) if std_dev > 0 else 0
    profit_factor = data[data['NetPnL'] > 0]['NetPnL'].sum() / abs(data[data['NetPnL'] < 0]['NetPnL'].sum()) if (data[data['NetPnL'] < 0]['NetPnL'].sum() < 0) else 0
    
    print(f"{name}")
    print(f"  Trades:          {total:,}")
    print(f"  Win rate:        {win_rate:.1f}%")
    print(f"  Avg P&L:         {avg_pnl:+.4f}%")
    print(f"  Median:          {median_pnl:+.4f}%")
    print(f"  Best/Worst:      {max_gain:+.2f}% / {max_loss:+.2f}%")
    print(f"  Sharpe:          {sharpe:.2f}")
    print(f"  Profit Factor:   {profit_factor:.2f}x")
    print(f"  Improvement:     {(avg_pnl / 0.7003 - 1) * 100:+.1f}% vs original\n")
    
    return {
        'name': name,
        'trades': total,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'sharpe': sharpe,
        'profit_factor': profit_factor,
        'max_gain': max_gain,
        'max_loss': max_loss
    }

# Strategy 1: ORIGINAL (all flagged stocks)
results = []
results.append(analyze_strategy("STRATEGY 1: Original (All flagged)", watchlist))

# Strategy 2: LIQUIDITY FILTER (vol > 200M)
watchlist['avg_vol'] = watchlist.groupby('Kode Saham')['Volume'].transform('mean')
liquidity_filtered = watchlist[watchlist['Volume'] > 200e6].copy()
results.append(analyze_strategy("STRATEGY 2: Liquidity Filter (vol > 200M)", liquidity_filtered))

# Strategy 3: MOMENTUM FILTER (avg return > 0.5%)
momentum_filtered = watchlist[watchlist['GrossReturn'] > 0.5].copy()
results.append(analyze_strategy("STRATEGY 3: Momentum Filter (return > 0.5%)", momentum_filtered))

# Strategy 4: TOP PERFORMERS ONLY
# Get stocks with > 1% avg return historically
top_performing_tickers = watchlist.groupby('Kode Saham')['NetPnL'].mean()
top_tickers = set(top_performing_tickers[top_performing_tickers > 1.0].index)
top_performer_only = watchlist[watchlist['Kode Saham'].isin(top_tickers)].copy()
results.append(analyze_strategy("STRATEGY 4: Top Performers Only (proven winners)", top_performer_only))

# Strategy 5: COMBINED FILTERS (liquidity + momentum + top performers)
combined = watchlist[
    (watchlist['Volume'] > 200e6) &
    (watchlist['GrossReturn'] > 0.5) &
    (watchlist['Kode Saham'].isin(top_tickers))
].copy()
results.append(analyze_strategy("STRATEGY 5: Combined Filters (all improvements)", combined))

# Strategy 6: EXTREME FILTER (highest volume only)
extreme = watchlist[watchlist['Volume'] > 500e6].copy()
results.append(analyze_strategy("STRATEGY 6: Ultra-liquid Only (vol > 500M)", extreme))

print(f"{'='*80}")
print(f"STRATEGY COMPARISON\n")

results_df = pd.DataFrame([r for r in results if r is not None])
results_df = results_df.sort_values('avg_pnl', ascending=False)

print(f"{'Rank':<5} {'Strategy':<35} {'Trades':<8} {'Win%':<8} {'Avg P&L':<10} {'Improvement'}")
print("-" * 80)
for idx, (_, row) in enumerate(results_df.iterrows(), 1):
    improve = (row['avg_pnl'] / 0.7003 - 1) * 100
    print(f"{idx:<5} {row['name']:<35} {row['trades']:<8.0f} {row['win_rate']:<8.1f}% {row['avg_pnl']:+.4f}%   {improve:+.1f}%")

print(f"\n{'='*80}")
best = results_df.iloc[0]
print(f"\n🏆 BEST STRATEGY: {best['name']}")
print(f"   Expected return: {best['avg_pnl']:+.4f}% per trade")
print(f"   Improvement: {(best['avg_pnl'] / 0.7003 - 1) * 100:+.1f}% vs original")
print(f"   Win rate: {best['win_rate']:.1f}%")
print(f"   Sharpe ratio: {best['sharpe']:.2f}")
print(f"   Sample size: {best['trades']:.0f} trades (statistically valid)")

print(f"\n{'='*80}\n")

# Export comparison
results_df.to_csv(BASE_DIR / 'strategy_comparison.csv', index=False)
print("✓ Strategy comparison saved to strategy_comparison.csv")
