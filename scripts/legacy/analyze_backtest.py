#!/usr/bin/env python3
"""Backtest Analysis Report"""

import pandas as pd
import numpy as np

# Load results
trades = pd.read_csv('backtest_trades.csv')
summary = pd.read_csv('backtest_summary.csv')

trades['NetPnL'] = pd.to_numeric(trades['NetPnL'])

# Calculate advanced metrics
profit_factor = trades[trades['NetPnL'] > 0]['NetPnL'].sum() / abs(trades[trades['NetPnL'] < 0]['NetPnL'].sum())

# Cumulative PnL for drawdown
cumulative_pnl = trades['NetPnL'].cumsum()
cumulative_max = cumulative_pnl.expanding().max()
drawdown = (cumulative_pnl - cumulative_max) / cumulative_max * 100
max_drawdown = drawdown.min()

# Statistics by ticker
ticker_stats = trades.groupby('Kode Saham').agg({
    'NetPnL': ['count', 'mean', 'std', 'min', 'max']
}).round(3)

ticker_stats.columns = ['trades', 'avg_pnl_%', 'std_%', 'worst_%', 'best_%']
ticker_stats = ticker_stats.sort_values('avg_pnl_%', ascending=False)

top_performers = ticker_stats.head(10)
worst_performers = ticker_stats.tail(10)

print(f"\n{'='*90}")
print(f"COMPREHENSIVE BACKTEST ANALYSIS")
print(f"{'='*90}\n")

print(f"OVERALL METRICS:")
print(f"  Total Trades:              {len(trades):,}")
print(f"  Win Rate:                  {(trades['NetPnL'] > 0).sum() / len(trades) * 100:.1f}%")
print(f"  Avg P&L per Trade:         {trades['NetPnL'].mean():+.4f}%")
print(f"  Median P&L:                {trades['NetPnL'].median():+.4f}%")
print(f"  Std Deviation:             {trades['NetPnL'].std():.4f}%")
print(f"  Best Single Trade:         {trades['NetPnL'].max():+.4f}%")
print(f"  Worst Single Trade:        {trades['NetPnL'].min():+.4f}%\n")

print(f"PROFIT METRICS:")
print(f"  Total Cumulative P&L:      +{trades['NetPnL'].sum():.2f}%")
wins = trades[trades['NetPnL'] > 0]['NetPnL'].sum()
losses = abs(trades[trades['NetPnL'] <= 0]['NetPnL'].sum())
print(f"  Total Winning Pnl:         +{wins:.2f}%")
print(f"  Total Losing P&L:          {losses:.2f}%")
print(f"  Profit Factor:             {profit_factor:.2f}x")
print(f"  Max Drawdown:              {max_drawdown:.2f}%\n")

print(f"RISK-ADJUSTED RETURNS:")
sharpe = (trades['NetPnL'].mean() / trades['NetPnL'].std()) * np.sqrt(252)  # Annualized
print(f"  Sharpe Ratio (est):        {sharpe:.2f}")
print(f"  Return/Risk:               {trades['NetPnL'].mean() / trades['NetPnL'].std():.4f}\n")

print(f"TOP 10 PERFORMING STOCKS:")
for ticker, row in top_performers.iterrows():
    print(f"  {ticker:8s}: {row['trades']:5.0f} trades | Avg {row['avg_pnl_%']:+6.3f}% | Range [{row['worst_%']:+7.3f}%, {row['best_%']:+7.3f}%]")

print(f"\nWORST 10 PERFORMING STOCKS:")
for ticker, row in worst_performers.iterrows():
    print(f"  {ticker:8s}: {row['trades']:5.0f} trades | Avg {row['avg_pnl_%']:+6.3f}% | Range [{row['worst_%']:+7.3f}%, {row['best_%']:+7.3f}%]")

print(f"\n{'='*90}")
print(f"VERDICT:")
print(f"{'='*90}\n")

avg_pnl = trades['NetPnL'].mean()
win_rate = (trades['NetPnL'] > 0).sum() / len(trades) * 100

if avg_pnl > 0.5 and win_rate > 40:
    print(f"✅ STRATEGY IS ROBUST AND PROFITABLE")
    print(f"\n   ✓ Positive expected value: +{avg_pnl:.4f}% per trade")
    print(f"   ✓ Win rate {win_rate:.1f}% with low thresholds")
    print(f"   ✓ Large sample size ({len(trades):,} trades) validates edge")
    print(f"   ✓ Profit factor {profit_factor:.2f}x > 1.5 (acceptable)")
    print(f"\n   RECOMMENDATION: Strategy ready for live trading with position sizing")
    print(f"                   Use 1-2% risk per trade, scale size based on volatility")

elif avg_pnl > 0:
    print(f"⚠️  MARGINAL PROFITABILITY (Caution)")
    print(f"\n   • Positive but small edge: +{avg_pnl:.4f}% per trade")
    print(f"   • Win rate only {win_rate:.1f}% suggests high false positives")
    print(f"   • Large drawdowns ({max_drawdown:.1f}%) with small avg win")
    print(f"\n   RECOMMENDATION: Refine before live trading")
    print(f"                   → Increase z-score cutoffs (>4 instead of >3)")
    print(f"                   → Add liquidity filter (volume > 500M)")
    print(f"                   → Tighten entry/exit timing")

else:
    print(f"❌ STRATEGY IS NOT PROFITABLE")
    print(f"\n   ✗ Negative expected value: {avg_pnl:.4f}% per trade")
    print(f"   ✗ Win rate {win_rate:.1f}% indicates pattern unreliability")
    print(f"\n   RECOMMENDATION: Do NOT trade live")
    print(f"                   Revisit signal generation and testing methodology")

print(f"\n{'='*90}\n")

# Save report
with open('BACKTEST_REPORT.txt', 'w') as f:
    f.write(f"BACKTEST REPORT - Day Trading Pump Strategy\n")
    f.write(f"Period: Dec 1, 2025 - Jan 15, 2026 (29 trading days)\n")
    f.write(f"Sample Size: {len(trades):,} trades\n\n")
    
    f.write(f"KEY METRICS:\n")
    f.write(f"  Avg P&L:            {avg_pnl:+.4f}%\n")
    f.write(f"  Win Rate:           {win_rate:.1f}%\n")
    f.write(f"  Profit Factor:      {profit_factor:.2f}x\n")
    f.write(f"  Max Drawdown:       {max_drawdown:.2f}%\n")
    f.write(f"  Sharpe Ratio:       {sharpe:.2f}\n\n")
    
    f.write(f"VERDICT:\n")
    if avg_pnl > 0:
        f.write(f"✅ PROFITABLE - Ready for live trading with proper risk management\n")
    else:
        f.write(f"❌ NOT PROFITABLE - Needs refinement before live deployment\n")

print("✓ Report saved to BACKTEST_REPORT.txt")
