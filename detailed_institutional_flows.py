import pandas as pd

# Read data
df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")

# Split by date
df_dec = df[df['SourceDate'] == '2025-12-01']
df_jan = df[df['SourceDate'] == '2026-01-21']

print("=" * 130)
print("INSTITUTIONAL FLOWS: WHICH STOCKS ARE BEING BOUGHT/SOLD")
print("=" * 130)

# Group by stock
stocks_dec = df_dec.groupby('Kode Saham').agg({
    'Foreign Buy': 'sum',
    'Foreign Sell': 'sum',
    'Penutupan': 'first',
    'Nama Perusahaan': 'first'
}).reset_index()

stocks_jan = df_jan.groupby('Kode Saham').agg({
    'Foreign Buy': 'sum',
    'Foreign Sell': 'sum',
    'Penutupan': 'first',
    'Nama Perusahaan': 'first'
}).reset_index()

stocks_dec.columns = ['Stock', 'Buy_Dec', 'Sell_Dec', 'Price_Dec', 'Company']
stocks_jan.columns = ['Stock', 'Buy_Jan', 'Sell_Jan', 'Price_Jan', 'Company']

# Merge
merged = pd.merge(stocks_dec, stocks_jan, on='Stock', how='outer', suffixes=('_dec', '_jan'))
merged = merged.fillna(0)

merged['Net_Dec'] = merged['Buy_Dec'] - merged['Sell_Dec']
merged['Net_Jan'] = merged['Buy_Jan'] - merged['Sell_Jan']
merged['Net_Change'] = merged['Net_Jan'] - merged['Net_Dec']
merged['Buy_Change'] = merged['Buy_Jan'] - merged['Buy_Dec']
merged['Sell_Change'] = merged['Sell_Jan'] - merged['Sell_Dec']

