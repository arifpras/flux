#!/usr/bin/env python3
"""
Append Ringkasan Saham-20260122.xlsx to ringkasan_histories_combined.csv
"""

import pandas as pd
from datetime import datetime

print("="*85)
print("APPENDING RINGKASAN SAHAM DATA TO COMBINED HISTORY")
print("="*85)

# File paths
excel_file = 'data/histories/Ringkasan Saham-20260122.xlsx'
csv_file = 'data/histories/ringkasan_histories_combined.csv'
backup_file = 'data/histories/ringkasan_histories_combined_backup_20260122.csv'

print(f"\n[1/5] Loading existing combined CSV...")
try:
    existing_df = pd.read_csv(csv_file)
    print(f"✓ Loaded {len(existing_df):,} rows from existing CSV")
    if 'SourceDate' in existing_df.columns:
        print(f"  Date range: {existing_df['SourceDate'].min()} to {existing_df['SourceDate'].max()}")
    print(f"  Columns: {existing_df.shape[1]} columns")
except FileNotFoundError:
    print("⚠️  Combined CSV not found, will create new file")
    existing_df = pd.DataFrame()

print(f"\n[2/5] Loading new Excel data...")
new_df = pd.read_excel(excel_file)
print(f"✓ Loaded {len(new_df):,} rows from Excel")
print(f"  Columns: {new_df.shape[1]} columns")

# Keep original column names (don't rename - just add SourceDate)
print(f"\n[3/5] Adding SourceDate column...")
# Add SourceDate from filename
new_df['SourceDate'] = '2026-01-22'
print(f"✓ Added SourceDate: 2026-01-22")

# Align columns to match existing format
if len(existing_df) > 0:
    existing_cols = set(existing_df.columns)
    new_cols = set(new_df.columns)
    
    # Columns in existing but not in new
    missing_in_new = existing_cols - new_cols
    if missing_in_new:
        print(f"⚠️  Adding {len(missing_in_new)} missing columns to new data")
        for col in missing_in_new:
            new_df[col] = None
    
    # Reorder columns to match existing
    new_df = new_df[existing_df.columns]
    print(f"✓ Aligned columns to existing format ({len(existing_df.columns)} columns)")

print(f"\n[4/5] Checking for duplicates...")
if len(existing_df) > 0 and 'SourceDate' in existing_df.columns:
    # Check if this date already exists
    date_to_add = '2026-01-22'
    duplicates = existing_df[existing_df['SourceDate'] == date_to_add]
    
    if len(duplicates) > 0:
        print(f"⚠️  Found {len(duplicates)} rows for date {date_to_add} in existing data")
        print(f"   Will remove existing data for this date before appending")
        existing_df = existing_df[existing_df['SourceDate'] != date_to_add]
        print(f"✓ Removed duplicates, {len(existing_df):,} rows remaining")
    else:
        print(f"✓ No duplicates found for date {date_to_add}")
else:
    print(f"✓ No duplicate check needed")

print(f"\n[5/5] Appending and saving...")

# Create backup of existing file
if len(existing_df) > 0:
    existing_df_backup = pd.read_csv(csv_file)
    existing_df_backup.to_csv(backup_file, index=False)
    print(f"✓ Backup created: {backup_file}")

# Combine dataframes
combined_df = pd.concat([existing_df, new_df], ignore_index=True)

# Sort by date and stock code
if 'SourceDate' in combined_df.columns and 'Kode Saham' in combined_df.columns:
    combined_df = combined_df.sort_values(['SourceDate', 'Kode Saham'])
    print(f"✓ Sorted by SourceDate and Kode Saham")

# Save combined data
combined_df.to_csv(csv_file, index=False)

print(f"\n{'='*85}")
print("APPEND COMPLETE")
print(f"{'='*85}")
print(f"Total rows in combined file: {len(combined_df):,}")
print(f"Rows added: {len(new_df):,}")
if len(existing_df) > 0:
    print(f"Previous total: {len(existing_df):,}")

if 'SourceDate' in combined_df.columns:
    print(f"\nDate range: {combined_df['SourceDate'].min()} to {combined_df['SourceDate'].max()}")
    print(f"Unique dates: {combined_df['SourceDate'].nunique()}")

if 'Kode Saham' in combined_df.columns:
    print(f"Unique stocks: {combined_df['Kode Saham'].nunique()}")

print(f"\n✓ Data saved to: {csv_file}")
print(f"✓ Backup saved to: {backup_file}")
print(f"{'='*85}")
