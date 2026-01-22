import os
from datetime import datetime
from pathlib import Path
import pandas as pd

# Configuration: accumulation calculation mode
# - 'positive_sum': sum of positive foreign and domestic nets (default)
# - 'foreign_only': use only positive foreign net
# - 'true_total': foreign net + domestic net (requires real domestic data)
ACCUMULATION_MODE = os.environ.get('ACCUMULATION_MODE', 'positive_sum')
DOMESTIC_FLOWS_FILE = os.environ.get('DOMESTIC_FLOWS_FILE', 'data/manual/domestic_flows_5d.csv')

df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")

# Convert date to datetime
df['SourceDate'] = pd.to_datetime(df['SourceDate'])

# Get last 5 trading days
dates = sorted(df['SourceDate'].unique())[-5:]

print("=" * 150)
print("5-DAY INSTITUTIONAL ANALYSIS: FOREIGN vs DOMESTIC DIVERGENCE")
print(f"Period: {dates[0].strftime('%B %d, %Y')} - {dates[-1].strftime('%B %d, %Y')}")
print("=" * 150)

# Filter for last 5 days
df_5d = df[df['SourceDate'].isin(dates)]

# Aggregate by stock and institution type
stocks = df_5d.groupby('Kode Saham').agg({
    'Foreign Buy': 'sum',
    'Foreign Sell': 'sum',
    'Volume': 'sum',
    'Penutupan': 'first',
    'Nama Perusahaan': 'first'
}).reset_index()

stocks.columns = ['Stock', 'Foreign_Buy', 'Foreign_Sell', 'Total_Volume', 'Price_Latest', 'Company']

# Get prices at period start and end
price_start = df_5d[df_5d['SourceDate'] == dates[0]].groupby('Kode Saham')['Penutupan'].first()
price_end = df_5d[df_5d['SourceDate'] == dates[-1]].groupby('Kode Saham')['Penutupan'].first()

stocks['Price_Start'] = stocks['Stock'].map(price_start)
stocks['Price_End'] = stocks['Stock'].map(price_end)
stocks['Price_Change'] = stocks['Price_End'] - stocks['Price_Start']
stocks['Price_Change_Pct'] = (stocks['Price_Change'] / stocks['Price_Start'] * 100).fillna(0)

stocks['Net_Foreign'] = stocks['Foreign_Buy'] - stocks['Foreign_Sell']

# Calculate domestic as total - foreign
domestic_source = 'synthetic'
try:
    manual_path = Path(DOMESTIC_FLOWS_FILE)
    if manual_path.exists():
        dom_df = pd.read_csv(manual_path)
        # Normalize columns
        if 'SourceDate' in dom_df.columns:
            dom_df['SourceDate'] = pd.to_datetime(dom_df['SourceDate'])
            dom_df = dom_df[dom_df['SourceDate'].isin(dates)]
        # Support either 'Kode Saham' or 'Stock'
        if 'Kode Saham' in dom_df.columns and 'Stock' not in dom_df.columns:
            dom_df = dom_df.rename(columns={'Kode Saham': 'Stock'})
        # Aggregate if needed
        group_cols = ['Stock']
        sum_cols = []
        if 'Domestic Buy' in dom_df.columns:
            sum_cols.append('Domestic Buy')
        if 'Domestic Sell' in dom_df.columns:
            sum_cols.append('Domestic Sell')
        if len(sum_cols) >= 2:
            dom_agg = dom_df.groupby(group_cols)[sum_cols].sum().reset_index()
            # Merge into stocks
            stocks = stocks.merge(dom_agg, on='Stock', how='left')
            stocks['Domestic_Buy'] = stocks['Domestic_Buy'].fillna(0)
            stocks['Domestic_Sell'] = stocks['Domestic_Sell'].fillna(0)
            stocks['Net_Domestic'] = stocks['Domestic_Buy'] - stocks['Domestic_Sell']
            domestic_source = 'manual'
        else:
            # Fallback to synthetic if required columns missing
            stocks['Domestic_Buy'] = (stocks['Total_Volume'] * 0.5) - stocks['Foreign_Buy']
            stocks['Domestic_Sell'] = (stocks['Total_Volume'] * 0.5) - stocks['Foreign_Sell']
            stocks['Net_Domestic'] = stocks['Domestic_Buy'] - stocks['Domestic_Sell']
    else:
        # Synthetic inference
        stocks['Domestic_Buy'] = (stocks['Total_Volume'] * 0.5) - stocks['Foreign_Buy']
        stocks['Domestic_Sell'] = (stocks['Total_Volume'] * 0.5) - stocks['Foreign_Sell']
        stocks['Net_Domestic'] = stocks['Domestic_Buy'] - stocks['Domestic_Sell']
