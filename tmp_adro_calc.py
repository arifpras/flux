import pandas as pd

# ADRO Broker Summary Jan 13-20, 2026
buy_data = """Broker,Value,Lot,AvgPrice
AK,228.8B,1000.0K,2252
LG,119.8B,533.9K,2243
KK,31.3B,140.4K,2244
PD,29.0B,129.1K,2249
ZP,28.1B,131.6K,2220
XA,3.3B,15.2K,2240
HD,2.4B,11.8K,2242
ES,2.2B,10.0K,2227
IN,1.4B,6.6K,2153
EP,1.2B,2.7K,2268
DR,882.1M,4.4K,2257
RF,782.3M,3.5K,2238
AG,568.4M,2.7K,2221
FZ,544.3M,2.4K,2257
RX,397.5M,1.8K,2154
SA,356.5M,1.6K,2251
BR,152.3M,635,2273
SS,102.7M,468,2217
QA,86.7M,379,2284
EL,23.7M,105,2255
PP,21.8M,85,2290
GI,5.7M,25,2270
RS,4.8M,1,2274"""

sell_data = """Broker,Value,Lot,AvgPrice
XL,106.9B,474.6K,2244
BB,52.5B,242.4K,2172
XC,37.0B,165.0K,2242
NI,36.5B,162.1K,2242
YP,27.7B,123.6K,2243
SQ,27.1B,120.4K,2245
KZ,23.6B,104.9K,2241
CC,22.7B,102.8K,2246
YU,18.6B,78.7K,2267
OD,15.2B,68.4K,2248
AZ,14.4B,66.8K,2215
IF,7.4B,33.3K,2232
BK,7.4B,30.6K,2252
GR,7.1B,32.0K,2236
DH,7.1B,32.0K,2222
KI,5.7B,25.2K,2247
MG,5.5B,25.3K,2223
BQ,3.1B,12.4K,2245
DX,2.8B,12.3K,2248
IH,2.4B,10.7K,2263
TP,2.4B,10.7K,2228
FS,2.3B,10.1K,2245
AT,1.8B,8.2K,2243
LS,1.6B,7.3K,2238
YB,1.5B,6.8K,2246"""

mult = {'B': 1e9, 'M': 1e6, 'K': 1e3}

def parse_number(value: str) -> float:
    unit = value[-1]
    if unit in mult:
        return float(value[:-1]) * mult[unit]
    return float(value)

def parse_data(data_str):
    rows = []
    for line in data_str.strip().split('\n')[1:]:  # Skip header
        parts = line.split(',')
        broker = parts[0]
        value = parse_number(parts[1])
        lots = parse_number(parts[2])
        avg = float(parts[3])
        rows.append((broker, value, lots, avg))
    return pd.DataFrame(rows, columns=['Broker', 'Value', 'Lots', 'AvgPrice'])

buy_df = parse_data(buy_data)
sell_df = parse_data(sell_data)

buy_df['Shares'] = buy_df['Lots'] * 100
sell_df['Shares'] = sell_df['Lots'] * 100

# Calculate totals
b_val = buy_df.Value.sum()
b_sh = buy_df.Shares.sum()
b_vwap = b_val / b_sh

s_val = sell_df.Value.sum()
s_sh = sell_df.Shares.sum()
s_vwap = s_val / s_sh

net_val = b_val - s_val
net_sh = b_sh - s_sh
net_vwap = net_val / net_sh if net_sh > 0 else 0

# Top 3 calculations
top3_buy_val = buy_df.nlargest(3, 'Value').Value.sum()
top3_sell_val = sell_df.nlargest(3, 'Value').Value.sum()
buy_concentration = (top3_buy_val / b_val) * 100
sell_concentration = (top3_sell_val / s_val) * 100
bci = buy_concentration / sell_concentration

# VWAP Premium
current_price = 2240
vpd = ((net_vwap - current_price) / current_price) * 100

print("=" * 60)
print("ADRO BROKER SUMMARY ANALYSIS (Jan 13-20, 2026)")
print("=" * 60)
print(f"\n📊 BUY SIDE:")
print(f"  Total Buy Value:    Rp {b_val:,.0f}")
print(f"  Total Buy Shares:   {b_sh:,.0f}")
print(f"  Buy VWAP:           Rp {b_vwap:,.2f}")
print(f"  Number of Buyers:   {len(buy_df)}")

print(f"\n📊 SELL SIDE:")
print(f"  Total Sell Value:   Rp {s_val:,.0f}")
print(f"  Total Sell Shares:  {s_sh:,.0f}")
print(f"  Sell VWAP:          Rp {s_vwap:,.2f}")
print(f"  Number of Sellers:  {len(sell_df)}")

print(f"\n💰 NET POSITION:")
print(f"  Net Value:          Rp {net_val:,.0f}")
print(f"  Net Shares:         {net_sh:,.0f}")
print(f"  Net-Flow VWAP:      Rp {net_vwap:,.2f}")
print(f"  Current Price:      Rp {current_price:,}")

print(f"\n🎯 KEY METRICS:")
print(f"  Buy Concentration (Top 3):  {buy_concentration:.1f}%")
print(f"  Sell Concentration (Top 3): {sell_concentration:.1f}%")
print(f"  BCI (Concentration Ratio):  {bci:.2f}")
print(f"  VWAP Premium/Discount:      {vpd:+.2f}%")
print(f"  Buy/Sell Volume Ratio:      {b_sh/s_sh:.2f}x")

print(f"\n🏆 TOP 3 BUYERS:")
for i, row in buy_df.nlargest(3, 'Value').iterrows():
    print(f"  {row.Broker:3s}: Rp {row.Value/1e9:6.1f}B  ({row.Lots/1e3:6.1f}K lots @ {row.AvgPrice:,})")

print(f"\n🔻 TOP 3 SELLERS:")
for i, row in sell_df.nlargest(3, 'Value').iterrows():
    print(f"  {row.Broker:3s}: Rp {row.Value/1e9:6.1f}B  ({row.Lots/1e3:6.1f}K lots @ {row.AvgPrice:,})")

print(f"\n✅ SIGNAL INTERPRETATION:")
if bci > 2.5:
    print(f"  BCI {bci:.2f} > 2.5: 🟢 STRONG INSTITUTIONAL ACCUMULATION")
elif bci > 2.0:
    print(f"  BCI {bci:.2f} > 2.0: 🟢 INSTITUTIONAL ACCUMULATION")
else:
    print(f"  BCI {bci:.2f} < 2.0: 🟡 MODERATE ACCUMULATION")

if vpd > 1.0:
    print(f"  VPD {vpd:+.2f}% > 1%: 🟢 STRONG CONVICTION BUYING (premium)")
elif vpd > 0:
    print(f"  VPD {vpd:+.2f}% > 0%: 🟢 CONVICTION BUYING (slight premium)")
else:
    print(f"  VPD {vpd:+.2f}% < 0%: 🟡 BUYING AT DISCOUNT")

print("\n" + "=" * 60)
