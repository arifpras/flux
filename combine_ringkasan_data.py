#!/usr/bin/env python3
"""
Combine Ringkasan Saham Excel data with historical CSV data
"""
import pandas as pd
from datetime import datetime

print("="*80)
print("COMBINING RINGKASAN SAHAM DATA")
print("="*80)

# Read the CSV with historical data
csv_data = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
print(f"\n✓ Loaded CSV: {csv_data.shape[0]} rows")
print(f"  Date range: {csv_data['SourceDate'].min()} to {csv_data['SourceDate'].max()}")

# Read the Excel with 2026-01-20 data
excel_data = pd.read_excel('data/histories/Ringkasan Saham-20260120.xlsx')
print(f"\n✓ Loaded Excel: {excel_data.shape[0]} rows")

# Add SourceDate column to Excel data (the date is in the filename)
excel_data['SourceDate'] = '2026-01-20'

# Reorder columns to match CSV structure
columns_order = ['SourceDate'] + [col for col in csv_data.columns if col != 'SourceDate']
excel_data = excel_data[columns_order]

# Append Excel data to CSV
combined_data = pd.concat([csv_data, excel_data], ignore_index=True)
print(f"\n✓ Combined data: {combined_data.shape[0]} rows")
print(f"  Date range: {combined_data['SourceDate'].min()} to {combined_data['SourceDate'].max()}")

# Sort by SourceDate and Kode Saham
combined_data = combined_data.sort_values(['SourceDate', 'Kode Saham']).reset_index(drop=True)

# Save to CSV
output_file = 'data/histories/ringkasan_histories_combined.csv'
combined_data.to_csv(output_file, index=False)
print(f"\n✓ Saved to: {output_file}")
print(f"  Total rows: {len(combined_data)}")

# Display summary
print(f"\n  Unique dates: {combined_data['SourceDate'].nunique()}")
print(f"  Latest date: {combined_data['SourceDate'].max()}")
print(f"  Sample of latest data (2026-01-20):")
latest_data = combined_data[combined_data['SourceDate'] == '2026-01-20'].head()
print(latest_data[['SourceDate', 'Kode Saham', 'Nama Perusahaan', 'Open Price', 'Penutupan', 'Volume']])

print("\n" + "="*80)
print("✅ COMBINATION COMPLETE!")
print("="*80)
