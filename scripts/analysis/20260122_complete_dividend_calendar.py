#!/usr/bin/env python3
"""
Complete dividend analysis by month - All IDX stocks ranked by dividend yield
"""

import pandas as pd
import numpy as np

print("="*100)
print("COMPLETE DIVIDEND CALENDAR - ALL IDX STOCKS BY MONTH (Ranked by Dividend Yield)")
print("="*100)

# Load dividend data
dividends = pd.read_csv('data/reference/idx_dividend_history.csv')
dividends['payment_date'] = pd.to_datetime(dividends['payment_date'])
dividends['payment_month'] = dividends['payment_date'].dt.month
dividends['payment_year'] = dividends['payment_date'].dt.year

# Load price data for yield calculation (close price from Ringkasan Saham-20260122.xlsx)
try:
    price_path = 'data/histories/Ringkasan Saham-20260122.xlsx'
    price_data = pd.read_excel(price_path, usecols=['Kode Saham', 'Penutupan'])
    price_data = price_data.rename(columns={'Kode Saham': 'Code', 'Penutupan': 'Last'})
    price_data = price_data.dropna(subset=['Code', 'Last'])
    price_dict = dict(zip(price_data['Code'], price_data['Last']))
    print(f"Loaded {len(price_dict)} prices from {price_path}")
except Exception as exc:  # noqa: BLE001
    print(f"⚠️  Could not load price data ({exc}), will use dividend amounts only")
    price_dict = {}

# Filter for last 3 years only
recent_divs = dividends[dividends['dividend_year'] >= 2023].copy()

print(f"\nData Summary:")
print(f"  Total dividend payments (2023-2026): {len(recent_divs)}")
print(f"  Unique stocks with dividends: {recent_divs['stock_code'].nunique()}")
print(f"  Date range: {recent_divs['payment_date'].min().strftime('%Y-%m-%d')} to {recent_divs['payment_date'].max().strftime('%Y-%m-%d')}")

# Calculate statistics per stock per month
monthly_stats = recent_divs.groupby(['stock_code', 'payment_month']).agg({
    'dividend_amount_numeric': ['sum', 'count', 'mean'],
    'payment_date': 'max'
}).reset_index()

monthly_stats.columns = ['stock_code', 'payment_month', 'total_dividend', 'payment_count', 'avg_dividend', 'last_payment']

# Add price and calculate yield
monthly_stats['current_price'] = monthly_stats['stock_code'].map(price_dict)

# If we don't have price, estimate yield score based on dividend amount only
monthly_stats['dividend_yield'] = np.where(
    monthly_stats['current_price'].notna() & (monthly_stats['current_price'] > 0),
    (monthly_stats['avg_dividend'] / monthly_stats['current_price'] * 100),
    np.nan
)

# Create a consistency score for ranking
monthly_stats['consistency_score'] = monthly_stats['payment_count'] / 3  # payments per year
monthly_stats['yield_score'] = monthly_stats['dividend_yield'].fillna(monthly_stats['avg_dividend'] / 100)

month_names = {
    1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL',
    5: 'MAY', 6: 'JUNE', 7: 'JULY', 8: 'AUGUST',
    9: 'SEPTEMBER', 10: 'OCTOBER', 11: 'NOVEMBER', 12: 'DECEMBER'
}

# Analyze each month
for month_num in range(1, 13):
    month_data = monthly_stats[monthly_stats['payment_month'] == month_num].copy()
    
    if len(month_data) == 0:
        print(f"\n{'='*100}")
        print(f"{month_names[month_num]} - NO DIVIDEND PAYMENTS FOUND")
        print(f"{'='*100}")
        continue
    
    # Sort by yield (or dividend amount if no yield available)
    month_data = month_data.sort_values(['dividend_yield', 'avg_dividend'], ascending=[False, False])
    
    print(f"\n{'='*100}")
    print(f"{month_names[month_num]} - {len(month_data)} Stocks Pay Dividends")
    print(f"{'='*100}")
    print(f"{'Rank':<6} {'Stock':<8} {'Avg Div':<12} {'Price':<10} {'Yield %':<10} {'Payments':<10} {'Last Payment':<15}")
    print("-"*100)
    
    # Show top 20 or all if less than 20
    display_count = min(20, len(month_data))
    
    for idx, (i, row) in enumerate(month_data.head(display_count).iterrows(), 1):
        price_str = f"{row['current_price']:,.0f}" if pd.notna(row['current_price']) else "N/A"
        yield_str = f"{row['dividend_yield']:.2f}" if pd.notna(row['dividend_yield']) else "N/A"
        last_pay = pd.to_datetime(row['last_payment']).strftime('%Y-%m-%d')
        
        print(f"{idx:<6} {row['stock_code']:<8} {row['avg_dividend']:>11,.0f} {price_str:>9} {yield_str:>9} {int(row['payment_count']):>9} {last_pay:<15}")
    
    if len(month_data) > display_count:
        print(f"... and {len(month_data) - display_count} more stocks")
    
    # Show summary statistics for the month
    total_stocks = len(month_data)
    avg_dividend = month_data['avg_dividend'].mean()
    max_dividend = month_data['avg_dividend'].max()
    
    print(f"\n{month_names[month_num]} Summary:")
    print(f"  Total stocks paying: {total_stocks}")
    print(f"  Average dividend: {avg_dividend:,.0f} IDR")
    print(f"  Highest dividend: {max_dividend:,.0f} IDR")
    if month_data['dividend_yield'].notna().sum() > 0:
        avg_yield = month_data['dividend_yield'].mean()
        max_yield = month_data['dividend_yield'].max()
        print(f"  Average yield: {avg_yield:.2f}%")
        print(f"  Highest yield: {max_yield:.2f}%")

