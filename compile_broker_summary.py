import pandas as pd

df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")
df['SourceDate'] = pd.to_datetime(df['SourceDate'])

broker_summary = df.groupby('SourceDate').agg({
    'Foreign Sell': 'sum',
    'Foreign Buy': 'sum',
    'Kode Saham': 'count'
}).reset_index()

broker_summary.columns = ['Date', 'Total_Foreign_Sell', 'Total_Foreign_Buy', 'Stocks_Traded']
broker_summary['Net_Foreign'] = broker_summary['Total_Foreign_Buy'] - broker_summary['Total_Foreign_Sell']
broker_summary = broker_summary.sort_values('Date')

broker_summary.to_csv("data/reference/ringkasan_broker_20251201_20260121.csv", index=False)

print(f"Total trading days: {len(broker_summary)}")
print(broker_summary.tail())
