import pandas as pd

file1 = "data/reference/Ringkasan Broker-20251201.xlsx"
file2 = "data/reference/Ringkasan Broker-20260121.xlsx"

# Read both files
df1 = pd.read_excel(file1)
df2 = pd.read_excel(file2)

# Add date column
df1['Date'] = '2025-12-01'
df2['Date'] = '2026-01-21'

# Reorder columns with Date first
cols = ['Date'] + [col for col in df1.columns if col != 'Date']
df1 = df1[cols]
df2 = df2[cols]

# Append both files
df_combined = pd.concat([df1, df2], ignore_index=True)

# Save to CSV
output_path = "data/reference/ringkasan_broker_combined_20251201_20260121.csv"
df_combined.to_csv(output_path, index=False)

print(f"✅ Appended broker data with date tracking")
print(f"2025-12-01: {len(df1)} records")
print(f"2026-01-21: {len(df2)} records")
print(f"Total: {len(df_combined)} records")
print(f"Saved to: {output_path}")
