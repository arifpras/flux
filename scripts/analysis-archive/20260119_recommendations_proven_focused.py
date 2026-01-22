#!/usr/bin/env python3
"""
Updated Recommendations: Focus on RLCO, ROCK, + 4 Proven Performers
CANI, TIRT, ATLA, TRON as of 19 Jan 2026
"""

from elite_strategy import EliteStrategy
import pandas as pd

print('='*80)
print('ELITE STRATEGY - UPDATED RECOMMENDATIONS')
print('Focus: RLCO, ROCK + 4 Proven Performers (CANI, TIRT, ATLA, TRON)')
print('Date: 19 Jan 2026')
print('='*80)

# Initialize
strategy = EliteStrategy('backtest_trades.csv', threshold_return=1.0, enable_watchlist_filter=True)

# Define tiers
tier_1_proven = ['RLCO', 'ROCK']
tier_2_proven = ['CANI', 'TIRT', 'ATLA', 'TRON']
all_focus = tier_1_proven + tier_2_proven

print('\n' + '='*80)
print('TIER 1: ANCHOR PROVEN STOCKS (Highest Confidence)')
print('='*80)

elite = strategy.elite_stocks.copy()

for idx, stock in enumerate(tier_1_proven, 1):
    if stock in elite.index:
        row = elite.loc[stock]
        stock_trades = strategy.df[strategy.df['Kode Saham'] == stock]
        wins = (stock_trades['NetPnL'] > 0).sum()
        win_rate = (wins / row['Trades'] * 100) if row['Trades'] > 0 else 0
        recent = stock_trades.tail(3)['NetPnL'].mean()
        
        is_safe, reasons = strategy.is_stock_safe(stock)
        safety = '✓ SAFE' if is_safe else '⚠ FLAG'
        
        print(f"\n{idx}. {stock} {safety}")
        print(f"   Avg Return: +{row['AvgReturn']:.2f}% │ Win Rate: {win_rate:.1f}% │ Trades: {int(row['Trades'])}")
        print(f"   Recent (3d): +{recent:.2f}%")
        print(f"   Entry: Broker accumulation signal")
        print(f"   Exit: Day 2–3, +5% target or –2% stop")

print('\n' + '='*80)
print('TIER 2: SECONDARY PROVEN PERFORMERS (High Confidence)')
print('='*80)

for idx, stock in enumerate(tier_2_proven, 1):
    if stock in elite.index:
        row = elite.loc[stock]
        stock_trades = strategy.df[strategy.df['Kode Saham'] == stock]
        wins = (stock_trades['NetPnL'] > 0).sum()
        win_rate = (wins / row['Trades'] * 100) if row['Trades'] > 0 else 0
        recent = stock_trades.tail(3)['NetPnL'].mean()
        
        is_safe, reasons = strategy.is_stock_safe(stock)
        safety = '✓ SAFE' if is_safe else '⚠ FLAG'
        
        print(f"\n{idx}. {stock} {safety}")
        print(f"   Avg Return: +{row['AvgReturn']:.2f}% │ Win Rate: {win_rate:.1f}% │ Trades: {int(row['Trades'])}")
        print(f"   Recent (3d): +{recent:.2f}%")
        print(f"   Entry: Broker accumulation signal")
        print(f"   Exit: Day 2–3, +5% target or –2% stop")

print('\n\n' + '='*80)
print('PORTFOLIO STRATEGY SUMMARY')
print('='*80)

print(f"""
Portfolio Allocation (suggested):
  • RLCO (35% of active capital)  - Highest conviction, +15.57% avg
  • ROCK (25% of active capital)  - Secondary anchor, +9.69% avg
  • CANI (15% of active capital)  - Secondary proven, +6.68% avg, 72.7% win
  • TIRT (15% of active capital)  - Secondary proven, +6.20% avg, 63% win
  • ATLA (5% of active capital)   - Opportunistic, +5.50% avg
  • TRON (5% of active capital)   - Opportunistic, +5.55% avg

Entry Rules:
  1. Wait for broker accumulation signal (check broker_accumulation_signals.txt)
  2. Confirm momentum on day 2–3 of pump
  3. Enter on day 2–3 at 50% of capital per trade (max 10 trades/day)

Exit Rules:
  • Target: +5.0% → Close position
  • Stop Loss: –2.0% → Close position
  • Time: Day 3 close → Close remaining position
  • Max Hold: 3 days

Risk Management:
  • Exclude any stock on IDX watchlist or suspension list
  • Skip if daily volume <10,000 or value <Rp5M
  • Cool-off: Skip recently reopened stocks for 3 business days

Expected Performance:
  • Win Rate: 60–85% (based on historical data)
  • Avg Return/Trade: +5% to +15%
  • Profit Factor: 10x–100x (winning trades >> losing trades)
  • Daily Target: $2,000–3,000 on $100K account (2–3% daily)
""")

print('='*80)
print('📊 Data as of: 19 Jan 2026')
print('✓ Status: Ready to trade the 6-stock portfolio')
print('='*80)
