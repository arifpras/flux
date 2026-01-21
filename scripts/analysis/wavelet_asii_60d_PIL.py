#!/usr/bin/env python3
"""
Wavelet Analysis for ASII (Astra International)
Using 60-day historical data with PIL for robust visualization
"""
import os
import pandas as pd
import numpy as np
import pywt
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Configuration
HIST_FILE = 'data/histories/idx_historical_60d_20260120.csv'
SYMBOL = 'ASII'
OUTPUT_DIR = f'wavelet_analysis/{SYMBOL}'
SCALES = list(range(1, 32))

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
    
    p = np.array(prices, dtype=float)
    p_norm = (p - np.mean(p)) / (np.std(p) + 1e-8)
    
    coeffs_list = pywt.cwt(p_norm, SCALES, 'morl', method='conv')
    # For list return, compute energy per scale
    energy_per_scale = np.array([np.sum(np.abs(c) ** 2) for c in coeffs_list])
    total_energy = float(np.sum(energy_per_scale))
    
    short_scales = float(np.sum(energy_per_scale[:5]))
    medium_scales = float(np.sum(energy_per_scale[5:15]))
    long_scales = float(np.sum(energy_per_scale[15:]))
    
    alignment = (short_scales + 2*medium_scales) / (total_energy + 1e-8) if total_energy > 0 else 0
    
    strength = 'STRONG' if alignment > 0.6 and total_energy > 0.5 else \
               'MODERATE' if alignment > 0.4 and total_energy > 0.2 else 'WEAK'
    
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
    
    trend = 'UP' if momentum > 0.01 else 'DOWN' if momentum < -0.01 else 'FLAT'
    
    return {
        'trend': trend,
        'recent_momentum': round(float(momentum) * 100, 2),
    }

