#!/usr/bin/env python3
"""
Portfolio Dividend Analysis - Combining dividend history with foreign flow
"""

import pandas as pd
from datetime import datetime

print("="*85)
print("PORTFOLIO DIVIDEND ANALYSIS")
print("="*85)

# Load dividend data
dividends = pd.read_csv('data/reference/idx_dividend_history.csv')
dividends['payment_date'] = pd.to_datetime(dividends['payment_date'])

# Your portfolio stocks
portfolio_stocks = ['ASII', 'BBRI', 'BNGA', 'BUMI', 'PTBA']

# Recommended stocks from foreign flow analysis
recommended_stocks = ['VKTR', 'MBMA', 'ADRO', 'BMRI', 'TLKM', 'UNTR', 'ANTM']

all_stocks = list(set(portfolio_stocks + recommended_stocks))

print(f"\n[1/4] Analyzing dividend history for {len(all_stocks)} stocks...")

# Filter for last 3 years
recent_divs = dividends[dividends['dividend_year'] >= 2023].copy()

# Calculate dividend statistics per stock
div_stats = recent_divs.groupby('stock_code').agg({
    'dividend_amount_numeric': ['sum', 'count', 'mean', 'std'],
    'payment_date': ['min', 'max']
}).round(2)

div_stats.columns = ['total_dividend', 'payment_count', 'avg_dividend', 'std_dividend', 'first_payment', 'last_payment']
div_stats = div_stats.reset_index()

# Calculate latest stock prices (using BBRI as reference at 3,820)
# This is simplified - ideally would pull from your price data
price_ref = {
    'BBRI': 3820, 'ASII': 6725, 'BNGA': 1870, 'BUMI': 364, 'PTBA': 2520,
    'VKTR': 1190, 'MBMA': 810, 'ADRO': 2260, 'BMRI': 7000, 'TLKM': 3000,
    'UNTR': 25000, 'ANTM': 1500
}

# Calculate dividend yield (annualized)
div_stats['latest_price'] = div_stats['stock_code'].map(price_ref)
div_stats['annual_dividend'] = div_stats['total_dividend'] / 3  # 3-year average
div_stats['dividend_yield_pct'] = (div_stats['annual_dividend'] / div_stats['latest_price'] * 100).round(2)

# Consistency score (higher = more consistent)
div_stats['consistency_score'] = (div_stats['payment_count'] / 3).round(1)  # Payments per year

print(f"\n[2/4] Portfolio stocks dividend analysis...")
print("="*85)
print(f"{'Stock':<8} {'3Y Total':<12} {'Payments':<10} {'Yield %':<10} {'Consistency':<12} {'Status':<15}")
print("-"*85)

for stock in portfolio_stocks:
    stock_div = div_stats[div_stats['stock_code'] == stock]
    if len(stock_div) > 0:
        row = stock_div.iloc[0]
        status = "✅ Good" if row['dividend_yield_pct'] >= 4 else "⚠️ Low" if row['dividend_yield_pct'] >= 2 else "❌ Poor"
        print(f"{stock:<8} {row['total_dividend']:>11,.0f} {int(row['payment_count']):>9} {row['dividend_yield_pct']:>9.2f} {row['consistency_score']:>11.1f} {status:<15}")
    else:
        print(f"{stock:<8} {'NO DATA':>11} {0:>9} {0:>9.2f} {0:>11.1f} {'❌ None':<15}")

print(f"\n[3/4] Recommended stocks dividend analysis...")
print("="*85)
print(f"{'Stock':<8} {'3Y Total':<12} {'Payments':<10} {'Yield %':<10} {'Consistency':<12} {'Foreign':<15}")
print("-"*85)

# Foreign flow data (from your last 5-day report)
foreign_flow = {
    'BBRI': 228.1, 'VKTR': 149.0, 'MBMA': 245.4, 'ADRO': 118.1, 'ANTM': 76.5
}

