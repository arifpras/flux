"""Day-trading scanner: Find stocks likely to pump on next opening (Jan 16, 2026)."""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
combined_path = BASE_DIR / 'data' / 'histories' / 'ringkasan_histories_combined.csv'
watchlist_path = BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts' / 'manipulation_watchlist.csv'

# Load data
df = pd.read_csv(combined_path)
watchlist = pd.read_csv(watchlist_path)

df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

# Convert to numeric
for col in ['Penutupan', 'Sebelumnya', 'Volume', 'Nilai']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

for col in ['Penutupan', 'Sebelumnya', 'Volume', 'Nilai']:
    if col in watchlist.columns:
        watchlist[col] = pd.to_numeric(watchlist[col], errors='coerce')

df['return'] = (df['Penutupan'] / df['Sebelumnya']) - 1.0

# Get latest date in data
latest_date = df['SourceDate'].max()
print(f"\n{'='*130}")
print(f"🚀 DAY-TRADING SCANNER - Pumping Stocks Alert for Next Opening")
print(f"Latest data date: {latest_date.strftime('%Y-%m-%d')}")
print(f"{'='*130}\n")

# Focus on stocks flagged in recent days (last 3 days of data)
recent_dates = sorted(df['SourceDate'].unique())[-3:]
recent_watchlist = watchlist[watchlist['SourceDate'].isin(recent_dates)].copy()

print(f"📊 Analyzing {len(recent_watchlist)} flagged stocks from recent {len(recent_dates)} days\n")

# Score stocks based on bullish manipulation patterns
scores = []

for ticker in recent_watchlist['Kode Saham'].unique():
    ticker_watchlist = recent_watchlist[recent_watchlist['Kode Saham'] == ticker].sort_values('SourceDate')
    ticker_combined = df[df['Kode Saham'] == ticker].sort_values('SourceDate')
    
    latest_row = ticker_watchlist.iloc[-1]
    latest_combined = ticker_combined.iloc[-1]
    
    # Bullish signals (pumping indicators)
    bullish_score = 0
    signals = []
    
    # 1. Volume spike (vol_spike_up)
    if 'vol_spike_up' in str(latest_row['flags']):
        bullish_score += 3
        signals.append("Volume spike + positive return")
    
    # 2. Book buy imbalance (more bids than asks)
    if 'book_buy_imbalance' in str(latest_row['flags']):
        bullish_score += 2
        signals.append("Buy imbalance (more bids)")
    
    # 3. Foreign divergence DOWN (price up despite foreign selling = domestic strength)
    if 'foreign_div_down' in str(latest_row['flags']):
        bullish_score += 2
        signals.append("Domestic strength (price up vs foreign selling)")
    
    # 4. Momentum (recent positive returns)
    recent_returns = ticker_combined.iloc[-5:]['return'].mean()
    if recent_returns > 0.01:
        bullish_score += 2
        signals.append(f"Positive momentum (+{recent_returns*100:.2f}%)")
    
    # 5. Volume strength
    recent_vol = ticker_combined.iloc[-5:]['Volume'].mean()
    latest_vol = latest_combined['Volume']
    if latest_vol > recent_vol * 0.8:
        bullish_score += 1
        signals.append("Strong volume maintained")
    
    # 6. Price above recent MA
    ma5 = ticker_combined.iloc[-5:]['Penutupan'].mean()
    if latest_combined['Penutupan'] > ma5:
        bullish_score += 1
        signals.append(f"Price above 5-day MA")
    
    if bullish_score >= 2:
        scores.append({
            'ticker': ticker,
            'price': latest_combined['Penutupan'],
            'prev_price': latest_combined['Sebelumnya'],
            'return_pct': latest_row['return'] * 100,
            'volume': latest_combined['Volume'],
            'foreign_ratio': latest_row.get('foreign_ratio', 0),
            'score': bullish_score,
            'signals': signals,
            'last_date': latest_row['SourceDate']
        })

# Sort by bullish score
scores.sort(key=lambda x: x['score'], reverse=True)

print("🔥 TOP PUMPING CANDIDATES (Ranked by Bullish Signals):\n")
print(f"{'Rank':<5} {'Ticker':<8} {'Price':<8} {'Return%':<10} {'Volume (B)':<12} {'Score':<8} {'Signals'}")
print("-" * 130)

for idx, stock in enumerate(scores[:20], 1):
    vol_b = stock['volume'] / 1e9
    signals_str = " | ".join(stock['signals'][:2])  # Show top 2 signals
    print(f"{idx:<5} {stock['ticker']:<8} {stock['price']:>7.0f} {stock['return_pct']:>9.2f}% {vol_b:>11.2f}B {stock['score']:<8} {signals_str}")

print(f"\n{'='*130}")
print("\n⚡ HOW TO USE THIS:")
print("  • Top scorers = highest bullish manipulation signals")
print("  • Look for: Volume spikes + Buy imbalance + Positive momentum")
print("  • Entry: At market open on Jan 16, buy those showing peak signals")
print("  • Stop loss: Below 2% from entry (day-trading risk)")
print("  • Target: 2-5% gain intraday (typical pump duration)")
print("\n📌 CAUTION:")
print("  • These are manipulated stocks - reversals can be sharp")
print("  • Use tight stops and take profits quickly")
print("  • Monitor volume throughout the day - when volume drops, exit")
print(f"\n{'='*130}\n")

# Export to CSV for reference
export_df = pd.DataFrame(scores)
export_path = BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts' / 'day_trading_candidates.csv'
export_df.to_csv(export_path, index=False)
print(f"✅ Saved to: {export_path}")
