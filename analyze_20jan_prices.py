#!/usr/bin/env python3
"""
Analyze closing prices of declining foreign buy stocks on 20 Jan 2026
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Read the declining stocks list
declining_stocks_df = pd.read_csv('data/histories/foreign_buy_declining_stocks.csv')
declining_stocks = declining_stocks_df['Stock Code'].tolist()

# Read historical price data
hist_df = pd.read_csv('data/histories/idx_historical_60d_20260120.csv')
hist_df['Date'] = pd.to_datetime(hist_df['Date'])

# Filter for declining stocks
hist_filtered = hist_df[hist_df['Symbol'].isin(declining_stocks)].copy()

# Separate data by date
hist_filtered['DateOnly'] = hist_filtered['Date'].dt.date
latest_date = hist_filtered['DateOnly'].max()
prev_date = (pd.to_datetime(latest_date) - timedelta(days=1)).date()

print("=" * 150)
print("ANALYSIS: DECLINING FOREIGN BUY STOCKS - CLOSING PRICES ON 20 JAN 2026")
print("=" * 150)
print(f"\nLatest trading date in data: {latest_date}")
print(f"Analysis comparing to previous trading day: {prev_date}\n")

results = []

for stock_code in declining_stocks:
    stock_data = hist_filtered[hist_filtered['Symbol'] == stock_code].sort_values('Date')
    
    if len(stock_data) == 0:
        continue
    
    # Get latest data
    latest_row = stock_data.iloc[-1]
    latest_close = latest_row['Close']
    latest_date_val = latest_row['DateOnly']
    
    # Get previous trading day data if available
    prev_rows = stock_data[stock_data['DateOnly'] < latest_date_val].sort_values('Date')
    prev_close = prev_rows.iloc[-1]['Close'] if len(prev_rows) > 0 else None
    
    # Get high/low for latest date
    latest_high = latest_row['High']
    latest_low = latest_row['Low']
    latest_open = latest_row['Open']
    latest_volume = latest_row['Volume']
    
    # Calculate changes
    intraday_change = latest_close - latest_open
    intraday_change_pct = (intraday_change / latest_open * 100) if latest_open > 0 else 0
    
    daily_change = latest_close - prev_close if prev_close else None
    daily_change_pct = (daily_change / prev_close * 100) if prev_close and prev_close > 0 else None
    
    # Get from declining stocks dataframe for context
    stock_info = declining_stocks_df[declining_stocks_df['Stock Code'] == stock_code].iloc[0]
    company_name = stock_info['Company Name']
    net_foreign_buy = stock_info['Net Foreign Buy']
    five_day_change_pct = stock_info['Price Change %']
    
    results.append({
        'Stock Code': stock_code,
        'Company Name': company_name,
        'Open (20 Jan)': latest_open,
        'High (20 Jan)': latest_high,
        'Low (20 Jan)': latest_low,
        'Close (20 Jan)': latest_close,
        'Volume (20 Jan)': latest_volume,
        'Intraday Change': intraday_change,
        'Intraday Change %': intraday_change_pct,
        'Daily Change': daily_change,
        'Daily Change %': daily_change_pct,
        '5-Day Change %': five_day_change_pct,
        'Net Foreign Buy': net_foreign_buy,
        'Previous Close': prev_close
    })

results_df = pd.DataFrame(results).sort_values('Close (20 Jan)', ascending=False)

print(f"{'Stock':<8} {'Company':<35} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Intraday %':<12} {'Daily %':<10} {'5D %':<8}")
print("-" * 150)

for idx, row in results_df.iterrows():
    company_short = str(row['Company Name'])[:35]
    intraday_pct_str = f"{row['Intraday Change %']:>10.2f}%" if row['Intraday Change %'] is not None else "N/A".rjust(11)
    daily_pct_str = f"{row['Daily Change %']:>8.2f}%" if row['Daily Change %'] is not None else "N/A".rjust(9)
    
    print(f"{row['Stock Code']:<8} {company_short:<35} {row['Open (20 Jan)']:>9,.0f} {row['High (20 Jan)']:>9,.0f} {row['Low (20 Jan)']:>9,.0f} {row['Close (20 Jan)']:>9,.0f} {intraday_pct_str:<12} {daily_pct_str:<10} {row['5-Day Change %']:>7.2f}%")

print("-" * 150)

# Analysis
print("\n\n" + "=" * 150)
print("DETAILED ANALYSIS")
print("=" * 150)

positive_intraday = results_df[results_df['Intraday Change %'] > 0]
negative_intraday = results_df[results_df['Intraday Change %'] < 0]

print(f"\nIntraday Performance (20 Jan 2026):")
print(f"  ✓ Stocks gaining during the day: {len(positive_intraday)}")
print(f"  ✗ Stocks declining during the day: {len(negative_intraday)}")

if len(positive_intraday) > 0:
    print(f"\n  Top gainers today:")
    for idx, row in positive_intraday.sort_values('Intraday Change %', ascending=False).head(5).iterrows():
        print(f"    {row['Stock Code']:<8} +{row['Intraday Change %']:>6.2f}% ({int(row['Net Foreign Buy']):>12,} foreign buy)")

if len(negative_intraday) > 0:
    print(f"\n  Top losers today:")
    for idx, row in negative_intraday.sort_values('Intraday Change %').head(5).iterrows():
        print(f"    {row['Stock Code']:<8} {row['Intraday Change %']:>6.2f}% ({int(row['Net Foreign Buy']):>12,} foreign buy)")

# Volume analysis
print(f"\n\nVolume Analysis (20 Jan 2026):")
high_volume = results_df[results_df['Volume (20 Jan)'] > results_df['Volume (20 Jan)'].quantile(0.75)]
print(f"  High volume trades (75th percentile+): {len(high_volume)} stocks")
if len(high_volume) > 0:
    print(f"  Largest volume:")
    for idx, row in high_volume.sort_values('Volume (20 Jan)', ascending=False).head(5).iterrows():
        print(f"    {row['Stock Code']:<8} {int(row['Volume (20 Jan)']):>14,} shares")

# Foreign buy concentration analysis
print(f"\n\nForeign Buy Analysis (Last 10 days):")
total_foreign_buy = results_df['Net Foreign Buy'].sum()
top_5_fb = results_df.nlargest(5, 'Net Foreign Buy')
top_5_pct = (top_5_fb['Net Foreign Buy'].sum() / total_foreign_buy * 100) if total_foreign_buy > 0 else 0

print(f"  Total foreign buy: {int(total_foreign_buy):,}")
print(f"  Top 5 stocks account for: {top_5_pct:.1f}% of foreign buying")
print(f"  Top 3 foreign buy targets:")
for idx, (_, row) in enumerate(top_5_fb.head(3).iterrows(), 1):
    print(f"    {idx}. {row['Stock Code']:<8} {int(row['Net Foreign Buy']):>14,} (Closing: {row['Close (20 Jan)']:>8,.0f})")

# Reversal signals
print(f"\n\nReversal Signals (Stocks bouncing vs declining trend):")
reversing_up = results_df[(results_df['Daily Change %'] > 0) | (results_df['Intraday Change %'] > 0)]
print(f"  Stocks showing recovery signals: {len(reversing_up)}")
if len(reversing_up) > 0:
    print(f"  Potential reversals with foreign accumulation:")
    for idx, row in reversing_up.sort_values('Net Foreign Buy', ascending=False).head(5).iterrows():
        print(f"    {row['Stock Code']:<8} 5D: {row['5-Day Change %']:>6.2f}% | Today: {row['Intraday Change %']:>+6.2f}% | Foreign: {int(row['Net Foreign Buy']):>12,}")

# Save detailed results
results_df.to_csv('data/histories/declining_stocks_20jan_analysis.csv', index=False)
print(f"\n\nDetailed results saved to: data/histories/declining_stocks_20jan_analysis.csv")
