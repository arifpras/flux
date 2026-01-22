#!/usr/bin/env python3
"""
Analyze which stocks typically pay dividends in February and March
"""

import pandas as pd
from collections import Counter

print("="*85)
print("FEBRUARY & MARCH DIVIDEND PAYERS ANALYSIS")
print("="*85)

# Load dividend data
dividends = pd.read_csv('data/reference/idx_dividend_history.csv')
dividends['payment_date'] = pd.to_datetime(dividends['payment_date'])
dividends['payment_month'] = dividends['payment_date'].dt.month
dividends['payment_year'] = dividends['payment_date'].dt.year

# Filter for February (2) and March (3)
feb_march = dividends[dividends['payment_month'].isin([2, 3])].copy()

print(f"\n[1/3] Historical dividend payments in Feb/March...")
print(f"Total payments found: {len(feb_march)}")
print(f"Unique stocks: {feb_march['stock_code'].nunique()}")
print(f"Date range: {feb_march['payment_date'].min().strftime('%Y-%m-%d')} to {feb_march['payment_date'].max().strftime('%Y-%m-%d')}")

# Count frequency by stock
stock_freq = feb_march['stock_code'].value_counts()

print(f"\n[2/3] Most consistent Feb/March dividend payers (3+ times in history):")
print("="*85)
print(f"{'Stock':<8} {'Times':<8} {'Avg Amount':<15} {'Last Payment':<15} {'Month Pattern':<20}")
print("-"*85)

for stock in stock_freq[stock_freq >= 3].index[:15]:
    stock_data = feb_march[feb_march['stock_code'] == stock]
    avg_amount = stock_data['dividend_amount_numeric'].mean()
    last_payment = stock_data['payment_date'].max()
    
    # Check if they pay in Feb, March, or both
    months = stock_data['payment_month'].unique()
    month_pattern = []
    if 2 in months:
        month_pattern.append("Feb")
    if 3 in months:
        month_pattern.append("Mar")
    month_str = " & ".join(month_pattern)
    
    print(f"{stock:<8} {len(stock_data):<8} {avg_amount:>14,.0f} {last_payment.strftime('%Y-%m-%d'):<15} {month_str:<20}")

print(f"\n[3/3] Expected dividend payments in Feb-Mar 2026 (based on historical pattern):")
print("="*85)

# Focus on stocks that paid in last 3 years in Feb/March
recent_payers = feb_march[feb_march['payment_year'] >= 2023].copy()
recent_stock_freq = recent_payers['stock_code'].value_counts()

# For stocks with consistent pattern, predict 2026 payment
print(f"{'Stock':<8} {'Historical':<12} {'Avg Amount':<15} {'Usual Month':<15} {'2026 Prob':<15}")
print("-"*85)

for stock in recent_stock_freq[recent_stock_freq >= 2].index[:20]:
    stock_data = recent_payers[recent_payers['stock_code'] == stock]
    avg_amount = stock_data['dividend_amount_numeric'].mean()
    
    # Determine usual month
    month_counter = Counter(stock_data['payment_month'])
    usual_month = "Feb" if month_counter.get(2, 0) >= month_counter.get(3, 0) else "Mar"
    
    # Check if there's 2024 or 2025 payment
    recent_years = stock_data['payment_year'].unique()
    if 2024 in recent_years or 2025 in recent_years:
        prob = "🟢 High (90%)"
    else:
        prob = "🟡 Medium (60%)"
    
    print(f"{stock:<8} {len(stock_data):>11} {avg_amount:>14,.0f} {usual_month:<15} {prob:<15}")

# Check which stocks from portfolio/recommendations typically pay in Feb/March
print(f"\n{'='*85}")
print("YOUR PORTFOLIO & RECOMMENDED STOCKS - Feb/March Payment History:")
print("="*85)

tracked_stocks = ['ASII', 'BBRI', 'BNGA', 'BUMI', 'PTBA', 'ADRO', 'BMRI', 'TLKM', 'UNTR', 'ANTM']

print(f"{'Stock':<8} {'Feb Payments':<15} {'Mar Payments':<15} {'Total Amount':<15} {'Pattern':<20}")
print("-"*85)

for stock in tracked_stocks:
    stock_feb = feb_march[(feb_march['stock_code'] == stock) & (feb_march['payment_month'] == 2)]
    stock_mar = feb_march[(feb_march['stock_code'] == stock) & (feb_march['payment_month'] == 3)]
    
    feb_count = len(stock_feb)
    mar_count = len(stock_mar)
    total_amount = stock_feb['dividend_amount_numeric'].sum() + stock_mar['dividend_amount_numeric'].sum()
    
    if feb_count > 0 or mar_count > 0:
        if feb_count >= 2:
            pattern = "✅ Regular Feb payer"
        elif mar_count >= 2:
            pattern = "✅ Regular Mar payer"
        elif feb_count + mar_count >= 2:
            pattern = "⚠️ Irregular"
        else:
            pattern = "🟡 Once only"
        
        print(f"{stock:<8} {feb_count:>14} {mar_count:>14} {total_amount:>14,.0f} {pattern:<20}")
    else:
        print(f"{stock:<8} {'-':>14} {'-':>14} {0:>14} {'❌ None':<20}")

print("\n" + "="*85)
print("CONCLUSION:")
print("="*85)

# Find top 5 most likely 2026 Feb/March payers
feb_2026_likely = recent_payers[recent_payers['payment_month'] == 2]['stock_code'].value_counts().head(5)
mar_2026_likely = recent_payers[recent_payers['payment_month'] == 3]['stock_code'].value_counts().head(5)

print(f"""
🗓️ FEBRUARY 2026 HIGH PROBABILITY:
   Top 5: {', '.join(feb_2026_likely.index.tolist())}
   
🗓️ MARCH 2026 HIGH PROBABILITY:
   Top 5: {', '.join(mar_2026_likely.index.tolist())}

💡 FROM YOUR TRACKED STOCKS:
   - ADRO: Typically pays in Feb/March (check for 2026 announcement)
   - PTBA: Coal sector usually pays after Q4 earnings (Feb-Mar window)
   - UNTR: Astra group typically March
   - BBRI: Banking sector usually April-May (after AGM), not Feb/Mar
   
⏰ KEY DATES TO WATCH:
   - Jan 25-31: Companies announce dividend plans for Feb payment
   - Feb 1-28: Ex-date usually 5-7 days before payment
   - Feb 15-28: Actual payment dates peak
   - Mar 1-15: Second wave of payments
""")

print("="*85)

# Save full list for reference
feb_march_sorted = feb_march.sort_values(['payment_date', 'dividend_amount_numeric'], ascending=[False, False])
feb_march_sorted.to_csv('results/20260122_feb_march_dividend_stocks.csv', index=False)
print(f"✓ Full list saved to: results/20260122_feb_march_dividend_stocks.csv")
print("="*85)
