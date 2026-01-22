"""Visualize BUMI manipulation patterns with detailed timeline."""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Load data
BASE_DIR = Path(__file__).resolve().parent
combined_path = BASE_DIR / 'data' / 'histories' / 'ringkasan_histories_combined.csv'
watchlist_path = BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts' / 'manipulation_watchlist.csv'

df = pd.read_csv(combined_path)
watchlist = pd.read_csv(watchlist_path)

# Filter BUMI
bumi = df[df['Kode Saham'] == 'BUMI'].copy()
bumi_flags = watchlist[watchlist['Kode Saham'] == 'BUMI'].copy()

# Convert columns
bumi['SourceDate'] = pd.to_datetime(bumi['SourceDate'])
bumi_flags['SourceDate'] = pd.to_datetime(bumi_flags['SourceDate'])

for col in ['Penutupan', 'Volume', 'Nilai', 'Foreign Buy', 'Foreign Sell']:
    bumi[col] = pd.to_numeric(bumi[col], errors='coerce')

bumi['foreign_net'] = bumi['Foreign Buy'] - bumi['Foreign Sell']
bumi['volume_bn'] = bumi['Volume'] / 1e9

# Create figure
fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
fig.suptitle('BUMI Resources - Manipulation Pattern Analysis', fontsize=16, fontweight='bold')

# Plot 1: Price
ax1 = axes[0]
ax1.plot(bumi['SourceDate'], bumi['Penutupan'], 'o-', linewidth=2, markersize=5, color='#2E86AB', label='Close Price')
ax1.scatter(bumi_flags['SourceDate'], bumi_flags['Penutupan'], s=150, color='red', marker='X', zorder=5, label='Flagged Dates')
ax1.set_ylabel('Price (IDR)', fontsize=11, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(loc='upper left')
ax1.set_title('Price Movement with Flagged Manipulation Dates', fontsize=12)

# Plot 2: Volume
ax2 = axes[1]
bars = ax2.bar(bumi['SourceDate'], bumi['volume_bn'], width=0.8, color='#A23B72', alpha=0.7, label='Volume')
# Highlight flagged dates
for date in bumi_flags['SourceDate']:
    vol = bumi[bumi['SourceDate'] == date]['volume_bn'].values
    if len(vol) > 0:
        ax2.bar(date, vol[0], width=0.8, color='red', alpha=0.9)
ax2.set_ylabel('Volume (Billions)', fontsize=11, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')
ax2.legend(loc='upper left')
ax2.set_title('Trading Volume (Red bars = Flagged)', fontsize=12)

# Plot 3: Foreign Flow
ax3 = axes[2]
colors = ['green' if x > 0 else 'red' for x in bumi['foreign_net']]
ax3.bar(bumi['SourceDate'], bumi['foreign_net'] / 1e6, width=0.8, color=colors, alpha=0.7)
# Mark flagged dates
for date in bumi_flags['SourceDate']:
    net = bumi[bumi['SourceDate'] == date]['foreign_net'].values
    if len(net) > 0:
        ax3.scatter(date, net[0] / 1e6, s=200, color='yellow', marker='*', edgecolors='black', linewidths=2, zorder=5)
ax3.axhline(0, color='black', linestyle='--', linewidth=0.8)
ax3.set_ylabel('Foreign Net (Millions)', fontsize=11, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')
ax3.set_title('Foreign Flow (Green=Buy, Red=Sell, ⭐=Flagged)', fontsize=12)

# Plot 4: Return %
ax4 = axes[3]
bumi['return_pct'] = ((bumi['Penutupan'] / bumi['Penutupan'].shift(1)) - 1) * 100
colors = ['green' if x > 0 else 'red' for x in bumi['return_pct'].fillna(0)]
ax4.bar(bumi['SourceDate'], bumi['return_pct'], width=0.8, color=colors, alpha=0.7)
# Mark flagged dates
for date in bumi_flags['SourceDate']:
    ret = bumi[bumi['SourceDate'] == date]['return_pct'].values
    if len(ret) > 0:
        ax4.scatter(date, ret[0], s=200, color='yellow', marker='D', edgecolors='black', linewidths=2, zorder=5)
ax4.axhline(0, color='black', linestyle='--', linewidth=0.8)
ax4.set_ylabel('Daily Return (%)', fontsize=11, fontweight='bold')
ax4.set_xlabel('Date', fontsize=11, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='y')
ax4.set_title('Daily Returns (♦=Flagged)', fontsize=12)

# Format x-axis
for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
output_path = BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts' / 'BUMI_manipulation_analysis.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✅ Chart saved to {output_path}")

# Print detailed flag summary
print("\n" + "="*120)
print("BUMI MANIPULATION FLAGS SUMMARY")
print("="*120)

for _, row in bumi_flags.iterrows():
    print(f"\n📅 {row['SourceDate'].strftime('%Y-%m-%d')}")
    print(f"   Price: {row['Penutupan']:.0f} → {row['Sebelumnya']:.0f}  |  Return: {row['return']*100:+.2f}%")
    print(f"   Volume: {row['Volume']:>15,.0f}  (z-score: {row['volume_z']:+.2f})")
    print(f"   Nilai:  {row['Nilai']:>15,.0f}  (z-score: {row['nilai_z']:+.2f})")
    print(f"   Freq:   {row['Frekuensi']:>15,.0f}  (z-score: {row['freq_z']:+.2f})")
    print(f"   Foreign Net: {row['foreign_ratio']:+.4f} ({row['foreign_ratio']*100:+.2f}% of volume)")
    print(f"   Book Imbalance: {row['book_imbalance']:+.4f}")
    print(f"   🚩 Flags: {row['flags']}")

print("\n" + "="*120)
print(f"Total flagged dates: {len(bumi_flags)}")
print("="*120)
