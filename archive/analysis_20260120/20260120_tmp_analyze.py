"""Simple Backtest Analysis - No Matplotlib Required"""
import pandas as pd
import numpy as np

# Load data
trades = pd.read_csv('data/backtest/backtest_trades.csv')
trades['SourceDate'] = pd.to_datetime(trades['SourceDate'])
trades['ExitDate'] = pd.to_datetime(trades['ExitDate'])

# Calculate return from NetPnL (already in percentage)
returns = trades['NetPnL'] / 100  # Convert to decimal
winners = returns[returns > 0]
losers = returns[returns <= 0]

# Calculate metrics
total_trades = len(returns)
win_rate = len(winners) / total_trades
avg_return = returns.mean()
median_return = returns.median()
std_return = returns.std()
avg_winner = winners.mean() if len(winners) > 0 else 0
avg_loser = losers.mean() if len(losers) > 0 else 0

sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
cum_returns = (1 + returns).cumprod()
total_return = cum_returns.iloc[-1] - 1
max_dd = (cum_returns / cum_returns.cummax() - 1).min()

gross_profit = winners.sum() if len(winners) > 0 else 0
gross_loss = abs(losers.sum()) if len(losers) > 0 else 0
profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

avg_rr = abs(avg_winner / avg_loser) if avg_loser != 0 else np.inf
expectancy = (win_rate * avg_winner) - ((1 - win_rate) * abs(avg_loser))

print('=' * 80)
print('BACKTEST RESULTS SUMMARY')
print('=' * 80)
print(f'Test Period: {trades["SourceDate"].min()} to {trades["SourceDate"].max()}')
print(f'Total Trades: {total_trades:,}')
print(f'Unique Stocks: {trades["Kode Saham"].nunique()}')
print()
print(f'Win Rate:            {win_rate:>10.2%}')
print(f'Average Return:      {avg_return:>10.2%}')
print(f'Median Return:       {median_return:>10.2%}')
print(f'Std Deviation:       {std_return:>10.2%}')
print()
print(f'Avg Winner:          {avg_winner:>10.2%}')
print(f'Avg Loser:           {avg_loser:>10.2%}')
print(f'Risk/Reward Ratio:   {avg_rr:>10.2f}')
print()
print(f'Total Return:        {total_return:>10.2%}')
print(f'Sharpe Ratio:        {sharpe:>10.2f}')
print(f'Max Drawdown:        {max_dd:>10.2%}')
print(f'Profit Factor:       {profit_factor:>10.2f}')
print(f'Expectancy:          {expectancy:>10.2%}')
print('=' * 80)

# Top performers
print('\nTOP 10 BEST TRADES:')
best = trades.nlargest(10, 'NetPnL')[['Kode Saham', 'SourceDate', 'NetPnL']]
print(best.to_string(index=False))

print('\nTOP 10 WORST TRADES:')
worst = trades.nsmallest(10, 'NetPnL')[['Kode Saham', 'SourceDate', 'NetPnL']]
print(worst.to_string(index=False))

# Monthly performance
trades['Month'] = trades['SourceDate'].dt.to_period('M')
monthly = trades.groupby('Month')['NetPnL'].agg(['count', 'mean']).reset_index()
monthly['Month'] = monthly['Month'].astype(str)
print('\nMONTHLY PERFORMANCE:')
print(monthly.to_string(index=False))
