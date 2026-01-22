#!/usr/bin/env python3
"""
Analyze financial fundamentals of our watchlist stocks
Using December 2025 financial data
"""
import pandas as pd
import numpy as np

# Load financial data (skip first 3 rows of headers)
financial_df = pd.read_excel('data/reference/Financial Data and Ratio - Dec 2025.xlsx', skiprows=3)

# Set proper column names from the first row
financial_df.columns = financial_df.iloc[0]
financial_df = financial_df[1:].reset_index(drop=True)

# Clean up column names
cols_map = {
    np.nan: 'Index',
    'Assets, b.IDR': 'Assets',
    'Liabilities, b.IDR': 'Liabilities',
    'Equity, b.IDR': 'Equity',
    'Sales, b.IDR': 'Sales',
    'EBT, b.IDR': 'EBT',
    'EPS, IDR': 'EPS',
    'Book Value, IDR': 'Book_Value',
    'P/E Ratio, x': 'PE_Ratio',
    'Price to BV, x': 'PBV_Ratio',
    'D/E Ratio, x': 'DE_Ratio',
    'ROA, %': 'ROA',
    'ROE, %': 'ROE',
    'NPM, %': 'NPM'
}

# Find Code column (should be one of the unnamed columns)
for i, col in enumerate(financial_df.columns):
    if col == col:  # Not NaN
        sample = str(financial_df.iloc[0, i])
        if len(sample) <= 5 and sample.isalpha():  # Likely stock code
            cols_map[col] = 'Code'

financial_df.rename(columns=cols_map, inplace=True)

# Find the Code column
code_col = None
for col in financial_df.columns:
    if 'Code' in str(col) or financial_df[col].astype(str).str.len().max() == 4:
        sample_values = financial_df[col].dropna().head(10).astype(str).tolist()
        if any(len(v) == 4 and v.isalpha() for v in sample_values):
            code_col = col
            break

if code_col is None:
    # Try column by position (usually column 5 or 6)
    for idx in [5, 6, 7]:
        if idx < len(financial_df.columns):
            sample = financial_df.iloc[:20, idx].dropna().astype(str)
            if sample.str.len().max() == 4:
                code_col = financial_df.columns[idx]
                break

# Our watchlist
FINAL_WATCHLIST = [
    'RLCO', 'ROCK', 'CANI', 'TIRT', 'HADE', 'VISI', 'KDTN', 'RICY', 
    'MTFN', 'TAXI', 'EURO', 'SINI', 'RMKO', 'PBSA', 'INPS', 'MORA', 
    'SSTM', 'INOV', 'NATO', 'DEWI'
]

print("="*100)
print("FINANCIAL FUNDAMENTALS ANALYSIS - DECEMBER 2025")
print("="*100)

