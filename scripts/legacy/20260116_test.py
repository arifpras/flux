import pandas as pd
print("Testing pandas import...")
df = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
print(f"Loaded {len(df)} rows")
print("✓ Success")
