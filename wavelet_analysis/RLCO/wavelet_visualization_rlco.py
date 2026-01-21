#!/usr/bin/env python3
"""
Wavelet Visualization for RLCO Stock
Creates comprehensive plots of wavelet analysis results
"""

import pandas as pd
import numpy as np
import pywt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

STOCK_SYMBOL = 'RLCO'
LOOKBACK_DAYS = 60
WAVELET = 'morl'
SCALES = np.arange(1, 32)

def load_rlco_data(csv_file='backtest_trades.csv'):
    """Load RLCO data"""
    df = pd.read_csv(csv_file)
    stock_data = df[df['Kode Saham'] == STOCK_SYMBOL].copy()
    stock_data['SourceDate'] = pd.to_datetime(stock_data['SourceDate'])
    stock_data = stock_data.sort_values('SourceDate').tail(LOOKBACK_DAYS)
    
    prices = stock_data['EntryPrice'].values
    dates = stock_data['SourceDate'].values.astype('datetime64[D]').astype(object)
    
    return prices, dates, stock_data

def normalize(prices):
    """Min-max normalization"""
    min_p = prices.min()
    max_p = prices.max()
    return (prices - min_p) / (max_p - min_p)

def create_wavelet_plot(prices, dates):
    """Create comprehensive wavelet visualization"""
    
    # Normalize
    normalized = normalize(prices)
    
    # Compute CWT
    coefficients = pywt.cwt(normalized, SCALES, WAVELET)[0]
    
    # Create figure
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(4, 2, figure=fig, hspace=0.35, wspace=0.3)
    
    # 1. Original Price Series
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(dates, prices, 'b-', linewidth=2, marker='o', markersize=4, label='RLCO Price')
    ax1.fill_between(dates, prices, alpha=0.3)
    ax1.set_ylabel('Price (IDR)', fontsize=11, fontweight='bold')
    ax1.set_title(f'{STOCK_SYMBOL} Stock Price - {len(dates)} Trading Days', 
                   fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 2. Continuous Wavelet Transform (Heatmap)
    ax2 = fig.add_subplot(gs[1, :])
    im = ax2.contourf(dates, SCALES, np.abs(coefficients), levels=100, cmap='jet')
    ax2.set_ylabel('Scale (Frequency)', fontsize=11, fontweight='bold')
    ax2.set_title('Continuous Wavelet Transform (CWT) - Power Spectrum', 
                   fontsize=12, fontweight='bold')
    cbar = plt.colorbar(im, ax=ax2, label='Wavelet Power')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 3. Multi-Scale Components
    ax3 = fig.add_subplot(gs[2, 0])
    short_scale = len(coefficients) // 4
    medium_scale = len(coefficients) // 2
    long_scale = 3 * len(coefficients) // 4
    
    ax3.plot(dates, np.real(coefficients[short_scale, :]), label='Short-term (High Freq)', linewidth=2)
    ax3.plot(dates, np.real(coefficients[medium_scale, :]), label='Medium-term (Mid Freq)', linewidth=2)
    ax3.plot(dates, np.real(coefficients[long_scale, :]), label='Long-term (Low Freq)', linewidth=2)
    ax3.set_ylabel('Wavelet Coefficient', fontsize=10, fontweight='bold')
    ax3.set_title('Multi-Scale Trend Components', fontsize=12, fontweight='bold')
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 4. Scale Energy Distribution
    ax4 = fig.add_subplot(gs[2, 1])
    energies = [np.sum(np.square(coefficients[i, :])) for i in range(len(coefficients))]
    colors = plt.cm.viridis(np.linspace(0, 1, len(SCALES)))
    ax4.bar(SCALES, energies, color=colors, edgecolor='black', linewidth=0.5)
    ax4.set_xlabel('Scale', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Energy', fontsize=10, fontweight='bold')
    ax4.set_title('Wavelet Energy by Scale', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Normalized Price with Reversed Scales
    ax5 = fig.add_subplot(gs[3, :])
    ax5_twin = ax5.twinx()
    
    ax5.plot(dates, normalized, 'b-', linewidth=2.5, label='Normalized Price', marker='o', markersize=4)
    
    # Overlay the mid-scale wavelet signal
    mid_scale = len(coefficients) // 2
    wavelet_signal = np.real(coefficients[mid_scale, :])
    wavelet_normalized = (wavelet_signal - wavelet_signal.min()) / (wavelet_signal.max() - wavelet_signal.min())
    
    ax5_twin.plot(dates, wavelet_normalized, 'r--', linewidth=2, label=f'Wavelet Signal (Scale {SCALES[mid_scale]})', alpha=0.7)
    
    ax5.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Normalized Price', fontsize=11, fontweight='bold', color='b')
    ax5_twin.set_ylabel('Normalized Wavelet Signal', fontsize=11, fontweight='bold', color='r')
    ax5.set_title('Price vs Wavelet Signal Alignment', fontsize=12, fontweight='bold')
    ax5.tick_params(axis='y', labelcolor='b')
    ax5_twin.tick_params(axis='y', labelcolor='r')
    ax5.grid(True, alpha=0.3)
    ax5.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Add legends
    lines1, labels1 = ax5.get_legend_handles_labels()
    lines2, labels2 = ax5_twin.get_legend_handles_labels()
    ax5.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # Main title
    fig.suptitle(f'Wavelet Analysis Report: {STOCK_SYMBOL} Stock\n'
                 f'{WAVELET.upper()} Wavelet - {len(dates)} Data Points - '
                 f'{dates[0].strftime("%Y-%m-%d")} to {dates[-1].strftime("%Y-%m-%d")}',
                 fontsize=14, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    
    # Save
    output_file = f'RLCO_wavelet_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Visualization saved: {output_file}")
    
    # Don't show in headless mode
    # plt.show()

def main():
    """Main execution"""
    print(f"\n{'='*70}")
    print(f"WAVELET VISUALIZATION: {STOCK_SYMBOL}")
    print(f"{'='*70}")
    
    prices, dates, data = load_rlco_data()
    print(f"✅ Loaded {len(prices)} data points for {STOCK_SYMBOL}")
    print(f"   Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    print(f"   Price range: {prices.min():.2f} - {prices.max():.2f}")
    
    print(f"\n🎨 Creating wavelet visualizations...")
    create_wavelet_plot(prices, dates)

if __name__ == '__main__':
    main()