if code_col:
    financial_df.rename(columns={code_col: 'Code'}, inplace=True)
    
    # Filter our watchlist
    watchlist_financial = financial_df[financial_df['Code'].isin(FINAL_WATCHLIST)].copy()
    
    # Convert numeric columns
    numeric_cols = ['Assets', 'Equity', 'Sales', 'EBT', 'EPS', 'Book_Value', 
                   'PE_Ratio', 'PBV_Ratio', 'DE_Ratio', 'ROA', 'ROE', 'NPM']
    
    for col in numeric_cols:
        if col in watchlist_financial.columns:
            watchlist_financial[col] = pd.to_numeric(watchlist_financial[col], errors='coerce')
    
    print(f"\n✓ Found {len(watchlist_financial)}/{len(FINAL_WATCHLIST)} stocks in financial data")
    
    if len(watchlist_financial) > 0:
        print(f"\n{'Stock':<8}{'Assets':>12}{'Equity':>12}{'Sales':>12}{'ROE%':>8}{'ROA%':>8}{'NPM%':>8}{'P/E':>8}{'P/BV':>8}{'D/E':>8}")
        print("-"*100)
        
        for _, row in watchlist_financial.iterrows():
            stock = row['Code']
            assets = row.get('Assets', 0)
            equity = row.get('Equity', 0)
            sales = row.get('Sales', 0)
            roe = row.get('ROE', 0)
            roa = row.get('ROA', 0)
            npm = row.get('NPM', 0)
            pe = row.get('PE_Ratio', 0)
            pbv = row.get('PBV_Ratio', 0)
            de = row.get('DE_Ratio', 0)
            
            print(f"{stock:<8}{assets:>11.1f}B{equity:>11.1f}B{sales:>11.1f}B{roe:>7.1f}%{roa:>7.1f}%{npm:>7.1f}%{pe:>7.1f}x{pbv:>7.2f}x{de:>7.2f}x")
        
        # Summary stats
        print("\n" + "="*100)
        print("FUNDAMENTAL METRICS SUMMARY")
        print("="*100)
        
        avg_roe = watchlist_financial['ROE'].mean()
        avg_roa = watchlist_financial['ROA'].mean()
        avg_npm = watchlist_financial['NPM'].mean()
        avg_pe = watchlist_financial['PE_Ratio'].mean()
        avg_pbv = watchlist_financial['PBV_Ratio'].mean()
        avg_de = watchlist_financial['DE_Ratio'].mean()
        
        print(f"\nAverage ROE: {avg_roe:.2f}%")
        print(f"Average ROA: {avg_roa:.2f}%")
        print(f"Average NPM: {avg_npm:.2f}%")
        print(f"Average P/E: {avg_pe:.2f}x")
        print(f"Average P/BV: {avg_pbv:.2f}x")
        print(f"Average D/E: {avg_de:.2f}x")
        
        # Identify strong fundamentals
        print("\n" + "="*100)
        print("STOCKS WITH STRONG FUNDAMENTALS")
        print("="*100)
        
        strong_roe = watchlist_financial[watchlist_financial['ROE'] > 15]
        strong_roa = watchlist_financial[watchlist_financial['ROA'] > 10]
        low_de = watchlist_financial[watchlist_financial['DE_Ratio'] < 1]
        undervalued_pe = watchlist_financial[watchlist_financial['PE_Ratio'] < 10]
        
        print(f"\n✓ High ROE (>15%): {len(strong_roe)} stocks")
        if len(strong_roe) > 0:
            for _, row in strong_roe.iterrows():
                print(f"  • {row['Code']}: ROE {row['ROE']:.1f}%")
        
        print(f"\n✓ High ROA (>10%): {len(strong_roa)} stocks")
        if len(strong_roa) > 0:
            for _, row in strong_roa.iterrows():
                print(f"  • {row['Code']}: ROA {row['ROA']:.1f}%")
        
        print(f"\n✓ Low Debt (D/E <1): {len(low_de)} stocks")
        if len(low_de) > 0:
            for _, row in low_de.iterrows():
                print(f"  • {row['Code']}: D/E {row['DE_Ratio']:.2f}x")
        
        print(f"\n✓ Undervalued (P/E <10): {len(undervalued_pe)} stocks")
        if len(undervalued_pe) > 0:
            for _, row in undervalued_pe.iterrows():
                print(f"  • {row['Code']}: P/E {row['PE_Ratio']:.2f}x")
        
        # Missing stocks
        found_stocks = watchlist_financial['Code'].tolist()
        missing = [s for s in FINAL_WATCHLIST if s not in found_stocks]
        
        if missing:
            print(f"\n⚠ No financial data available ({len(missing)} stocks): {', '.join(missing)}")
    
else:
    print("\n⚠ Could not identify Code column in financial data")
    print("Available columns:", list(financial_df.columns[:15]))

print("\n" + "="*100)
print("CONCLUSION")
print("="*100)
print("""
Financial fundamentals provide additional context but are NOT the primary
predictor for 2-3 day momentum trades.

Key Insights:
  • Our method focuses on actual recent performance (7-day validation)
  • Fundamentals are backward-looking (Q4 2025 data)
  • Short-term momentum driven by price action, not quarterly reports
  
Recommendation:
  • Use fundamentals as tie-breaker between similar momentum stocks
  • Prefer stocks with ROE >15%, low D/E <1, P/E <10 when all else equal
  • Primary filter remains: recent performance + pattern matching
""")
print("="*100)
