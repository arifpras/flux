#!/usr/bin/env python3
"""
SWING TRADER ANALYSIS - ASII, ADRO, BUMI
Strategies: 3.12 (Two Moving Averages), 3.14 (Pivot Points), 3.4 (Volatility)
Date: 22 January 2026
"""

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/histories/ringkasan_histories_combined.csv')

# Sort by date to get latest data
df['SourceDate'] = pd.to_datetime(df['SourceDate'])
df = df.sort_values('SourceDate')

# Analyze each stock
stocks = ['ASII', 'ADRO', 'BUMI']

print("=" * 100)
print("SWING TRADER ANALYSIS - STRATEGIES 3.12, 3.14, 3.4")
print("Date: 22 January 2026 | Timeframe: Last 30 days")
print("=" * 100)

for stock in stocks:
    stock_data = df[df['Kode Saham'] == stock].copy()
    
    if len(stock_data) == 0:
        print(f"\n❌ {stock} NOT FOUND")
        continue
    
    # Get last 30 days
    recent = stock_data.tail(30).copy()
    recent = recent.sort_values('SourceDate')
    
    if len(recent) < 5:
        print(f"\n⚠️  {stock} - Insufficient data ({len(recent)} days)")
        continue
    
    prices = recent['Penutupan'].values
    highs = recent['Tertinggi'].values
    lows = recent['Terendah'].values
    close = prices[-1]
    high_30 = highs.max()
    low_30 = lows.min()
    open_price = recent['Open Price'].values[-1]
    
    # Strategy 3.12: Moving Averages
    ma_10 = prices[-10:].mean() if len(prices) >= 10 else prices.mean()
    ma_30 = prices[-30:].mean() if len(prices) >= 30 else prices.mean()
    
    # Strategy 3.14: Pivot Points
    h = highs[-1]
    l = lows[-1]
    c = close
    pivot = (h + l + c) / 3
    resistance = 2 * pivot - l
    support = 2 * pivot - h
    
    # Strategy 3.4: Volatility
    returns = np.diff(prices) / prices[:-1]
    volatility = np.std(returns) * 100
    
    # Signals
    ma_signal = "🟢 BULLISH" if ma_10 > ma_30 else "🔴 BEARISH"
    
    # Price position
    if close < support:
        price_level = "📍 AT SUPPORT (BUY ZONE)"
    elif close > resistance:
        price_level = "📍 AT RESISTANCE (SELL ZONE)"
    else:
        price_level = "📍 IN MIDDLE"
    
    vol_signal = "✅ LOW VOLATILITY (Good)" if volatility < 3 else "⚠️  HIGH VOLATILITY (Risky)" if volatility > 5 else "⚡ NORMAL VOLATILITY"
    
    # Print analysis
    print(f"\n{'-' * 100}")
    print(f"📊 {stock.upper()}")
    print(f"{'-' * 100}")
    print(f"Latest Date: {recent['SourceDate'].iloc[-1].strftime('%d %b %Y')}")
    print(f"\n💹 PRICE LEVELS:")
    print(f"   Current Price:     {close:>10,.0f}")
    print(f"   Open (today):      {open_price:>10,.0f}")
    print(f"   30-day High:       {high_30:>10,.0f}")
    print(f"   30-day Low:        {low_30:>10,.0f}")
    
    print(f"\n📈 STRATEGY 3.12 - TWO MOVING AVERAGES:")
    print(f"   MA(10):            {ma_10:>10,.0f}")
    print(f"   MA(30):            {ma_30:>10,.0f}")
    print(f"   Signal:            {ma_signal}")
    
    print(f"\n🎯 STRATEGY 3.14 - PIVOT POINTS (ENTRY/EXIT):")
    print(f"   Resistance:        {resistance:>10,.0f}  ← 🔴 SELL TARGET")
    print(f"   Pivot:             {pivot:>10,.0f}")
    print(f"   Support:           {support:>10,.0f}  ← 🟢 BUY ZONE")
    print(f"   Price Level:       {price_level}")
    
    print(f"\n⚡ STRATEGY 3.4 - VOLATILITY CHECK:")
    print(f"   Volatility (σ):    {volatility:>10.2f}%")
    print(f"   Assessment:        {vol_signal}")
    
    # Swing trading recommendation
    print(f"\n🎲 SWING TRADE SETUP:")
    if ma_10 > ma_30:
        if close < resistance:
            print(f"   Action: 🟢 BUY near support ({support:,.0f})")
            print(f"   Target: {resistance:,.0f} (resistance level)")
            print(f"   Stop:   {support * 0.98:,.0f} (-2%)")
            if volatility < 3:
                print(f"   ✅ RECOMMENDED - Good trend + Low volatility")
            elif volatility < 5:
                print(f"   ⚠️  CAUTION - Good trend but higher volatility")
            else:
                print(f"   ❌ AVOID - High volatility (>5%)")
        else:
            print(f"   Action: 🔴 HOLD/WAIT - Already near resistance")
            print(f"   Entry: Wait for pullback to {pivot:,.0f}")
    else:
        print(f"   Action: 🔴 HOLD/SHORT - Downtrend (MA(10) < MA(30))")
        print(f"   Short Target: {support:,.0f}")
        print(f"   Short Stop:   {resistance:,.0f}")

print(f"\n{'=' * 100}\n")
print("SUMMARY TABLE")
print("=" * 100)

# Summary table
summary_data = []
for stock in stocks:
    stock_data = df[df['Kode Saham'] == stock].copy()
    if len(stock_data) == 0:
        continue
    
    recent = stock_data.tail(30).copy()
    recent = recent.sort_values('SourceDate')
    if len(recent) < 5:
        continue
    
    prices = recent['Penutupan'].values
    ma_10 = prices[-10:].mean()
    ma_30 = prices[-30:].mean()
    
    returns = np.diff(prices) / prices[:-1]
    volatility = np.std(returns) * 100
    
    trend = "🟢 UP" if ma_10 > ma_30 else "🔴 DOWN"
    
    h = recent['Tertinggi'].values[-1]
    l = recent['Terendah'].values[-1]
    c = prices[-1]
    pivot = (h + l + c) / 3
    support = 2 * pivot - h
    resistance = 2 * pivot - l
    
    vol_status = "✅ Good" if volatility < 3 else "⚡ OK" if volatility < 5 else "⚠️  Risky"
    
    summary_data.append({
        'Stock': stock,
        'Price': f"{c:,.0f}",
        'MA(10)': f"{ma_10:,.0f}",
        'MA(30)': f"{ma_30:,.0f}",
        'Trend': trend,
        'Support': f"{support:,.0f}",
        'Resistance': f"{resistance:,.0f}",
        'Vol%': f"{volatility:.1f}%",
        'Vol Status': vol_status
    })

summary_df = pd.DataFrame(summary_data)
print(summary_df.to_string(index=False))
print("\n" + "=" * 100)
