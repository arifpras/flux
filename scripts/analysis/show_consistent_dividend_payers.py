#!/usr/bin/env python3
"""
Display stocks that consistently paid dividends in the last 3 years (2023-2025)
"""

import pandas as pd

# Load the consistent dividend payers
df = pd.read_csv('results/20260122_consistent_dividend_payers.csv')

print('='*100)
print('STOCKS THAT CONSISTENTLY PAID DIVIDENDS IN THE LAST 3 YEARS (2023-2025)')
print('='*100)
print(f'\nTotal stocks found: {len(df)}')

# Clean up the years_paid column for better display
df['years_paid'] = df['years_paid'].astype(str)

# Calculate average per payment
df['avg_per_payment'] = df['total_3y_dividend'] / df['payment_count']
df['yield_per_payment'] = df['dividend_yield'] / df['payment_count']

print('\n' + '='*100)
print('TOP 30 CONSISTENT DIVIDEND PAYERS (Sorted by Dividend Yield)')
print('='*100)
print(f"{'Rank':<6} {'Stock':<8} {'Annual':<12} {'Price':<10} {'Yield %':<10} {'Payments':<10} {'Avg/Payment':<14} {'Yield/Pay':<12}")
print('-'*100)

for idx, row in df.head(30).iterrows():
    rank = idx + 1
    price = f"{row['current_price']:.0f}" if pd.notna(row['current_price']) else 'N/A'
    yield_pct = f"{row['dividend_yield']:.2f}" if pd.notna(row['dividend_yield']) else 'N/A'
    avg_payment = f"{row['avg_per_payment']:.0f}" if pd.notna(row['avg_per_payment']) else 'N/A'
    yield_payment = f"{row['yield_per_payment']:.2f}%" if pd.notna(row['yield_per_payment']) else 'N/A'
    
    print(f"{rank:<6} {row['stock_code']:<8} {row['annual_avg_dividend']:>11,.0f} {price:>9} {yield_pct:>9} {int(row['payment_count']):>9} {avg_payment:>13} {yield_payment:>11}")

print('\n' + '='*100)
print('STATISTICS BY DIVIDEND YIELD RANGE')
print('='*100)

# Filter out NaN yields for statistics
df_with_yield = df[df['dividend_yield'].notna()]

ranges = [
    ('> 15%', df_with_yield[df_with_yield['dividend_yield'] > 15]),
    ('10-15%', df_with_yield[(df_with_yield['dividend_yield'] >= 10) & (df_with_yield['dividend_yield'] <= 15)]),
    ('5-10%', df_with_yield[(df_with_yield['dividend_yield'] >= 5) & (df_with_yield['dividend_yield'] < 10)]),
    ('< 5%', df_with_yield[df_with_yield['dividend_yield'] < 5])
]

for range_name, range_df in ranges:
    if len(range_df) > 0:
        print(f'\n{range_name}: {len(range_df)} stocks')
        if len(range_df) <= 10:
            print(f"  Stocks: {', '.join(range_df['stock_code'].tolist())}")
        else:
            print(f"  Top 10: {', '.join(range_df.head(10)['stock_code'].tolist())}")

print('\n' + '='*100)
print('SUMMARY STATISTICS')
print('='*100)
print(f'Total consistent payers (2023-2025): {len(df)} stocks')
print(f'Stocks with price data: {df["current_price"].notna().sum()} stocks')
print(f'Average dividend yield: {df["dividend_yield"].mean():.2f}%')
print(f'Median dividend yield: {df["dividend_yield"].median():.2f}%')
highest_yield_idx = df['dividend_yield'].idxmax()
print(f'Highest dividend yield: {df.loc[highest_yield_idx, "dividend_yield"]:.2f}% ({df.loc[highest_yield_idx, "stock_code"]})')
print(f'Average annual dividend: IDR {df["annual_avg_dividend"].mean():,.0f}')

# Show some additional insights
print('\n' + '='*100)
print('ADDITIONAL INSIGHTS')
print('='*100)

print('\nNote: Avg/Payment = Average dividend amount per payment')
print('      Yield/Pay = Average yield percentage per payment (Total Yield / Number of Payments)')
print('      This helps compare stocks with different payment frequencies.')

# Most frequent payers
most_payments = df.nlargest(10, 'payment_count')
print('\nTop 10 by Payment Frequency (most payments in 3 years):')
for idx, row in most_payments.iterrows():
    yield_per = f"{row['yield_per_payment']:.2f}%" if pd.notna(row['yield_per_payment']) else 'N/A'
    print(f"  {row['stock_code']:<8} - {int(row['payment_count'])} payments ({yield_per} per payment)")

# Highest absolute dividends
highest_div = df.nlargest(10, 'annual_avg_dividend')
print('\nTop 10 by Annual Dividend Amount:')
for idx, row in highest_div.iterrows():
    print(f"  {row['stock_code']:<8} - IDR {row['annual_avg_dividend']:>12,.0f}")

print('\n' + '='*100)
print(f'\nFull data is available in: results/20260122_consistent_dividend_payers.csv')
print('='*100)
