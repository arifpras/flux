#!/usr/bin/env python3
"""
Find stocks with net foreign buy in the last 10 trading days
"""
import pandas as pd
from datetime import datetime, timedelta

# Read the CSV file
df = pd.read_csv('data/histories/ringkasan_histories_combined.csv')

# Convert SourceDate to datetime
df['SourceDate'] = pd.to_datetime(df['SourceDate'])

# Get unique dates and sort them
unique_dates = sorted(df['SourceDate'].unique())
print(f"Total unique dates: {len(unique_dates)}")
print(f"Latest date: {unique_dates[-1]}")
print(f"Earliest date: {unique_dates[0]}")

# Last 5 business days
last_5_days = unique_dates[-5:]
print(f"\nLast 5 dates in data:")
for date in last_5_days:
    print(f"  {date.date()}")

# Filter for last 5 days
df_last_5 = df[df['SourceDate'].isin(last_5_days)].copy()

# Calculate net foreign buy per stock
# Net Foreign Buy = Foreign Buy - Foreign Sell
df_last_5['Net Foreign Buy'] = df_last_5['Foreign Buy'] - df_last_5['Foreign Sell']

# Group by stock and sum the net foreign buy
stock_net_foreign = df_last_5.groupby('Kode Saham').agg({
    'Net Foreign Buy': 'sum',
    'Foreign Buy': 'sum',
    'Foreign Sell': 'sum',
    'Nama Perusahaan': 'first'
}).reset_index()

# Filter for stocks with positive net foreign buy
stocks_with_buy = stock_net_foreign[stock_net_foreign['Net Foreign Buy'] > 0].sort_values('Net Foreign Buy', ascending=False)

print(f"\n\nStocks with NET FOREIGN BUY in last 5 days:")
print("=" * 100)
print(f"{'Stock Code':<12} {'Company Name':<40} {'Foreign Buy':<15} {'Foreign Sell':<15} {'Net Foreign Buy':<15}")
print("=" * 100)

for idx, row in stocks_with_buy.iterrows():
    print(f"{row['Kode Saham']:<12} {str(row['Nama Perusahaan'])[:40]:<40} {int(row['Foreign Buy']):>14,} {int(row['Foreign Sell']):>14,} {int(row['Net Foreign Buy']):>14,}")

print(f"\nTotal stocks with net foreign buy: {len(stocks_with_buy)}")

# Save to CSV
stocks_with_buy.to_csv('data/histories/foreign_buy_stocks_last5days.csv', index=False)
print(f"\nResults saved to: data/histories/foreign_buy_stocks_last5days.csv")
