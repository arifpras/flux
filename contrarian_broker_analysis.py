import pandas as pd
import numpy as np

# Read broker data
df = pd.read_csv("data/reference/ringkasan_broker_combined_20251201_20260121.csv")

print("=" * 100)
print("CONTRARIAN BROKER ANALYSIS (CFA PERSPECTIVE)")
print("Period: Dec 1, 2025 - Jan 21, 2026")
print("=" * 100)

# Split by date
df_dec = df[df['Date'] == '2025-12-01'].copy()
df_jan = df[df['Date'] == '2026-01-21'].copy()

# 1. Market Concentration Analysis (HHI)
print("\n📊 MARKET STRUCTURE & CONCENTRATION")
print("-" * 100)

def calc_hhi(volumes):
    total = volumes.sum()
    shares = (volumes / total) * 100
    hhi = (shares ** 2).sum()
    return hhi

hhi_dec = calc_hhi(df_dec['Volume'])
hhi_jan = calc_hhi(df_jan['Volume'])

print(f"HHI Dec 1:  {hhi_dec:.2f} (Market concentration index)")
print(f"HHI Jan 21: {hhi_jan:.2f} (Market concentration index)")
print(f"Change: {hhi_jan - hhi_dec:+.2f} ({'More concentrated' if hhi_jan > hhi_dec else 'More competitive'})")

# 2. Top Brokers Analysis
print("\n🏆 DOMINANT PLAYERS (TOP 5 BY VOLUME)")
print("-" * 100)

print("\nDec 1, 2025:")
top5_dec = df_dec.nlargest(5, 'Volume')[['Nama Perusahaan', 'Volume', 'Nilai', 'Frekuensi']]
for i, (idx, row) in enumerate(top5_dec.iterrows(), 1):
    vol_pct = (row['Volume'] / df_dec['Volume'].sum()) * 100
    print(f"{i}. {row['Nama Perusahaan']:<40} Vol: {vol_pct:>5.1f}% | Avg trade: {row['Nilai']/row['Frekuensi']:>12,.0f}")

print("\nJan 21, 2026:")
top5_jan = df_jan.nlargest(5, 'Volume')[['Nama Perusahaan', 'Volume', 'Nilai', 'Frekuensi']]
for i, (idx, row) in enumerate(top5_jan.iterrows(), 1):
    vol_pct = (row['Volume'] / df_jan['Volume'].sum()) * 100
    print(f"{i}. {row['Nama Perusahaan']:<40} Vol: {vol_pct:>5.1f}% | Avg trade: {row['Nilai']/row['Frekuensi']:>12,.0f}")

# 3. Efficiency Analysis (Value per Trade)
print("\n⚡ MARKET EFFICIENCY (VALUE PER TRADE)")
print("-" * 100)

df_dec['AvgTradeValue'] = df_dec['Nilai'] / df_dec['Frekuensi']
df_jan['AvgTradeValue'] = df_jan['Nilai'] / df_jan['Frekuensi']

avg_trade_dec = df_dec['Nilai'].sum() / df_dec['Frekuensi'].sum()
avg_trade_jan = df_jan['Nilai'].sum() / df_jan['Frekuensi'].sum()

print(f"Dec 1 market avg trade size: Rp {avg_trade_dec:>12,.0f}")
print(f"Jan 21 market avg trade size: Rp {avg_trade_jan:>12,.0f}")
print(f"Change: {((avg_trade_jan/avg_trade_dec)-1)*100:+.2f}% (Trade size {'increased' if avg_trade_jan > avg_trade_dec else 'decreased'})")

# 4. Activity Metrics
print("\n📈 MARKET ACTIVITY")
print("-" * 100)

total_vol_dec = df_dec['Volume'].sum()
total_vol_jan = df_jan['Volume'].sum()
total_val_dec = df_dec['Nilai'].sum()
total_val_jan = df_jan['Nilai'].sum()
total_freq_dec = df_dec['Frekuensi'].sum()
total_freq_jan = df_jan['Frekuensi'].sum()

print(f"\nDec 1:")
print(f"  Total Volume: {total_vol_dec:>20,.0f} shares")
print(f"  Total Value:  Rp {total_val_dec:>18,.0f}")
print(f"  Total Trades: {total_freq_dec:>20,.0f}")

print(f"\nJan 21:")
print(f"  Total Volume: {total_vol_jan:>20,.0f} shares")
print(f"  Total Value:  Rp {total_val_jan:>18,.0f}")
print(f"  Total Trades: {total_freq_jan:>20,.0f}")

