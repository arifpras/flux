#!/usr/bin/env python3
"""
Extract Today's IDX Closing Prices
Uses latest available historical data from bulk download
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

# Read the latest historical data we have
hist_file = Path('data/histories/idx_historical_60d_20260120.csv')
df = pd.read_csv(hist_file)
df['Date'] = pd.to_datetime(df['Date'])

# Get latest close for all stocks (Jan 20, 2026)
latest_data = df.sort_values('Date').groupby('Symbol').tail(1)[['Symbol', 'Date', 'Close', 'Open', 'High', 'Low', 'Volume']].copy()
latest_data = latest_data.reset_index(drop=True)

# Save today's closing prices
output_file = Path('data/histories') / f"idx_today_closing_{datetime.now().strftime('%Y%m%d')}.csv"
latest_data.to_csv(output_file, index=False)

print('\n' + '='*80)
print('TODAY\'S IDX CLOSING PRICES (Latest Available: 20 January 2026)')
print('='*80)
print(f'Total stocks: {len(latest_data)}')
print(f'Data date: {latest_data["Date"].max().strftime("%d %B %Y")}')
print(f'Saved to: {output_file}\n')

print(f'{"Symbol":<8} {"Close":<12} {"Open":<12} {"High":<12} {"Low":<12} {"Volume"}')
print('-'*90)
for _, row in latest_data.sort_values('Close', ascending=False).iterrows():
    print(f'{row["Symbol"]:<8} Rp{row["Close"]:>10,.0f}  Rp{row["Open"]:>10,.0f}  Rp{row["High"]:>10,.0f}  Rp{row["Low"]:>10,.0f}  {int(row["Volume"]):>12,}')

print('='*90)
