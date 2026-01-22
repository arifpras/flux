#!/usr/bin/env python3
"""
ENHANCED SWING TRADER ANALYSIS - 11 STOCKS
Base Strategies: 3.12 (MA), 3.14 (Pivot), 3.4 (Volatility)
Enhancement: 3.13 (Bollinger Bands), 3.10 (Short-Term Reversals)
Date: 22 January 2026
Stocks: ASII, ADRO, BUMI, BBNI, BNGA, PTBA, BBRI, BMRI, HEXA, BSSR, LPPF
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
DATA_FILE = 'data/histories/ringkasan_histories_combined.csv'
STOCKS = ['PTBA', 'ASII', 'LPPF', 'HEXA', 'BBNI', 'BBRI', 'BNGA', 'BSSR', 'ADRO', 'BMRI', 'BUMI']
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
    volatility = np.std(returns) * 100
    
    if volatility < 3:
        quality = "LOW (Excellent)"
    elif volatility < 5:
        quality = "NORMAL (Acceptable)"
    else:
        quality = "HIGH (Risky)"
    
    return volatility, quality

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Strategy 3.13: Bollinger Bands"""
    if len(prices) < period:
        return None, None, None, "INSUFFICIENT DATA"
    
    # Use last 20 days for BB calculation
    recent_prices = prices[-period:]
    ma_20 = recent_prices.mean()
    std = recent_prices.std()
    
    upper_band = ma_20 + (std_dev * std)
    lower_band = ma_20 - (std_dev * std)
    
    current_price = prices[-1]
    
    # Calculate position within bands (0 = lower band, 1 = upper band)
    bb_position = (current_price - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
    
    # Determine signal
    if bb_position < 0.2:
        signal = "OVERSOLD (Near Lower Band - Strong Buy)"
    elif bb_position < 0.4:
        signal = "BELOW MIDDLE (Good Buy)"
    elif bb_position < 0.6:
        signal = "NEUTRAL (Middle Zone)"
    elif bb_position < 0.8:
        signal = "ABOVE MIDDLE (Consider Sell)"
    else:
        signal = "OVERBOUGHT (Near Upper Band - Take Profit)"
    
    return lower_band, ma_20, upper_band, signal, bb_position

def calculate_short_term_reversal(prices):
    """Strategy 3.10: Short-Term Reversals"""
    if len(prices) < 5:
        return None, "INSUFFICIENT DATA"
    
    # Calculate 1-day, 2-day, 3-day returns
    return_1d = (prices[-1] / prices[-2] - 1) * 100
    return_2d = (prices[-1] / prices[-3] - 1) * 100
    return_3d = (prices[-1] / prices[-4] - 1) * 100
    
    # Short-term reversal: Recent decline = buying opportunity
    if return_1d < -1 and return_3d < -2:
        signal = "STRONG PULLBACK (Excellent Entry)"
        opportunity = "HIGH"
    elif return_1d < 0 and return_2d < -1:
        signal = "MINOR PULLBACK (Good Entry)"
        opportunity = "MEDIUM"
    elif return_1d > 2:
        signal = "RECENT SURGE (Wait for Pullback)"
        opportunity = "LOW"
    else:
        signal = "STABLE (Normal Entry)"
        opportunity = "MEDIUM"
    
    return return_1d, return_2d, return_3d, signal, opportunity

def generate_enhanced_recommendation(ma_signal, volatility, bb_signal, bb_position, 
                                    reversal_opportunity, current_price, support, 
                                    resistance, bb_lower, bb_upper):
    """Generate enhanced swing trade recommendation"""
    if ma_signal == "BEARISH":
        return "❌ SKIP", "Bearish trend", None, None, None
    
    if volatility is None or volatility > 5:
        return "❌ AVOID", "High volatility (>5%)", None, None, None
    
    # Calculate scores
    score = 0
    reasons = []
    
    # Volatility score
    if volatility < 2:
        score += 3
        reasons.append("Ultra-low volatility")
    elif volatility < 3:
        score += 2
        reasons.append("Low volatility")
    else:
        score += 1
        reasons.append("Normal volatility")
    
    # Bollinger Band score
    if bb_position < 0.3:
        score += 3
        reasons.append("Near lower BB (oversold)")
        entry_type = "EXCELLENT"
    elif bb_position < 0.5:
        score += 2
        reasons.append("Below middle BB")
        entry_type = "GOOD"
    elif bb_position < 0.7:
        score += 1
        reasons.append("Middle zone")
        entry_type = "FAIR"
    else:
        score += 0
        reasons.append("Near upper BB (wait)")
        entry_type = "POOR"
    
    # Reversal opportunity score
    if reversal_opportunity == "HIGH":
        score += 3
        reasons.append("Recent pullback")
    elif reversal_opportunity == "MEDIUM":
        score += 1
    else:
        score += 0
        reasons.append("No pullback (overextended)")
    
    # Generate recommendation
    if score >= 7:
        status = "🥇 EXCELLENT BUY"
        priority = "HIGH"
    elif score >= 5:
        status = "✅ GOOD BUY"
        priority = "MEDIUM"
    elif score >= 3:
        status = "⚡ FAIR BUY"
        priority = "LOW"
    else:
        status = "⏳ WAIT"
        priority = "WAIT"
        reasons.append("Better entry later")
    
    # Enhanced targets
    standard_target = resistance
    enhanced_target = bb_upper if bb_upper > resistance else resistance
    
    # Enhanced entry
    if bb_lower < support:
        enhanced_entry = bb_lower
        entry_reason = "Bollinger lower band (better than support)"
    else:
        enhanced_entry = support
        entry_reason = "Support level"
    
    return status, " + ".join(reasons), enhanced_entry, enhanced_target, priority

def analyze_stock(df, stock_code):
    """Analyze a single stock using enhanced swing strategies"""
    stock_data = df[df['Kode Saham'] == stock_code].copy()
    
    if len(stock_data) == 0:
        return {'stock': stock_code, 'status': 'NOT FOUND'}
    
    recent = stock_data.tail(LOOKBACK_DAYS).sort_values('SourceDate')
    
    if len(recent) < 10:
        return {'stock': stock_code, 'status': 'INSUFFICIENT DATA', 'days_available': len(recent)}
    
    # Extract data
    prices = recent['Penutupan'].values
    current_price = prices[-1]
    high = recent['Tertinggi'].iloc[-1]
    low = recent['Terendah'].iloc[-1]
    
    # Base strategies
    ma_10, ma_30, ma_signal = calculate_moving_averages(prices)
    pivot, support, resistance = calculate_pivot_points(high, low, current_price)
    volatility, vol_quality = calculate_volatility(prices)
    
    # Enhancement strategies
    bb_lower, bb_mid, bb_upper, bb_signal, bb_position = calculate_bollinger_bands(prices)
    return_1d, return_2d, return_3d, reversal_signal, reversal_opportunity = calculate_short_term_reversal(prices)
    
    # Enhanced recommendation
    recommendation, reason, enhanced_entry, enhanced_target, priority = generate_enhanced_recommendation(
        ma_signal, volatility, bb_signal, bb_position, reversal_opportunity,
        current_price, support, resistance, bb_lower, bb_upper
    )
    
    # Calculate profits
    stop_loss = current_price * 0.98
    
    # Standard profit (pivot resistance)
    standard_profit = ((resistance - current_price) / current_price) * 100
    
    # Enhanced profit (Bollinger upper band)
    enhanced_profit = ((enhanced_target - enhanced_entry) / enhanced_entry) * 100 if enhanced_target and enhanced_entry else standard_profit
    
    # Entry improvement
    entry_improvement = ((current_price - enhanced_entry) / current_price) * 100 if enhanced_entry else 0
    
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
        'bb_lower': bb_lower,
        'bb_mid': bb_mid,
        'bb_upper': bb_upper,
        'bb_signal': bb_signal,
        'bb_position': bb_position,
        'return_1d': return_1d,
        'return_2d': return_2d,
        'return_3d': return_3d,
        'reversal_signal': reversal_signal,
        'reversal_opportunity': reversal_opportunity,
        'recommendation': recommendation,
        'reason': reason,
        'priority': priority,
        'enhanced_entry': enhanced_entry,
        'enhanced_target': enhanced_target,
        'standard_profit': standard_profit,
        'enhanced_profit': enhanced_profit,
        'entry_improvement': entry_improvement,
        'stop_loss': stop_loss,
        'days_analyzed': len(recent)
    }

