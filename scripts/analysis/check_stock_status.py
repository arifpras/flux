#!/usr/bin/env python3
"""
Check trading status of stocks - identify suspended or illiquid stocks
"""

import pandas as pd
from datetime import datetime, timedelta

# Load historical data
hist = pd.read_csv('data/histories/ringkasan_histories_combined.csv')

# Convert Indonesian month names to dates
month_map = {
    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 
    'Mei': '05', 'Jun': '06', 'Jul': '07', 'Agu': '08',
    'Sep': '09', 'Okt': '10', 'Nov': '11', 'Des': '12'
}
hist['date_str'] = hist['Tanggal Perdagangan Terakhir'].str.strip()
for ind_month, eng_month in month_map.items():
    hist['date_str'] = hist['date_str'].str.replace(ind_month, eng_month)
hist['date'] = pd.to_datetime(hist['date_str'], format='%d %m %Y')
hist = hist.rename(columns={'Kode Saham': 'stock_code', 'Volume': 'volume'})

# Get latest date
latest_date = hist['date'].max()
print(f'Latest data date: {latest_date.date()}')

# Check portfolio stocks + recommended stocks
check_stocks = ['ASII', 'BBRI', 'BNGA', 'BUMI', 'PTBA', 'RLCO', 'BELL', 'HOPE', 'BAIK', 'VKTR', 'MBMA', 'IFSH', 'TIRT', 'MKAP']

print('\n=== TRADING STATUS CHECK (last 5 trading days) ===\n')
print(f"{'Stock':<8} {'Last Trade':<12} {'Days':<6} {'Last Volume':<15} {'Avg Volume':<15} {'Status':<15}")
print('-' * 90)

results = []

for stock in check_stocks:
    stock_data = hist[hist['stock_code'] == stock].sort_values('date', ascending=False)
    
    if len(stock_data) == 0:
        print(f"{stock:<8} {'NO DATA':<12} {'N/A':<6} {'N/A':<15} {'N/A':<15} {'NOT FOUND':<15}")
        results.append({'stock': stock, 'status': 'NOT_FOUND', 'tradeable': False})
        continue
    
    last_trade = stock_data.iloc[0]
    days_ago = (latest_date - last_trade['date']).days
    
    # Check last 5 days for volume
    recent = stock_data.head(5)
    avg_volume = recent['volume'].mean()
    last_volume = last_trade['volume']
    
    # Determine status
    if days_ago > 5:
        status = 'SUSPENDED?'
        tradeable = False
    elif last_volume == 0 or avg_volume < 1000:
        status = 'NO VOLUME'
        tradeable = False
    elif days_ago > 2:
        status = 'STALE'
        tradeable = False
    else:
        status = 'ACTIVE'
        tradeable = True
    
    print(f"{stock:<8} {str(last_trade['date'].date()):<12} {days_ago:<6} {int(last_volume):>13,} {int(avg_volume):>13,}  {status:<15}")
    
    results.append({
        'stock': stock,
        'last_trade_date': last_trade['date'].date(),
        'days_ago': days_ago,
        'last_volume': int(last_volume),
        'avg_volume_5d': int(avg_volume),
        'status': status,
        'tradeable': tradeable
    })

# Summary
tradeable = [r for r in results if r['tradeable']]
suspended = [r for r in results if not r['tradeable']]

print('\n' + '='*90)
print(f"\nSUMMARY:")
print(f"  ✅ TRADEABLE: {len(tradeable)} stocks - {', '.join([r['stock'] for r in tradeable])}")
print(f"  ❌ AVOID: {len(suspended)} stocks - {', '.join([r['stock'] for r in suspended])}")

if suspended:
    print(f"\n⚠️  WARNING: Do not recommend these stocks:")
    for r in suspended:
        print(f"     - {r['stock']}: {r['status']}")
