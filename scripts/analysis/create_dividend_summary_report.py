#!/usr/bin/env python3
"""
Create a detailed summary report of consistent dividend payers
"""

import pandas as pd
from datetime import datetime

# Load the consistent dividend payers
df = pd.read_csv('results/20260122_consistent_dividend_payers.csv')

# Calculate average per payment
df['avg_per_payment'] = df['total_3y_dividend'] / df['payment_count']
df['yield_per_payment'] = df['dividend_yield'] / df['payment_count']

# Create output file
output_file = f'results/{datetime.now().strftime("%Y%m%d")}_CONSISTENT_DIVIDEND_REPORT.txt'

with open(output_file, 'w') as f:
    f.write('='*100 + '\n')
    f.write('STOCKS THAT CONSISTENTLY PAID DIVIDENDS IN THE LAST 3 YEARS (2023-2025)\n')
    f.write('='*100 + '\n')
    f.write(f'\nGenerated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write(f'Total stocks found: {len(df)}\n')
    f.write(f'Data source: results/20260122_consistent_dividend_payers.csv\n')
    
    # Summary Statistics
    f.write('\n' + '='*100 + '\n')
    f.write('SUMMARY STATISTICS\n')
    f.write('='*100 + '\n')
    f.write(f'Total consistent payers (2023-2025): {len(df)} stocks\n')
    f.write(f'Stocks with price data: {df["current_price"].notna().sum()} stocks\n')
    f.write(f'Average dividend yield: {df["dividend_yield"].mean():.2f}%\n')
    f.write(f'Median dividend yield: {df["dividend_yield"].median():.2f}%\n')
    highest_yield_idx = df['dividend_yield'].idxmax()
    f.write(f'Highest dividend yield: {df.loc[highest_yield_idx, "dividend_yield"]:.2f}% ({df.loc[highest_yield_idx, "stock_code"]})\n')
    f.write(f'Average annual dividend: IDR {df["annual_avg_dividend"].mean():,.0f}\n')
    f.write(f'Average payment frequency: {df["payment_count"].mean():.1f} times in 3 years\n')
    f.write(f'Average yield per payment: {df["yield_per_payment"].mean():.2f}%\n')
    f.write(f'Average amount per payment: IDR {df["avg_per_payment"].mean():,.0f}\n')
    
    # Distribution by yield range
    f.write('\n' + '='*100 + '\n')
    f.write('DISTRIBUTION BY DIVIDEND YIELD RANGE\n')
    f.write('='*100 + '\n')
    
    df_with_yield = df[df['dividend_yield'].notna()]
    
    ranges = [
        ('Excellent (>15%)', df_with_yield[df_with_yield['dividend_yield'] > 15]),
        ('Good (10-15%)', df_with_yield[(df_with_yield['dividend_yield'] >= 10) & (df_with_yield['dividend_yield'] <= 15)]),
        ('Fair (5-10%)', df_with_yield[(df_with_yield['dividend_yield'] >= 5) & (df_with_yield['dividend_yield'] < 10)]),
        ('Low (<5%)', df_with_yield[df_with_yield['dividend_yield'] < 5])
    ]
    
    for range_name, range_df in ranges:
        f.write(f'\n{range_name}: {len(range_df)} stocks\n')
    
    # Top 50 by dividend yield
    f.write('\n' + '='*100 + '\n')
    f.write('TOP 50 STOCKS BY DIVIDEND YIELD\n')
    f.write('='*100 + '\n')
    f.write(f"{'Rank':<6} {'Stock':<8} {'Annual Div':<13} {'Price':<10} {'Yield %':<10} {'Pay#':<6} {'Yield/Pay':<11} {'Avg/Pay':<12}\n")
    f.write('-'*100 + '\n')
    
    for idx, row in df.head(50).iterrows():
        rank = idx + 1
        price = f"{row['current_price']:,.0f}" if pd.notna(row['current_price']) else 'N/A'
        yield_pct = f"{row['dividend_yield']:.2f}%" if pd.notna(row['dividend_yield']) else 'N/A'
        yield_per = f"{row['yield_per_payment']:.2f}%" if pd.notna(row['yield_per_payment']) else 'N/A'
        avg_per = f"{row['avg_per_payment']:,.0f}" if pd.notna(row['avg_per_payment']) else 'N/A'
        
        f.write(f"{rank:<6} {row['stock_code']:<8} {row['annual_avg_dividend']:>12,.0f} {price:>9} {yield_pct:>9} {int(row['payment_count']):>5} {yield_per:>10} {avg_per:>11}\n")
    
    # High yield stocks (>15%)
    f.write('\n' + '='*100 + '\n')
    f.write('EXCELLENT DIVIDEND YIELD (>15%) - DETAILED LIST\n')
    f.write('='*100 + '\n')
    
    high_yield = df[df['dividend_yield'] > 15].sort_values('dividend_yield', ascending=False)
    f.write(f'\nTotal: {len(high_yield)} stocks\n\n')
    
    for idx, row in high_yield.iterrows():
        f.write(f"{row['stock_code']:<8} - {row['dividend_yield']:.2f}% yield\n")
        f.write(f"  Annual dividend: IDR {row['annual_avg_dividend']:,.0f}\n")
        f.write(f"  Current price: IDR {row['current_price']:,.0f}\n" if pd.notna(row['current_price']) else "  Current price: N/A\n")
        f.write(f"  Payment count: {int(row['payment_count'])} times in 3 years\n")
        f.write(f"  Avg per payment: IDR {row['avg_per_payment']:,.0f} ({row['yield_per_payment']:.2f}% yield per payment)\n")
        f.write(f"  Payment months: {row['payment_months']}\n")
        f.write(f"  Last payment: {row['last_payment']}\n\n")
    
    # Good yield stocks (10-15%)
    f.write('\n' + '='*100 + '\n')
    f.write('GOOD DIVIDEND YIELD (10-15%) - DETAILED LIST\n')
    f.write('='*100 + '\n')
    
    good_yield = df[(df['dividend_yield'] >= 10) & (df['dividend_yield'] <= 15)].sort_values('dividend_yield', ascending=False)
    f.write(f'\nTotal: {len(good_yield)} stocks\n\n')
    
    for idx, row in good_yield.iterrows():
        f.write(f"{row['stock_code']:<8} - {row['dividend_yield']:.2f}% yield\n")
        f.write(f"  Annual dividend: IDR {row['annual_avg_dividend']:,.0f}\n")
        f.write(f"  Current price: IDR {row['current_price']:,.0f}\n" if pd.notna(row['current_price']) else "  Current price: N/A\n")
        f.write(f"  Payment count: {int(row['payment_count'])} times in 3 years\n")
        f.write(f"  Avg per payment: IDR {row['avg_per_payment']:,.0f} ({row['yield_per_payment']:.2f}% yield per payment)\n")
        f.write(f"  Payment months: {row['payment_months']}\n")
        f.write(f"  Last payment: {row['last_payment']}\n\n")
    
    # Most frequent payers
    f.write('\n' + '='*100 + '\n')
    f.write('TOP 20 BY PAYMENT FREQUENCY (Most Payments in 3 Years)\n')
    f.write('='*100 + '\n\n')
    
    most_payments = df.nlargest(20, 'payment_count')
    for idx, row in most_payments.iterrows():
        f.write(f"{row['stock_code']:<8} - {int(row['payment_count'])} payments ({row['dividend_yield']:.2f}% yield)\n")
    
    # Highest absolute dividends
    f.write('\n' + '='*100 + '\n')
    f.write('TOP 20 BY ANNUAL DIVIDEND AMOUNT\n')
    f.write('='*100 + '\n\n')
    
    highest_div = df.nlargest(20, 'annual_avg_dividend')
    for idx, row in highest_div.iterrows():
        f.write(f"{row['stock_code']:<8} - IDR {row['annual_avg_dividend']:>14,.0f} ({row['dividend_yield']:.2f}% yield)\n")
    
    # All stocks list
    f.write('\n' + '='*100 + '\n')
    f.write('COMPLETE LIST OF ALL CONSISTENT DIVIDEND PAYERS\n')
    f.write('='*100 + '\n\n')
    
    f.write(f"{'Stock':<8} {'Annual Div':<15} {'Price':<12} {'Yield %':<10} {'Payments':<10}\n")
    f.write('-'*100 + '\n')
    
    for idx, row in df.iterrows():
        price = f"{row['current_price']:,.0f}" if pd.notna(row['current_price']) else 'N/A'
        yield_pct = f"{row['dividend_yield']:.2f}%" if pd.notna(row['dividend_yield']) else 'N/A'
        
        f.write(f"{row['stock_code']:<8} {row['annual_avg_dividend']:>14,.0f} {price:>11} {yield_pct:>9} {int(row['payment_count']):>9}\n")
    
    f.write('\n' + '='*100 + '\n')
    f.write('END OF REPORT\n')
    f.write('='*100 + '\n')

print(f'✓ Detailed report saved to: {output_file}')
print(f'\nKey findings:')
print(f'  - {len(df)} stocks paid dividends consistently (2023-2025)')
print(f'  - {len(df[df["dividend_yield"] > 15])} stocks with excellent yield (>15%)')
print(f'  - {len(df[(df["dividend_yield"] >= 10) & (df["dividend_yield"] <= 15)])} stocks with good yield (10-15%)')
print(f'  - Average yield: {df["dividend_yield"].mean():.2f}%')
print(f'  - Best performer: {df.loc[df["dividend_yield"].idxmax(), "stock_code"]} ({df["dividend_yield"].max():.2f}% yield)')
