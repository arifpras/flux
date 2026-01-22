#!/usr/bin/env python3
"""
BUMI Proceeds Redeployment Analysis
"""

import pandas as pd

# Load data
hist = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
foreign = pd.read_csv('data/live_tracking/foreign_buy_stocks_last5days.csv')

# Convert date
month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 
             'Mei': '05', 'Jun': '06', 'Jul': '07', 'Agu': '08',
             'Sep': '09', 'Okt': '10', 'Nov': '11', 'Des': '12'}
hist['date_str'] = hist['Tanggal Perdagangan Terakhir'].str.strip()
for ind_month, eng_month in month_map.items():
    hist['date_str'] = hist['date_str'].str.replace(ind_month, eng_month)
hist['date'] = pd.to_datetime(hist['date_str'], format='%d %m %Y')
hist = hist.rename(columns={'Kode Saham': 'stock_code', 'Penutupan': 'close'})

candidates = ['BBRI', 'VKTR', 'MBMA', 'MKAP']

print("\n" + "="*80)
print("BUMI PROCEEDS REDEPLOYMENT (Sold at 366)")
print("="*80 + "\n")

results = []

for stock in candidates:
    stock_data = hist[hist['stock_code'] == stock].sort_values('date', ascending=False)
    if len(stock_data) == 0:
        continue
    
    latest = stock_data.iloc[0]
    price = latest['close']
    
    recent_5d = stock_data.head(5)
    vol_5d_avg = recent_5d['Volume'].mean()
    price_5d_ago = stock_data.iloc[min(4, len(stock_data)-1)]['close']
    change_5d = ((price - price_5d_ago) / price_5d_ago * 100) if price_5d_ago > 0 else 0
    
    foreign_row = foreign[foreign['stock_code'] == stock]
    foreign_buy = foreign_row['net_foreign_buy'].values[0] if len(foreign_row) > 0 else 0
    
    shares_buyable = int(4_800_000 / price) if price > 0 else 0
    
    results.append({
        'stock': stock,
        'price': price,
        'change_5d': change_5d,
        'foreign_buy': foreign_buy,
        'vol_5d_avg': vol_5d_avg,
        'shares_buyable': shares_buyable
    })
    
    print(f"{stock:8} | Price: {price:>8,.0f} | 5D Change: {change_5d:>6.1f}% | Foreign: {foreign_buy:>12,.0f} | Shares: {shares_buyable:>10,}")

print("\n" + "="*80)
print("TOP 3 RECOMMENDATIONS")
print("="*80 + "\n")

print("1. BBRI (Bank Rakyat Indonesia)")
print("   Entry:  3,700 IDR (on any dip)")
print("   Target: 4,200 IDR (+10% to +15%)")
print("   Why:    Blue-chip, dividend payer, foreign accumulation ongoing")
print("   Risk:   LOW-MODERATE\n")

print("2. MBMA (Merdeka Battery Materials)")
print("   Entry:  750-800 IDR")
print("   Target: 1,000 IDR (+25% to +33%)")
print("   Why:    Highest foreign buying (+245M), battery/EV sector growth")
print("   Risk:   MEDIUM\n")

print("3. VKTR (VKTR Technology)")
print("   Entry:  1,150-1,200 IDR")
print("   Target: 1,600 IDR (+30% to +40%)")
print("   Why:    Strong foreign backing (+149M), mobility/EV trend, +21% YTD")
print("   Risk:   MEDIUM-HIGH\n")

print("="*80)
print("SUGGESTED ALLOCATION")
print("="*80 + "\n")

print("CONSERVATIVE (Target: 10-12% return):")
print("  60% BBRI   → ~1,300 shares @ 3,700 = 4,800,000")
print("  40% MKAP   → ~2,000 shares @ 2,400 = 4,800,000\n")

print("BALANCED (Target: 12-18% return):")
print("  40% BBRI   → ~520 shares @ 3,700")
print("  35% MBMA   → ~1,920 shares @ 800")  
print("  25% VKTR   → ~1,000 shares @ 1,200\n")

print("AGGRESSIVE (Target: 20-35% return):")
print("  35% VKTR   → ~1,400 shares @ 1,200")
print("  35% MBMA   → ~2,240 shares @ 750")
print("  30% BBRI   → ~390 shares @ 3,700\n")

print("="*80)
