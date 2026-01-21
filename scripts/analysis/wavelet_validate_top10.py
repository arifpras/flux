#!/usr/bin/env python3
"""
Fetch historical prices for top 10 candidates and run wavelet analysis
to validate momentum strength and multi-scale alignment.
"""
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pywt
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
HIST_DIR = os.path.join(DATA_DIR, 'histories')
BACKTEST_TRADES = os.path.join(BASE_DIR, 'backtest_trades.csv')

# Top 10 candidates by confluence
CANDIDATES = ['ASII', 'INCO', 'MDKA', 'UNTR', 'ADRO', 'TPIA', 'INDF', 'ANTM', 'ISAT', 'BBNI']
OUTPUT_FILE = os.path.join(HIST_DIR, 'wavelet_scores_top10.json')

def load_price_series(symbol: str, days_back: 30) -> pd.DataFrame:
    """Load backtest trades for symbol, extract and sort prices."""
    df = pd.read_csv(BACKTEST_TRADES)
    df = df[df['Kode Saham'] == symbol].copy()
    if df.empty:
        return pd.DataFrame()
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])
    df = df.sort_values('SourceDate').tail(days_back)
    return df[['SourceDate', 'EntryPrice']].rename(columns={'EntryPrice': 'Close'})

def compute_cwt_energy(prices: np.ndarray, scales=None) -> dict:
    """
    Compute Continuous Wavelet Transform (Morlet) and extract multi-scale energy.
    Returns: dict with total energy, per-scale breakdown, and alignment scores.
    """
    if scales is None:
        scales = list(range(1, 32))
    
    if len(prices) < 10:
        return {'total_energy': 0, 'alignment_score': 0, 'strength': 'WEAK', 'short_scale_energy': 0, 'medium_scale_energy': 0, 'long_scale_energy': 0}
    
    # Normalize to zero-mean
    p = np.array(prices, dtype=float)
    p_norm = (p - np.mean(p)) / (np.std(p) + 1e-8)
    
    # CWT with Morlet
    coeffs_list = pywt.cwt(p_norm, scales, 'morl', method='conv')
    
    # Energy by scale: coeffs_list is tuple of arrays (one per scale)
    energy_per_scale = np.array([np.sum(np.abs(c) ** 2) for c in coeffs_list])
    total_energy = float(np.sum(energy_per_scale))
    
    # Multi-scale alignment: high energy on short/medium scales (fast reversal)
    short_scales = float(np.sum(energy_per_scale[:5]))  # scales 1-5 (fast)
    medium_scales = float(np.sum(energy_per_scale[5:15]))  # scales 6-15 (medium)
    long_scales = float(np.sum(energy_per_scale[15:]))  # scales 16+ (long)
    
    # Good alignment: short + medium >> long (momentum-driven, not drift)
    if total_energy > 0:
        alignment = (short_scales + 2*medium_scales) / (total_energy + 1e-8)
    else:
        alignment = 0
    
    # Classify strength
    if alignment > 0.6 and total_energy > 0.5:
        strength = 'STRONG'
    elif alignment > 0.4 and total_energy > 0.2:
        strength = 'MODERATE'
    else:
        strength = 'WEAK'
    
    return {
        'total_energy': round(float(total_energy), 4),
        'short_scale_energy': round(float(short_scales), 4),
        'medium_scale_energy': round(float(medium_scales), 4),
        'long_scale_energy': round(float(long_scales), 4),
        'alignment_score': round(float(alignment), 4),
        'strength': strength
    }

def analyze_recent_trend(prices: np.ndarray) -> dict:
    """Analyze recent 5-day trend direction and momentum."""
    if len(prices) < 5:
        return {'trend': 'UNKNOWN', 'momentum': 0}
    
    recent = prices[-5:]
    returns = np.diff(recent) / recent[:-1]
    momentum = returns.mean()
    
    if momentum > 0.01:
        trend = 'UP'
    elif momentum < -0.01:
        trend = 'DOWN'
    else:
        trend = 'FLAT'
    
    return {
        'trend': trend,
        'recent_momentum': round(float(momentum) * 100, 2)
    }

def main():
    print('Fetching prices and running wavelet analysis on top 10 candidates...\n')
    
    results = {}
    for symbol in CANDIDATES:
        price_data = load_price_series(symbol, days_back=30)
        if price_data.empty:
            print(f'{symbol}: No data found.')
            results[symbol] = {'status': 'NO_DATA'}
            continue
        
        prices = price_data['Close'].values
        
        # Wavelet analysis
        cwt = compute_cwt_energy(prices)
        trend = analyze_recent_trend(prices)
        
        # Combined score: wavelet alignment + trend momentum
        score = cwt['alignment_score'] + (0.05 if trend['trend'] == 'UP' else -0.05 if trend['trend'] == 'DOWN' else 0)
        
        results[symbol] = {
            'data_points': len(prices),
            'date_range': f"{price_data['SourceDate'].min().date()} to {price_data['SourceDate'].max().date()}",
            'latest_price': round(float(prices[-1]), 2),
            'wavelet': cwt,
            'trend': trend,
            'combined_score': round(float(score), 4),
            'rank': None  # Will be filled after sorting
        }
        
        print(f'{symbol}:')
        print(f"  Strength: {cwt['strength']} | Alignment: {cwt['alignment_score']} | Trend: {trend['trend']} (+{trend['recent_momentum']}%)")
        print(f"  Score: {score:.4f}\n")
    
    # Rank by score
    sorted_syms = sorted([s for s in results if results[s].get('status') != 'NO_DATA'],
                         key=lambda s: results[s]['combined_score'], reverse=True)
    for rank, sym in enumerate(sorted_syms, 1):
        results[sym]['rank'] = rank
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f'\n✓ Wavelet analysis complete. Results saved to {OUTPUT_FILE}')
    print('\nTop 5 by Wavelet Score:')
    for rank, sym in enumerate(sorted_syms[:5], 1):
        r = results[sym]
        print(f"{rank}. {sym} ({r['combined_score']:.4f}) - {r['wavelet']['strength']}")

if __name__ == '__main__':
    main()
