#!/usr/bin/env python3
"""Quick wavelet analysis for BUMI"""
import pandas as pd
import numpy as np
import pywt

# Load BUMI data
df = pd.read_csv('backtest_trades.csv')
bumi = df[df['Kode Saham'] == 'BUMI'].copy()
bumi['SourceDate'] = pd.to_datetime(bumi['SourceDate'])
bumi = bumi.sort_values('SourceDate')

print(f'BUMI Data Points: {len(bumi)}')
print(f'Date Range: {bumi["SourceDate"].min().date()} to {bumi["SourceDate"].max().date()}')
print(f'Price Range: {bumi["EntryPrice"].min():.0f} - {bumi["EntryPrice"].max():.0f} IDR')
print(f'Average Return: {bumi["GrossReturn"].mean():.2f}%')
print()

# Normalize prices
prices = bumi['EntryPrice'].values
normalized = (prices - prices.min()) / (prices.max() - prices.min())

# Wavelet analysis
SCALES = np.arange(1, min(len(prices), 16))
coefficients = pywt.cwt(normalized, SCALES, 'morl')[0]

# Generate signals
short_scale = len(coefficients) // 4
medium_scale = len(coefficients) // 2
long_scale = 3 * len(coefficients) // 4

signals = []
for i in range(len(prices)):
    alignment = 0
    if i < len(coefficients[short_scale]) and coefficients[short_scale][i] > 0:
        alignment += 1
    if i < len(coefficients[medium_scale]) and coefficients[medium_scale][i] > 0:
        alignment += 1
    if i < len(coefficients[long_scale]) and coefficients[long_scale][i] > 0:
        alignment += 1
    
    if alignment == 3:
        signal = 'STRONG BUY'
    elif alignment == 2:
        signal = 'BUY'
    elif alignment == 1:
        signal = 'NEUTRAL'
    else:
        signal = 'SELL'
    
    signals.append({'price': prices[i], 'signal': signal, 'alignment': alignment})

# Show progression
print('BUMI Signal Progression:')
for i, sig in enumerate(signals, start=1):
    bar = '█' * (sig['alignment'] * 3)
    print(f'  Day {i}: [{bar:<9}] {sig["signal"]:10s} @ {sig["price"]:>6.0f} IDR')

print()
print(f'Current Signal: {signals[-1]["signal"]} ({signals[-1]["alignment"]}/3)')
print(f'Current Price: {prices[-1]:.0f} IDR')
print(f'Price Change: {((prices[-1] - prices[0]) / prices[0] * 100):+.2f}%')

# Calculate entropy
energies = [np.sum(np.square(coefficients[i])) for i in range(len(coefficients))]
total_energy = np.sum(energies)
probabilities = energies / total_energy
entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))

print(f'Shannon Entropy: {entropy:.2f}')
print(f'Volatility: {"HIGH" if entropy > 3.5 else "MODERATE" if entropy > 2.5 else "LOW"}')
