#!/usr/bin/env python3
"""
Generate stock recommendations using Elite Strategy with Watchlist Filter
Includes real-time suspension tracking
"""

from elite_strategy import EliteStrategy
import pandas as pd

print('='*80)
print('ELITE STRATEGY STOCK RECOMMENDATIONS')
print('='*80)

# Initialize with watchlist filter
strategy = EliteStrategy('backtest_trades.csv', threshold_return=1.0, enable_watchlist_filter=True)

# Show top performing stocks
print('\n📊 TOP ELITE STOCKS (Winners-Only Rotation)')
print('-'*80)
print(f'Criteria: Average return > {strategy.threshold_return}%')
print('\nTop 20 Performers:\n')

elite = strategy.elite_stocks.head(20)
print(f'{"Rank":<6}{"Stock":<10}{"Avg Return":<12}{"Trades":<10}{"Total Return":<14}{"Win Rate":<10}')
print('-'*80)

for idx, (stock, row) in enumerate(elite.iterrows(), 1):
    # Check if stock is safe
    is_safe, reasons = strategy.is_stock_safe(stock)
    status = '✓' if is_safe else '⚠'
    
    # Calculate win rate
    stock_trades = strategy.df[strategy.df['Kode Saham'] == stock]
    wins = (stock_trades['NetPnL'] > 0).sum()
    win_rate = (wins / row['Trades'] * 100) if row['Trades'] > 0 else 0
    
    print(f'{status} {idx:<4}{stock:<10}{row["AvgReturn"]:>8.2f}%  {int(row["Trades"]):>8}  {row["TotalReturn"]:>10.2f}%  {win_rate:>7.1f}%')

# Filter for safe stocks only
print('\n\n🎯 RECOMMENDED STOCKS (Safe + High Performance)')
print('-'*80)

safe_stocks = []
risky_stocks = []
suspended_stocks = []

for stock in elite.head(20).index:
    is_safe, reasons = strategy.is_stock_safe(stock)
    
    if not is_safe:
        # Check if it's a suspension issue
        if any('suspended' in reason.lower() for reason in reasons):
            suspended_stocks.append((stock, reasons))
        else:
            risky_stocks.append((stock, reasons))
    else:
        safe_stocks.append(stock)

print(f'\nTop 10 Safe Stocks for Trading:\n')
for idx, stock in enumerate(safe_stocks[:10], 1):
    row = elite.loc[stock]
    stock_trades = strategy.df[strategy.df['Kode Saham'] == stock]
    wins = (stock_trades['NetPnL'] > 0).sum()
    win_rate = (wins / row['Trades'] * 100) if row['Trades'] > 0 else 0
    
    # Calculate hold days
    stock_trades['HoldDays'] = (pd.to_datetime(stock_trades['ExitDate']) - pd.to_datetime(stock_trades['SourceDate'])).dt.days
    avg_hold = stock_trades['HoldDays'].mean()
    
    print(f'{idx:>2}. {stock:<8} │ Avg: +{row["AvgReturn"]:>5.2f}% │ WinRate: {win_rate:>5.1f}% │ Trades: {int(row["Trades"]):>3} │ Avg Hold: {avg_hold:.1f} days')

if risky_stocks:
    print(f'\n\n⚠ EXCLUDED STOCKS (Watchlist Detected):')
    print('-'*80)
    for stock, reasons in risky_stocks[:5]:
        print(f'{stock:<10} - {reasons[0][:60]}')

if suspended_stocks:
    print(f'\n\n🚫 SUSPENDED STOCKS (Cannot trade):')
    print('-'*80)
    for stock, reasons in suspended_stocks:
        print(f'{stock:<10} - {reasons[0]}')

# Trading strategy summary
print('\n\n📋 TRADING STRATEGY RULES')
print('-'*80)
print(f'Entry Criteria:')
print(f'  • Stock must be in Top 10 Safe list above')
print(f'  • Broker accumulation signal detected')
print(f'  • Momentum confirmation on day 2-3')
print(f'\nPosition Management:')
print(f'  • Position size: {strategy.strategy_rules["position_size_pct"]*100:.0f}% of capital per trade')
print(f'  • Hold period: {strategy.strategy_rules["min_hold_days"]}-{strategy.strategy_rules["max_hold_days"]} days')
print(f'  • Take profit: +{strategy.strategy_rules["take_profit"]}%')
print(f'  • Stop loss: {strategy.strategy_rules["stop_loss"]}%')
print(f'  • Max trades/day: {strategy.strategy_rules["max_trades_per_day"]}')

print('\n' + '='*80)
print('✅ Recommendations Ready - Trade the Top 10 Safe Stocks')
print('='*80)