print(f"\nChange:")
print(f"  Volume:  {((total_vol_jan/total_vol_dec)-1)*100:+.2f}%")
print(f"  Value:   {((total_val_jan/total_val_dec)-1)*100:+.2f}%")
print(f"  Trades:  {((total_freq_jan/total_freq_dec)-1)*100:+.2f}%")

# 5. Broker Survival & Entry/Exit
print("\n🔄 BROKER TURNOVER (MARKET ENTRY/EXIT)")
print("-" * 100)

dec_brokers = set(df_dec['Kode Perusahaan'])
jan_brokers = set(df_jan['Kode Perusahaan'])

exited = dec_brokers - jan_brokers
entered = jan_brokers - dec_brokers
survived = dec_brokers & jan_brokers

print(f"Brokers in Dec 1: {len(dec_brokers)}")
print(f"Brokers in Jan 21: {len(jan_brokers)}")
print(f"Survived (both dates): {len(survived)}")
print(f"Exited market: {len(exited)} - {', '.join(exited) if exited else 'None'}")
print(f"Entered market: {len(entered)} - {', '.join(entered) if entered else 'None'}")

# 6. CONTRARIAN SIGNALS
print("\n🎯 CONTRARIAN INSIGHTS & SIGNALS")
print("-" * 100)

# Which brokers changed position most?
df_dec_sorted = df_dec.sort_values('Volume', ascending=False).reset_index(drop=True)
df_jan_sorted = df_jan.sort_values('Volume', ascending=False).reset_index(drop=True)

dec_ranks = dict(zip(df_dec_sorted['Kode Perusahaan'], range(1, len(df_dec_sorted)+1)))
jan_ranks = dict(zip(df_jan_sorted['Kode Perusahaan'], range(1, len(df_jan_sorted)+1)))

rank_changes = {}
for broker in survived:
    if broker in dec_ranks and broker in jan_ranks:
        rank_changes[broker] = jan_ranks[broker] - dec_ranks[broker]

biggest_gainers = sorted(rank_changes.items(), key=lambda x: x[1], reverse=True)[:5]
biggest_losers = sorted(rank_changes.items(), key=lambda x: x[1])[:5]

print("\n🔺 BROKERS GAINING MARKET SHARE (Moving UP in rankings):")
for broker_code, change in biggest_gainers:
    broker_name = df_jan[df_jan['Kode Perusahaan'] == broker_code]['Nama Perusahaan'].values[0]
    print(f"  {broker_code} {broker_name:<38} Rank: {dec_ranks[broker_code]} → {jan_ranks[broker_code]} ({change:+d})")

print("\n🔻 BROKERS LOSING MARKET SHARE (Moving DOWN in rankings):")
for broker_code, change in biggest_losers:
    broker_name = df_dec[df_dec['Kode Perusahaan'] == broker_code]['Nama Perusahaan'].values[0]
    print(f"  {broker_code} {broker_name:<38} Rank: {dec_ranks[broker_code]} → {jan_ranks[broker_code]} ({change:+d})")

# 7. CONTRARIAN THESIS
print("\n💡 CONTRARIAN TRADING THESIS")
print("-" * 100)

if hhi_jan > hhi_dec:
    print("⚠️  CONCENTRATION INCREASING")
    print("    → Retail capital consolidating into major brokers")
    print("    → Smaller brokers losing retail flow → potential SHORT opportunity for illiquid names")
else:
    print("✅ MARKET BECOMING MORE COMPETITIVE")
    print("    → Capital dispersing across brokers")
    print("    → Market structure more resilient")

if avg_trade_jan > avg_trade_dec:
    print("\n📈 AVERAGE TRADE SIZE INCREASED")
    print("    → Institutional participation rising")
    print("    → Retail retail dominance weakening → less retail-driven volatility")
    print("    → Potential LONG-term uptrend confirmation (professionals accumulating)")
else:
    print("\n📉 AVERAGE TRADE SIZE DECREASED")
    print("    → Retail participation rising")
    print("    → Market becoming noisier → higher variance")
    print("    → Contrarians watch for panic capitulation")

if ((total_freq_jan/total_freq_dec)-1)*100 > 10:
    print("\n🚀 TRADE FREQUENCY SURGING")
    print("    → Retail excitement increasing")
    print("    → Possible late-stage bull market behavior")
    print("    → Contrarians should prepare for reversal positions")
elif ((total_freq_jan/total_freq_dec)-1)*100 < -10:
    print("\n⏸️  TRADE FREQUENCY DECLINING")
    print("    → Retail interest waning")
    print("    → Potential accumulation phase by professionals")
    print("    → Contrarians position for recovery")

print("\n" + "=" * 100)