def plot_cwt_pil(symbol: str, prices: np.ndarray, energy_per_scale: list, output_path: str):
    """Generate visualization using PIL (robust on Dropbox filesystem)."""
    W, H = 1300, 1000
    img = Image.new('RGB', (W, H), 'white')
    draw = ImageDraw.Draw(img)
    
    # Colors
    BLACK = (0, 0, 0)
    BLUE = (50, 100, 200)
    RED = (215, 48, 39)
    YELLOW = (254, 224, 144)
    GREEN = (26, 152, 80)
    GRAY = (200, 200, 200)
    DARK_GRAY = (100, 100, 100)
    
    # ==================== PANEL 1: PRICE ====================
    y1_top, y1_height = 50, int(H * 0.28)
    y1_bottom = y1_top + y1_height
    draw.rectangle([(50, y1_top), (W-50, y1_bottom)], outline=BLACK, width=2)
    
    # Title
    draw.text((70, y1_top + 10), f"{symbol} - 60-Day Price Series", fill=DARK_GRAY)
    
    # Draw price line
    price_min, price_max = prices.min(), prices.max()
    x_step = (W - 100) / max(len(prices) - 1, 1)
    y_range = price_max - price_min + 1
    y_scale = (y1_height - 40) / y_range
    
    for i in range(len(prices) - 1):
        x1 = 50 + int(i * x_step)
        y1 = y1_bottom - int((prices[i] - price_min) * y_scale) - 20
        x2 = 50 + int((i+1) * x_step)
        y2 = y1_bottom - int((prices[i+1] - price_min) * y_scale) - 20
        draw.line([(x1, y1), (x2, y2)], fill=BLUE, width=2)
        # Draw points
        draw.ellipse([(x1-2, y1-2), (x1+2, y1+2)], fill=BLUE)
    
    # Y-axis labels
    draw.text((15, y1_bottom - 30), f"{int(price_max)}", fill=DARK_GRAY)
    draw.text((15, y1_top + 10), f"{int(price_min)}", fill=DARK_GRAY)
    
    # ==================== PANEL 2: ENERGY ====================
    y2_top, y2_height = y1_bottom + 30, int(H * 0.28)
    y2_bottom = y2_top + y2_height
    draw.rectangle([(50, y2_top), (W-50, y2_bottom)], outline=BLACK, width=2)
    
    draw.text((70, y2_top + 10), "Wavelet Energy Distribution (Scale 1-31)", fill=DARK_GRAY)
    
    energy_max = max(energy_per_scale) if energy_per_scale else 1
    bar_w = (W - 100) / 31
    
    for i, e in enumerate(energy_per_scale):
        x = 50 + int(i * bar_w)
        bar_h = int((e / energy_max) * (y2_height - 40)) if energy_max > 0 else 0
        
        # Color by scale: Red (1-5), Yellow (6-15), Green (16-31)
        if i < 5:
            color = RED
        elif i < 15:
            color = YELLOW
        else:
            color = GREEN
        
        if bar_h > 0:
            draw.rectangle([(x, y2_bottom - bar_h - 10), (x + int(bar_w) - 2, y2_bottom - 10)],
                          fill=color, outline=BLACK, width=1)
    
    # Legend
    draw.rectangle([(70, y2_bottom + 10), (90, y2_bottom + 30)], fill=RED)
    draw.text((100, y2_bottom + 10), "Short (1-5)", fill=DARK_GRAY)
    
    draw.rectangle([(250, y2_bottom + 10), (270, y2_bottom + 30)], fill=YELLOW)
    draw.text((280, y2_bottom + 10), "Medium (6-15)", fill=DARK_GRAY)
    
    draw.rectangle([(480, y2_bottom + 10), (500, y2_bottom + 30)], fill=GREEN)
    draw.text((510, y2_bottom + 10), "Long (16-31)", fill=DARK_GRAY)
    
    # ==================== PANEL 3: RETURNS ====================
    y3_top, y3_height = y2_bottom + 40, int(H * 0.25)
    y3_bottom = y3_top + y3_height
    draw.rectangle([(50, y3_top), (W-50, y3_bottom)], outline=BLACK, width=2)
    
    draw.text((70, y3_top + 10), "Daily Price Changes (%)", fill=DARK_GRAY)
    
    returns = np.diff(prices) / prices[:-1] * 100
    if len(returns) > 0:
        ret_max = max(abs(returns))
        bar_w = (W - 100) / len(returns)
        
        for i, r in enumerate(returns):
            x = 50 + int(i * bar_w)
            bar_h = int(abs(r) * (y3_height - 30) / ret_max) if ret_max > 0 else 0
            color = GREEN if r >= 0 else RED
            
            if bar_h > 0:
                draw.rectangle([(x, y3_bottom - bar_h - 10), (x + int(bar_w) - 2, y3_bottom - 10)],
                              fill=color, outline=BLACK, width=1)
    
    # Center line for 0%
    y_center = y3_bottom - 10
    draw.line([(50, y_center), (W-50, y_center)], fill=GRAY, width=1)
    
    # ==================== TITLE ====================
    draw.text((350, 15), f"{symbol} - 60-Day Wavelet Analysis", fill=BLACK)
    draw.text((350, 32), f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", fill=GRAY)
    
    # Save
    img.save(output_path, 'PNG', optimize=False)
    return os.path.getsize(output_path) / 1024

def main():
    print("="*80)
    print(f"Wavelet Analysis: {SYMBOL}")
    print("="*80)
    
    ensure_dir(OUTPUT_DIR)
    
    # Load data
    print(f"\n📊 Loading {SYMBOL} data from {HIST_FILE}...")
    df = load_symbol_data(SYMBOL)
    prices = df['Close'].values
    dates = df['Date']
    
    print(f"   Date range: {dates.iloc[0].date()} to {dates.iloc[-1].date()}")
    print(f"   Data points: {len(prices)}")
    print(f"   Price range: Rp {int(prices.min())} - Rp {int(prices.max())}")
    
    # Compute CWT
    print(f"\n🌊 Running Continuous Wavelet Transform (Morlet, scales 1-31)...")
    
    p_norm = (prices - np.mean(prices)) / (np.std(prices) + 1e-8)
    result = pywt.cwt(p_norm, SCALES, 'morl', method='conv')
    # Handle both tuple and array returns
    if isinstance(result, tuple):
        coeffs = result[0]
    else:
        coeffs = result
    
    # Energy per scale
    if isinstance(coeffs, np.ndarray) and coeffs.ndim == 2:
        energy_per_scale = [float(np.sum(np.abs(coeffs[i, :]) ** 2)) for i in range(coeffs.shape[0])]
    else:
        energy_per_scale = [float(np.sum(np.abs(c) ** 2)) for c in coeffs]
    
    # Analysis
    cwt_results = compute_cwt_energy(prices)
    trend_results = analyze_trend(prices)
    
    print("\n" + "="*80)
    print("WAVELET ANALYSIS RESULTS")
    print("="*80)
    
    print(f"\n📈 Energy Distribution:")
    print(f"   Total Energy: {cwt_results['total_energy']:.4f}")
    pct_short = (cwt_results['short_scale_energy'] / cwt_results['total_energy'] * 100) if cwt_results['total_energy'] > 0 else 0
    pct_medium = (cwt_results['medium_scale_energy'] / cwt_results['total_energy'] * 100) if cwt_results['total_energy'] > 0 else 0
    pct_long = (cwt_results['long_scale_energy'] / cwt_results['total_energy'] * 100) if cwt_results['total_energy'] > 0 else 0
    print(f"   Short-scale (1-5):    {cwt_results['short_scale_energy']:.4f} ({pct_short:.1f}%)")
    print(f"   Medium-scale (6-15):  {cwt_results['medium_scale_energy']:.4f} ({pct_medium:.1f}%)")
    print(f"   Long-scale (16-31):   {cwt_results['long_scale_energy']:.4f} ({pct_long:.1f}%)")
    
    print(f"\n💡 Multi-Scale Alignment:")
    print(f"   Alignment Score: {cwt_results['alignment_score']:.4f}")
    stars = "⭐" * 5
    print(f"   Strength: {cwt_results['strength']} {stars}")
    
    print(f"\n📊 Trend Analysis (Last 5 days):")
    print(f"   Trend: {trend_results['trend']}")
    print(f"   Recent Momentum: {trend_results['recent_momentum']:+.2f}%")
    
    print(f"\n🎯 Final Score: {cwt_results['alignment_score']:.4f}")
    print(f"   Interpretation: High quality wavelet alignment" if cwt_results['alignment_score'] > 0.8 else "   Interpretation: Moderate alignment")
    
    # Generate visualization
    print(f"\n🎨 Generating wavelet visualization...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(OUTPUT_DIR, f"{SYMBOL}_wavelet_60d_{timestamp}.png")
    
    file_size = plot_cwt_pil(SYMBOL, prices, energy_per_scale, output_path)
    print(f"✓ Saved visualization: {output_path}")
    print(f"  Size: {file_size:.1f} KB")
    
    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("="*80)

if __name__ == '__main__':
    main()
