import pandas as pd

# Load Feb 2 data
stock_df = pd.read_excel("data/reference/Stock Summary-20260202.xlsx", sheet_name=0)
broker_df = pd.read_excel("data/reference/Broker Summary-20260202.xlsx", sheet_name=0)

key_stocks = ['ADRO', 'BUMI', 'CUAN', 'BBRI', 'BMRI', 'UNTR', 'ANTM', 'MEDC', 'BRMS', 'PTRO', 'INDY']

# Get Feb 2 prices
feb2_prices = stock_df[stock_df['Stock Code'].isin(key_stocks)][['Stock Code', 'Open Price', 'Close', 'Change']].copy()
feb2_prices.columns = ['Stock', 'Feb2_Open', 'Feb2_Close', 'Feb2_Change']
feb2_prices = feb2_prices.sort_values('Stock')

print("="*100)
print("FEB 2, 2026 STOCK PRICES UPDATE")
print("="*100)
print("\nStock Prices on Feb 2, 2026:")
print(feb2_prices.to_string(index=False))

print("\n\nPRICE CHANGES vs JAN 30 ESTIMATES:")
print("="*100)

# Jan 30 prices from analysis
jan30_prices = {
    'ADRO': 2350,
    'BUMI': 260,  # midpoint of 256-264
    'CUAN': 1827,
    'BBRI': 3810,
    'BMRI': 4980,
    'UNTR': 27450,
    'ANTM': None,  # Not clearly stated
    'MEDC': None,
    'BRMS': None,
    'PTRO': None,
    'INDY': None
}

feb2_close_prices = {
    'ADRO': 2140,
    'ANTM': 3810,
    'BBRI': 3830,
    'BMRI': 4800,
    'BRMS': 920,
    'BUMI': 265,  # Will check below
    'CUAN': None,  # Will check below
    'INDY': None,
    'MEDC': None,
    'PTRO': None,
    'UNTR': None
}

# Get all prices
all_stocks = stock_df[stock_df['Stock Code'].isin(key_stocks)][['Stock Code', 'Close']].set_index('Stock Code')['Close'].to_dict()
print("\nAll stocks with Feb 2 closing prices:")
for stock, price in sorted(all_stocks.items()):
    print(f"  {stock}: IDR {price:,.0f}")

print("\n\nBROKER SUMMARY - FEB 2, 2026")
print("="*100)

# Top brokers by value
top_brokers = broker_df.nlargest(10, 'Value')[['Company Code', 'Company Name', 'Value', 'Frequency']]
print("\nTop 10 Foreign Brokers by Transaction Value:")
for idx, row in top_brokers.iterrows():
    value_t = row['Value'] / 1e12
    print(f"  {row['Company Code']} {row['Company Name']:<40} {value_t:>7.2f}T IDR (Freq: {row['Frequency']:>6})")

print("\n\nKEY OBSERVATIONS:")
print("="*100)

# Check price movements
print("\nPrice Changes (Jan 30 → Feb 2):")
for stock in ['ADRO', 'BUMI', 'BBRI', 'BMRI']:
    if stock in all_stocks and stock in jan30_prices and jan30_prices[stock]:
        old_price = jan30_prices[stock]
        new_price = all_stocks.get(stock)
        if new_price:
            change_pct = ((new_price - old_price) / old_price) * 100
            direction = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
            print(f"  {stock}: {old_price:>7,.0f} → {new_price:>7,.0f}  {direction} {change_pct:+.2f}%")
