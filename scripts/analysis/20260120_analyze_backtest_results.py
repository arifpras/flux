"""
Backtest Results Analysis and Visualization
============================================
Analyze the robustness of the foreign buy + declining stocks strategy
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)

# Paths
DATA_DIR = Path(__file__).parent.parent.parent / 'data' / 'backtest'
REPORT_DIR = Path(__file__).parent.parent.parent / 'REPORTS'

print("=" * 80)
print("BACKTEST RESULTS ANALYSIS")
print("=" * 80)

# Load results
print("\n1. Loading backtest results...")
trades = pd.read_csv(DATA_DIR / 'backtest_trades.csv')
trades['EntryDate'] = pd.to_datetime(trades['EntryDate'])
trades['ExitDate'] = pd.to_datetime(trades['ExitDate'])

print(f"   Total trades: {len(trades):,}")
print(f"   Date range: {trades['EntryDate'].min()} to {trades['EntryDate'].max()}")
print(f"   Unique stocks: {trades['Ticker'].nunique()}")

# Calculate returns
returns = trades['Return']

# 1. OVERALL PERFORMANCE METRICS
print("\n" + "=" * 80)
print("1. OVERALL PERFORMANCE")
print("=" * 80)

total_trades = len(returns)
winners = returns[returns > 0]
losers = returns[returns <= 0]
breakeven = returns[returns == 0]

win_rate = len(winners) / total_trades
avg_return = returns.mean()
median_return = returns.median()
std_return = returns.std()

avg_winner = winners.mean() if len(winners) > 0 else 0
avg_loser = losers.mean() if len(losers) > 0 else 0

# Risk metrics
sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
cum_returns = (1 + returns).cumprod()
total_return = cum_returns.iloc[-1] - 1
max_dd = (cum_returns / cum_returns.cummax() - 1).min()

# Profit factor
gross_profit = winners.sum() if len(winners) > 0 else 0
gross_loss = abs(losers.sum()) if len(losers) > 0 else 0
profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

# Risk-reward ratio
avg_rr = abs(avg_winner / avg_loser) if avg_loser != 0 else np.inf

# Expectancy
expectancy = (win_rate * avg_winner) - ((1 - win_rate) * abs(avg_loser))

print(f"Total Trades:        {total_trades:>10,}")
print(f"  Winners:           {len(winners):>10,} ({len(winners)/total_trades:>6.2%})")
print(f"  Losers:            {len(losers):>10,} ({len(losers)/total_trades:>6.2%})")
print(f"  Breakeven:         {len(breakeven):>10,} ({len(breakeven)/total_trades:>6.2%})")
print()
print(f"Avg Return:          {avg_return:>10.2%}")
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

# 2. DISTRIBUTION ANALYSIS
print("\n" + "=" * 80)
print("2. RETURN DISTRIBUTION")
print("=" * 80)

percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
print("\nPercentiles:")
for p in percentiles:
    val = returns.quantile(p/100)
    print(f"  {p:>2}th:  {val:>8.2%}")

print("\nReturn Buckets:")
buckets = [
    ("Loss > 10%", (returns <= -0.10).sum()),
    ("Loss 5-10%", ((returns > -0.10) & (returns <= -0.05)).sum()),
    ("Loss 0-5%", ((returns > -0.05) & (returns < 0)).sum()),
    ("Breakeven", (returns == 0).sum()),
    ("Gain 0-5%", ((returns > 0) & (returns <= 0.05)).sum()),
    ("Gain 5-10%", ((returns > 0.05) & (returns <= 0.10)).sum()),
    ("Gain > 10%", (returns > 0.10).sum()),
]
for label, count in buckets:
    pct = count / total_trades
    print(f"  {label:<15} {count:>6,} ({pct:>6.2%})")

# 3. TIME-BASED ANALYSIS
print("\n" + "=" * 80)
print("3. PERFORMANCE OVER TIME")
print("=" * 80)

# Group by month
trades['Month'] = trades['EntryDate'].dt.to_period('M')
monthly_stats = trades.groupby('Month')['Return'].agg([
    ('count', 'count'),
    ('win_rate', lambda x: (x > 0).sum() / len(x)),
    ('avg_return', 'mean'),
    ('median_return', 'median')
]).reset_index()
monthly_stats['Month'] = monthly_stats['Month'].astype(str)

print("\nMonthly Performance:")
print(monthly_stats.to_string(index=False))

# 4. STOCK-LEVEL ANALYSIS
print("\n" + "=" * 80)
print("4. STOCK-LEVEL STATISTICS")
print("=" * 80)

stock_stats = trades.groupby('Ticker').agg({
    'Return': ['count', lambda x: (x > 0).sum() / len(x), 'mean', 'median']
}).reset_index()
stock_stats.columns = ['Ticker', 'Trades', 'WinRate', 'AvgReturn', 'MedianReturn']
stock_stats = stock_stats[stock_stats['Trades'] >= 3]  # Min 3 trades
stock_stats = stock_stats.sort_values('AvgReturn', ascending=False)

print(f"\nStocks with ≥3 trades: {len(stock_stats)}")
print("\nTop 10 Best Performing Stocks:")
print(stock_stats.head(10).to_string(index=False))

print("\nTop 10 Worst Performing Stocks:")
print(stock_stats.tail(10).to_string(index=False))

# 5. EXTREME TRADES ANALYSIS
print("\n" + "=" * 80)
print("5. EXTREME TRADES")
print("=" * 80)

print("\nTop 10 Best Trades:")
best = trades.nlargest(10, 'Return')[['Ticker', 'EntryDate', 'ExitDate', 'Return', 'NetForeignBuy', 'PriceChange']]
print(best.to_string(index=False))

print("\nTop 10 Worst Trades:")
worst = trades.nsmallest(10, 'Return')[['Ticker', 'EntryDate', 'ExitDate', 'Return', 'NetForeignBuy', 'PriceChange']]
print(worst.to_string(index=False))

# 6. CORRELATION ANALYSIS
print("\n" + "=" * 80)
print("6. SIGNAL STRENGTH ANALYSIS")
print("=" * 80)

# Correlation between signals and returns
correlations = {
    'NetForeignBuy': trades[['NetForeignBuy', 'Return']].corr().iloc[0, 1],
    'PriceChange': trades[['PriceChange', 'Return']].corr().iloc[0, 1],
}

print("\nCorrelation with Forward Returns:")
for signal, corr in correlations.items():
    print(f"  {signal:<20} {corr:>8.4f}")

# Quintile analysis
print("\nQuintile Analysis (by Foreign Buy Size):")
trades['ForeignBuyQuintile'] = pd.qcut(trades['NetForeignBuy'], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
quintile_stats = trades.groupby('ForeignBuyQuintile')['Return'].agg([
    ('count', 'count'),
    ('win_rate', lambda x: (x > 0).sum() / len(x)),
    ('avg_return', 'mean')
])
print(quintile_stats.to_string())

# 7. ROBUSTNESS CHECKS
print("\n" + "=" * 80)
print("7. ROBUSTNESS CHECKS")
print("=" * 80)

# Split by time period
mid_point = trades['EntryDate'].quantile(0.5)
first_half = trades[trades['EntryDate'] <= mid_point]['Return']
second_half = trades[trades['EntryDate'] > mid_point]['Return']

print("\nFirst Half vs Second Half:")
print(f"  First Half:  Trades={len(first_half):,}, WinRate={((first_half > 0).sum() / len(first_half)):.2%}, AvgReturn={first_half.mean():.2%}")
print(f"  Second Half: Trades={len(second_half):,}, WinRate={((second_half > 0).sum() / len(second_half)):.2%}, AvgReturn={second_half.mean():.2%}")

# Consistency check
print("\nConsistency Check (% of positive months):")
monthly_positive = (monthly_stats['avg_return'] > 0).sum()
consistency = monthly_positive / len(monthly_stats)
print(f"  Positive months: {monthly_positive}/{len(monthly_stats)} ({consistency:.1%})")

# 8. SAVE SUMMARY REPORT
print("\n" + "=" * 80)
print("8. SAVING DETAILED REPORT")
print("=" * 80)

report_file = REPORT_DIR / 'BACKTEST_ANALYSIS_REPORT.txt'
with open(report_file, 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("BACKTEST ANALYSIS REPORT\n")
    f.write("Foreign Buy + Declining Stocks Strategy\n")
    f.write("=" * 80 + "\n\n")
    
    f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Test Period: {trades['EntryDate'].min()} to {trades['EntryDate'].max()}\n")
    f.write(f"Total Trades: {len(trades):,}\n")
    f.write(f"Unique Stocks: {trades['Ticker'].nunique()}\n\n")
    
    f.write("PERFORMANCE METRICS\n")
    f.write("-" * 80 + "\n")
    f.write(f"Win Rate:            {win_rate:.2%}\n")
    f.write(f"Average Return:      {avg_return:.2%}\n")
    f.write(f"Median Return:       {median_return:.2%}\n")
    f.write(f"Avg Winner:          {avg_winner:.2%}\n")
    f.write(f"Avg Loser:           {avg_loser:.2%}\n")
    f.write(f"Risk/Reward:         {avg_rr:.2f}\n")
    f.write(f"Total Return:        {total_return:.2%}\n")
    f.write(f"Sharpe Ratio:        {sharpe:.2f}\n")
    f.write(f"Max Drawdown:        {max_dd:.2%}\n")
    f.write(f"Profit Factor:       {profit_factor:.2f}\n")
    f.write(f"Expectancy:          {expectancy:.2%}\n\n")
    
    f.write("ROBUSTNESS ASSESSMENT\n")
    f.write("-" * 80 + "\n")
    f.write(f"Consistency (% positive months): {consistency:.1%}\n")
    f.write(f"First Half Avg Return:           {first_half.mean():.2%}\n")
    f.write(f"Second Half Avg Return:          {second_half.mean():.2%}\n\n")
    
    f.write("CONCLUSION\n")
    f.write("-" * 80 + "\n")
    
    if win_rate > 0.5 and avg_return > 0.01 and sharpe > 1.0:
        f.write("✓ ROBUST STRATEGY\n")
        f.write("The strategy shows consistent positive expectancy with acceptable risk-adjusted returns.\n")
    elif win_rate > 0.4 and avg_return > 0:
        f.write("⚠ MARGINALLY PROFITABLE\n")
        f.write("The strategy has positive expectancy but moderate win rate. Consider refinements.\n")
    else:
        f.write("✗ WEAK STRATEGY\n")
        f.write("The strategy shows weak performance. Significant improvements needed.\n")

print(f"\nReport saved to: {report_file}")

# 9. CREATE VISUALIZATIONS
print("\n" + "=" * 80)
print("9. CREATING VISUALIZATIONS")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. Return distribution
ax1 = axes[0, 0]
returns.hist(bins=50, ax=ax1, edgecolor='black')
ax1.axvline(0, color='red', linestyle='--', linewidth=2)
ax1.axvline(avg_return, color='green', linestyle='--', linewidth=2, label=f'Mean: {avg_return:.2%}')
ax1.set_xlabel('Return (%)')
ax1.set_ylabel('Frequency')
ax1.set_title('Return Distribution')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. Cumulative returns
ax2 = axes[0, 1]
cum_returns_pct = (cum_returns - 1) * 100
ax2.plot(cum_returns_pct.values, linewidth=2)
ax2.fill_between(range(len(cum_returns_pct)), 0, cum_returns_pct.values, alpha=0.3)
ax2.set_xlabel('Trade Number')
ax2.set_ylabel('Cumulative Return (%)')
ax2.set_title(f'Cumulative Returns (Total: {total_return:.1%})')
ax2.grid(True, alpha=0.3)

# 3. Win rate over time
ax3 = axes[1, 0]
rolling_win_rate = pd.Series([(returns[:i+1] > 0).mean() for i in range(len(returns))])
ax3.plot(rolling_win_rate.values, linewidth=2)
ax3.axhline(0.5, color='red', linestyle='--', linewidth=1)
ax3.axhline(win_rate, color='green', linestyle='--', linewidth=2, label=f'Overall: {win_rate:.1%}')
ax3.set_xlabel('Trade Number')
ax3.set_ylabel('Win Rate')
ax3.set_title('Rolling Win Rate')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. Monthly performance
ax4 = axes[1, 1]
monthly_stats['avg_return_pct'] = monthly_stats['avg_return'] * 100
colors = ['green' if x > 0 else 'red' for x in monthly_stats['avg_return_pct']]
ax4.bar(range(len(monthly_stats)), monthly_stats['avg_return_pct'], color=colors, edgecolor='black')
ax4.set_xticks(range(len(monthly_stats)))
ax4.set_xticklabels(monthly_stats['Month'], rotation=45, ha='right')
ax4.set_xlabel('Month')
ax4.set_ylabel('Avg Return (%)')
ax4.set_title('Monthly Average Returns')
ax4.axhline(0, color='black', linewidth=1)
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
chart_file = REPORT_DIR / 'backtest_analysis_charts.png'
plt.savefig(chart_file, dpi=150, bbox_inches='tight')
print(f"\nCharts saved to: {chart_file}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print(f"\nResults saved to:")
print(f"  - {report_file}")
print(f"  - {chart_file}")
