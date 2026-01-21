import pandas as pd

df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")

df_dec = df[df['SourceDate'] == '2025-12-01']
df_jan = df[df['SourceDate'] == '2026-01-21']

dec = df_dec.groupby('Kode Saham')[['Foreign Buy', 'Foreign Sell', 'Penutupan', 'Nama Perusahaan']].agg({'Foreign Buy': 'sum', 'Foreign Sell': 'sum', 'Penutupan': 'first', 'Nama Perusahaan': 'first'})
jan = df_jan.groupby('Kode Saham')[['Foreign Buy', 'Foreign Sell', 'Penutupan', 'Nama Perusahaan']].agg({'Foreign Buy': 'sum', 'Foreign Sell': 'sum', 'Penutupan': 'first', 'Nama Perusahaan': 'first'})

dec.columns = ['Buy_Dec', 'Sell_Dec', 'Price_Dec', 'Company']
jan.columns = ['Buy_Jan', 'Sell_Jan', 'Price_Jan', 'Company']

m = pd.concat([dec, jan], axis=1).fillna(0)
m['Net_Dec'] = m['Buy_Dec'] - m['Sell_Dec']
m['Net_Jan'] = m['Buy_Jan'] - m['Sell_Jan']
m['Net_Chg'] = m['Net_Jan'] - m['Net_Dec']

print("=" * 120)
print("STOCKS INSTITUTIONS ARE BUYING")
print("=" * 120)
print(f"{'Stock':<8} {'Company':<40} {'Dec Buy':<15} {'Jan Buy':<15} {'Change':<15} {'Net Position':<15}")
print("-" * 120)

for stock in m.nlargest(15, 'Buy_Jan').index:
    row = m.loc[stock]
    print(f"{stock:<8} {str(row['Company'])[:38]:<40} Rp {row['Buy_Dec']:>13,.0f} Rp {row['Buy_Jan']:>13,.0f} Rp {row['Buy_Jan']-row['Buy_Dec']:>13,.0f} Rp {row['Net_Jan']:>13,.0f}")

print("\n" + "=" * 120)
print("STOCKS INSTITUTIONS ARE SELLING")
print("=" * 120)
print(f"{'Stock':<8} {'Company':<40} {'Dec Sell':<15} {'Jan Sell':<15} {'Change':<15} {'Net Position':<15}")
print("-" * 120)

for stock in m.nlargest(15, 'Sell_Jan').index:
    row = m.loc[stock]
    print(f"{stock:<8} {str(row['Company'])[:38]:<40} Rp {row['Sell_Dec']:>13,.0f} Rp {row['Sell_Jan']:>13,.0f} Rp {row['Sell_Jan']-row['Sell_Dec']:>13,.0f} Rp {row['Net_Jan']:>13,.0f}")

print("\n" + "=" * 120)
print("NET POSITIONS: ACCUMULATION (BUY > SELL)")
print("=" * 120)
print(f"{'Stock':<8} {'Company':<40} {'Dec Net':<15} {'Jan Net':<15} {'Change':<15}")
print("-" * 120)

for stock in m.nlargest(15, 'Net_Jan').index:
    row = m.loc[stock]
    print(f"{stock:<8} {str(row['Company'])[:38]:<40} Rp {row['Net_Dec']:>13,.0f} Rp {row['Net_Jan']:>13,.0f} Rp {row['Net_Chg']:>13,.0f}")

print("\n" + "=" * 120)
print("NET POSITIONS: DISTRIBUTION (SELL > BUY)")
print("=" * 120)
print(f"{'Stock':<8} {'Company':<40} {'Dec Net':<15} {'Jan Net':<15} {'Change':<15}")
print("-" * 120)

for stock in m.nsmallest(15, 'Net_Jan').index:
    row = m.loc[stock]
    print(f"{stock:<8} {str(row['Company'])[:38]:<40} Rp {row['Net_Dec']:>13,.0f} Rp {row['Net_Jan']:>13,.0f} Rp {row['Net_Chg']:>13,.0f}")

print("\n" + "=" * 120)
