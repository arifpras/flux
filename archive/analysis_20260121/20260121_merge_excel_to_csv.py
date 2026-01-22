#!/usr/bin/env python3
import pandas as pd

excel_path = "data/histories/Ringkasan Saham-20260121.xlsx"
csv_path = "data/histories/ringkasan_histories_combined.csv"

# Read files
df_excel = pd.read_excel(excel_path)
df_csv = pd.read_csv(csv_path)

# Add SourceDate column to Excel data
df_excel['SourceDate'] = '2026-01-21'

# Reorder columns to match CSV structure
column_order = ['SourceDate', 'No', 'Kode Saham', 'Nama Perusahaan', 'Remarks', 'Sebelumnya', 
                'Open Price', 'Tanggal Perdagangan Terakhir', 'First Trade', 'Tertinggi', 
                'Terendah', 'Penutupan', 'Selisih', 'Volume', 'Nilai', 'Frekuensi', 
                'Index Individual', 'Offer', 'Offer Volume', 'Bid', 'Bid Volume', 
                'Listed Shares', 'Tradeble Shares', 'Weight For Index', 'Foreign Sell', 
                'Foreign Buy', 'Non Regular Volume', 'Non Regular Value', 'Non Regular Frequency']

df_excel = df_excel[column_order]

# Append to CSV
df_combined = pd.concat([df_csv, df_excel], ignore_index=True)

# Save
df_combined.to_csv(csv_path, index=False)

print(f"✅ Merged successfully!")
print(f"📊 Original CSV: {len(df_csv)} rows")
print(f"➕ Added from Excel: {len(df_excel)} rows")
print(f"📈 New total: {len(df_combined)} rows")
print(f"📅 Date range: {df_combined['SourceDate'].min()} to {df_combined['SourceDate'].max()}")
print(f"📁 Saved to: {csv_path}")
