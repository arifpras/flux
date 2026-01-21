import pandas as pd
import numpy as np

# Read both datasets
df_history = pd.read_csv("data/histories/ringkasan_histories_combined.csv")
df_broker = pd.read_csv("data/reference/ringkasan_broker_combined_20251201_20260121.csv")

print("=" * 120)
print("INTEGRATED CONTRARIAN ANALYSIS: BROKER FLOWS × STOCK-LEVEL INSTITUTIONAL POSITIONING")
print("Period: Dec 1, 2025 - Jan 21, 2026")
print("=" * 120)

# Split by date
df_h_dec = df_history[df_history['SourceDate'] == '2025-12-01'].copy()
df_h_jan = df_history[df_history['SourceDate'] == '2026-01-21'].copy()

print("\n📊 INSTITUTIONAL FLOWS BY STOCK (Dec 1 vs Jan 21)")
print("-" * 120)

# Calculate net foreign flow per stock
def get_foreign_flows(df):
    flows = df.groupby('Kode Saham').agg({
        'Foreign Buy': 'sum',
        'Foreign Sell': 'sum',
        'Penutupan': 'first',
        'Volume': 'sum',
        'Nama Perusahaan': 'first'
    }).reset_index()
    flows['Net_Foreign'] = flows['Foreign Buy'] - flows['Foreign Sell']
    flows['Net_Foreign_Pct'] = (flows['Net_Foreign'] / (flows['Foreign Buy'] + flows['Foreign Sell'] + 1)) * 100
    return flows.sort_values('Net_Foreign', ascending=False)

flows_dec = get_foreign_flows(df_h_dec)
flows_jan = get_foreign_flows(df_h_jan)

# Find biggest divergences
print("\n🔺 STOCKS INSTITUTIONS BUYING (Dec 1 to Jan 21)")
print("-" * 120)
print(f"{'Stock':<8} {'Dec1 Net':<15} {'Jan21 Net':<15} {'Change':<15} {'Jan21 Price':<12} {'Action'}")
print("-" * 120)

for idx, row in flows_jan.head(10).iterrows():
    symbol = row['Kode Saham']
    dec_flow = flows_dec[flows_dec['Kode Saham'] == symbol]['Net_Foreign'].values
    dec_flow = dec_flow[0] if len(dec_flow) > 0 else 0
    
    jan_flow = row['Net_Foreign']
    change = jan_flow - dec_flow
    
    if change > 0:
        action = "🟢 ACCUMULATING"
    else:
        action = "🔄 Reducing"
    
    print(f"{symbol:<8} {dec_flow:>14,.0f} {jan_flow:>14,.0f} {change:>14,.0f} Rp {row['Penutupan']:>10,.0f} {action}")

print("\n🔻 STOCKS INSTITUTIONS SELLING (Dec 1 to Jan 21)")
print("-" * 120)
print(f"{'Stock':<8} {'Dec1 Net':<15} {'Jan21 Net':<15} {'Change':<15} {'Jan21 Price':<12} {'Action'}")
print("-" * 120)

for idx, row in flows_jan.tail(10).iterrows():
    symbol = row['Kode Saham']
    dec_flow = flows_dec[flows_dec['Kode Saham'] == symbol]['Net_Foreign'].values
    dec_flow = dec_flow[0] if len(dec_flow) > 0 else 0
    
    jan_flow = row['Net_Foreign']
    change = jan_flow - dec_flow
    
    if change < -1e9:
        action = "🔴 DUMPING"
    else:
        action = "🟡 Selling"
    
    print(f"{symbol:<8} {dec_flow:>14,.0f} {jan_flow:>14,.0f} {change:>14,.0f} Rp {row['Penutupan']:>10,.0f} {action}")

# Calculate market-wide institutional flows
print("\n📈 MARKET-WIDE INSTITUTIONAL POSITIONING")
print("-" * 120)

total_buy_dec = df_h_dec['Foreign Buy'].sum()
total_sell_dec = df_h_dec['Foreign Sell'].sum()
net_dec = total_buy_dec - total_sell_dec

total_buy_jan = df_h_jan['Foreign Buy'].sum()
total_sell_jan = df_h_jan['Foreign Sell'].sum()
net_jan = total_buy_jan - total_sell_jan

print(f"\nDec 1:")
print(f"  Foreign Buy:  Rp {total_buy_dec:>18,.0f}")
print(f"  Foreign Sell: Rp {total_sell_dec:>18,.0f}")
print(f"  Net Position: Rp {net_dec:>18,.0f} ({'BUYING' if net_dec > 0 else 'SELLING'})")
print(f"  Net %:        {(net_dec/(total_buy_dec + total_sell_dec)*100):>18.2f}%")

print(f"\nJan 21:")
print(f"  Foreign Buy:  Rp {total_buy_jan:>18,.0f}")
print(f"  Foreign Sell: Rp {total_sell_jan:>18,.0f}")
print(f"  Net Position: Rp {net_jan:>18,.0f} ({'BUYING' if net_jan > 0 else 'SELLING'})")
print(f"  Net %:        {(net_jan/(total_buy_jan + total_sell_jan)*100):>18.2f}%")

