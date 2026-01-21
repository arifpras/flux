import csv, io
import pandas as pd

mult = {'B': 1e9, 'M': 1e6, 'K': 1e3}
raw = """Side,Broker,Value,Lot,AvgPrice
Buy,CC,215.7B,298.3K,7231
Buy,KZ,146.7B,200.3K,7294
Buy,BB,70.2B,98.5K,7137
Buy,AG,44.5B,62.4K,7150
Buy,AK,22.5B,31.3K,7252
Buy,YB,1.7B,2.5K,7045
Buy,FZ,1.3B,1.8K,7175
Buy,AZ,1.1B,1.3K,7363
Buy,PP,895.4M,1.2K,7276
Buy,SF,411.7M,583,7077
Buy,QA,24.4M,33,7275
Buy,IH,14.7M,20,7292
Buy,PC,3.9M,6,7111
Buy,RB,3.6M,5,7150
Buy,TF,2.2M,3,7425
Buy,MU,1.0M,0,7150
Buy,JB,720K,1,7070
Buy,AD,35K,0,7400
Sell,DH,53.7B,75.2K,7142
Sell,BK,52.9B,72.3K,7244
Sell,YP,46.9B,64.7K,7238
Sell,YU,38.0B,51.3K,7267
Sell,SQ,34.7B,47.7K,7266
Sell,RX,29.2B,41.5K,7140
Sell,PD,28.5B,38.8K,7318
Sell,LG,23.8B,33.0K,7207
Sell,OD,18.0B,24.7K,7265
Sell,ZP,17.4B,26.2K,7216
Sell,DX,16.4B,22.5K,7257
Sell,IF,15.6B,21.6K,7242
Sell,TP,14.7B,20.5K,7216
Sell,KK,14.2B,19.5K,7280
Sell,GR,13.2B,18.1K,7249
Sell,BQ,12.0B,16.4K,7295
Sell,NI,9.7B,13.5K,7272
Sell,DR,8.9B,12.4K,7227
Sell,ES,7.8B,10.5K,7416
Sell,CD,6.5B,9.1K,7202
Sell,XC,5.9B,8.1K,7264
Sell,XL,4.4B,5.9K,7258
Sell,DP,3.5B,4.8K,7226
Sell,EP,3.1B,4.2K,7301
Sell,SH,2.8B,3.8K,7371
"""

def parse_number(value: str) -> float:
    unit = value[-1]
    if unit in mult:
        return float(value[:-1]) * mult[unit]
    return float(value)

rows = []
for row in csv.reader(io.StringIO(raw)):
    if not row or row[0] == 'Side':
        continue
    side, broker, val, lot, avg = row
    value = parse_number(val)
    lots = parse_number(lot)
    rows.append((side, broker, value, lots, float(avg)))

df = pd.DataFrame(rows, columns=['Side', 'Broker', 'Value', 'Lots', 'AvgPrice'])
df['Shares'] = df['Lots'] * 100

buy = df[df.Side == 'Buy']
sell = df[df.Side == 'Sell']

b_val = buy.Value.sum(); b_sh = buy.Shares.sum(); b_vwap = b_val / b_sh
s_val = sell.Value.sum(); s_sh = sell.Shares.sum(); s_vwap = s_val / s_sh
net_val = b_val - s_val; net_sh = b_sh - s_sh; net_vwap = net_val / net_sh

print('Buy Value Rp', f"{b_val:,.0f}")
print('Buy Shares', f"{b_sh:,.0f}")
print('Buy VWAP', f"{b_vwap:,.2f}")
print('\nSell Value Rp', f"{s_val:,.0f}")
print('Sell Shares', f"{s_sh:,.0f}")
print('Sell VWAP', f"{s_vwap:,.2f}")
print('\nNet Value Rp', f"{net_val:,.0f}")
print('Net Shares', f"{net_sh:,.0f}")
print('Net VWAP (net buys)', f"{net_vwap:,.2f}")

print('\nTop 3 buy brokers:')
print(buy.sort_values('Value', ascending=False).head(3))
print('\nTop 3 sell brokers:')
print(sell.sort_values('Value', ascending=False).head(3))
