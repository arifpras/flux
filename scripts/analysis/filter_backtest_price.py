"""
Filter Backtest Results: Price > 100 IDR
==========================================
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Paths
DATA_DIR = Path('data/backtest')
RESULTS_DIR = Path('data/backtest')

print("=" * 80)
print("FILTERING BACKTEST RESULTS: Price > 100 IDR")
print("=" * 80)

# Load original backtest
trades = pd.read_csv(DATA_DIR / 'backtest_trades.csv')
trades['SourceDate'] = pd.to_datetime(trades['SourceDate'])
trades['ExitDate'] = pd.to_datetime(trades['ExitDate'])

print(f"\nOriginal backtest:")
print(f"  Total trades: {len(trades):,}")
print(f"  Date range: {trades['SourceDate'].min()} to {trades['SourceDate'].max()}")
print(f"  Unique stocks: {trades['Kode Saham'].nunique()}")

# Filter for price > 100
filtered_trades = trades[trades['EntryPrice'] > 100].copy()

print(f"\nFiltered backtest (Price > 100):")
print(f"  Total trades: {len(filtered_trades):,}")
print(f"  Unique stocks: {filtered_trades['Kode Saham'].nunique()}")
print(f"  Trades removed: {len(trades) - len(filtered_trades):,} ({(len(trades) - len(filtered_trades))/len(trades):.1%})")

# Calculate returns
returns = filtered_trades['NetPnL'] / 100  # Convert to decimal
winners = returns[returns > 0]
losers = returns[returns <= 0]

# Calculate metrics
total_trades = len(returns)
win_rate = len(winners) / total_trades if total_trades > 0 else 0
avg_return = returns.mean()
median_return = returns.median()
std_return = returns.std()
avg_winner = winners.mean() if len(winners) > 0 else 0
avg_loser = losers.mean() if len(losers) > 0 else 0

sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
cum_returns = (1 + returns).cumprod()
total_return = cum_returns.iloc[-1] - 1 if len(cum_returns) > 0 else 0
max_dd = (cum_returns / cum_returns.cummax() - 1).min() if len(cum_returns) > 0 else 0

gross_profit = winners.sum() if len(winners) > 0 else 0
gross_loss = abs(losers.sum()) if len(losers) > 0 else 0
profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

avg_rr = abs(avg_winner / avg_loser) if avg_loser != 0 else np.inf
expectancy = (win_rate * avg_winner) - ((1 - win_rate) * abs(avg_loser))

print("\n" + "=" * 80)
print("PERFORMANCE METRICS (Price > 100)")
print("=" * 80)
print(f"Total Trades:        {total_trades:>10,}")
print(f"Win Rate:            {win_rate:>10.2%}")
print(f"Average Return:      {avg_return:>10.2%}")
print(f"Median Return:       {median_return:>10.2%}")
print(f"Std Deviation:       {std_return:>10.2%}")
print()
print(f"Avg Winner:          {avg_winner:>10.2%}")
print(f"Avg Loser:           {avg_loser:>10.2%}")
print(f"Risk/Reward Ratio:   {avg_rr:>10.2f}")
print()
print(f"Total Return:        {total_return:>10.2%}")
print(f"Sharpe Ratio:        {sharpe:>10.2f}")
print(f"Max Drawdown:        {max_dd:>10.2%}")
print(f"Profit Factor:       {profit_factor:>10.2f}")
print(f"Expectancy:          {expectancy:>10.2%}")
print("=" * 80)

# Comparison with original
print("\n" + "=" * 80)
print("COMPARISON: Original vs Filtered")
print("=" * 80)

original_returns = trades['NetPnL'] / 100
original_win_rate = (original_returns > 0).sum() / len(original_returns)
original_avg_return = original_returns.mean()
original_sharpe = (original_avg_return / original_returns.std() * np.sqrt(252))

print(f"{'Metric':<25} {'Original':>15} {'Filtered (>100)':>15} {'Change':>10}")
print("-" * 80)
print(f"{'Total Trades':<25} {len(trades):>15,} {total_trades:>15,} {total_trades - len(trades):>10,}")
print(f"{'Win Rate':<25} {original_win_rate:>15.2%} {win_rate:>15.2%} {win_rate - original_win_rate:>10.2%}")
print(f"{'Avg Return':<25} {original_avg_return:>15.2%} {avg_return:>15.2%} {avg_return - original_avg_return:>10.2%}")
print(f"{'Sharpe Ratio':<25} {original_sharpe:>15.2f} {sharpe:>15.2f} {sharpe - original_sharpe:>10.2f}")
print(f"{'Profit Factor':<25} {1.50:>15.2f} {profit_factor:>15.2f} {profit_factor - 1.50:>10.2f}")

# Save filtered results
output_file = RESULTS_DIR / 'backtest_trades_filtered_price100.csv'
filtered_trades.to_csv(output_file, index=False)
print(f"\nFiltered trades saved to: {output_file}")

# Save summary
summary = pd.DataFrame([{
    'filter': 'Price > 100',
    'total_trades': total_trades,
    'unique_stocks': filtered_trades['Kode Saham'].nunique(),
    'win_rate': win_rate,
    'avg_return': avg_return,
    'median_return': median_return,
    'avg_winner': avg_winner,
    'avg_loser': avg_loser,
    'risk_reward_ratio': avg_rr,
    'sharpe_ratio': sharpe,
    'profit_factor': profit_factor,
    'max_drawdown': max_dd,
    'expectancy': expectancy
}])

summary_file = RESULTS_DIR / 'backtest_summary_filtered.csv'
summary.to_csv(summary_file, index=False)
print(f"Summary saved to: {summary_file}")

# Top/Bottom performers
print("\n" + "=" * 80)
print("TOP 10 BEST TRADES (Price > 100)")
print("=" * 80)
best = filtered_trades.nlargest(10, 'NetPnL')[['Kode Saham', 'SourceDate', 'EntryPrice', 'NetPnL']]
print(best.to_string(index=False))

print("\n" + "=" * 80)
print("TOP 10 WORST TRADES (Price > 100)")
print("=" * 80)
worst = filtered_trades.nsmallest(10, 'NetPnL')[['Kode Saham', 'SourceDate', 'EntryPrice', 'NetPnL']]
print(worst.to_string(index=False))

# Monthly performance
filtered_trades['Month'] = filtered_trades['SourceDate'].dt.to_period('M')
monthly = filtered_trades.groupby('Month')['NetPnL'].agg(['count', 'mean']).reset_index()
monthly['Month'] = monthly['Month'].astype(str)
print("\n" + "=" * 80)
print("MONTHLY PERFORMANCE (Price > 100)")
print("=" * 80)
print(monthly.to_string(index=False))

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
