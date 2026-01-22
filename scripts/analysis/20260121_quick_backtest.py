"""
Quick Backtesting Script - Simplified Version
==============================================
Faster execution for initial validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
RESULTS_DIR = Path(__file__).parent.parent.parent / 'data' / 'backtest'
RESULTS_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("QUICK BACKTEST: Foreign Buy + Declining Stocks Strategy")
print("=" * 80)

# Load data
print("\n1. Loading data...")
foreign_data = pd.read_csv(DATA_DIR / 'histories' / 'ringkasan_histories_combined.csv')
foreign_data['SourceDate'] = pd.to_datetime(foreign_data['SourceDate'])
foreign_data['NetForeignBuy'] = foreign_data['Foreign Buy'] - foreign_data['Foreign Sell']
print(f"   Foreign data: {len(foreign_data):,} rows ({foreign_data['SourceDate'].min()} to {foreign_data['SourceDate'].max()})")

price_data = pd.read_csv(DATA_DIR / 'histories' / 'idx_historical_60d_20260120.csv')
price_data['Date'] = pd.to_datetime(price_data['Date'])
price_data = price_data.rename(columns={'Symbol': 'Ticker'})
print(f"   Price data: {len(price_data):,} rows ({price_data['Date'].min()} to {price_data['Date'].max()})")

# Parameters
LOOKBACK = 5
HOLDING = 5
DECLINE_MIN = -0.05
DECLINE_MAX = -0.005
MIN_PRICE = 100  # Filter out penny stocks

print(f"\n2. Strategy parameters:")
print(f"   Lookback period: {LOOKBACK} days")
print(f"   Holding period: {HOLDING} days")
print(f"   Decline range: {DECLINE_MIN:.1%} to {DECLINE_MAX:.1%}")
print(f"   Minimum price: Rp {MIN_PRICE}")

# Get all trading dates
all_dates = sorted(price_data['Date'].unique())
print(f"   Total trading days: {len(all_dates)}")

# Prepare data structures for faster access
print("\n3. Preparing data structures...")
foreign_by_date = {k: v for k, v in foreign_data.groupby('SourceDate')}
price_by_date = {k: v for k, v in price_data.groupby('Date')}

# Run backtest
print("\n4. Running backtest...")
trades = []
test_dates = all_dates[LOOKBACK+5:-HOLDING]  # Leave buffer for lookback and forward
print(f"   Testing on {len(test_dates)} dates")

for i, analysis_date in enumerate(test_dates):
    if (i + 1) % 5 == 0:
        print(f"   Progress: {i+1}/{len(test_dates)} ({100*(i+1)/len(test_dates):.1f}%)", end='\r')
    
    # Get lookback dates
    analysis_idx = all_dates.index(analysis_date)
    lookback_dates = all_dates[analysis_idx-LOOKBACK:analysis_idx]
    
    # Calculate foreign buy (sum over lookback period)
    foreign_sum = []
    for date in lookback_dates:
        if date in foreign_by_date:
            df = foreign_by_date[date][['Kode Saham', 'NetForeignBuy']]
            foreign_sum.append(df)
    
    if not foreign_sum:
        continue
    
    foreign_agg = pd.concat(foreign_sum).groupby('Kode Saham')['NetForeignBuy'].sum().reset_index()
    foreign_agg.columns = ['Ticker', 'NetForeignBuy']
    foreign_agg = foreign_agg[foreign_agg['NetForeignBuy'] > 0]
    
    if len(foreign_agg) == 0:
        continue
    
    # Calculate price change
    start_date = lookback_dates[0]
    end_date = lookback_dates[-1]
    
    if start_date not in price_by_date or end_date not in price_by_date:
        continue
    
    start_prices = price_by_date[start_date][['Ticker', 'Close']].copy()
    start_prices.columns = ['Ticker', 'StartPrice']
    
    end_prices = price_by_date[end_date][['Ticker', 'Close']].copy()
    end_prices.columns = ['Ticker', 'EndPrice']
    
    price_change = pd.merge(start_prices, end_prices, on='Ticker')
    price_change['PriceChange'] = (price_change['EndPrice'] - price_change['StartPrice']) / price_change['StartPrice']
    
    # Filter declining stocks with minimum price threshold
    declining = price_change[
        (price_change['PriceChange'] >= DECLINE_MIN) &
        (price_change['PriceChange'] <= DECLINE_MAX) &
        (price_change['EndPrice'] > MIN_PRICE)  # Only stocks with price > 100
    ].copy()
    
    if len(declining) == 0:
        continue
    
    # Combine signals
    signals = pd.merge(foreign_agg, declining, on='Ticker')
    
    if len(signals) == 0:
        continue
    
    # Calculate forward returns
    entry_date = analysis_date
    exit_date_idx = analysis_idx + HOLDING
    
    if exit_date_idx >= len(all_dates):
        continue
    
    exit_date = all_dates[exit_date_idx]
    
    if entry_date not in price_by_date or exit_date not in price_by_date:
        continue
    
    entry_prices = price_by_date[entry_date][['Ticker', 'Close']].copy()
    entry_prices.columns = ['Ticker', 'EntryPrice']
    
    # Additional price filter at entry
    entry_prices = entry_prices[entry_prices['EntryPrice'] > MIN_PRICE]
    
    exit_prices = price_by_date[exit_date][['Ticker', 'Close']].copy()
    exit_prices.columns = ['Ticker', 'ExitPrice']
    
    returns = pd.merge(entry_prices, exit_prices, on='Ticker')
    returns['Return'] = (returns['ExitPrice'] - returns['EntryPrice']) / returns['EntryPrice']
    
    # Combine with signals
    trade = pd.merge(signals, returns, on='Ticker')
    trade['EntryDate'] = entry_date
    trade['ExitDate'] = exit_date
    
    trades.append(trade)

print("\n")

if not trades:
    print("ERROR: No trades generated!")
    exit(1)

# Combine results
results = pd.concat(trades, ignore_index=True)
print(f"\n5. Results summary:")
print(f"   Total trades: {len(results)}")
print(f"   Unique stocks: {results['Ticker'].nunique()}")
print(f"   Unique entry dates: {results['EntryDate'].nunique()}")

# Calculate metrics
returns = results['Return']
winners = returns[returns > 0]
losers = returns[returns <= 0]

win_rate = len(winners) / len(returns)
avg_return = returns.mean()
median_return = returns.median()
avg_winner = winners.mean() if len(winners) > 0 else 0
avg_loser = losers.mean() if len(losers) > 0 else 0

cum_returns = (1 + returns).cumprod()
total_return = cum_returns.iloc[-1] - 1
max_dd = (cum_returns / cum_returns.cummax() - 1).min()

gross_profit = winners.sum() if len(winners) > 0 else 0
gross_loss = abs(losers.sum()) if len(losers) > 0 else 0
profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf

sharpe = (avg_return / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

print("\n" + "=" * 80)
print("PERFORMANCE METRICS")
print("=" * 80)
print(f"Total Trades:        {len(returns):>8,}")
print(f"Win Rate:            {win_rate:>8.2%}")
print(f"Avg Return:          {avg_return:>8.2%}")
print(f"Median Return:       {median_return:>8.2%}")
print(f"Avg Winner:          {avg_winner:>8.2%}")
print(f"Avg Loser:           {avg_loser:>8.2%}")
print(f"Total Return:        {total_return:>8.2%}")
print(f"Sharpe Ratio:        {sharpe:>8.2f}")
print(f"Max Drawdown:        {max_dd:>8.2%}")
print(f"Profit Factor:       {profit_factor:>8.2f}")
print("=" * 80)

# Save results
output_file = RESULTS_DIR / 'backtest_trades.csv'
results.to_csv(output_file, index=False)
print(f"\nTrades saved to: {output_file}")

# Save summary
summary = pd.DataFrame([{
    'lookback_days': LOOKBACK,
    'holding_days': HOLDING,
    'total_trades': len(returns),
    'win_rate': win_rate,
    'avg_return': avg_return,
    'median_return': median_return,
    'avg_winner': avg_winner,
    'avg_loser': avg_loser,
    'total_return': total_return,
    'sharpe_ratio': sharpe,
    'max_drawdown': max_dd,
    'profit_factor': profit_factor
}])

summary_file = RESULTS_DIR / 'backtest_summary.csv'
summary.to_csv(summary_file, index=False)
print(f"Summary saved to: {summary_file}")

# Top/Bottom performers
print("\n" + "=" * 80)
print("TOP 10 BEST TRADES")
print("=" * 80)
top_trades = results.nlargest(10, 'Return')[['Ticker', 'EntryDate', 'Return', 'NetForeignBuy']]
print(top_trades.to_string(index=False))

print("\n" + "=" * 80)
print("TOP 10 WORST TRADES")
print("=" * 80)
worst_trades = results.nsmallest(10, 'Return')[['Ticker', 'EntryDate', 'Return', 'NetForeignBuy']]
print(worst_trades.to_string(index=False))

print("\n" + "=" * 80)
print("BACKTEST COMPLETE")
print("=" * 80)