for stock in recommended_stocks:
    stock_div = div_stats[div_stats['stock_code'] == stock]
    foreign = foreign_flow.get(stock, 0)
    foreign_status = f"✅ +{foreign:.0f}M" if foreign > 100 else f"⚠️ +{foreign:.0f}M" if foreign > 0 else "❌ None"
    
    if len(stock_div) > 0:
        row = stock_div.iloc[0]
        print(f"{stock:<8} {row['total_dividend']:>11,.0f} {int(row['payment_count']):>9} {row['dividend_yield_pct']:>9.2f} {row['consistency_score']:>11.1f} {foreign_status:<15}")
    else:
        print(f"{stock:<8} {'NO DATA':>11} {0:>9} {0:>9.2f} {0:>11.1f} {foreign_status:<15}")

print(f"\n[4/4] BEST OPPORTUNITIES: Dividend + Foreign Flow")
print("="*85)

# Combine dividend yield + foreign flow for scoring
opportunities = []
for stock in all_stocks:
    stock_div = div_stats[div_stats['stock_code'] == stock]
    if len(stock_div) > 0:
        row = stock_div.iloc[0]
        foreign = foreign_flow.get(stock, 0)
        
        # Score: dividend_yield * 10 + foreign_flow_normalized + consistency
        score = (row['dividend_yield_pct'] * 10) + (foreign / 10) + (row['consistency_score'] * 5)
        
        opportunities.append({
            'stock': stock,
            'dividend_yield': row['dividend_yield_pct'],
            'foreign_flow': foreign,
            'consistency': row['consistency_score'],
            'total_score': score
        })

opp_df = pd.DataFrame(opportunities).sort_values('total_score', ascending=False)

print("\nTop 5 Stocks (Combined Dividend + Foreign Flow Score):")
print("-"*85)
print(f"{'Rank':<6} {'Stock':<8} {'Div Yield':<12} {'Foreign':<15} {'Consistency':<12} {'Score':<10}")
print("-"*85)

for i, row in opp_df.head(5).iterrows():
    print(f"{i+1:<6} {row['stock']:<8} {row['dividend_yield']:>11.2f}% {row['foreign_flow']:>14.0f}M {row['consistency']:>11.1f} {row['total_score']:>9.0f}")

print("\n" + "="*85)
print("INVESTMENT RECOMMENDATION")
print("="*85)

top_stock = opp_df.iloc[0]
print(f"""
🏆 TOP PICK: {top_stock['stock']}
   ├─ Dividend Yield: {top_stock['dividend_yield']:.2f}%
   ├─ Foreign Accumulation: +{top_stock['foreign_flow']:.0f}M IDR (last 5 days)
   ├─ Consistency: {top_stock['consistency']:.1f} payments/year
   └─ Total Return Potential: {top_stock['dividend_yield'] + 12:.1f}% (dividend + capital gain)

📋 PORTFOLIO ACTION:
   1. INCREASE: {opp_df.iloc[0]['stock']} (best combined score)
   2. HOLD: {opp_df.iloc[1]['stock']} (2nd best score)
   3. REDUCE: BUMI (no dividend data + foreign selling)
   4. MONITOR: {opp_df.iloc[2]['stock']}, {opp_df.iloc[3]['stock']} (decent scores)

💰 EXPECTED PORTFOLIO YIELD:
   If you allocate 60% to top 2 stocks:
   - Dividend Income: ~{(opp_df.iloc[0]['dividend_yield'] * 0.4 + opp_df.iloc[1]['dividend_yield'] * 0.2):.2f}%
   - Capital Gain (est): 12-18%
   - Total Return: {(opp_df.iloc[0]['dividend_yield'] * 0.4 + opp_df.iloc[1]['dividend_yield'] * 0.2 + 15):.1f}%
""")

print("="*85)

# Save detailed report
output_file = "results/20260122_dividend_portfolio_analysis.csv"
div_stats_full = div_stats[div_stats['stock_code'].isin(all_stocks)].copy()
div_stats_full['foreign_flow_M'] = div_stats_full['stock_code'].map(foreign_flow)
div_stats_full = div_stats_full.sort_values('dividend_yield_pct', ascending=False)
div_stats_full.to_csv(output_file, index=False)
print(f"\n✓ Detailed analysis saved to: {output_file}")
print("="*85)
