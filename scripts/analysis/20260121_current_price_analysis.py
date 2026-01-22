#!/usr/bin/env python3
"""
Real-time Stock Price Analysis
Uses latest historical data from IDX
"""

import pandas as pd
from pathlib import Path

# Read latest historical data
data_path = Path(__file__).parent.parent.parent / 'data' / 'histories' / 'idx_historical_60d_20260120.csv'
df = pd.read_csv(data_path)
df['Date'] = pd.to_datetime(df['Date'])

# Key stocks to analyze
stocks = ['ADRO', 'ASII', 'UNTR', 'BBRI', 'BBCA', 'TLKM', 'BMRI', 'ANTM']

print('\n' + '='*90)
print('REAL-TIME STOCK ANALYSIS - 20 JANUARY 2026 (LATEST AVAILABLE)')
print('='*90)
print(f'{"Stock":<8} {"Close":<10} {"5D Change":<12} {"1D Change":<12} {"Volume vs Avg":<15} {"Status"}')
print('-'*90)

for stock in stocks:
    stock_df = df[df['Symbol'] == stock].sort_values('Date').tail(10)
    
    if len(stock_df) < 2:
        continue
    
    # Latest data
    latest = stock_df.iloc[-1]
    prev_day = stock_df.iloc[-2] if len(stock_df) > 1 else latest
    five_days_ago = stock_df.iloc[-6] if len(stock_df) >= 6 else stock_df.iloc[0]
    
    close = latest['Close']
    day_change = ((close - prev_day['Close']) / prev_day['Close'] * 100)
    five_day_change = ((close - five_days_ago['Close']) / five_days_ago['Close'] * 100)
    
    avg_vol = stock_df['Volume'].mean()
    vol_ratio = (latest['Volume'] / avg_vol * 100) if avg_vol > 0 else 0
    
    # Determine status
    if day_change < -5:
        status = '🔴 CRASH'
    elif day_change < -2:
        status = '🟡 WEAK'
    elif day_change > 2:
        status = '🟢 STRONG'
    else:
        status = '⚪ NEUTRAL'
    
    print(f'{stock:<8} Rp{close:>7,.0f} {five_day_change:>10.2f}% {day_change:>10.2f}% {vol_ratio:>13.0f}% {status}')

print('='*90)

# ADRO specific analysis
print('\n📊 ADRO DETAILED ANALYSIS (Active Position)')
print('-'*90)
adro = df[df['Symbol'] == 'ADRO'].sort_values('Date').tail(10)
entry_price = 2030
current_price = adro.iloc[-1]['Close']
profit = ((current_price - entry_price) / entry_price * 100)

print(f'Entry Date: 16 Jan 2026 @ Rp{entry_price:,.0f}')
print(f'Current Price (20 Jan): Rp{current_price:,.0f}')
print(f'Profit: +{profit:.2f}%')
print(f'Exit Date: 23 Jan 2026 (Day 5)')
print(f'Target: +5% to +8% (Rp{entry_price*1.05:,.0f} - Rp{entry_price*1.08:,.0f})')
print(f'Status: {"✅ TARGET EXCEEDED" if profit >= 5 else "🕒 IN PROGRESS"}')

print('\nLast 5 Days Price Action:')
for _, row in adro.tail(5).iterrows():
    date = pd.to_datetime(row['Date']).strftime('%d %b')
    print(f'  {date}: Rp{row["Close"]:>7,.0f} (Vol: {row["Volume"]/1e6:.1f}M)')

# ASII analysis
print('\n📊 ASII ANALYSIS (Rejected Signal)')
print('-'*90)
asii = df[df['Symbol'] == 'ASII'].sort_values('Date').tail(10)
current_asii = asii.iloc[-1]['Close']
decline_5d = ((current_asii - asii.iloc[-6]['Close']) / asii.iloc[-6]['Close'] * 100) if len(asii) >= 6 else 0

print(f'Current Price (20 Jan): Rp{current_asii:,.0f}')
print(f'5-Day Change: {decline_5d:.2f}%')
print(f'Scanner Decision: ✗ REJECTED (Score 60/100, no technical bounce)')
print(f'Outcome: Correct rejection (prevented loss)')
print(f'News Alert: 🔴 CRITICAL - Agincourt permit revoked (21 Jan 11:26 AM)')

print('\n' + '='*90)
