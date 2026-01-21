#!/usr/bin/env python3
"""
WATCHLIST VERIFICATION - Compare predictions vs actual 19 Jan 2026 performance
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Load actual trading data from 19 Jan 2026
actual_file = 'data/histories/Ringkasan Saham-20260119.xlsx'
actual_df = pd.read_excel(actual_file)

# Clean column names
actual_df.columns = actual_df.columns.str.strip()

# Our final watchlist
FINAL_WATCHLIST = [
    'RLCO', 'ROCK', 'CANI', 'TIRT', 'HADE', 'VISI', 'KDTN', 'RICY', 
    'MTFN', 'TAXI', 'EURO', 'SINI', 'RMKO', 'PBSA', 'INPS', 'MORA', 
    'SSTM', 'INOV', 'NATO', 'DEWI'
]

print("="*100)
print("WATCHLIST VERIFICATION - 19 JAN 2026 ACTUAL PERFORMANCE")
print("="*100)

# Filter for our watchlist stocks
watchlist_actual = actual_df[actual_df['Kode Saham'].isin(FINAL_WATCHLIST)].copy()

if len(watchlist_actual) == 0:
    print("\n⚠ No stocks from watchlist found in actual data. Checking all stocks...")
    print(f"\nWatchlist stocks: {FINAL_WATCHLIST}")
    print(f"\nSample of actual stock codes: {actual_df['Kode Saham'].head(20).tolist()}")
else:
    # Calculate actual performance
    watchlist_actual['Price_Change_Pct'] = (watchlist_actual['Selisih'] / watchlist_actual['Sebelumnya'] * 100)
    watchlist_actual['Is_Profitable'] = watchlist_actual['Selisih'] > 0
    
    # Sort by price change
    watchlist_actual = watchlist_actual.sort_values('Price_Change_Pct', ascending=False)
    
    print(f"\n✓ Found {len(watchlist_actual)} / {len(FINAL_WATCHLIST)} watchlist stocks in actual data")
    print(f"\nActual Performance on 19 Jan 2026:\n")
    
    print(f"{'Stock':<8}{'Previous':<12}{'Close':<12}{'Change':<12}{'Change %':<12}{'Volume':<15}{'Value (Rp)':<20}")
    print("-"*100)
    
    for _, row in watchlist_actual.iterrows():
        stock = row['Kode Saham']
        prev = row['Sebelumnya']
        close = row['Penutupan']
        change = row['Selisih']
        change_pct = row['Price_Change_Pct']
        volume = row['Volume']
        value = row['Nilai']
        
        status = "✓" if change > 0 else "✗" if change < 0 else "="
        print(f"{status} {stock:<6}{prev:>11.0f}{close:>11.0f}{change:>11.0f}{change_pct:>11.2f}%{volume:>14,.0f}{value:>19,.0f}")
    
    # Summary statistics
    print("\n" + "="*100)
    print("PERFORMANCE SUMMARY")
    print("="*100)
    
    total_stocks = len(watchlist_actual)
    profitable = watchlist_actual['Is_Profitable'].sum()
    unprofitable = (watchlist_actual['Selisih'] < 0).sum()
    unchanged = (watchlist_actual['Selisih'] == 0).sum()
    
    avg_change = watchlist_actual['Price_Change_Pct'].mean()
    max_gain = watchlist_actual['Price_Change_Pct'].max()
    max_loss = watchlist_actual['Price_Change_Pct'].min()
    
    total_volume = watchlist_actual['Volume'].sum()
    total_value = watchlist_actual['Nilai'].sum()
    
    print(f"\nStocks Analyzed: {total_stocks}")
    print(f"Profitable: {profitable} ({profitable/total_stocks*100:.1f}%)")
    print(f"Unprofitable: {unprofitable} ({unprofitable/total_stocks*100:.1f}%)")
    print(f"Unchanged: {unchanged} ({unchanged/total_stocks*100:.1f}%)")
    
    print(f"\nAverage Change: {avg_change:+.2f}%")
    print(f"Best Performer: {watchlist_actual.iloc[0]['Kode Saham']} ({max_gain:+.2f}%)")
    print(f"Worst Performer: {watchlist_actual.iloc[-1]['Kode Saham']} ({max_loss:+.2f}%)")
    
    print(f"\nTotal Volume Traded: {total_volume:,.0f} shares")
    print(f"Total Value Traded: Rp {total_value:,.0f}")
    
    # Missing stocks
    missing = set(FINAL_WATCHLIST) - set(watchlist_actual['Kode Saham'])
    if missing:
        print(f"\n⚠ Missing from actual data ({len(missing)} stocks): {', '.join(sorted(missing))}")
    
    # Tier analysis
    print("\n" + "="*100)
    print("TIER PERFORMANCE ANALYSIS")
    print("="*100)
    
    tier1 = ['RLCO', 'ROCK']
    tier2 = ['CANI', 'TIRT', 'INPS', 'VISI', 'KDTN', 'RICY']
    tier3 = [s for s in FINAL_WATCHLIST if s not in tier1 and s not in tier2]
    
    for tier_name, tier_stocks in [('TIER 1 (Anchor)', tier1), ('TIER 2 (Top Performers)', tier2), ('TIER 3 (Supporting)', tier3)]:
        tier_data = watchlist_actual[watchlist_actual['Kode Saham'].isin(tier_stocks)]
        if len(tier_data) > 0:
            tier_profitable = tier_data['Is_Profitable'].sum()
            tier_avg = tier_data['Price_Change_Pct'].mean()
            print(f"\n{tier_name}:")
            print(f"  Stocks: {len(tier_data)} / {len(tier_stocks)}")
            print(f"  Profitable: {tier_profitable} ({tier_profitable/len(tier_data)*100:.1f}%)")
            print(f"  Avg Change: {tier_avg:+.2f}%")
    
    # Validation check
    print("\n" + "="*100)
    print("METHOD VALIDATION")
    print("="*100)
    
    validation_result = "✓ PASS" if profitable/total_stocks >= 0.5 else "✗ FAIL"
    print(f"\nSuccess Rate Test (>50% profitable): {validation_result} ({profitable/total_stocks*100:.1f}%)")
    
    avg_result = "✓ PASS" if avg_change > 0 else "✗ FAIL"
    print(f"Positive Average Return: {avg_result} ({avg_change:+.2f}%)")
    
    if profitable/total_stocks >= 0.5 and avg_change > 0:
        print(f"\n🎯 VALIDATION SUCCESS: Method correctly predicted profitable stocks!")
    else:
        print(f"\n⚠ VALIDATION NEEDS REVIEW: Performance below expectations")
    
    # Check liquidity (volume)
    low_volume_threshold = 10000
    low_volume = watchlist_actual[watchlist_actual['Volume'] < low_volume_threshold]
    if len(low_volume) > 0:
        print(f"\n⚠ Low Volume Warning ({len(low_volume)} stocks with < {low_volume_threshold:,} shares):")
        for _, row in low_volume.iterrows():
            print(f"  {row['Kode Saham']}: {row['Volume']:,.0f} shares")
    
    # Check price filter (< Rp100)
    low_price = watchlist_actual[watchlist_actual['Penutupan'] < 100]
    if len(low_price) > 0:
        print(f"\n⚠ Low Price Warning ({len(low_price)} stocks < Rp100):")
        for _, row in low_price.iterrows():
            print(f"  {row['Kode Saham']}: Rp {row['Penutupan']:.0f}")

print("\n" + "="*100)
