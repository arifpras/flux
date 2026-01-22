#!/usr/bin/env python3
"""
IDX Dividend Data Scraper - SahamIDX.com
Downloads comprehensive dividend history from https://www.new.sahamidx.com
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re

print("="*85)
print("IDX DIVIDEND DATA SCRAPER - SahamIDX.com")
print("="*85)

# Configuration
BASE_URL = "https://www.new.sahamidx.com/?/deviden/page/{}"
OUTPUT_FILE = "data/reference/idx_dividend_history.csv"
BACKUP_FILE = "data/reference/idx_dividend_history_backup.csv"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

all_dividends = []
page = 1
max_pages = 100  # Safety limit

print(f"\n[1/3] Starting dividend data scraping...")
print(f"   Source: {BASE_URL.format(1)}")

while page <= max_pages:
    url = BASE_URL.format(page)
    
    try:
        print(f"\n   Fetching page {page}...", end=" ")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the dividend table
        # Looking for table rows with dividend data
        tables = soup.find_all('table')
        
        if not tables:
            print("No more data found. Stopping.")
            break
        
        found_data = False
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                
                # Expected format: Stock Code | Amount | Cum Date | Ex Date | Recording Date | Payment Date
                if len(cols) >= 6:
                    try:
                        stock_code = cols[0].get_text(strip=True)
                        amount = cols[1].get_text(strip=True)
                        cum_date = cols[2].get_text(strip=True)
                        ex_date = cols[3].get_text(strip=True)
                        recording_date = cols[4].get_text(strip=True)
                        payment_date = cols[5].get_text(strip=True)
                        
                        # Validate stock code (should be 4 letters)
                        if len(stock_code) == 4 and stock_code.isalpha():
                            dividend_record = {
                                'stock_code': stock_code.upper(),
                                'dividend_amount': amount,
                                'cum_date': cum_date,
                                'ex_date': ex_date,
                                'recording_date': recording_date,
                                'payment_date': payment_date,
                                'scraped_date': datetime.now().strftime('%Y-%m-%d'),
                                'page': page
                            }
                            all_dividends.append(dividend_record)
                            found_data = True
                    except Exception as e:
                        continue
        
        if found_data:
            print(f"✓ Found {len([d for d in all_dividends if d['page'] == page])} dividends")
        else:
            print("No data found. Stopping.")
            break
        
        # Check for next page link or page numbers
        # Look for pagination links
        pagination = soup.find_all('a', href=re.compile(r'/deviden/page/\d+'))
        max_page_found = max([int(re.search(r'/page/(\d+)', a.get('href', '')).group(1)) 
                              for a in pagination if re.search(r'/page/(\d+)', a.get('href', ''))], 
                             default=page)
        
        if page >= max_page_found:
            print(f"\n   Reached last page (page {max_page_found}).")
            break
        
        page += 1
        time.sleep(0.5)  # Be polite to the server
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        print(f"   Stopping at page {page}")
        break
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        break

print(f"\n[2/3] Processing scraped data...")
print(f"   Total dividend records: {len(all_dividends)}")

if len(all_dividends) == 0:
    print("\n   ⚠️  No dividend data scraped. Please check:")
    print("   1. Internet connection")
    print("   2. Website availability")
    print("   3. Website structure hasn't changed")
    exit(1)

# Convert to DataFrame
df = pd.DataFrame(all_dividends)

# Data cleaning and enrichment
print(f"\n   Cleaning data...")

# Parse dates
date_cols = ['cum_date', 'ex_date', 'recording_date', 'payment_date']
for col in date_cols:
    try:
        df[col] = pd.to_datetime(df[col], format='%d-%b-%Y', errors='coerce')
    except:
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        except:
            pass

# Convert dividend amount to float
df['dividend_amount_numeric'] = pd.to_numeric(
    df['dividend_amount'].str.replace(',', ''), 
    errors='coerce'
)

# Calculate dividend year
df['dividend_year'] = df['payment_date'].dt.year

# Sort by payment date (newest first)
df = df.sort_values('payment_date', ascending=False)

# Remove duplicates (same stock + payment date)
df_dedup = df.drop_duplicates(subset=['stock_code', 'payment_date'], keep='first')

print(f"   ✓ After deduplication: {len(df_dedup)} unique dividend records")
print(f"   ✓ Date range: {df['payment_date'].min()} to {df['payment_date'].max()}")
print(f"   ✓ Unique stocks: {df['stock_code'].nunique()}")

# Summary statistics
print(f"\n   Dividend Statistics:")
print(f"   - Total dividends: {len(df_dedup)}")
print(f"   - Last 3 years: {len(df_dedup[df_dedup['dividend_year'] >= 2023])}")
print(f"   - Unique companies: {df_dedup['stock_code'].nunique()}")

# Top dividend payers
top_payers = df_dedup.groupby('stock_code').agg({
    'dividend_amount_numeric': 'sum',
    'payment_date': 'count'
}).rename(columns={'payment_date': 'payment_count'}).sort_values('dividend_amount_numeric', ascending=False).head(10)

print(f"\n   Top 10 Dividend Payers (by total amount):")
for stock, row in top_payers.iterrows():
    print(f"      {stock}: {row['dividend_amount_numeric']:.0f} IDR ({int(row['payment_count'])} payments)")

print(f"\n[3/3] Saving data...")

# Backup existing file if it exists
import os
if os.path.exists(OUTPUT_FILE):
    import shutil
    shutil.copy(OUTPUT_FILE, BACKUP_FILE)
    print(f"   ✓ Backed up existing file to {BACKUP_FILE}")

# Save to CSV
df_dedup.to_csv(OUTPUT_FILE, index=False)
print(f"   ✓ Saved {len(df_dedup)} records to {OUTPUT_FILE}")

# Save summary report
summary_file = OUTPUT_FILE.replace('.csv', '_summary.txt')
with open(summary_file, 'w') as f:
    f.write("="*85 + "\n")
    f.write("IDX DIVIDEND DATA - SCRAPING SUMMARY\n")
    f.write("="*85 + "\n\n")
    f.write(f"Scraped Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Source: {BASE_URL.format(1)}\n")
    f.write(f"Pages Scraped: {page}\n")
    f.write(f"Total Records: {len(df_dedup)}\n")
    f.write(f"Unique Stocks: {df_dedup['stock_code'].nunique()}\n")
    f.write(f"Date Range: {df['payment_date'].min()} to {df['payment_date'].max()}\n\n")
    
    f.write("="*85 + "\n")
    f.write("TOP 20 DIVIDEND PAYERS (Last 3 Years)\n")
    f.write("="*85 + "\n\n")
    
    recent = df_dedup[df_dedup['dividend_year'] >= 2023]
    top20 = recent.groupby('stock_code').agg({
        'dividend_amount_numeric': ['sum', 'count', 'mean']
    }).round(2)
    top20.columns = ['total_amount', 'payment_count', 'avg_amount']
    top20 = top20.sort_values('total_amount', ascending=False).head(20)
    
    f.write(f"{'Stock':<8} {'Total (IDR)':<15} {'Payments':<12} {'Avg (IDR)':<15}\n")
    f.write("-"*85 + "\n")
    for stock, row in top20.iterrows():
        f.write(f"{stock:<8} {row['total_amount']:>14,.0f} {int(row['payment_count']):>11} {row['avg_amount']:>14,.2f}\n")

print(f"   ✓ Saved summary report to {summary_file}")

print("\n" + "="*85)
print("✅ SCRAPING COMPLETE")
print("="*85)
print(f"\nOutput files:")
print(f"  - Data: {OUTPUT_FILE}")
print(f"  - Summary: {summary_file}")
print(f"  - Backup: {BACKUP_FILE} (if existed)")
print("\nNext steps:")
print("  1. Review the data in Excel or text editor")
print("  2. Use the data for dividend analysis")
print("  3. Combine with foreign flow data for stock selection")
print("="*85)
