#!/usr/bin/env python3
"""
Generic Wavelet Visualization for a Given Stock Symbol
Reads augmented price series and generates wavelet plots similar to RLCO.
"""
import os
import argparse
import pandas as pd
import numpy as np
import pywt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
HIST_DIR = os.path.join(DATA_DIR, 'histories')
AUGMENTED = os.path.join(HIST_DIR, 'augmented_prices_5stocks.csv')

WAVELET = 'morl'
SCALES = np.arange(1, 32)

def normalize(prices):
    mn, mx = np.min(prices), np.max(prices)
    if mx == mn:
        return np.zeros_like(prices)
    return (prices - mn) / (mx - mn)

def load_series(symbol: str, lookback: int = 60):
    df = pd.read_csv(AUGMENTED, parse_dates=['SourceDate'])
    df = df[df['Symbol'] == symbol].sort_values('SourceDate')
    if lookback:
        df = df.tail(lookback)
    prices = df['Price'].astype(float).values
    dates = df['SourceDate'].values.astype('datetime64[D]').astype(object)
    return prices, dates, df

def create_wavelet_plot(symbol: str, prices, dates, out_dir: str):
    normalized = normalize(prices)
    coeffs = pywt.cwt(normalized, SCALES, WAVELET)[0]

    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(4, 2, figure=fig, hspace=0.35, wspace=0.3)

    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(dates, prices, 'b-', linewidth=2, marker='o', markersize=4, label=f'{symbol} Price')
    ax1.fill_between(dates, prices, alpha=0.3)
    ax1.set_ylabel('Price (IDR)', fontsize=11, fontweight='bold')
    ax1.set_title(f'{symbol} Stock Price - {len(dates)} Trading Days', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

    ax2 = fig.add_subplot(gs[1, :])
    im = ax2.contourf(dates, SCALES, np.abs(coeffs), levels=100, cmap='jet')
    ax2.set_ylabel('Scale (Frequency)', fontsize=11, fontweight='bold')
    ax2.set_title('Continuous Wavelet Transform (CWT) - Power Spectrum', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax2, label='Wavelet Power')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

    ax3 = fig.add_subplot(gs[2, 0])
    short_scale = len(coeffs) // 4
    medium_scale = len(coeffs) // 2
    long_scale = 3 * len(coeffs) // 4
    ax3.plot(dates, np.real(coeffs[short_scale, :]), label='Short-term (High Freq)', linewidth=2)
    ax3.plot(dates, np.real(coeffs[medium_scale, :]), label='Medium-term (Mid Freq)', linewidth=2)
    ax3.plot(dates, np.real(coeffs[long_scale, :]), label='Long-term (Low Freq)', linewidth=2)
    ax3.set_ylabel('Wavelet Coefficient', fontsize=10, fontweight='bold')
    ax3.set_title('Multi-Scale Trend Components', fontsize=12, fontweight='bold')
    ax3.legend(loc='best'); ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')

    ax4 = fig.add_subplot(gs[2, 1])
    energies = [np.sum(np.square(coeffs[i, :])) for i in range(len(coeffs))]
    colors = plt.cm.viridis(np.linspace(0, 1, len(SCALES)))
    ax4.bar(SCALES, energies, color=colors, edgecolor='black', linewidth=0.5)
    ax4.set_xlabel('Scale', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Energy', fontsize=10, fontweight='bold')
    ax4.set_title('Wavelet Energy by Scale', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    ax5 = fig.add_subplot(gs[3, :])
    ax5_twin = ax5.twinx()
    ax5.plot(dates, normalized, 'b-', linewidth=2.5, label='Normalized Price', marker='o', markersize=4)
    mid_scale = len(coeffs) // 2
    wave = np.real(coeffs[mid_scale, :])
    wave_norm = (wave - wave.min()) / (wave.max() - wave.min() + 1e-9)
    ax5_twin.plot(dates, wave_norm, 'r--', linewidth=2, label=f'Wavelet Signal (Scale {SCALES[mid_scale]})', alpha=0.7)
    ax5.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Normalized Price', fontsize=11, fontweight='bold', color='b')
    ax5_twin.set_ylabel('Normalized Wavelet Signal', fontsize=11, fontweight='bold', color='r')
    ax5.set_title('Price vs Wavelet Signal Alignment', fontsize=12, fontweight='bold')
    ax5.tick_params(axis='y', labelcolor='b'); ax5_twin.tick_params(axis='y', labelcolor='r')
    ax5.grid(True, alpha=0.3)
    ax5.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')
    lines1, labels1 = ax5.get_legend_handles_labels(); lines2, labels2 = ax5_twin.get_legend_handles_labels()
    ax5.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    fig.suptitle(f'Wavelet Analysis Report: {symbol} Stock\n{WAVELET.upper()} Wavelet - {len(dates)} Data Points - {dates[0].strftime("%Y-%m-%d")} to {dates[-1].strftime("%Y-%m-%d")}', fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()

    os.makedirs(out_dir, exist_ok=True)
    output_file = os.path.join(out_dir, f'{symbol}_wavelet_analysis.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f'✅ Saved visualization: {output_file}')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--symbol', required=True, help='Stock symbol (e.g., RLCO)')
    ap.add_argument('--lookback', type=int, default=60, help='Max points to include')
    args = ap.parse_args()

    prices, dates, df = load_series(args.symbol, args.lookback)
    if len(prices) < 10:
        print(f'⚠️ Not enough data points for {args.symbol}: {len(prices)}. Need >= 10.')
        return
    out_dir = os.path.join(BASE_DIR, 'wavelet_analysis', args.symbol)
    create_wavelet_plot(args.symbol, prices, dates, out_dir)

if __name__ == '__main__':
    main()
