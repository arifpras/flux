import pandas as pd

# Load watchlist
watchlist = pd.read_csv('data/IHSGstockdata/alerts/manipulation_watchlist.csv')
bumi_alerts = watchlist[watchlist['Kode Saham'] == 'BUMI'].copy()

print(f"BUMI flagged entries: {len(bumi_alerts)}\n")
print("="*120)

for _, row in bumi_alerts.iterrows():
    print(f"\n📅 {row['SourceDate']}")
    print(f"   Price: {row['Penutupan']:.0f} (prev: {row['Sebelumnya']:.0f}) → Return: {row['return']*100:+.2f}%")
    print(f"   Volume: {row['Volume']:>15,.0f}  (z={row['volume_z']:+.2f})")
    print(f"   Nilai:  {row['Nilai']:>15,.0f}  (z={row['nilai_z']:+.2f})")
    print(f"   Freq:   {row['Frekuensi']:>15,.0f}  (z={row['freq_z']:+.2f})")
    print(f"   Non-reg ratio: {row['non_regular_ratio']:.4f}")
    print(f"   Foreign ratio: {row['foreign_ratio']:+.4f}")
    print(f"   Book imbal:    {row['book_imbalance']:+.4f}")
    print(f"   🚩 Flags: {row['flags']}")
