#!/usr/bin/env python3
"""
IDX Dividend Data Scraper - Yahoo Finance
Fetches last 3 years of dividend payments for all IDX stocks
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import os

print("="*85)
print("IDX DIVIDEND DATA SCRAPER - Yahoo Finance")
print("="*85)

# Load list of IDX stocks
print("\n[1/5] Loading IDX stock list...")
try:
    idx_df = pd.read_excel('data/reference/IDX-Stock-Screener-20Jan2026.xlsx')
    stock_codes = idx_df['Kode Saham'].unique().tolist()
    print(f"   ✓ Loaded {len(stock_codes)} stocks from IDX screener")
except Exception as e:
    print(f"   Error loading IDX screener: {e}")
    print("   Falling back to historical data...")
    hist = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
    stock_codes = hist['Kode Saham'].unique().tolist()
    print(f"   ✓ Loaded {len(stock_codes)} stocks from historical data")

# Date range: last 3 years
end_date = datetime.now()
start_date = end_date - timedelta(days=3*365)

print(f"\n[2/5] Fetching dividends from {start_date.date()} to {end_date.date()}")
print(f"   This will take approximately {len(stock_codes)*2/60:.1f} minutes...")

# Results storage
all_dividends = []
success_count = 0
error_count = 0
no_dividend_count = 0

# Process each stock
print("\n[3/5] Scraping dividend data...")
for i, stock_code in enumerate(stock_codes, 1):
    ticker_symbol = f"{stock_code}.JK"  # Yahoo Finance uses .JK for Indonesia
    
    # Progress indicator
    if i % 50 == 0:
        print(f"   Progress: {i}/{len(stock_codes)} stocks ({i/len(stock_codes)*100:.1f}%)")
    
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker_symbol)
        dividends = stock.dividends
        
        # Filter last 3 years
        if len(dividends) > 0:
            dividends_3y = dividends[dividends.index >= start_date]
            
            if len(dividends_3y) > 0:
                for date, amount in dividends_3y.items():
                    all_dividends.append({
                        'stock_code': stock_code,
                        'ticker': ticker_symbol,
                        'ex_date': date.date(),
                        'dividend_amount': amount,
                        'year': date.year
                    })
                success_count += 1
            else:
                no_dividend_count += 1
        else:
            no_dividend_count += 1
        
        # Rate limiting - be nice to Yahoo Finance
        time.sleep(0.1)
        
    except Exception as e:
        error_count += 1
        if i <= 10:  # Show first 10 errors for debugging
            print(f"   ⚠️  {stock_code}: {str(e)[:50]}")
        continue

print(f"\n[4/5] Scraping complete!")
print(f"   ✓ Success: {success_count} stocks with dividends")
print(f"   ○ No dividends: {no_dividend_count} stocks")
print(f"   ✗ Errors: {error_count} stocks")

# Create DataFrame
if len(all_dividends) > 0:
    df_dividends = pd.DataFrame(all_dividends)
    
    # Calculate some statistics
    df_dividends['dividend_amount'] = pd.to_numeric(df_dividends['dividend_amount'], errors='coerce')
    
    # Sort by date descending
    df_dividends = df_dividends.sort_values(['stock_code', 'ex_date'], ascending=[True, False])
    
    # Save to CSV
    output_file = 'data/reference/idx_dividend_history_3years.csv'
    df_dividends.to_csv(output_file, index=False)
    
    print(f"\n[5/5] Results saved to: {output_file}")
    print(f"   Total dividend payments: {len(df_dividends)}")
    print(f"   Date range: {df_dividends['ex_date'].min()} to {df_dividends['ex_date'].max()}")
    
    # Summary by year
    print("\n" + "="*85)
    print("DIVIDEND PAYMENTS BY YEAR")
    print("="*85)
    yearly_summary = df_dividends.groupby('year').agg({
        'stock_code': 'count',
        'dividend_amount': ['sum', 'mean']
    }).round(2)
    yearly_summary.columns = ['Number of Payments', 'Total Amount (IDR)', 'Average Amount (IDR)']
    print(yearly_summary)
    
    # Top dividend payers
    print("\n" + "="*85)
    print("TOP 20 DIVIDEND PAYERS (by total amount in last 3 years)")
    print("="*85)
    top_payers = df_dividends.groupby('stock_code').agg({
        'dividend_amount': ['sum', 'count', 'mean']
    }).round(2)
    top_payers.columns = ['Total Dividends (IDR)', 'Number of Payments', 'Avg Per Payment (IDR)']
    top_payers = top_payers.sort_values('Total Dividends (IDR)', ascending=False).head(20)
    print(top_payers)
    
    # Your portfolio stocks
    portfolio_stocks = ['BBRI', 'ASII', 'BNGA', 'BUMI', 'PTBA']
    print("\n" + "="*85)
    print("YOUR PORTFOLIO - DIVIDEND HISTORY")
    print("="*85)
    
    for stock in portfolio_stocks:
        stock_divs = df_dividends[df_dividends['stock_code'] == stock]
        if len(stock_divs) > 0:
            total = stock_divs['dividend_amount'].sum()
            count = len(stock_divs)
            avg = stock_divs['dividend_amount'].mean()
            print(f"\n{stock}:")
            print(f"   Total paid: {total:,.0f} IDR")
            print(f"   Payments: {count} times")
            print(f"   Average: {avg:,.0f} IDR per payment")
            print(f"   Latest: {stock_divs.iloc[0]['ex_date']} - {stock_divs.iloc[0]['dividend_amount']:.0f} IDR")
        else:
            print(f"\n{stock}:")
            print(f"   ❌ No dividend data found in last 3 years")
    
    # Recommended stocks with foreign buying + dividends
    print("\n" + "="*85)
    print("RECOMMENDED: DIVIDEND STOCKS WITH FOREIGN ACCUMULATION")
    print("="*85)
    
    foreign_stocks = ['BBRI', 'MBMA', 'VKTR', 'ADRO', 'ANTM', 'MDKA', 'INCO', 'BRMS']
    print(f"\nChecking foreign-backed stocks for dividend history...\n")
    
    for stock in foreign_stocks:
        stock_divs = df_dividends[df_dividends['stock_code'] == stock]
        if len(stock_divs) > 0:
            recent = stock_divs.iloc[0]
            print(f"✓ {stock:6} - Latest dividend: {recent['ex_date']} ({recent['dividend_amount']:.0f} IDR)")
        else:
            print(f"○ {stock:6} - No dividends (growth stock)")
    
else:
    print("\n⚠️  No dividend data found!")
    print("   This could mean:")
    print("   - Yahoo Finance doesn't have IDX dividend data")
    print("   - Network connection issues")
    print("   - API rate limiting")

print("\n" + "="*85)
print("SCRAPING COMPLETE")
print("="*85)
