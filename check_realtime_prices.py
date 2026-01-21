import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Indonesian stocks (ticker format for Yahoo Finance)
stocks = ['ADRO.JK', 'ASII.JK', 'BMTR.JK', 'BSIM.JK', 'BNBR.JK']

print("=" * 80)
print("REAL-TIME STOCK PRICES - 21 JANUARY 2026")
print("=" * 80)
print()

# Create comparison table
data = []

for ticker in stocks:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='10d')
        
        if not hist.empty:
            latest = hist.iloc[-1]
            prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else latest['Close']
            change_pct = ((latest['Close'] - prev_close) / prev_close * 100)
            
            # 5-day change
            five_days_ago = hist.iloc[0]['Close'] if len(hist) >= 5 else hist.iloc[0]['Close']
            five_day_change = ((latest['Close'] - five_days_ago) / five_days_ago * 100)
            
            stock_name = ticker.replace('.JK', '')
            data.append({
                'Stock': stock_name,
                'Close': f"{latest['Close']:,.0f}",
                'Day Change %': f"{change_pct:+.2f}%",
                '5D Change %': f"{five_day_change:+.2f}%",
                'High': f"{latest['High']:,.0f}",
                'Low': f"{latest['Low']:,.0f}",
                'Volume': f"{int(latest['Volume']):,}"
            })
            
            print(f"✓ {stock_name}")
            
    except Exception as e:
        print(f"✗ {ticker}: {str(e)}")

# Display as table
if data:
    df = pd.DataFrame(data)
    print()
    print(df.to_string(index=False))
    print()
    print("=" * 80)
    print("RECOMMENDATION VALIDATION AGAINST REAL PRICES")
    print("=" * 80)
    print()
    
    # Check ADRO specifically
    adro_data = [d for d in data if d['Stock'] == 'ADRO']
    if adro_data:
        print("🎯 ADRO ANALYSIS:")
        print(f"   Current Price: Rp {adro_data[0]['Close']}")
        print(f"   My Recommendation Entry: Rp 2,240-2,260")
        print(f"   Status: {'✅ MATCH' if '2200' in adro_data[0]['Close'] or '2300' in adro_data[0]['Close'] else '⚠️ CHECK'}")
        print()
