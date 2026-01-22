#!/usr/bin/env python3
"""
SWING TRADER ANALYSIS - 8 STOCKS (Banks & Mining)
Strategies: 3.12 (Two MA), 3.14 (Pivot Points), 3.4 (Volatility Filter)
Date: 22 January 2026
Stocks: BBNI, BNGA, PTBA, BBRI, BMRI, HEXA, BSSR, LPPF
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
DATA_FILE = 'data/histories/ringkasan_histories_combined.csv'
STOCKS = ['BBNI', 'BNGA', 'PTBA', 'BBRI', 'BMRI', 'HEXA', 'BSSR', 'LPPF']
LOOKBACK_DAYS = 30

def load_data():
    """Load historical data from CSV"""
    df = pd.read_csv(DATA_FILE)
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])
    return df

def calculate_moving_averages(prices):
    """Strategy 3.12: Two Moving Averages"""
    if len(prices) < 30:
        return None, None, "INSUFFICIENT DATA"
    
    ma_10 = prices[-10:].mean()
    ma_30 = prices[-30:].mean()
    signal = "BULLISH" if ma_10 > ma_30 else "BEARISH"
    
    return ma_10, ma_30, signal

def calculate_pivot_points(high, low, close):
    """Strategy 3.14: Pivot Points"""
    pivot = (high + low + close) / 3
    resistance = 2 * pivot - low
    support = 2 * pivot - high
    
    return pivot, support, resistance

def calculate_volatility(prices):
    """Strategy 3.4: Low-Volatility Anomaly"""
    if len(prices) < 2:
        return None, "INSUFFICIENT DATA"
    
    returns = np.diff(prices) / prices[:-1]
    volatility = np.std(returns) * 100  # Convert to percentage
    
    if volatility < 3:
        quality = "LOW (Excellent)"
    elif volatility < 5:
        quality = "NORMAL (Acceptable)"
    else:
        quality = "HIGH (Risky)"
    
    return volatility, quality

def generate_recommendation(ma_signal, volatility, current_price, support, resistance):
    """Generate swing trade recommendation"""
    if ma_signal == "BEARISH":
        return "❌ SKIP", "Bearish trend (MA(10) < MA(30))"
    
    if volatility is None:
        return "⚠️ SKIP", "Insufficient data"
    
    # Check volatility
    if volatility > 5:
        return "❌ AVOID", "High volatility (>5%)"
    elif volatility > 3:
        status = "⚡ CAUTION"
        reason = "Normal volatility (3-5%)"
    else:
        status = "✅ BUY"
        reason = "Low volatility + Uptrend"
    
    # Calculate stop loss (2% below current)
    stop_loss = current_price * 0.98
    
    return status, reason

def analyze_stock(df, stock_code):
    """Analyze a single stock using swing trading strategies"""
    stock_data = df[df['Kode Saham'] == stock_code].copy()
    
    if len(stock_data) == 0:
        return {
            'stock': stock_code,
            'status': 'NOT FOUND',
            'error': 'No data available'
        }
    
    # Get last 30 days
    recent = stock_data.tail(LOOKBACK_DAYS).sort_values('SourceDate')
    
    if len(recent) < 10:
        return {
            'stock': stock_code,
            'status': 'INSUFFICIENT DATA',
            'days_available': len(recent)
        }
    
    # Extract data
    prices = recent['Penutupan'].values
    current_price = prices[-1]
    high = recent['Tertinggi'].iloc[-1]
    low = recent['Terendah'].iloc[-1]
    
    # Calculate indicators
    ma_10, ma_30, ma_signal = calculate_moving_averages(prices)
    pivot, support, resistance = calculate_pivot_points(high, low, current_price)
    volatility, vol_quality = calculate_volatility(prices)
    
    # Generate recommendation
    recommendation, reason = generate_recommendation(
        ma_signal, volatility, current_price, support, resistance
    )
    
    # Calculate stop loss and target
    stop_loss = current_price * 0.98
    profit_potential = ((resistance - current_price) / current_price) * 100
    
    return {
        'stock': stock_code,
        'current_price': current_price,
        'ma_10': ma_10,
        'ma_30': ma_30,
        'ma_signal': ma_signal,
        'support': support,
        'pivot': pivot,
        'resistance': resistance,
        'volatility': volatility,
        'vol_quality': vol_quality,
        'recommendation': recommendation,
        'reason': reason,
        'stop_loss': stop_loss,
        'profit_potential': profit_potential,
        'days_analyzed': len(recent)
    }

def print_analysis(results):
    """Print formatted analysis results"""
    print("=" * 80)
    print("SWING TRADER ANALYSIS - 8 STOCKS (Banks & Mining)")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%d %B %Y')}")
    print(f"Strategies: 3.12 (MA), 3.14 (Pivot Points), 3.4 (Volatility)")
    print(f"Timeframe: Last {LOOKBACK_DAYS} days")
    print("=" * 80)
    print()
    
    # Sort by recommendation priority
    priority_order = {'✅ BUY': 1, '⚡ CAUTION': 2, '❌ AVOID': 3, '❌ SKIP': 4, 'NOT FOUND': 5}
    results_sorted = sorted(results, key=lambda x: priority_order.get(x.get('recommendation', 'NOT FOUND'), 99))
    
    for i, result in enumerate(results_sorted, 1):
        stock = result['stock']
        
        if result.get('status') == 'NOT FOUND':
            print(f"{i}. {stock}")
            print("=" * 4)
            print(f"❌ STATUS: Data not found in CSV")
            print()
            continue
        
        if result.get('status') == 'INSUFFICIENT DATA':
            print(f"{i}. {stock}")
            print("=" * 4)
            print(f"⚠️ STATUS: Insufficient data (only {result['days_available']} days available)")
            print()
            continue
        
        # Format price
        price = result['current_price']
        if price >= 1000:
            price_str = f"{price:,.0f}"
        else:
            price_str = f"{price:,.0f}"
        
        print(f"{i}. {stock}")
        print("=" * 4)
        print(f"Current Price: {price_str}")
        print()
        
        # MA Signal
        ma_10_str = f"{result['ma_10']:,.0f}" if result['ma_10'] >= 1000 else f"{result['ma_10']:,.0f}"
        ma_30_str = f"{result['ma_30']:,.0f}" if result['ma_30'] >= 1000 else f"{result['ma_30']:,.0f}"
        
        trend_emoji = "🟢" if result['ma_signal'] == "BULLISH" else "🔴"
        print(f"MA(10): {ma_10_str} | MA(30): {ma_30_str} → {trend_emoji} {result['ma_signal']}")
        
        # Pivot Points
        support_str = f"{result['support']:,.0f}"
        resistance_str = f"{result['resistance']:,.0f}"
        pivot_str = f"{result['pivot']:,.0f}"
        
        print(f"Support: {support_str} | Pivot: {pivot_str} | Resistance: {resistance_str}")
        
        # Volatility
        vol_icon = "✅" if result['volatility'] < 3 else "⚡" if result['volatility'] < 5 else "⚠️"
        print(f"Volatility: {result['volatility']:.2f}% → {vol_icon} {result['vol_quality']}")
        print()
        
        # Recommendation
        print(f"RECOMMENDATION: {result['recommendation']}")
        if result['recommendation'] in ['✅ BUY', '⚡ CAUTION']:
            print(f"  Entry: {price_str} (current) or {support_str} (support)")
            print(f"  Target: {resistance_str} (+{result['profit_potential']:.1f}%)")
            print(f"  Stop: {result['stop_loss']:,.0f} (-2%)")
        print(f"  Reason: {result['reason']}")
        print()
    
    # Summary Table
    print("=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Stock':<6} | {'Price':<8} | {'Trend':<8} | {'Vol%':<6} | {'Recommendation':<20}")
    print("-" * 80)
    
    for result in results_sorted:
        if result.get('status') in ['NOT FOUND', 'INSUFFICIENT DATA']:
            status = result.get('status', 'ERROR')
            print(f"{result['stock']:<6} | {'N/A':<8} | {'N/A':<8} | {'N/A':<6} | {status:<20}")
            continue
        
        stock = result['stock']
        price = f"{result['current_price']:,.0f}"
        trend = "🟢 UP" if result['ma_signal'] == "BULLISH" else "🔴 DOWN"
        vol = f"{result['volatility']:.1f}%"
        rec = result['recommendation']
        
        print(f"{stock:<6} | {price:<8} | {trend:<8} | {vol:<6} | {rec:<20}")
    
    print("=" * 80)
    print()
    
    # Top Picks
    buy_stocks = [r for r in results_sorted if r.get('recommendation') == '✅ BUY']
    caution_stocks = [r for r in results_sorted if r.get('recommendation') == '⚡ CAUTION']
    
    print("🎯 TOP PICKS FOR SWING TRADING:")
    print("-" * 40)
    
    if buy_stocks:
        print("\n✅ BEST CHOICES (Low volatility + Uptrend):")
        for r in buy_stocks:
            print(f"  • {r['stock']}: Entry {r['current_price']:,.0f} → Target {r['resistance']:,.0f} (+{r['profit_potential']:.1f}%)")
    
    if caution_stocks:
        print("\n⚡ SECONDARY CHOICES (Higher volatility):")
        for r in caution_stocks:
            print(f"  • {r['stock']}: Entry {r['current_price']:,.0f} → Target {r['resistance']:,.0f} (+{r['profit_potential']:.1f}%)")
    
    avoid_stocks = [r for r in results_sorted if r.get('recommendation') in ['❌ AVOID', '❌ SKIP']]
    if avoid_stocks:
        print("\n❌ AVOID:")
        for r in avoid_stocks:
            reason = r.get('reason', 'Unknown')
            print(f"  • {r['stock']}: {reason}")
    
    print()
    print("=" * 80)
    print("Analysis complete. Use this data for swing trading decisions (2-5 day holds).")
    print("=" * 80)

def main():
    """Main execution"""
    print("Loading data...")
    df = load_data()
    print(f"✓ Loaded {len(df)} rows from CSV")
    print()
    
    results = []
    for stock in STOCKS:
        result = analyze_stock(df, stock)
        results.append(result)
    
    print_analysis(results)

if __name__ == "__main__":
    main()
