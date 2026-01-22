"""Detect pump-end signals in BUMI using volume, momentum, and foreign flow divergence."""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
combined_path = BASE_DIR / 'data' / 'histories' / 'ringkasan_histories_combined.csv'

df = pd.read_csv(combined_path)
bumi = df[df['Kode Saham'] == 'BUMI'].copy()
bumi['SourceDate'] = pd.to_datetime(bumi['SourceDate'])

# Convert to numeric
for col in ['Sebelumnya', 'Penutupan', 'Volume', 'Nilai', 'Foreign Buy', 'Foreign Sell', 'Frekuensi']:
    bumi[col] = pd.to_numeric(bumi[col], errors='coerce')

bumi.sort_values('SourceDate', inplace=True)

# Calculate metrics
bumi['return'] = (bumi['Penutupan'] / bumi['Sebelumnya']) - 1.0
bumi['high_low_range'] = (bumi['Tertinggi'] - bumi['Terendah']) / bumi['Sebelumnya']
bumi['foreign_net'] = bumi['Foreign Buy'] - bumi['Foreign Sell']
bumi['foreign_ratio'] = bumi['foreign_net'] / (bumi['Volume'] + 1e-9)
bumi['volume_ma5'] = bumi['Volume'].rolling(5).mean()
bumi['vol_strength'] = bumi['Volume'] / (bumi['volume_ma5'] + 1e-9)

# Pump-end signals
signals = []

print("\n" + "="*120)
print("🔍 BUMI PUMP-END DETECTION ANALYSIS")
print("="*120)

for idx in range(len(bumi)):
    row = bumi.iloc[idx]
    date = row['SourceDate']
    
    # Signal 1: Volume divergence (price up but volume declining)
    if idx >= 4:
        recent_vol = bumi.iloc[max(0, idx-4):idx]['Volume'].mean()
        curr_vol = row['Volume']
        vol_divergence = curr_vol < recent_vol * 0.7  # Volume dropped 30%+
    else:
        vol_divergence = False
    
    # Signal 2: Momentum weakening (returns declining despite price up)
    if idx >= 3:
        recent_returns = bumi.iloc[max(0, idx-3):idx]['return'].mean()
        curr_return = row['return']
        momentum_weakening = (curr_return < recent_returns * 0.5) and (recent_returns > 0)
    else:
        momentum_weakening = False
    
    # Signal 3: Foreign divergence strengthening (price up but foreign heavy selling)
    foreign_dump = (row['foreign_ratio'] < -0.2) and (row['return'] > 0.01)
    
    # Signal 4: Price consolidation after spike (low volatility after high volume day)
    if idx >= 1:
        prev_range = bumi.iloc[idx-1]['high_low_range']
        curr_range = row['high_low_range']
        consolidation = (curr_range < 0.02) and (prev_range > 0.05)
    else:
        consolidation = False
    
    # Signal 5: Frequency/participation declining (fewer trades despite volume)
    if idx >= 3:
        recent_freq_avg = bumi.iloc[max(0, idx-3):idx]['Frekuensi'].mean()
        curr_freq = row['Frekuensi']
        freq_divergence = curr_freq < recent_freq_avg * 0.7
    else:
        freq_divergence = False
    
    signal_count = sum([vol_divergence, momentum_weakening, foreign_dump, consolidation, freq_divergence])
    
    if signal_count >= 2:
        signals.append({
            'date': date,
            'price': row['Penutupan'],
            'volume': row['Volume'],
            'return': row['return'],
            'foreign_ratio': row['foreign_ratio'],
            'signal_count': signal_count,
            'signals': [
                f"Vol divergence: {vol_divergence}",
                f"Momentum weakening: {momentum_weakening}",
                f"Foreign dump: {foreign_dump}",
                f"Consolidation: {consolidation}",
                f"Freq divergence: {freq_divergence}"
            ]
        })

# Print warnings
print(f"\n📊 BUMI Price Range: {bumi['Penutupan'].min():.0f} → {bumi['Penutupan'].max():.0f}")
print(f"📈 Total Return: {((bumi['Penutupan'].iloc[-1] / bumi['Penutupan'].iloc[0]) - 1)*100:.1f}%")
print(f"💨 Latest: {bumi['Penutupan'].iloc[-1]:.0f} IDR on {bumi['SourceDate'].iloc[-1].strftime('%Y-%m-%d')}\n")

if signals:
    print(f"⚠️  PUMP-END WARNING SIGNALS: {len(signals)} dates show 2+ reversal indicators\n")
    for sig in signals:
        print(f"📅 {sig['date'].strftime('%Y-%m-%d')} | Price: {sig['price']:.0f} | Return: {sig['return']*100:+.2f}%")
        print(f"   Volume: {sig['volume']:,.0f} | Foreign: {sig['foreign_ratio']:+.4f}")
        print(f"   🚩 Signals ({sig['signal_count']}):")
        for s in sig['signals']:
            if "True" in s:
                print(f"      ✓ {s}")
        print()
else:
    print("✅ No strong pump-end signals yet, but watch for:")
    print("   • Volume divergence (price up, volume down)")
    print("   • Momentum weakening (declining daily returns)")
    print("   • Foreign seller persistence (institutional dumping)")
    print("   • Volatility collapse (tighter daily ranges)")
    print("   • Transaction count decline (fewer participants)\n")

# Risk score
latest = bumi.iloc[-1]
prev5 = bumi.iloc[-5:] if len(bumi) >= 5 else bumi

risk_factors = 0
if latest['foreign_ratio'] < -0.15:
    risk_factors += 1
    print("🔴 High foreign selling pressure (likely pump-and-dump phase)")
if bumi['Volume'].iloc[-5:].mean() > bumi['Volume'].iloc[-20:-5].mean() * 1.5:
    print("🔴 Volume still elevated (pump continuing)")
if prev5['return'].mean() < 0.005:
    risk_factors += 1
    print("🟡 Momentum declining (approaching reversal)")

print("\n" + "="*120)
print("PUMP-END PROBABILITY: HIGH if 3+ signals appear simultaneously")
print("REVERSAL TRIGGER: Look for volume collapse + negative return + continued foreign selling")
print("="*120)
