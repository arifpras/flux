#!/usr/bin/env python3
"""
Wavelet Analysis for ASII (Astra International)
Using 60-day historical data from idx_historical_60d_20260120.csv
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pywt
import shutil
import tempfile
from datetime import datetime

# Configuration
HIST_FILE = 'data/histories/idx_historical_60d_20260120.csv'
SYMBOL = 'ASII'
OUTPUT_DIR = f'wavelet_analysis/{SYMBOL}'
SCALES = list(range(1, 32))  # Explicit list, not range object

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def load_symbol_data(symbol: str) -> pd.DataFrame:
    """Load symbol data from the bulk 60-day file."""
    df = pd.read_csv(HIST_FILE)
    df = df[df['Symbol'] == symbol].copy()
    if df.empty:
        raise ValueError(f"{symbol} not found in {HIST_FILE}")
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    return df

def compute_cwt_energy(prices: np.ndarray) -> dict:
    """Compute CWT energy and multi-scale alignment."""
    if len(prices) < 10:
        return {'total_energy': 0, 'alignment_score': 0, 'strength': 'WEAK'}
    
    # Normalize
    p = np.array(prices, dtype=float)
    p_norm = (p - np.mean(p)) / (np.std(p) + 1e-8)
    
    # CWT with Morlet
    coeffs_list = pywt.cwt(p_norm, SCALES, 'morl', method='conv')
    energy_per_scale = np.array([np.sum(np.abs(c) ** 2) for c in coeffs_list])
    total_energy = float(np.sum(energy_per_scale))
    
    # Multi-scale alignment
    short_scales = float(np.sum(energy_per_scale[:5]))   # scales 1-5
    medium_scales = float(np.sum(energy_per_scale[5:15]))  # scales 6-15
    long_scales = float(np.sum(energy_per_scale[15:]))    # scales 16+
    
    if total_energy > 0:
        alignment = (short_scales + 2*medium_scales) / (total_energy + 1e-8)
    else:
        alignment = 0
    
    # Strength
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
        'strength': strength,
    }

def analyze_trend(prices: np.ndarray) -> dict:
    """Analyze recent trend (last 5 days)."""
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
        'recent_momentum': round(float(momentum) * 100, 2),
    }

def plot_cwt(symbol: str, prices: np.ndarray, dates: pd.DatetimeIndex, output_path: str):
    """Generate CWT heatmap and price overlay."""
    p_norm = (prices - np.mean(prices)) / (np.std(prices) + 1e-8)
    result = pywt.cwt(p_norm, list(SCALES), 'morl', method='conv')
    
    # pywt.cwt returns (coefficients_array, frequencies)
    # coefficients_array has shape (num_scales, num_timepoints)
    coeffs_array = result[0]  # Shape: (31, 58)
    
    # Energy per scale: sum across time dimension for each scale row
    energy_per_scale = [float(np.sum(np.abs(coeffs_array[i, :]) ** 2)) for i in range(coeffs_array.shape[0])]
    
    # Create figure
    fig, axes = plt.subplots(3, 1, figsize=(14, 11), dpi=100)
    
    # 1. Price series (top, larger)
    ax1 = axes[0]
    x_indices = np.arange(len(prices))
    ax1.plot(x_indices, prices, 'b-', linewidth=2.5, marker='o', markersize=4, label='Close Price')
    ax1.set_ylabel('Price (IDR)', fontsize=12, fontweight='bold')
    ax1.set_title(f'{symbol} - 60-Day Price Series & Wavelet Analysis', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.4, linestyle='--')
    ax1.legend(fontsize=11, loc='upper left')
    ax1.set_xlim(-1, len(prices))
    
    # 2. Energy distribution histogram
    ax2 = axes[1]
    scales_list = list(range(1, 32))
    colors = ['#d73027' if s <= 5 else '#fee090' if s <= 15 else '#1a9850' for s in scales_list]
    ax2.bar(scales_list, energy_per_scale, color=colors, alpha=0.85, edgecolor='black', linewidth=1)
    ax2.set_ylabel('Energy', fontsize=12, fontweight='bold')
    ax2.set_title('Wavelet Energy Distribution (Red=Short 1-5, Yellow=Medium 6-15, Green=Long 16-31)', fontsize=12)
    ax2.axvline(5.5, color='black', linestyle='--', alpha=0.4, linewidth=2)
    ax2.axvline(15.5, color='black', linestyle='--', alpha=0.4, linewidth=2)
    ax2.set_xlim(0, 32)
    ax2.set_xlabel('Wavelet Scale', fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
    
    # 3. Price changes (momentum)
    ax3 = axes[2]
    price_changes = np.diff(prices) / prices[:-1] * 100
    colors_mom = ['green' if x >= 0 else 'red' for x in price_changes]
    ax3.bar(range(len(price_changes)), price_changes, color=colors_mom, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax3.axhline(0, color='black', linestyle='-', linewidth=0.8)
    ax3.set_xlabel('Time (days)', fontsize=11)
    ax3.set_ylabel('Daily Return (%)', fontsize=12, fontweight='bold')
    ax3.set_title('Daily Price Changes', fontsize=12)
    ax3.grid(True, alpha=0.3, axis='y', linestyle='--')
    
    fig.tight_layout()
    
    # Save to temp location first (avoids Dropbox caching issues)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = os.path.join(tmpdir, 'temp.png')
        fig.savefig(tmp_path, format='png', dpi=100, bbox_inches='tight', facecolor='white')
        # Copy to final destination
        shutil.copy(tmp_path, output_path)
    
    file_size = os.path.getsize(output_path) / 1024
    print(f"✓ Saved high-resolution chart: {output_path}")
    print(f"  Size: {file_size:.1f} KB")
    
    plt.close(fig)  # Close specific figure
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()

def main():
    print("=" * 80)
    print(f"Wavelet Analysis: {SYMBOL}")
    print("=" * 80)
    
    ensure_dir(OUTPUT_DIR)
    
    # Load data
    print(f"\n📊 Loading {SYMBOL} data from {HIST_FILE}...")
    df = load_symbol_data(SYMBOL)
    prices = df['Close'].values
    dates = df['Date']
    
    print(f"   Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
    print(f"   Data points: {len(prices)}")
    print(f"   Price range: Rp {prices.min():.0f} - Rp {prices.max():.0f}")
    
    # Wavelet analysis
    print(f"\n🌊 Running Continuous Wavelet Transform (Morlet, scales 1-31)...")
    cwt = compute_cwt_energy(prices)
    trend = analyze_trend(prices)
    
    # Combined score
    score = cwt['alignment_score'] + (0.05 if trend['trend'] == 'UP' else -0.05 if trend['trend'] == 'DOWN' else 0)
    
    # Print results
    print(f"\n{'='*80}")
    print(f"WAVELET ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    print(f"\n📈 Energy Distribution:")
    print(f"   Total Energy: {cwt['total_energy']:.4f}")
    print(f"   Short-scale (1-5):    {cwt['short_scale_energy']:.4f} ({cwt['short_scale_energy']/cwt['total_energy']*100:.1f}%)")
    print(f"   Medium-scale (6-15):  {cwt['medium_scale_energy']:.4f} ({cwt['medium_scale_energy']/cwt['total_energy']*100:.1f}%)")
    print(f"   Long-scale (16-31):   {cwt['long_scale_energy']:.4f} ({cwt['long_scale_energy']/cwt['total_energy']*100:.1f}%)")
    
    print(f"\n💡 Multi-Scale Alignment:")
    print(f"   Alignment Score: {cwt['alignment_score']:.4f}")
    print(f"   Strength: {cwt['strength']} ⭐" * (1 + min(4, int(cwt['alignment_score'] * 5))))
    
    print(f"\n📊 Trend Analysis (Last 5 days):")
    print(f"   Trend: {trend['trend']}")
    print(f"   Recent Momentum: {trend['recent_momentum']:+.2f}%")
    
    print(f"\n🎯 Final Score: {score:.4f}")
    print(f"   Interpretation: {'Strong uptrend with high momentum coherence' if cwt['strength'] == 'STRONG' and trend['trend'] == 'UP' else 'High quality wavelet alignment' if cwt['strength'] == 'STRONG' else 'Moderate momentum pattern' if cwt['strength'] == 'MODERATE' else 'Weak or noisy signal'}")
    
    # Generate plot
    print(f"\n🎨 Generating wavelet visualization...")
    plot_file = os.path.join(OUTPUT_DIR, f'{SYMBOL}_wavelet_60d_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plot_cwt(SYMBOL, prices, dates, plot_file)
    
    print(f"\n{'='*80}")
    print(f"✅ Analysis complete!")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
