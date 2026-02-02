import pandas as pd

# Read Jan 30 Stock Summary file
df = pd.read_excel("data/reference/Stock Summary-20260130.xlsx", sheet_name=0)

# Print column names to understand structure
print("Columns:", df.columns.tolist())
print("\nDataframe shape:", df.shape)

# Key stocks
key_stocks = ['ADRO', 'BUMI', 'CUAN', 'UNTR', 'BMRI', 'BBRI', 'ANTM', 'BRMS', 'MEDC', 'PTRO', 'INDY']

print("\n=== JAN 30, 2026 PRICES ===\n")

# Looking at column indices - appears to be (Code, Name, Date, Close, High, Low, Open...)
for stock in key_stocks:
    row = df[df.iloc[:, 1] == stock]
    if not row.empty:
        close_price = row.iloc[0, 3]  # Column index 3 appears to be Close
        print(f"{stock}: {close_price}")
    else:
        print(f"{stock}: NOT FOUND")
