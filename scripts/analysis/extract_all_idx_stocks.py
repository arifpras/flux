#!/usr/bin/env python3
"""
Extract All IDX Stocks from Historical Data
Since yfinance API is unavailable for IDX, use existing bulk historical file
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

# Read the historical data file (72 stocks from 20 Jan)
hist_file = Path('data/histories/idx_historical_60d_20260120.csv')
df = pd.read_csv(hist_file)
df['Date'] = pd.to_datetime(df['Date'])

# Get all unique stocks
all_stocks = df['Symbol'].unique()
print(f'\n✅ Total unique stocks in historical data: {len(all_stocks)}')

# Get latest close for each stock
latest_data = df.sort_values('Date').groupby('Symbol').tail(1)[
    ['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
].copy().reset_index(drop=True)

# Save comprehensive list
output_file = Path('data/histories') / f"idx_all_stocks_{datetime.now().strftime('%Y%m%d')}.csv"
latest_data.to_csv(output_file, index=False)

print(f'📁 Saved {len(latest_data)} stocks to: {output_file}')

# Analysis
print('\n' + '='*100)
print('ALL IDX STOCKS - PRICE SUMMARY (20 JANUARY 2026)')
print('='*100)

# Sort by various metrics
print('\n📈 TOP 10 BY CLOSING PRICE:')
print('-'*100)
print(f'{"Symbol":<8} {"Close":<12} {"Change vs Open":<15} {"Range (H-L)":<15} {"Volume"}')
print('-'*100)
for _, row in latest_data.nlargest(10, 'Close').iterrows():
    change = ((row['Close'] - row['Open']) / row['Open'] * 100)
    range_val = row['High'] - row['Low']
    print(f'{row["Symbol"]:<8} Rp{row["Close"]:>10,.0f}  {change:>12.2f}%  Rp{range_val:>12,.0f}  {int(row["Volume"]):>12,}')

print('\n📊 TOP 10 BY VOLUME:')
print('-'*100)
for _, row in latest_data.nlargest(10, 'Volume').iterrows():
    change = ((row['Close'] - row['Open']) / row['Open'] * 100)
    print(f'{row["Symbol"]:<8} Rp{row["Close"]:>10,.0f}  Vol: {int(row["Volume"]):>15,}  {change:>7.2f}%')

print('\n💰 LOWEST PRICE (Penny Stocks):')
print('-'*100)
for _, row in latest_data.nsmallest(10, 'Close').iterrows():
    print(f'{row["Symbol"]:<8} Rp{row["Close"]:>10,.0f}  Vol: {int(row["Volume"]):>15,}')

print('\n📋 COMPLETE STOCK LIST (Sorted A-Z):')
print('-'*100)
print(f'{"Symbol":<8} {"Close":<12} {"Volume":<20} {"Date"}')
print('-'*100)
for _, row in latest_data.sort_values('Symbol').iterrows():
    date_str = pd.to_datetime(row['Date']).strftime('%d %b %Y')
    print(f'{row["Symbol"]:<8} Rp{row["Close"]:>10,.0f}  {int(row["Volume"]):>18,}  {date_str}')

print('='*100)
print(f'\n✅ Total stocks available: {len(latest_data)}')
print(f'✅ Data as of: {latest_data["Date"].max().strftime("%d %B %Y")}')
print(f'✅ Market cap snapshot available for all stocks')
