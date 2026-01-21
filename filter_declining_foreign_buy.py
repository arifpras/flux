#!/usr/bin/env python3
"""
Filter foreign buy stocks with declining price trends
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read the foreign buy stocks
foreign_buy_stocks = pd.read_csv('data/histories/foreign_buy_stocks_last5days.csv')
foreign_buy_codes = set(foreign_buy_stocks['Kode Saham'].tolist())

# Read the historical price data
hist_df = pd.read_csv('data/histories/idx_historical_60d_20260120.csv')

# Convert Date to datetime
hist_df['Date'] = pd.to_datetime(hist_df['Date'])

# Filter for our foreign buy stocks
hist_filtered = hist_df[hist_df['Symbol'].isin(foreign_buy_codes)].copy()

# Get the latest 10 trading days for each stock
results = []

for stock_code in foreign_buy_codes:
    stock_data = hist_filtered[hist_filtered['Symbol'] == stock_code].sort_values('Date')
    
    if len(stock_data) < 2:
        continue
    
    # Get last 5 days or all available data
    last_5 = stock_data.tail(5)
    
    if len(last_5) < 2:
        continue
    
    # Calculate price trend
    first_close = last_5.iloc[0]['Close']
    last_close = last_5.iloc[-1]['Close']
    
    # Calculate percentage change
    price_change = ((last_close - first_close) / first_close) * 100
    
    # Get company name from foreign buy data
    company_name = foreign_buy_stocks[foreign_buy_stocks['Kode Saham'] == stock_code]['Nama Perusahaan'].values
    company_name = company_name[0] if len(company_name) > 0 else 'N/A'
    
    # Get net foreign buy
    net_foreign_buy = foreign_buy_stocks[foreign_buy_stocks['Kode Saham'] == stock_code]['Net Foreign Buy'].values
    net_foreign_buy = net_foreign_buy[0] if len(net_foreign_buy) > 0 else 0
    
    results.append({
        'Stock Code': stock_code,
        'Company Name': company_name,
        'First Close (5d ago)': first_close,
        'Last Close': last_close,
        'Price Change %': price_change,
        'Net Foreign Buy': net_foreign_buy,
        'Data Points': len(last_5)
    })

# Convert to dataframe
results_df = pd.DataFrame(results)

# Filter for declining prices (negative price change)
declining_stocks = results_df[results_df['Price Change %'] < 0].sort_values('Price Change %')

print("=" * 130)
print("FOREIGN BUY STOCKS WITH DECLINING PRICE TRENDS")
print("=" * 130)
print(f"\nTotal stocks analyzed: {len(results_df)}")
print(f"Stocks with DECLINING prices: {len(declining_stocks)}")
print(f"\nLast 5 trading days period\n")

print(f"{'Stock':<10} {'Company Name':<45} {'First Close':<12} {'Last Close':<12} {'Change %':<10} {'Net FB':<15}")
print("-" * 130)

for idx, row in declining_stocks.iterrows():
    print(f"{row['Stock Code']:<10} {str(row['Company Name'])[:45]:<45} {row['First Close (5d ago)']:>11,.0f} {row['Last Close']:>11,.0f} {row['Price Change %']:>9.2f}% {int(row['Net Foreign Buy']):>14,}")

print("-" * 130)
print(f"\nTotal declining stocks: {len(declining_stocks)}")

# Save results
declining_stocks.to_csv('data/histories/foreign_buy_declining_stocks.csv', index=False)
print(f"\nResults saved to: data/histories/foreign_buy_declining_stocks.csv")

# Show top 20 most declining
print(f"\n\nTOP 20 MOST DECLINING STOCKS WITH FOREIGN BUY")
print("=" * 130)
for idx, row in declining_stocks.head(20).iterrows():
    print(f"{row['Stock Code']:<10} {str(row['Company Name'])[:45]:<45} {row['First Close (5d ago)']:>11,.0f} {row['Last Close']:>11,.0f} {row['Price Change %']:>9.2f}% {int(row['Net Foreign Buy']):>14,}")
