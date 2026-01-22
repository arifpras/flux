#!/usr/bin/env python3
"""
Analyze which stocks typically pay dividends in May and June (peak dividend season)
"""

import pandas as pd
from collections import Counter

print("="*85)
print("MAY & JUNE DIVIDEND PAYERS ANALYSIS (Peak Dividend Season)")
print("="*85)

# Load dividend data
dividends = pd.read_csv('data/reference/idx_dividend_history.csv')
dividends['payment_date'] = pd.to_datetime(dividends['payment_date'])
dividends['payment_month'] = dividends['payment_date'].dt.month
dividends['payment_year'] = dividends['payment_date'].dt.year

# Filter for May (5) and June (6)
may_june = dividends[dividends['payment_month'].isin([5, 6])].copy()

print(f"\n[1/4] Historical dividend payments in May/June...")
print(f"Total payments found: {len(may_june)}")
print(f"Unique stocks: {may_june['stock_code'].nunique()}")
print(f"Date range: {may_june['payment_date'].min().strftime('%Y-%m-%d')} to {may_june['payment_date'].max().strftime('%Y-%m-%d')}")

# Count frequency by stock
stock_freq = may_june['stock_code'].value_counts()

print(f"\n[2/4] Most consistent May/June dividend payers (2+ times in history):")
print("="*85)
print(f"{'Stock':<8} {'Times':<8} {'Avg Amount':<15} {'Last Payment':<15} {'Month Pattern':<20}")
print("-"*85)

for stock in stock_freq[stock_freq >= 2].index[:25]:
    stock_data = may_june[may_june['stock_code'] == stock]
    avg_amount = stock_data['dividend_amount_numeric'].mean()
    last_payment = stock_data['payment_date'].max()
    
    # Check if they pay in May, June, or both
    months = stock_data['payment_month'].unique()
    month_pattern = []
    if 5 in months:
        month_pattern.append("May")
    if 6 in months:
        month_pattern.append("Jun")
    month_str = " & ".join(month_pattern)
    
    print(f"{stock:<8} {len(stock_data):<8} {avg_amount:>14,.0f} {last_payment.strftime('%Y-%m-%d'):<15} {month_str:<20}")

print(f"\n[3/4] Expected dividend payments in May-Jun 2026 (based on historical pattern):")
print("="*85)

# Focus on stocks that paid in last 3 years in May/June
recent_payers = may_june[may_june['payment_year'] >= 2023].copy()
recent_stock_freq = recent_payers['stock_code'].value_counts()

# For stocks with consistent pattern, predict 2026 payment
print(f"{'Stock':<8} {'Historical':<12} {'Avg Amount':<15} {'Usual Month':<15} {'2026 Prob':<15}")
print("-"*85)

for stock in recent_stock_freq[recent_stock_freq >= 2].index[:30]:
    stock_data = recent_payers[recent_payers['stock_code'] == stock]
    avg_amount = stock_data['dividend_amount_numeric'].mean()
    
    # Determine usual month
    month_counter = Counter(stock_data['payment_month'])
    usual_month = "May" if month_counter.get(5, 0) >= month_counter.get(6, 0) else "Jun"
    
    # Check if there's 2024 or 2025 payment
    recent_years = stock_data['payment_year'].unique()
    if 2025 in recent_years:
        prob = "🟢 High (95%)"
    elif 2024 in recent_years:
        prob = "🟡 Medium (75%)"
    else:
        prob = "⚪ Low (50%)"
    
    print(f"{stock:<8} {len(stock_data):>11} {avg_amount:>14,.0f} {usual_month:<15} {prob:<15}")

# Check which stocks from portfolio/recommendations typically pay in May/June
print(f"\n{'='*85}")
print("YOUR PORTFOLIO & RECOMMENDED STOCKS - May/June Payment History:")
print("="*85)

tracked_stocks = ['ASII', 'BBRI', 'BNGA', 'BUMI', 'PTBA', 'ADRO', 'BMRI', 'TLKM', 'UNTR', 'ANTM', 'VKTR', 'MBMA']

print(f"{'Stock':<8} {'May Payments':<15} {'Jun Payments':<15} {'Total Amount':<15} {'Pattern':<25}")
print("-"*85)

