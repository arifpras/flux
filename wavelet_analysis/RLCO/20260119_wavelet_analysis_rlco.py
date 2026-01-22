#!/usr/bin/env python3
"""
Wavelet Analysis for RLCO Stock
Analyzes multi-scale price trends and identifies trading signals using continuous wavelet transform
"""

import pandas as pd
import numpy as np
import pywt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import signal
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration
STOCK_SYMBOL = 'RLCO'
LOOKBACK_DAYS = 60
WAVELET = 'morl'  # Morlet wavelet - best for trading signals
SCALES = np.arange(1, 32)  # Multiple scales for decomposition

class WaveletAnalyzer:
    """Perform wavelet analysis on stock price data"""
    
    def __init__(self, symbol, lookback_days=60):
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.data = None
        self.closing_prices = None
        self.normalized_prices = None
        
    def load_data(self, csv_file='backtest_trades.csv'):
        """Load historical data for the stock from backtest trades"""
        try:
            df = pd.read_csv(csv_file)
            
            # Filter for the symbol (column name is 'Kode Saham')
            stock_data = df[df['Kode Saham'] == self.symbol].copy()
            
            if stock_data.empty:
                print(f"❌ No data found for {self.symbol}")
                return False
            
            # Parse date and sort
            stock_data['SourceDate'] = pd.to_datetime(stock_data['SourceDate'])
            stock_data = stock_data.sort_values('SourceDate').tail(self.lookback_days)
            
            # Get entry prices as proxy for closing prices
            if 'EntryPrice' in stock_data.columns:
                self.closing_prices = stock_data['EntryPrice'].values
            else:
                print(f"❌ No price column found")
                return False
            
            self.data = stock_data
            self.normalized_prices = self._normalize(self.closing_prices)
            
            print(f"✅ Loaded {len(self.data)} data points for {self.symbol}")
            print(f"   Date range: {stock_data['SourceDate'].min().date()} to {stock_data['SourceDate'].max().date()}")
            print(f"   Price range: {self.closing_prices.min():.2f} - {self.closing_prices.max():.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def _normalize(self, prices):
        """Min-max normalization for better wavelet analysis"""
        min_price = prices.min()
        max_price = prices.max()
        return (prices - min_price) / (max_price - min_price)
    
    def continuous_wavelet_transform(self, wavelet='morl'):
        """Perform continuous wavelet transform"""
        print(f"\n🌊 Computing Continuous Wavelet Transform ({wavelet})...")
        
        # Perform CWT - use scale as 1/frequency
        result = pywt.cwt(
            self.normalized_prices,
            SCALES,
            wavelet
        )
        
        # Extract coefficients (pywt.cwt returns a tuple)
        coefficients = result[0] if isinstance(result, tuple) else result
        
        print(f"   CWT shape: {coefficients.shape}")
        print(f"   Number of scales analyzed: {len(coefficients)}")
        
        return coefficients
    
    def discrete_wavelet_decomposition(self, level=3, wavelet='sym3'):
        """Decompose signal into approximation and detail coefficients"""
        print(f"\n📊 Computing Discrete Wavelet Decomposition (level {level})...")
        
        decomposition = {}
        signal_data = self.normalized_prices.copy()
        
        # Multi-level decomposition
        for i in range(level):
            cA, cD = pywt.dwt(signal_data, wavelet)
            decomposition[f'level_{i+1}'] = {
                'approximation': cA,
                'detail': cD
            }
            signal_data = cA  # Continue with approximation for next level
        
        print(f"   Decomposition complete: {len(decomposition)} levels")
        
        return decomposition
    
    def identify_trend_reversals(self, coefficients, threshold=0.5):
        """Identify potential trend reversals from wavelet coefficients"""
        print(f"\n🔍 Identifying Trend Reversals...")
        
        # Use mid-scale coefficients (best signal-to-noise ratio)
        mid_scale = len(coefficients) // 2
        wavelet_signal = coefficients[mid_scale]
        
        # Find extrema (peaks and troughs)
        peaks, _ = signal.find_peaks(wavelet_signal, height=threshold)
        troughs, _ = signal.find_peaks(-wavelet_signal, height=threshold)
        
        # Combine and sort
        reversals = np.sort(np.concatenate([peaks, troughs]))
        
        print(f"   Found {len(peaks)} peaks and {len(troughs)} troughs")
        print(f"   Potential reversal points: {len(reversals)}")
        
        return reversals, peaks, troughs
    
    def calculate_wavelet_entropy(self, coefficients):
        """Calculate Shannon entropy of wavelet coefficients"""
        print(f"\n📈 Calculating Wavelet Entropy (signal complexity)...")
        
        energies = []
        for coeff in coefficients:
            # Energy of each scale
            energy = np.sum(np.square(coeff))
            energies.append(energy)
        
        energies = np.array(energies)
        total_energy = np.sum(energies)
        
        # Normalize to probability
        probabilities = energies / total_energy
        
        # Shannon entropy
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        
        print(f"   Total wavelet energy: {total_energy:.6f}")
        print(f"   Shannon entropy: {entropy:.4f}")
        print(f"   Interpretation: {'Low (organized)' if entropy < 4 else 'High (chaotic)'}")
        
        return entropy, energies
    
    def generate_trading_signals(self, coefficients):
        """Generate trading signals from wavelet analysis"""
        print(f"\n💡 Generating Trading Signals...")
        
        signals = []
        
        # Use multiple scales (short, medium, long term)
        short_scale = len(coefficients) // 4  # High frequency
        medium_scale = len(coefficients) // 2  # Medium frequency
        long_scale = 3 * len(coefficients) // 4  # Low frequency
        
        short_term = coefficients[short_scale]
        medium_term = coefficients[medium_scale]
        long_term = coefficients[long_scale]
        
        # Generate signals
        for i in range(1, len(self.normalized_prices)):
            signal_info = {
                'index': i,
                'price': self.closing_prices[i],
                'wavelet_short': short_term[i] if i < len(short_term) else 0,
                'wavelet_medium': medium_term[i] if i < len(medium_term) else 0,
                'wavelet_long': long_term[i] if i < len(long_term) else 0,
            }
            
            # Determine signal strength
            alignment = 0
            if signal_info['wavelet_short'] > 0:
                alignment += 1
            if signal_info['wavelet_medium'] > 0:
                alignment += 1
            if signal_info['wavelet_long'] > 0:
                alignment += 1
            
            signal_info['alignment'] = alignment
            
            # Signal type
            if alignment == 3:
                signal_info['signal'] = 'STRONG BUY'
                signal_info['strength'] = 3
            elif alignment == 2:
                signal_info['signal'] = 'BUY'
                signal_info['strength'] = 2
            elif alignment == 1:
                signal_info['signal'] = 'NEUTRAL'
                signal_info['strength'] = 1
            else:
                signal_info['signal'] = 'SELL'
                signal_info['strength'] = 0
            
            signals.append(signal_info)
        
        # Get recent signals
        recent_signals = signals[-10:]
        
        print(f"\n   Last 10 signals:")
        for sig in recent_signals:
            bar_length = sig['strength'] * 3
            bar = '█' * bar_length
            print(f"   [{bar:<9}] {sig['signal']:10s} | Price: {sig['price']:8.2f}")
        
        return signals
    
    def print_report(self):
        """Generate comprehensive wavelet analysis report"""
        if self.data is None or self.closing_prices is None:
            print("❌ No data loaded")
            return
        
        print(f"\n{'='*70}")
        print(f"WAVELET ANALYSIS REPORT: {self.symbol}")
        print(f"{'='*70}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data Points: {len(self.data)}")
        print(f"Wavelet: {WAVELET}")
        print(f"Price Range: {self.closing_prices.min():.2f} - {self.closing_prices.max():.2f}")
        
        # Perform analyses
        coefficients = self.continuous_wavelet_transform(WAVELET)
        decomposition = self.discrete_wavelet_decomposition(level=3, wavelet='sym3')
        reversals, peaks, troughs = self.identify_trend_reversals(coefficients)
        entropy, energies = self.calculate_wavelet_entropy(coefficients)
        signals = self.generate_trading_signals(coefficients)
        
        # Summary
        print(f"\n{'='*70}")
        print(f"SUMMARY & INTERPRETATION")
        print(f"{'='*70}")
        
        # Current trend
        current_signal = signals[-1]
        print(f"\n📌 Current Status:")
        print(f"   Signal: {current_signal['signal']}")
        print(f"   Current Price: {current_signal['price']:.2f}")
        print(f"   Multi-scale Alignment: {current_signal['alignment']}/3")
        
        # Trend direction
        price_change = ((self.closing_prices[-1] - self.closing_prices[0]) / self.closing_prices[0]) * 100
        print(f"\n📊 Price Trend:")
        print(f"   Change (lookback): {price_change:+.2f}%")
        print(f"   Highest: {self.closing_prices.max():.2f}")
        print(f"   Lowest: {self.closing_prices.min():.2f}")
        
        # Volatility from wavelet decomposition
        detail_energies = []
        for level_data in decomposition.values():
            detail = level_data['detail']
            detail_energies.append(np.sum(np.square(detail)))
        avg_detail_energy = np.mean(detail_energies)
        
        print(f"\n⚡ Volatility (from wavelet details):")
        print(f"   Average detail energy: {avg_detail_energy:.6f}")
        print(f"   Volatility level: {'High' if avg_detail_energy > 0.01 else 'Moderate' if avg_detail_energy > 0.005 else 'Low'}")
        
        # Scale-by-scale energy
        print(f"\n🌊 Scale Analysis (Energy Distribution):")
        top_3_scales = np.argsort(energies)[-3:][::-1]
        for i, scale_idx in enumerate(top_3_scales, 1):
            print(f"   {i}. Scale {scale_idx}: Energy = {energies[scale_idx]:.6f}")
        
        print(f"\n{'='*70}\n")


def main():
    """Main execution"""
    analyzer = WaveletAnalyzer(STOCK_SYMBOL, LOOKBACK_DAYS)
    
    if analyzer.load_data():
        analyzer.print_report()
    else:
        print(f"Failed to analyze {STOCK_SYMBOL}")


if __name__ == '__main__':
    main()