print("\n" + "=" * 150)
print("🟢 TOP 15: INSTITUTIONAL ACCUMULATION (BUYING MORE)")
print("=" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Buying Change':<18} {'Selling Change':<18} {'Net Change':<18} {'Price %':<10} {'Volume %':<10}")
print("-" * 150)

top_buyers = detailed.nlargest(15, 'Net_Change')
for idx, row in top_buyers.iterrows():
    symbol = row['Kode Saham']
    company = str(row['Company'])[:33]
    buy_chg = row['Buy_Change']
    sell_chg = row['Sell_Change']
    net_chg = row['Net_Change']
    price_pct = row['Price_Change_Pct']
    vol_pct = row['Vol_Change_Pct']
    
    # Determine signal strength
    if net_chg > 1e10:
        signal = "🟢🟢 HEAVY"
    elif net_chg > 5e9:
        signal = "🟢 STRONG"
    else:
        signal = "🟡 MODERATE"
    
    print(f"{symbol:<8} {company:<35} Rp {buy_chg:>15,.0f} Rp {sell_chg:>16,.0f} Rp {net_chg:>16,.0f} {price_pct:>8.1f}% {vol_pct:>8.1f}% {signal}")

print("\n" + "=" * 150)
print("🔴 TOP 15: INSTITUTIONAL DISTRIBUTION (SELLING MORE)")
print("=" * 150)
print(f"{'Stock':<8} {'Company':<35} {'Buying Change':<18} {'Selling Change':<18} {'Net Change':<18} {'Price %':<10} {'Volume %':<10}")
print("-" * 150)

top_sellers = detailed.nsmallest(15, 'Net_Change')
for idx, row in top_sellers.iterrows():
    symbol = row['Kode Saham']
    company = str(row['Company'])[:33]
    buy_chg = row['Buy_Change']
    sell_chg = row['Sell_Change']
    net_chg = row['Net_Change']
    price_pct = row['Price_Change_Pct']
    vol_pct = row['Vol_Change_Pct']
    
    # Determine signal strength
    if net_chg < -1e10:
        signal = "🔴🔴 PANIC"
    elif net_chg < -5e9:
        signal = "🔴 HEAVY DUMP"
    else:
        signal = "🟠 SELLING"
    
    print(f"{symbol:<8} {company:<35} Rp {buy_chg:>15,.0f} Rp {sell_chg:>16,.0f} Rp {net_chg:>16,.0f} {price_pct:>8.1f}% {vol_pct:>8.1f}% {signal}")

# Detailed breakdown per stock
print("\n" + "=" * 150)
print("📊 DETAILED BREAKDOWN: INSTITUTIONAL POSITIONING BY STOCK")
print("=" * 150)

# Focus on top 10 accumulation and top 10 distribution
print("\n🟢 ACCUMULATION PLAYS (Top 10)")
print("-" * 150)

for idx, row in top_buyers.head(10).iterrows():
    symbol = row['Kode Saham']
    company = str(row['Company'])
    
    print(f"\n{symbol} - {company}")
    print(f"  Dec 1:  Buy Rp {row['Buy_Before']:>14,.0f} | Sell Rp {row['Sell_Before']:>14,.0f} | Net {'+' if row['Net_Before'] > 0 else ''}{row['Net_Before']:>14,.0f}")
    print(f"  Jan 21: Buy Rp {row['Buy_After']:>14,.0f} | Sell Rp {row['Sell_After']:>14,.0f} | Net {'+' if row['Net_After'] > 0 else ''}{row['Net_After']:>14,.0f}")
    print(f"  Change: Buy {'+' if row['Buy_Change'] > 0 else ''}{row['Buy_Change']:>14,.0f} | Sell {'+' if row['Sell_Change'] > 0 else ''}{row['Sell_Change']:>14,.0f} | Net {'+' if row['Net_Change'] > 0 else ''}{row['Net_Change']:>14,.0f}")
    print(f"  Price:  Rp {row['Price_Before']:>8,.0f} → Rp {row['Price_After']:>8,.0f} ({row['Price_Change_Pct']:+.1f}%)")
    print(f"  Volume: {row['Vol_Before']:>15,.0f} → {row['Vol_After']:>15,.0f} ({row['Vol_Change_Pct']:+.1f}%)")
    
    # Interpretation
    if row['Net_Change'] > 0 and row['Price_Change_Pct'] > 0:
        print(f"  🎯 INTERPRETATION: Institutions buying + price rising = REAL accumulation (bullish)")
    elif row['Net_Change'] > 0 and row['Price_Change_Pct'] < 0:
        print(f"  ⚠️  INTERPRETATION: Institutions buying but price falling = Deep accumulation (hidden strength)")
    elif row['Net_Change'] > 0 and row['Price_Change_Pct'] == 0:
        print(f"  🟡 INTERPRETATION: Institutions buying but price flat = Preparing move")

print("\n" + "-" * 150)
print("\n🔴 DISTRIBUTION PLAYS (Top 10)")
print("-" * 150)

for idx, row in top_sellers.head(10).iterrows():
    symbol = row['Kode Saham']
    company = str(row['Company'])
    
    print(f"\n{symbol} - {company}")
    print(f"  Dec 1:  Buy Rp {row['Buy_Before']:>14,.0f} | Sell Rp {row['Sell_Before']:>14,.0f} | Net {'+' if row['Net_Before'] > 0 else ''}{row['Net_Before']:>14,.0f}")
    print(f"  Jan 21: Buy Rp {row['Buy_After']:>14,.0f} | Sell Rp {row['Sell_After']:>14,.0f} | Net {'+' if row['Net_After'] > 0 else ''}{row['Net_After']:>14,.0f}")
    print(f"  Change: Buy {'+' if row['Buy_Change'] > 0 else ''}{row['Buy_Change']:>14,.0f} | Sell {'+' if row['Sell_Change'] > 0 else ''}{row['Sell_Change']:>14,.0f} | Net {'+' if row['Net_Change'] > 0 else ''}{row['Net_Change']:>14,.0f}")
    print(f"  Price:  Rp {row['Price_Before']:>8,.0f} → Rp {row['Price_After']:>8,.0f} ({row['Price_Change_Pct']:+.1f}%)")
    print(f"  Volume: {row['Vol_Before']:>15,.0f} → {row['Vol_After']:>15,.0f} ({row['Vol_Change_Pct']:+.1f}%)")
    
    # Interpretation
    if row['Net_Change'] < 0 and row['Price_Change_Pct'] > 0:
        print(f"  🚨 INTERPRETATION: Institutions dumping while retail buys (top before crash)")
    elif row['Net_Change'] < 0 and row['Price_Change_Pct'] < 0:
        print(f"  🔴 INTERPRETATION: Institutions exiting + price falling = Confirmed reversal (bearish)")
    elif row['Net_Change'] < 0 and row['Price_Change_Pct'] == 0:
        print(f"  ⚠️  INTERPRETATION: Institutions exiting silently = Quiet distribution")

# Sector-based analysis
print("\n" + "=" * 150)
print("📈 SECTOR ANALYSIS: WHERE ARE INSTITUTIONS ROTATING?")
print("=" * 150)

# Classify by sector based on stock names
sector_map = {
    'BBCA': 'Banking', 'BBRI': 'Banking', 'BBNI': 'Banking', 'BMRI': 'Banking', 'BBKP': 'Banking',
    'ASII': 'Automotive', 'AUTO': 'Automotive',
    'ADRO': 'Energy', 'ANTM': 'Mining', 'NCKL': 'Mining', 'INCO': 'Mining',
    'GOTO': 'Technology', 'BUKA': 'Technology',
    'BUMI': 'Commodities', 'PWON': 'Property', 'PJAA': 'Property',
    'DEWA': 'Energy', 'RICY': 'Energy',
    'CANI': 'Agriculture'
}

detailed['Sector'] = detailed['Kode Saham'].map(sector_map).fillna('Other')

sector_analysis = detailed.groupby('Sector').agg({
    'Net_Change': 'sum',
    'Buy_Change': 'sum',
    'Sell_Change': 'sum',
    'Price_Change_Pct': 'mean',
    'Kode Saham': 'count'
}).reset_index()
sector_analysis.columns = ['Sector', 'Net_Flow', 'Buy_Flow', 'Sell_Flow', 'Avg_Price_Chg', 'Stocks']
sector_analysis = sector_analysis.sort_values('Net_Flow', ascending=False)

print(f"\n{'Sector':<20} {'Net Flow':<20} {'Buy Flow':<20} {'Sell Flow':<20} {'Avg Price %':<15} {'Stocks':<8} {'Signal'}")
print("-" * 150)

for idx, row in sector_analysis.iterrows():
    sector = row['Sector']
    net = row['Net_Flow']
    buy = row['Buy_Flow']
    sell = row['Sell_Flow']
    price = row['Avg_Price_Chg']
    stocks = int(row['Stocks'])
    
    if net > 5e9:
        signal = "🟢 INSTITUTIONAL BUYING"
    elif net < -5e9:
        signal = "🔴 INSTITUTIONAL SELLING"
    else:
        signal = "🟡 NEUTRAL"
    
    print(f"{sector:<20} Rp {net:>17,.0f} Rp {buy:>17,.0f} Rp {sell:>17,.0f} {price:>13.2f}% {stocks:>7d} {signal}")

print("\n" + "=" * 150)
print("🎯 CONTRARIAN THESIS SUMMARY")
print("=" * 150)

positive_sectors = sector_analysis[sector_analysis['Net_Flow'] > 0].sort_values('Net_Flow', ascending=False)
negative_sectors = sector_analysis[sector_analysis['Net_Flow'] < 0].sort_values('Net_Flow')

print("\n✅ INSTITUTIONAL FAVORITES (Accumulation):")
for idx, row in positive_sectors.iterrows():
    print(f"   → {row['Sector']}: +Rp {row['Net_Flow']:,.0f} (institutions loading)")

print("\n❌ INSTITUTIONAL EXITS (Distribution):")
for idx, row in negative_sectors.iterrows():
    print(f"   → {row['Sector']}: Rp {row['Net_Flow']:,.0f} (institutions dumping)")

print("\n" + "=" * 150)