# Create overall summary
print(f"\n{'='*100}")
print("ANNUAL DIVIDEND CALENDAR SUMMARY")
print(f"{'='*100}")

monthly_summary = monthly_stats.groupby('payment_month').agg({
    'stock_code': 'count',
    'avg_dividend': 'mean',
    'dividend_yield': 'mean'
}).reset_index()

monthly_summary.columns = ['month', 'stock_count', 'avg_dividend', 'avg_yield']
monthly_summary['month_name'] = monthly_summary['month'].map(month_names)

print(f"\n{'Month':<15} {'# Stocks':<12} {'Avg Dividend':<18} {'Avg Yield':<15}")
print("-"*100)

for _, row in monthly_summary.iterrows():
    yield_str = f"{row['avg_yield']:.2f}%" if pd.notna(row['avg_yield']) else "N/A"
    print(f"{row['month_name']:<15} {int(row['stock_count']):>11} {row['avg_dividend']:>17,.0f} {yield_str:>14}")

# Identify peak months
peak_month = monthly_summary.loc[monthly_summary['stock_count'].idxmax()]
print(f"\n🏆 PEAK DIVIDEND MONTH: {peak_month['month_name']} ({int(peak_month['stock_count'])} stocks)")

# Top dividend payers overall
print(f"\n{'='*100}")
print("TOP 30 DIVIDEND YIELDS - ALL STOCKS (regardless of payment month)")
print(f"{'='*100}")

# Calculate annual dividend per stock (sum across all months)
annual_divs = recent_divs.groupby('stock_code').agg({
    'dividend_amount_numeric': ['sum', 'count'],
    'payment_date': 'max',
    'payment_month': lambda x: ', '.join(month_names[m][:3] for m in sorted(x.unique())),
    'payment_year': lambda x: sorted(x.unique())
}).reset_index()

annual_divs.columns = ['stock_code', 'total_3y_dividend', 'payment_count', 'last_payment', 'payment_months', 'payment_years']
annual_divs['annual_avg_dividend'] = annual_divs['total_3y_dividend'] / 3  # Average per year
annual_divs['current_price'] = annual_divs['stock_code'].map(price_dict)
annual_divs['dividend_yield'] = np.where(
    annual_divs['current_price'].notna() & (annual_divs['current_price'] > 0),
    (annual_divs['annual_avg_dividend'] / annual_divs['current_price'] * 100),
    np.nan
)

annual_divs = annual_divs.sort_values(['dividend_yield', 'annual_avg_dividend'], ascending=[False, False])

print(f"{'Rank':<6} {'Stock':<8} {'Annual Div':<15} {'Price':<10} {'Yield %':<10} {'Payments':<10} {'Months':<20}")
print("-"*100)

for idx, (i, row) in enumerate(annual_divs.head(30).iterrows(), 1):
    price_str = f"{row['current_price']:,.0f}" if pd.notna(row['current_price']) else "N/A"
    yield_str = f"{row['dividend_yield']:.2f}" if pd.notna(row['dividend_yield']) else "N/A"
    
    print(f"{idx:<6} {row['stock_code']:<8} {row['annual_avg_dividend']:>14,.0f} {price_str:>9} {yield_str:>9} {int(row['payment_count']):>9} {row['payment_months']:<20}")

print(f"\n{'='*100}")

# Consistent payers (at least one dividend in 2023, 2024, 2025)
required_years = {2023, 2024, 2025}
annual_divs['years_paid'] = annual_divs['payment_years'].apply(set)
consistent_payers = annual_divs[annual_divs['years_paid'].apply(lambda yrs: required_years.issubset(yrs))]

print("CONSISTENT PAYERS (paid every year 2023-2025) - Top 20 by yield")
print("-"*100)
print(f"{'Rank':<6} {'Stock':<8} {'Annual Div':<15} {'Price':<10} {'Yield %':<10} {'Years':<12} {'Months':<20}")

for idx, (i, row) in enumerate(consistent_payers.head(20).iterrows(), 1):
    price_str = f"{row['current_price']:,.0f}" if pd.notna(row['current_price']) else "N/A"
    yield_str = f"{row['dividend_yield']:.2f}" if pd.notna(row['dividend_yield']) else "N/A"
    years_str = ','.join(str(y) for y in sorted(row['years_paid']))
    print(f"{idx:<6} {row['stock_code']:<8} {row['annual_avg_dividend']:>14,.0f} {price_str:>9} {yield_str:>9} {years_str:<12} {row['payment_months']:<20}")

# Save detailed reports
output_by_month = 'results/20260122_dividend_calendar_by_month.csv'
output_annual = 'results/20260122_top_dividend_yields_annual.csv'
output_consistent = 'results/20260122_consistent_dividend_payers.csv'

monthly_stats.to_csv(output_by_month, index=False)
annual_divs.to_csv(output_annual, index=False)
consistent_payers.to_csv(output_consistent, index=False)

print(f"\n✓ Monthly dividend calendar saved to: {output_by_month}")
print(f"✓ Annual dividend rankings saved to: {output_annual}")
print(f"✓ Consistent payers (2023-2025) saved to: {output_consistent}")
print(f"{'='*100}")