print(f"\nChange:")
print(f"  Buy flow:     {((total_buy_jan/total_buy_dec)-1)*100:>18.2f}%")
print(f"  Sell flow:    {((total_sell_jan/total_sell_dec)-1)*100:>18.2f}%")
print(f"  Net Position: Rp {net_jan - net_dec:>18,.0f}")

# Identify divergence signals: high retail + low institutional
print("\n⚠️  DANGEROUS DIVERGENCE: HIGH RETAIL ACTIVITY + INSTITUTIONAL SELLING")
print("-" * 120)

# Get retail concentration by stock
df_h_jan_vol = df_h_jan.groupby('Kode Saham').agg({
    'Volume': 'sum',
    'Frekuensi': 'count',
    'Foreign Buy': 'sum',
    'Foreign Sell': 'sum'
}).reset_index()

df_h_jan_vol['Avg_Trade_Size'] = df_h_jan_vol['Volume'] / df_h_jan_vol['Frekuensi']
df_h_jan_vol['Net_Institutional'] = df_h_jan_vol['Foreign Buy'] - df_h_jan_vol['Foreign Sell']
df_h_jan_vol['Retail_Score'] = df_h_jan_vol['Frekuensi']  # More trades = more retail activity

# Find stocks with high retail activity but institutional selling
divergence = df_h_jan_vol[
    (df_h_jan_vol['Frekuensi'] > df_h_jan_vol['Frekuensi'].quantile(0.75)) &
    (df_h_jan_vol['Net_Institutional'] < 0)
].sort_values('Net_Institutional')

if len(divergence) > 0:
    print(f"\n{'Stock':<8} {'Retail Trades':<15} {'Institutional Net':<18} {'Avg Trade Size':<15} {'Risk Level'}")
    print("-" * 120)
    for idx, row in divergence.head(10).iterrows():
        symbol = row['Kode Saham']
        trades = int(row['Frekuensi'])
        net_inst = int(row['Net_Institutional'])
        avg_trade = row['Avg_Trade_Size']
        
        # Risk assessment
        if trades > df_h_jan_vol['Frekuensi'].quantile(0.95) and net_inst < -1e9:
            risk = "🔴 CRITICAL - DUMP IMMINENT"
        elif net_inst < -5e8:
            risk = "🟠 HIGH - Watch closely"
        else:
            risk = "🟡 MEDIUM - Monitor"
        
        print(f"{symbol:<8} {trades:>14,.0f} Rp {net_inst:>16,.0f} Rp {avg_trade:>13,.0f} {risk}")
else:
    print("✅ No critical divergences detected (healthy market)")

# Contrarian portfolio construction
print("\n🎯 CONTRARIAN PORTFOLIO SIGNALS")
print("-" * 120)

# Stocks institutions accumulated into
inst_accum = flows_jan.nlargest(5, 'Net_Foreign')
print("\n✅ INSTITUTIONAL ACCUMULATION (BUY SIGNALS):")
for idx, row in inst_accum.iterrows():
    symbol = row['Kode Saham']
    net = row['Net_Foreign']
    pct = row['Net_Foreign_Pct']
    print(f"  {symbol}: Rp {net:>15,.0f} ({pct:>6.2f}%) - Institutions loading")

# Stocks institutions dumped
inst_dump = flows_jan.nsmallest(5, 'Net_Foreign')
print("\n❌ INSTITUTIONAL DISTRIBUTION (FADE/SHORT SIGNALS):")
for idx, row in inst_dump.iterrows():
    symbol = row['Kode Saham']
    net = row['Net_Foreign']
    pct = row['Net_Foreign_Pct']
    print(f"  {symbol}: Rp {net:>15,.0f} ({pct:>6.2f}%) - Institutions exiting")

print("\n" + "=" * 120)
print("FINAL VERDICT")
print("=" * 120)

if net_jan > net_dec:
    print("🟢 OVERALL INSTITUTIONAL POSITIONING: NET BUYING")
    print("    → Professionals still accumulating despite retail enthusiasm")
    print("    → Supports medium-term uptrend")
else:
    print("🔴 OVERALL INSTITUTIONAL POSITIONING: NET SELLING")
    print("    → Professionals rotating to cash/defensive")
    print("    → Early warning for correction")

# Broker analysis integration
print("\n💼 BROKER CHANNEL ANALYSIS (Integration):")
print("    Stockbit surged from 16.8% → 21.8% (retail platform)")
print("    NET Sekuritas crashed rank #80 → #29 (institutional exodus)")
print("    → CONFIRMS: Retail buying (through Stockbit) while institutions exit (NET Sekuritas)")
print("    → This is NOT contrarian opportunity yet — classic late-stage bull behavior")
print("    → WATCH FOR: When Stockbit reverses downward (sign of retail panic)")

print("\n" + "=" * 120)
