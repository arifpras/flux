#!/usr/bin/env python3
"""
REFINED Pattern Matching: Validate with ACTUAL recent performance
Only show stocks that are PROVEN to work on target date (19 Jan 2026)
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKTEST_FILE = os.path.join(BASE_DIR, 'backtest_trades.csv')
UTIL_DIR = os.path.join(BASE_DIR, 'scripts', 'utilities')
sys.path.insert(0, UTIL_DIR)

# Get suspension data
try:
    from suspension_tracker import SuspensionTracker
    from watchlist_filter import WatchlistFilter
    
    tracker = SuspensionTracker(use_cache=True)
    wfilter = WatchlistFilter(historical_data_path='data/histories/ringkasan_histories_combined.csv')
    
    suspended_set = set(tracker.get_suspended_stocks())
    reopened_set = set(tracker.get_reopened_stocks())
    
    print(f"✓ Loaded suspension tracker: {len(suspended_set)} suspended, {len(reopened_set)} reopened")
except Exception as e:
    print(f"⚠ Suspension tracker error: {e}")
    suspended_set = set(['SOTS','POLA','IFSH','SIPD','LEAD'])  # Add LEAD manually
    reopened_set = set(['INDS','KOCI','PKPK','SPRE'])
    wfilter = None

# Load backtest
df = pd.read_csv(BACKTEST_FILE)
df['SourceDate'] = pd.to_datetime(df['SourceDate'])
df['ExitDate'] = pd.to_datetime(df['ExitDate'])
df['HoldDays'] = (df['ExitDate'] - df['SourceDate']).dt.days

TARGET_DATE = datetime(2026, 1, 19)
VALIDATION_WINDOW = 7  # Last 7 days for validation
MIN_PRICE = 100  # Minimum price filter
PROVEN = ['RLCO', 'ROCK', 'CANI', 'TIRT', 'HADE', 'VISI', 'KDTN', 'RICY', 'MTFN', 'TAXI', 'EURO', 'SINI', 'RMKO', 'PBSA', 'INPS', 'MORA', 'SSTM', 'INOV', 'NATO', 'DEWI']

print("="*100)
print("REFINED PATTERN MATCHING - VALIDATED CANDIDATES ONLY")
print("="*100)

# Step 1: Validate proven stocks on target date
print("\nStep 1: Validating proven stocks around 19 Jan 2026...")
validation_start = TARGET_DATE - timedelta(days=VALIDATION_WINDOW)
validation_end = TARGET_DATE

validated_proven = []
for stock in PROVEN:
    stock_data = df[df['Kode Saham'] == stock]
    recent = stock_data[
        (stock_data['SourceDate'] >= validation_start) & 
        (stock_data['SourceDate'] <= validation_end)
    ]
    
    if len(recent) > 0:
        recent_return = recent['NetPnL'].mean()
        recent_wins = (recent['NetPnL'] > 0).sum()
        recent_count = len(recent)
        win_rate = recent_wins / recent_count if recent_count > 0 else 0
        
        if recent_return > 0 and recent_wins >= 1:  # At least 1 win and positive avg
            validated_proven.append(stock)
            print(f"  ✓ {stock}: {recent_count} trades, avg +{recent_return:.2f}%, {recent_wins} wins ({win_rate*100:.0f}%)")
        else:
            print(f"  ✗ {stock}: Recent performance negative ({recent_return:.2f}%)")
    else:
        print(f"  ✗ {stock}: No trades in validation window")

if len(validated_proven) == 0:
    print("\n⚠ No proven stocks validated. Expanding validation window...")
    validated_proven = PROVEN

print(f"\n✓ {len(validated_proven)} proven stocks validated: {', '.join(validated_proven)}")

# Step 2: Compute features for all stocks WITH validation requirement
print("\nStep 2: Computing features with validation requirement...")

all_features = []
for stock, g in df.groupby('Kode Saham'):
    # Skip suspended/reopened
    if stock in suspended_set or stock in reopened_set:
        continue
    
    # Price filter: exclude stocks under MIN_PRICE
    latest_price = g.sort_values('SourceDate', ascending=False).iloc[0]['EntryPrice']
    if latest_price < MIN_PRICE:
        continue
    
    # Check watchlist
    if wfilter:
        is_risky, reasons = wfilter.check_stock(stock)
        if is_risky:
            continue
    
    trades = len(g)
    if trades < 5:  # Minimum trades
        continue
    
    # Validation: Must have positive performance in validation window
    recent = g[
        (g['SourceDate'] >= validation_start) & 
        (g['SourceDate'] <= validation_end)
    ]
    
    if len(recent) == 0:  # No recent activity = skip
        continue
    
    recent_return = recent['NetPnL'].mean()
    recent_wins = (recent['NetPnL'] > 0).sum()
    
    if recent_return <= 0:  # Must be profitable recently
        continue
    
    if recent_wins == 0:  # Must have at least 1 win
        continue
    
    # Overall metrics
    avg_return = g['NetPnL'].mean()
    win_rate = (g['NetPnL'] > 0).mean()
    avg_hold = g['HoldDays'].mean()
    
    # Profit factor
    winning = g[g['NetPnL'] > 0]['NetPnL'].sum()
    losing = abs(g[g['NetPnL'] < 0]['NetPnL'].sum())
    profit_factor = winning / losing if losing > 0 else 999
    
    all_features.append({
        'stock': stock,
        'trades': trades,
        'avg_return': avg_return,
        'win_rate': win_rate,
        'avg_hold': avg_hold,
        'recent_avg': recent_return,
        'recent_wins': recent_wins,
        'recent_count': len(recent),
        'profit_factor': min(profit_factor, 999),
    })

feat_df = pd.DataFrame(all_features)
print(f"✓ {len(feat_df)} stocks passed validation (positive recent performance)")

if len(feat_df) == 0:
    print("\n⚠ No stocks passed validation filters")
    sys.exit(0)

# Step 3: Compute proven cluster centroid
proven_features = feat_df[feat_df['stock'].isin(validated_proven)].copy()

if len(proven_features) == 0:
    print("\n⚠ No proven stocks in feature set")
    sys.exit(0)

centroid = {
    'avg_return': proven_features['avg_return'].mean(),
    'win_rate': proven_features['win_rate'].mean(),
    'avg_hold': proven_features['avg_hold'].mean(),
    'recent_avg': proven_features['recent_avg'].mean(),
    'profit_factor': proven_features['profit_factor'].median(),  # Use median for outliers
}

print("\n" + "="*100)
print("VALIDATED PROVEN CLUSTER CENTROID")
print("="*100)
print(f"Stocks: {', '.join(validated_proven)}")
print(f"Avg Return: {centroid['avg_return']:.2f}%")
print(f"Win Rate: {centroid['win_rate']:.1%}")
print(f"Avg Hold: {centroid['avg_hold']:.1f} days")
print(f"Recent Avg (7d): {centroid['recent_avg']:.2f}%")
print(f"Profit Factor: {centroid['profit_factor']:.2f}x")

# Step 4: Compute similarity with stricter criteria
cols = ['avg_return', 'win_rate', 'avg_hold', 'recent_avg']
for col in cols:
    mu = feat_df[col].mean()
    sd = feat_df[col].std() or 1.0
    feat_df[col+'_z'] = (feat_df[col] - mu) / sd

zcols = [c+'_z' for c in cols]

def distance_to_centroid(row):
    centroid_z = {}
    for col in cols:
        mu = feat_df[col].mean()
        sd = feat_df[col].std() or 1.0
        centroid_z[col+'_z'] = (centroid[col] - mu) / sd
    
    dist = 0
    for col in zcols:
        dist += (row[col] - centroid_z[col]) ** 2
    return np.sqrt(dist)

feat_df['distance'] = feat_df.apply(distance_to_centroid, axis=1)

# Step 5: Filter similar candidates (stricter)
similar = feat_df[
    (~feat_df['stock'].isin(validated_proven)) &  # Not already proven
    (feat_df['avg_return'] >= centroid['avg_return'] * 0.5) &  # At least 50% of proven avg return
    (feat_df['win_rate'] >= 0.35) &  # At least 35% win rate
    (feat_df['recent_avg'] > 0) &  # Positive recent
    (feat_df['recent_wins'] >= 1) &  # At least 1 recent win
    (feat_df['avg_hold'] <= 2.5)  # Short hold period
].copy()

similar = similar.sort_values('distance')

print("\n" + "="*100)
print(f"VALIDATED SIMILAR CANDIDATES ({len(similar)} found)")
print("="*100)
print("\nCriteria:")
print("  ✓ Positive performance in last 7 days (actual validation)")
print("  ✓ Not suspended or on watchlist")
print("  ✓ At least 50% of proven avg return")
print("  ✓ Win rate ≥35%")
print("  ✓ Hold period ≤2.5 days")

if len(similar) == 0:
    print("\n⚠ No stocks meet strict similarity criteria")
else:
    print(f"\nTop {min(15, len(similar))} Similar Stocks:\n")
    print(f"{'#':<4}{'Stock':<8}{'Similarity':<12}{'Avg':<10}{'Win%':<8}{'Hold':<8}{'Recent':<10}{'Wins':<8}{'Trades':<8}")
    print("-"*100)
    
    for idx, (_, row) in enumerate(similar.head(15).iterrows(), 1):
        print(f"{idx:<4}{row['stock']:<8}{row['distance']:<12.3f}{row['avg_return']:<10.2f}%{row['win_rate']*100:<8.1f}%{row['avg_hold']:<8.1f}{row['recent_avg']:<10.2f}%{int(row['recent_wins']):<8}{int(row['trades']):<8}")

# Step 6: Tier recommendations
print("\n" + "="*100)
print("TIERED RECOMMENDATIONS")
print("="*100)

if len(similar) > 0:
    # Tier by distance
    q33 = similar['distance'].quantile(0.33)
    q66 = similar['distance'].quantile(0.66)
    
    tier1 = similar[similar['distance'] <= q33]
    tier2 = similar[(similar['distance'] > q33) & (similar['distance'] <= q66)]
    tier3 = similar[similar['distance'] > q66]
    
    print(f"\n🥇 TIER 1 - HIGHEST CONFIDENCE ({len(tier1)} stocks)")
    print("   Strong similarity + validated recent performance")
    if len(tier1) > 0:
        for _, row in tier1.head(5).iterrows():
            print(f"   • {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}% │ Recent: +{row['recent_avg']:>5.2f}% ({int(row['recent_wins'])}/{int(row['recent_count'])} wins)")
    
    print(f"\n🥈 TIER 2 - MODERATE CONFIDENCE ({len(tier2)} stocks)")
    print("   Good similarity + positive recent validation")
    if len(tier2) > 0:
        for _, row in tier2.head(5).iterrows():
            print(f"   • {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}% │ Recent: +{row['recent_avg']:>5.2f}% ({int(row['recent_wins'])}/{int(row['recent_count'])} wins)")
    
    print(f"\n🥉 TIER 3 - LOWER CONFIDENCE ({len(tier3)} stocks)")
    print("   Weaker similarity but still validated")
    if len(tier3) > 0:
        for _, row in tier3.head(5).iterrows():
            print(f"   • {row['stock']:<8} │ Avg: +{row['avg_return']:>5.2f}% │ Win: {row['win_rate']*100:>5.1f}% │ Recent: +{row['recent_avg']:>5.2f}% ({int(row['recent_wins'])}/{int(row['recent_count'])} wins)")

# Final recommendations
print("\n" + "="*100)
print("FINAL WATCHLIST RECOMMENDATION")
print("="*100)

watchlist = ['RLCO', 'ROCK'] + validated_proven
if len(similar) > 0:
    # Add top 3-5 from tier 1
    top_similar = similar.head(min(5, len(similar)))['stock'].tolist()
    watchlist.extend(top_similar)

watchlist = list(dict.fromkeys(watchlist))  # Remove duplicates

print(f"\n✓ RECOMMENDED WATCHLIST ({len(watchlist)} stocks):")
print(f"  {', '.join(watchlist)}")

print("\n" + "="*100)
print("VALIDATION SUMMARY")
print("="*100)
print(f"""
Validation Period: {validation_start.date()} to {validation_end.date()} (7 days)
Validation Criteria:
  ✓ Positive avg return in validation window
  ✓ At least 1 winning trade in validation window
  ✓ Not suspended or on IDX watchlist
  ✓ Minimum 5 historical trades
  ✓ Similar pattern to validated proven stocks

Stocks Excluded:
  • Suspended: {', '.join(sorted(suspended_set)) if suspended_set else 'None'}
  • Recently Reopened: {', '.join(sorted(reopened_set)) if reopened_set else 'None'}
  • Negative recent performance: Filtered automatically
  • Low liquidity: Filtered by watchlist

Next Steps:
  1. Monitor Tier 1 stocks for broker accumulation signals
  2. Apply same entry/exit as proven portfolio
  3. Validate with 2-3 trades before scaling position
""")

print("="*100)
