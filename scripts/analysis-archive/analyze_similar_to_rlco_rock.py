#!/usr/bin/env python3
"""
Find stocks with patterns similar to RLCO and ROCK as of Jan 19, 2026.
Uses backtest_trades.csv to compute performance features and nearest neighbors.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKTEST_FILE = os.path.join(BASE_DIR, 'backtest_trades.csv')
UTIL_DIR = os.path.join(BASE_DIR, 'scripts', 'utilities')
sys.path.insert(0, UTIL_DIR)

# Optional: import suspension tracker for exclusion
try:
    from suspension_tracker import SuspensionTracker
    tracker = SuspensionTracker(use_cache=True)
    suspended_set = set(tracker.get_suspended_stocks())
    reopened_set = set(tracker.get_reopened_stocks())
except Exception as e:
    print(f"⚠ Suspension tracker not available: {e}")
    suspended_set = set(['SOTS','POLA','IFSH','SIPD'])
    reopened_set = set(['INDS','KOCI','PKPK','SPRE'])

# Target date
TARGET_DATE = datetime(2026, 1, 19)
DATE_WINDOW = 3  # days for recent momentum

# Load backtest
df = pd.read_csv(BACKTEST_FILE)
df['SourceDate'] = pd.to_datetime(df['SourceDate'])
df['ExitDate'] = pd.to_datetime(df['ExitDate'])

# Compute per-stock features
features = []
for stock, g in df.groupby('Kode Saham'):
    trades = len(g)
    avg_return = g['NetPnL'].mean()
    win_rate = (g['NetPnL'] > 0).mean()
    avg_hold = (g['ExitDate'] - g['SourceDate']).dt.days.mean()
    # Recent window around target date
    start = TARGET_DATE - timedelta(days=DATE_WINDOW)
    end = TARGET_DATE
    recent = g[(g['SourceDate'] >= start) & (g['SourceDate'] <= end)]
    if len(recent) == 0:
        recent = g.tail(min(trades, 5))
    recent_avg = recent['NetPnL'].mean() if len(recent) > 0 else 0.0
    features.append({
        'stock': stock,
        'avg_return': avg_return,
        'win_rate': win_rate,
        'trades': trades,
        'avg_hold': avg_hold if not np.isnan(avg_hold) else 0.0,
        'recent_avg': recent_avg,
    })

feat_df = pd.DataFrame(features)
feat_df = feat_df.replace([np.inf, -np.inf], np.nan).fillna(0)

# Normalize features
cols = ['avg_return','win_rate','trades','avg_hold','recent_avg']
for c in cols:
    mu = feat_df[c].mean()
    sd = feat_df[c].std() or 1.0
    feat_df[c+'_z'] = (feat_df[c] - mu) / sd

zcols = [c+'_z' for c in cols]

def distance(a_vec, b_vec):
    return np.linalg.norm(a_vec - b_vec)

def nearest_to(stock):
    if stock not in feat_df['stock'].values:
        return pd.DataFrame(columns=['stock','dist'])
    target_vec = feat_df.loc[feat_df['stock']==stock, zcols].values[0]
    dists = []
    for _, row in feat_df.iterrows():
        if row['stock'] == stock:
            continue
        d = distance(target_vec, row[zcols].values)
        dists.append({'stock': row['stock'], 'dist': d})
    dist_df = pd.DataFrame(dists).sort_values('dist')
    return dist_df

# Find nearest neighbors
rlco_neighbors = nearest_to('RLCO')
rock_neighbors = nearest_to('ROCK')

# Exclusions
def is_excluded(s):
    if s in suspended_set:
        return True, 'Suspended'
    if s in reopened_set:
        return True, 'Recently reopened'
    return False, None

def summarize(neighbors, title):
    print('\n' + '='*80)
    print(title)
    print('='*80)
    shown = 0
    for _, row in neighbors.iterrows():
        stock = row['stock']
        dist = row['dist']
        excl, reason = is_excluded(stock)
        if excl:
            continue
        # Pull metrics
        m = feat_df.loc[feat_df['stock']==stock].iloc[0]
        print(f"{stock:<8} │ sim={dist:>6.3f} │ avg={m['avg_return']:>6.2f}% │ win={m['win_rate']*100:>5.1f}% │ hold={m['avg_hold']:.1f}d │ recent={m['recent_avg']:>6.2f}%")
        shown += 1
        if shown >= 8:
            break
    if shown == 0:
        print('No close peers found (after exclusions).')

print('\n' + '='*80)
print('Similar Stocks Analysis (to RLCO and ROCK) — as of 19 Jan 2026')
print('='*80)

# Show profiles for RLCO and ROCK
for anchor in ['RLCO','ROCK']:
    m = feat_df.loc[feat_df['stock']==anchor]
    if len(m):
        m = m.iloc[0]
        print(f"\nAnchor {anchor}: avg={m['avg_return']:>6.2f}% │ win={m['win_rate']*100:>5.1f}% │ hold={m['avg_hold']:.1f}d │ recent={m['recent_avg']:>6.2f}% │ trades={int(m['trades'])}")

summarize(rlco_neighbors, 'Closest Peers to RLCO')
summarize(rock_neighbors, 'Closest Peers to ROCK')