for stock in tracked_stocks:
    stock_may = may_june[(may_june['stock_code'] == stock) & (may_june['payment_month'] == 5)]
    stock_jun = may_june[(may_june['stock_code'] == stock) & (may_june['payment_month'] == 6)]
    
    may_count = len(stock_may)
    jun_count = len(stock_jun)
    total_amount = stock_may['dividend_amount_numeric'].sum() + stock_jun['dividend_amount_numeric'].sum()
    
    if may_count > 0 or jun_count > 0:
        if may_count >= 2:
            pattern = "✅ Regular May payer"
        elif jun_count >= 2:
            pattern = "✅ Regular Jun payer"
        elif may_count + jun_count >= 2:
            pattern = "✅ Both months (flexible)"
        else:
            pattern = "🟡 Once only"
        
        # Add expected 2026 payment if consistent
        if may_count + jun_count >= 2:
            pattern += " → Expect 2026"
        
        print(f"{stock:<8} {may_count:>14} {jun_count:>14} {total_amount:>14,.0f} {pattern:<25}")
    else:
        print(f"{stock:<8} {'-':>14} {'-':>14} {0:>14} {'❌ None':<25}")

print("\n" + "="*85)
print("SECTOR ANALYSIS - May/June Dividend Patterns:")
print("="*85)

# Group by sector (we'll need to add sector data - for now use stock prefix patterns)
banking_stocks = ['BBRI', 'BMRI', 'BBCA', 'BBNI', 'BRIS']
coal_mining = ['ADRO', 'PTBA', 'ITMG', 'INDY']
telecom = ['TLKM', 'ISAT', 'EXCL']
consumer = ['UNTR', 'ASII', 'ICBP', 'INDF']

sectors = {
    'Banking': banking_stocks,
    'Coal/Mining': coal_mining,
    'Telecom': telecom,
    'Consumer/Auto': consumer
}

for sector_name, stocks in sectors.items():
    sector_may_june = may_june[may_june['stock_code'].isin(stocks)]
    if len(sector_may_june) > 0:
        payers = sector_may_june['stock_code'].unique()
        avg_amount = sector_may_june['dividend_amount_numeric'].mean()
        total_payments = len(sector_may_june)
        print(f"\n{sector_name}:")
        print(f"  Payers: {', '.join(payers)}")
        print(f"  Total Payments: {total_payments}")
        print(f"  Average Amount: {avg_amount:,.0f} IDR")

print("\n" + "="*85)
print("CONCLUSION & 2026 RECOMMENDATIONS:")
print("="*85)

# Find top stocks most likely to pay in May/June 2026
may_2026_likely = recent_payers[recent_payers['payment_month'] == 5]['stock_code'].value_counts().head(10)
jun_2026_likely = recent_payers[recent_payers['payment_month'] == 6]['stock_code'].value_counts().head(10)

# Count your tracked stocks that are likely to pay
your_stocks_likely = [s for s in tracked_stocks if s in recent_stock_freq[recent_stock_freq >= 2].index]

print(f"""
🗓️ MAY 2026 HIGH PROBABILITY PAYERS:
   Top 10: {', '.join(may_2026_likely.index.tolist())}
   
🗓️ JUNE 2026 HIGH PROBABILITY PAYERS:
   Top 10: {', '.join(jun_2026_likely.index.tolist())}

💰 YOUR PORTFOLIO - Expected May/Jun 2026 Dividends:
   Stocks likely to pay: {', '.join(your_stocks_likely) if your_stocks_likely else 'None found in May/June pattern'}
   
⏰ KEY DATES FOR MAY/JUNE 2026:
   - Mar 15-31: Most companies hold AGM (Annual General Meeting)
   - Apr 1-15: Dividend announcements post-AGM
   - Apr 20-30: Ex-dividend dates (buy before this to get dividend!)
   - May 5-25: Peak payment period (most dividends paid)
   - Jun 1-20: Second wave of payments
   
💡 STRATEGY:
   1. Watch for AGM announcements in March (check IDX announcements)
   2. Buy dividend stocks 1-2 weeks before ex-date
   3. Banking sector (BBRI, BMRI) typically pays in May
   4. Coal sector (ADRO, PTBA) timing varies but often May-June
   5. Hold until payment date (usually 2-4 weeks after ex-date)
   
🎯 ACTION PLAN FOR DIVIDEND HARVEST:
   - Now-Feb: Accumulate dividend stocks with foreign support (ADRO, BBRI)
   - March: Monitor AGM announcements
   - Late April: Last chance to buy before ex-dates
   - May-June: Collect dividends + evaluate capital gains
""")

print("="*85)

# Save full list for reference
may_june_sorted = may_june.sort_values(['payment_date', 'dividend_amount_numeric'], ascending=[False, False])
may_june_sorted.to_csv('results/20260122_may_june_dividend_stocks.csv', index=False)

# Create a focused list for portfolio stocks
portfolio_may_june = may_june[may_june['stock_code'].isin(tracked_stocks)].sort_values('payment_date', ascending=False)
portfolio_may_june.to_csv('results/20260122_portfolio_may_june_dividends.csv', index=False)

print(f"✓ Full list saved to: results/20260122_may_june_dividend_stocks.csv")
print(f"✓ Portfolio-focused list saved to: results/20260122_portfolio_may_june_dividends.csv")
print("="*85)