def print_enhanced_analysis(results):
    """Print enhanced analysis results"""
    print("=" * 90)
    print("ENHANCED SWING TRADER ANALYSIS - 11 STOCKS")
    print("=" * 90)
    print(f"Date: {datetime.now().strftime('%d %B %Y')}")
    print(f"Base: 3.12 (MA), 3.14 (Pivot), 3.4 (Volatility)")
    print(f"Enhanced: 3.13 (Bollinger Bands), 3.10 (Short-Term Reversals)")
    print("=" * 90)
    print()
    
    # Sort by priority and enhanced profit
    priority_order = {'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'WAIT': 4}
    results_sorted = sorted(
        [r for r in results if r.get('status') not in ['NOT FOUND', 'INSUFFICIENT DATA']],
        key=lambda x: (priority_order.get(x.get('priority', 'WAIT'), 99), -x.get('enhanced_profit', 0))
    )
    
    for i, result in enumerate(results_sorted, 1):
        stock = result['stock']
        price = result['current_price']
        price_str = f"{price:,.0f}"
        
        print(f"{i}. {stock} - {result['recommendation']}")
        print("=" * 90)
        print(f"Current Price: IDR {price_str}")
        print()
        
        # Trend & Volatility
        ma_emoji = "🟢" if result['ma_signal'] == "BULLISH" else "🔴"
        print(f"TREND: MA(10): {result['ma_10']:,.0f} | MA(30): {result['ma_30']:,.0f} → {ma_emoji} {result['ma_signal']}")
        vol_emoji = "✅" if result['volatility'] < 3 else "⚡" if result['volatility'] < 5 else "⚠️"
        print(f"VOLATILITY: {result['volatility']:.2f}% → {vol_emoji} {result['vol_quality']}")
        print()
        
        # Bollinger Bands (NEW)
        bb_emoji = "🔵" if result['bb_position'] < 0.3 else "🟢" if result['bb_position'] < 0.7 else "🟡"
        print(f"BOLLINGER BANDS: {bb_emoji} {result['bb_signal']}")
        print(f"  Lower: {result['bb_lower']:,.0f} | Middle: {result['bb_mid']:,.0f} | Upper: {result['bb_upper']:,.0f}")
        print(f"  Position: {result['bb_position']:.1%} (0%=oversold, 100%=overbought)")
        print()
        
        # Short-Term Reversal (NEW)
        rev_emoji = "📉" if result['reversal_opportunity'] == "HIGH" else "➡️"
        print(f"SHORT-TERM REVERSAL: {rev_emoji} {result['reversal_signal']}")
        print(f"  1-day: {result['return_1d']:+.2f}% | 2-day: {result['return_2d']:+.2f}% | 3-day: {result['return_3d']:+.2f}%")
        print(f"  Opportunity Level: {result['reversal_opportunity']}")
        print()
        
        # Standard vs Enhanced Setup
        print("TRADING SETUP COMPARISON:")
        print()
        print(f"  STANDARD METHOD (3.12+3.14):")
        print(f"    Entry: {price_str} (current) or {result['support']:,.0f} (support)")
        print(f"    Target: {result['resistance']:,.0f} (pivot resistance)")
        print(f"    Profit: +{result['standard_profit']:.1f}%")
        print()
        print(f"  ENHANCED METHOD (+ Bollinger + Reversal):")
        if result['enhanced_entry'] and result['enhanced_target']:
            print(f"    Entry: {result['enhanced_entry']:,.0f} (BB/support - SAVE {result['entry_improvement']:.1f}%)")
            print(f"    Target: {result['enhanced_target']:,.0f} (BB upper band)")
            print(f"    Profit: +{result['enhanced_profit']:.1f}%")
            print(f"    Stop: {result['stop_loss']:,.0f} (-2%)")
            print()
            profit_improvement = result['enhanced_profit'] - result['standard_profit']
            improvement_pct = (profit_improvement / result['standard_profit'] * 100) if result['standard_profit'] > 0 else 0
            print(f"  💰 PROFIT IMPROVEMENT: +{profit_improvement:.1f}% ({improvement_pct:+.0f}% better)")
        else:
            print(f"    N/A - Stock should be avoided")
            print()
        print()
        
        # Why this recommendation
        print(f"RECOMMENDATION REASON:")
        print(f"  {result['reason']}")
        print()
        print()
    
    # Summary
    print("=" * 90)
    print("ENHANCED STRATEGY SUMMARY")
    print("=" * 90)
    print()
    
    high_priority = [r for r in results_sorted if r.get('priority') == 'HIGH']
    medium_priority = [r for r in results_sorted if r.get('priority') == 'MEDIUM']
    
    if high_priority:
        print("🥇 HIGH PRIORITY TRADES (Best Setup):")
        for r in high_priority:
            print(f"  • {r['stock']}: Entry {r['enhanced_entry']:,.0f} → Target {r['enhanced_target']:,.0f} (+{r['enhanced_profit']:.1f}%)")
            print(f"    Advantage: {r['entry_improvement']:.1f}% better entry + {r['enhanced_profit'] - r['standard_profit']:.1f}% higher target")
        print()
    
    if medium_priority:
        print("✅ MEDIUM PRIORITY TRADES (Good Setup):")
        for r in medium_priority:
            print(f"  • {r['stock']}: Entry {r['enhanced_entry']:,.0f} → Target {r['enhanced_target']:,.0f} (+{r['enhanced_profit']:.1f}%)")
        print()
    
    # Wait signals
    wait_stocks = [r for r in results_sorted if r.get('priority') == 'WAIT']
    if wait_stocks:
        print("⏳ WAIT FOR BETTER ENTRY:")
        for r in wait_stocks:
            print(f"  • {r['stock']}: {r['reason']}")
        print()
    
    # Calculate portfolio improvement
    top_3 = results_sorted[:3]
    standard_avg = np.mean([r['standard_profit'] for r in top_3])
    enhanced_avg = np.mean([r['enhanced_profit'] for r in top_3])
    improvement = enhanced_avg - standard_avg
    
    print("=" * 90)
    print("PORTFOLIO IMPACT (Top 3 Stocks):")
    print(f"  Standard Method Avg Profit: +{standard_avg:.2f}%")
    print(f"  Enhanced Method Avg Profit: +{enhanced_avg:.2f}%")
    print(f"  Improvement: +{improvement:.2f}% ({improvement/standard_avg*100:+.0f}% better)")
    print()
    print(f"  On 100M capital:")
    print(f"    Standard Expected: +{standard_avg * 100_000_000 / 100:,.0f}")
    print(f"    Enhanced Expected: +{enhanced_avg * 100_000_000 / 100:,.0f}")
    print(f"    Extra Profit: +{improvement * 100_000_000 / 100:,.0f}")
    print("=" * 90)

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
    
    print_enhanced_analysis(results)

if __name__ == "__main__":
    main()
