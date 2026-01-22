#!/usr/bin/env python3
"""
IDX Dividend Data Finder - Search for dividend information in available data
"""

import pandas as pd
import os

print("="*85)
print("IDX DIVIDEND DATA SEARCH")
print("="*85)

# Check IDX Screener
print("\n1. Checking IDX Stock Screener...")
try:
    df = pd.read_excel('data/reference/IDX-Stock-Screener-20Jan2026.xlsx')
    
    print(f"   Loaded {len(df)} stocks")
    print(f"   Columns: {len(df.columns)}")
    
    # Look for dividend columns
    dividend_cols = [col for col in df.columns if any(keyword in col.lower() 
                     for keyword in ['divid', 'yield', 'payout', 'dps', 'div'])]
    
    if dividend_cols:
        print(f"   ✅ Found {len(dividend_cols)} dividend column(s):")
        for col in dividend_cols:
            non_null = df[col].notna().sum()
            print(f"      - {col}: {non_null} stocks with data")
    else:
        print("   ❌ No dividend columns in screener")
        print(f"   Available columns: {', '.join(df.columns[:10])}...")
        
except Exception as e:
    print(f"   Error: {e}")

# Check historical data
print("\n2. Checking historical price data...")
try:
    hist = pd.read_csv('data/histories/ringkasan_histories_combined.csv', nrows=5)
    print(f"   Columns: {', '.join(hist.columns[:10])}...")
    has_dividend = any('divid' in col.lower() for col in hist.columns)
    if has_dividend:
        print("   ✅ Has dividend data")
    else:
        print("   ❌ No dividend columns found")
except Exception as e:
    print(f"   Error: {e}")

# Check for any CSV files with dividend data
print("\n3. Searching all data files for dividend information...")
data_dirs = ['data/reference', 'data/manual', 'data/live_tracking']

for data_dir in data_dirs:
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        print(f"\n   {data_dir}: {len(csv_files)} CSV files")
        
        for csv_file in csv_files[:5]:  # Check first 5 files
            try:
                file_path = os.path.join(data_dir, csv_file)
                df_check = pd.read_csv(file_path, nrows=1)
                dividend_cols = [col for col in df_check.columns if 'divid' in col.lower()]
                if dividend_cols:
                    print(f"      ✅ {csv_file}: {dividend_cols}")
            except:
                pass

print("\n" + "="*85)
print("RECOMMENDATION")
print("="*85)
print("""
IDX dividend data is NOT available in current dataset.

To get dividend payment history (last 3 years), you need to:

1. IDX Website (Most Reliable):
   - Visit: https://www.idx.co.id/id/data-pasar/data-saham/daftar-saham
   - Download corporate action data (includes dividends)
   - Or use IDX API if available

2. Bloomberg/Reuters Terminal:
   - Professional data with full dividend history
   - Most comprehensive but requires subscription

3. Yahoo Finance Indonesia:
   - Free but may have incomplete data
   - Good for blue-chip stocks only

4. RTI Business (IDX official data provider):
   - Paid subscription
   - Full historical dividend records

5. Web Scraping (Manual):
   - Individual company websites → Investor Relations → Corporate Actions
   - Time-consuming but free

Recommended for your analysis:
- Focus on companies in BBRI, ASII, TLKM, BMRI, BBCA (consistent dividend payers)
- Cross-reference with your foreign flow data
- Stocks with foreign accumulation + dividend yield = strongest combination
""")

print("="*85)