except Exception:
    # Safe fallback
    stocks['Domestic_Buy'] = (stocks['Total_Volume'] * 0.5) - stocks['Foreign_Buy']
    stocks['Domestic_Sell'] = (stocks['Total_Volume'] * 0.5) - stocks['Foreign_Sell']
    stocks['Net_Domestic'] = stocks['Domestic_Buy'] - stocks['Domestic_Sell']

stocks['Divergence'] = abs(stocks['Net_Foreign'] - stocks['Net_Domestic'])

# Report meta section (timestamp + configuration)
print("\n" + "=" * 150)
print("🕒 REPORT META")
print("=" * 150)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (local)")
print(f"Accumulation Mode: {ACCUMULATION_MODE}")
print(f"Domestic Source: {domestic_source}")

print("\n📊 TRADING DAYS IN PERIOD")
print("-" * 150)
for d in dates:
    print(f"  {d.strftime('%A, %B %d, %Y')}")

print("\n" + "=" * 150)
print("🌍 FOREIGN INSTITUTIONAL FLOWS")
print("=" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Buy':<18} {'Sell':<18} {'Net Position':<18} {'Price':<15} {'Perf':<10}")
print("-" * 150)

for stock in stocks.nlargest(15, 'Net_Foreign').index:
    row = stocks.iloc[stock]
    price_str = f"Rp {row['Price_End']:>8,.0f}" if pd.notna(row['Price_End']) else "N/A"
    perf = f"{row['Price_Change_Pct']:>+6.2f}%" if pd.notna(row['Price_Change_Pct']) else "N/A"
    perf_signal = "📈" if row['Price_Change_Pct'] > 0 else "📉" if row['Price_Change_Pct'] < 0 else "➡️"
    print(f"{row['Stock']:<8} {str(row['Company'])[:33]:<35} Rp {row['Foreign_Buy']:>16,.0f} Rp {row['Foreign_Sell']:>16,.0f} Rp {row['Net_Foreign']:>16,.0f} {price_str:<15} {perf_signal} {perf:<8}")

print("\n" + "=" * 150)
print("🏛️  DOMESTIC INSTITUTIONAL FLOWS")
print("=" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Buy':<18} {'Sell':<18} {'Net Position':<18} {'Price':<15} {'Perf':<10}")
print("-" * 150)

for stock in stocks.nlargest(15, 'Net_Domestic').index:
    row = stocks.iloc[stock]
    price_str = f"Rp {row['Price_End']:>8,.0f}" if pd.notna(row['Price_End']) else "N/A"
    perf = f"{row['Price_Change_Pct']:>+6.2f}%" if pd.notna(row['Price_Change_Pct']) else "N/A"
    perf_signal = "📈" if row['Price_Change_Pct'] > 0 else "📉" if row['Price_Change_Pct'] < 0 else "➡️"
    print(f"{row['Stock']:<8} {str(row['Company'])[:33]:<35} Rp {row['Domestic_Buy']:>16,.0f} Rp {row['Domestic_Sell']:>16,.0f} Rp {row['Net_Domestic']:>16,.0f} {price_str:<15} {perf_signal} {perf:<8}")

# Comparison
print("\n" + "=" * 150)
print("⚔️  FOREIGN vs DOMESTIC DIVERGENCE: MAJOR DISAGREEMENTS")
print("=" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Foreign':<18} {'Domestic':<18} {'Divergence':<18} {'Signal':<25}")
print("-" * 150)

stocks_sorted = stocks.sort_values('Divergence', ascending=False)

for idx, row in stocks_sorted.head(15).iterrows():
    stock = row['Stock']
    company = str(row['Company'])[:33]
    foreign_net = row['Net_Foreign']
    domestic_net = row['Net_Domestic']
    diverg = row['Divergence']
    
    if foreign_net > 0 and domestic_net < 0:
        signal = "FOREIGN BUY, DOM SELL"
    elif foreign_net < 0 and domestic_net > 0:
        signal = "FOREIGN SELL, DOM BUY"
    elif foreign_net > 0 and domestic_net > 0:
        signal = "BOTH BUYING"
    elif foreign_net < 0 and domestic_net < 0:
        signal = "BOTH SELLING"
    else:
        signal = "Mixed"
    
    print(f"{stock:<8} {company:<35} Rp {foreign_net:>16,.0f} Rp {domestic_net:>16,.0f} Rp {diverg:>16,.0f} {signal:<25}")

# Summary statistics
print("\n" + "=" * 150)
print("📈 MARKET-WIDE INSTITUTIONAL POSITIONING")
print("=" * 150)

total_foreign_buy = stocks['Foreign_Buy'].sum()
total_foreign_sell = stocks['Foreign_Sell'].sum()
total_domestic_buy = stocks['Domestic_Buy'].sum()
total_domestic_sell = stocks['Domestic_Sell'].sum()

foreign_net = total_foreign_buy - total_foreign_sell
domestic_net = total_domestic_buy - total_domestic_sell

print(f"\n🌍 FOREIGN INSTITUTIONS:")
print(f"  Total Buy:  Rp {total_foreign_buy:>20,.0f}")
print(f"  Total Sell: Rp {total_foreign_sell:>20,.0f}")
print(f"  Net:        Rp {foreign_net:>20,.0f} ({'NET BUYING' if foreign_net > 0 else 'NET SELLING'})")
print(f"  %:          {(foreign_net/(total_foreign_buy + total_foreign_sell)*100):>20.2f}%")

print(f"\n🏛️  DOMESTIC INSTITUTIONS:")
print(f"  Total Buy:  Rp {total_domestic_buy:>20,.0f}")
print(f"  Total Sell: Rp {total_domestic_sell:>20,.0f}")
print(f"  Net:        Rp {domestic_net:>20,.0f} ({'NET BUYING' if domestic_net > 0 else 'NET SELLING'})")
print(f"  %:          {(domestic_net/(total_domestic_buy + total_domestic_sell)*100):>20.2f}%")

# Final verdict
print("\n" + "=" * 150)
print("🎯 CONTRARIAN VERDICT")
print("=" * 150)

if foreign_net > 0 and domestic_net > 0:
    verdict = "✅ CONSENSUS: Both accumulating → BULLISH"
elif foreign_net < 0 and domestic_net < 0:
    verdict = "⚠️  WARNING: Both liquidating → BEARISH"
elif foreign_net > 0 and domestic_net < 0:
    verdict = "🔴 DIVERGENCE: Foreign buying INTO domestic selling → Trap forming"
elif foreign_net < 0 and domestic_net > 0:
    verdict = "🟢 HEALTHY: Foreign exiting, domestic supporting → Distribution phase"

print(f"\n{verdict}")

if foreign_net < 0 and domestic_net > 0:
    print("\nInformation Asymmetry Detected:")
    print("  • Foreigners have exit signal (likely macro/capital flow driven)")
    print("  • Domestics stepping in (likely retail FOMO or yield chasing)")
    print("  • This is classic distribution: smart money exiting to retail")
    print("  • Short-term: Domestic support keeps market up")
    print("  • Long-term: Expect reversal when domestic runs out of cash")

# ===== HIGHEST POTENTIAL STOCKS ANALYSIS =====
print("\n" + "=" * 150)
print("🚀 HIGHEST POTENTIAL STOCKS (Consensus + Price Validation)")
print("=" * 150)

# Find stocks with BOTH foreign and domestic accumulation (consensus buying)
stocks['Both_Buying'] = (stocks['Net_Foreign'] > 0) & (stocks['Net_Domestic'] > 0)
stocks['Combined_Net'] = stocks['Net_Foreign'] + stocks['Net_Domestic']

consensus_stocks = stocks[stocks['Both_Buying']].sort_values('Combined_Net', ascending=False)

print(f"\n📊 CONSENSUS ACCUMULATION: Stocks both foreign AND domestic institutions are buying")
print("-" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Foreign':<18} {'Domestic':<18} {'Total Net':<18} {'Price':<15} {'Perf':<10} {'Score':<8}")
print("-" * 150)

if len(consensus_stocks) > 0:
    for idx, row in consensus_stocks.head(10).iterrows():
        # Calculate potential score: net position + price performance
        position_score = min(100, max(0, (row['Combined_Net'] / abs(consensus_stocks['Combined_Net'].max())) * 100))
        perf_score = min(100, max(0, (row['Price_Change_Pct'] + 50) * 2))  # Normalize -50% to +50%
        total_score = (position_score * 0.6) + (perf_score * 0.4)  # Weight position 60%, performance 40%
        
        price_str = f"Rp {row['Price_End']:>8,.0f}" if pd.notna(row['Price_End']) else "N/A"
        perf = f"{row['Price_Change_Pct']:>+6.2f}%" if pd.notna(row['Price_Change_Pct']) else "N/A"
        perf_signal = "📈" if row['Price_Change_Pct'] > 0 else "📉" if row['Price_Change_Pct'] < 0 else "➡️"
        
        score_signal = "🟢🟢" if total_score >= 75 else "🟢" if total_score >= 60 else "🟡"
        
        print(f"{row['Stock']:<8} {str(row['Company'])[:33]:<35} Rp {row['Net_Foreign']:>16,.0f} Rp {row['Net_Domestic']:>16,.0f} Rp {row['Combined_Net']:>16,.0f} {price_str:<15} {perf_signal} {perf:<8} {score_signal} {total_score:>5.1f}")
else:
    print("⚠️  No consensus buying detected in this period")

# Find divergence plays with potential (foreign buying despite domestic selling, or vice versa)
print(f"\n\n📊 CONTRARIAN OPPORTUNITY: Stocks with informed buying despite retail indifference")
print("-" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Foreign':<18} {'Domestic':<18} {'Signal':<30} {'Price':<15} {'Perf':<10}")
print("-" * 150)

foreign_buying_vs_domestic_selling = stocks[(stocks['Net_Foreign'] > 0) & (stocks['Net_Domestic'] < 0)].sort_values('Net_Foreign', ascending=False)

if len(foreign_buying_vs_domestic_selling) > 0:
    for idx, row in foreign_buying_vs_domestic_selling.head(5).iterrows():
        price_str = f"Rp {row['Price_End']:>8,.0f}" if pd.notna(row['Price_End']) else "N/A"
        perf = f"{row['Price_Change_Pct']:>+6.2f}%" if pd.notna(row['Price_Change_Pct']) else "N/A"
        perf_signal = "📈" if row['Price_Change_Pct'] > 0 else "📉" if row['Price_Change_Pct'] < 0 else "➡️"
        signal = "Smart money vs retail skepticism"
        print(f"{row['Stock']:<8} {str(row['Company'])[:33]:<35} Rp {row['Net_Foreign']:>16,.0f} Rp {row['Net_Domestic']:>16,.0f} {signal:<30} {price_str:<15} {perf_signal} {perf:<8}")

# Stocks with strong price performance + institutional support
print(f"\n\n📊 PRICE VALIDATORS: Stocks with positive price movement + institutional accumulation")
print("-" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Accum.':<18} {'Price Chg':<15} {'3-Day Trend':<20} {'Volume':<18}")
print("-" * 150)

# Filter for positive price change and net positive flows
price_validated = stocks[(stocks['Price_Change_Pct'] > 0) & ((stocks['Net_Foreign'] > 0) | (stocks['Net_Domestic'] > 0))].sort_values('Price_Change_Pct', ascending=False)

if len(price_validated) > 0:
    for idx, row in price_validated.head(10).iterrows():
        # Choose accumulation calculation based on mode
        if ACCUMULATION_MODE == 'foreign_only':
            total_accum = max(row['Net_Foreign'], 0)
        elif ACCUMULATION_MODE == 'true_total':
            total_accum = row['Net_Foreign'] + row['Net_Domestic']
        else:  # positive_sum (default)
            total_accum = max(row['Net_Foreign'], 0) + max(row['Net_Domestic'], 0)
        accum_signal = "🟢" if total_accum > 0 else "🔴"
        
        # Get volume info
        stock_data = df_5d[df_5d['Kode Saham'] == row['Stock']]
        avg_volume = stock_data['Volume'].mean()
        vol_trend = "↗️ Rising" if stock_data['Volume'].iloc[-1] > avg_volume else "↘️ Falling"
        
        perf = f"{row['Price_Change_Pct']:>+6.2f}%"
        
        print(f"{row['Stock']:<8} {str(row['Company'])[:33]:<35} {accum_signal} Rp {total_accum:>15,.0f} {perf:<15} {vol_trend:<20} {avg_volume:>16,.0f}")
else:
    print("⚠️  No strong price validators found")

# Final recommendation
print("\n" + "=" * 150)
print("💡 TRADING IMPLICATIONS")
print("=" * 150)
print("""
1. SAFEST ENTRY: Consensus accumulation (both buying)
   → Institutions aligned = lower risk
   → Domestic strength + foreign support = stable
   
2. CONTRARIAN PLAYS: Foreign buying vs retail selling
   → Institutions sees opportunity retail misses
   → Requires conviction and patience
   → Watch volume: must confirm (volume following price)
   
3. VALIDATORS: Positive price + institutional accumulation
   → Price rise + accumulation = trend continuation likely
   → Watch for rejection/reversal candles = exit signal
   
4. DANGER ZONE: Foreign selling + domestic buying
   → Smart money knows something retail doesn't
   → High risk of snapback when domestic runs out of buying
   → Best for 1-2 day swing, not 5-day holds
""")

print("\n" + "=" * 150)
