import pandas as pd

df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")

# Select broker-related columns
broker_cols = ['SourceDate', 'Kode Saham', 'Nama Perusahaan', 'Penutupan', 'Volume', 'Foreign Sell', 'Foreign Buy']
df_broker = df[broker_cols].copy()

# Sort by date and stock
df_broker = df_broker.sort_values(['SourceDate', 'Kode Saham'])

# Save to reference folder
df_broker.to_csv("data/reference/ringkasan_broker_20251201_20260121.csv", index=False)

print(f"✅ Appended broker data")
print(f"Total records: {len(df_broker)}")
print(f"Date range: {df_broker['SourceDate'].min()} to {df_broker['SourceDate'].max()}")
print(f"Columns: {', '.join(df_broker.columns.tolist())}")
