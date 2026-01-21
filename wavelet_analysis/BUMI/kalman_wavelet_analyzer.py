"""
Kalman Filter + Wavelet Analysis for BUMI Stock
Combines trend filtering with multi-scale signal detection
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pywt
from scipy import signal
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')


class KalmanWaveletAnalyzer:
    """Combined Kalman Filter and Wavelet analysis for stock price prediction"""
    
    def __init__(self, ticker='BUMI', csv_file='data/histories/ringkasan_histories_combined.csv'):
        self.ticker = ticker
        self.csv_file = csv_file
        self.prices = None
        self.dates = None
        self.kalman_trend = None
        self.noise = None
        self.wavelet_signal = None
        
    def load_data(self):
        """Load stock data"""
        df = pd.read_csv(self.csv_file)
        ticker_data = df[df['Kode Saham'] == self.ticker].copy()
        
        if len(ticker_data) == 0:
            raise ValueError(f"No data found for {self.ticker}")
        
        ticker_data['SourceDate'] = pd.to_datetime(ticker_data['SourceDate'])
        ticker_data = ticker_data.sort_values('SourceDate').reset_index(drop=True)
        
        self.prices = ticker_data['Penutupan'].values.astype(float)
        self.dates = ticker_data['SourceDate'].values
        
        print(f"✓ Loaded {len(self.prices)} trading days for {self.ticker}")
        return self.prices, self.dates
    
    def apply_kalman_filter(self, alpha=0.3):
        """
        Apply Simple Kalman-like exponential smoothing for trend extraction
        
        Alpha: Smoothing factor (0.0-1.0, lower = smoother trend)
        """
        filtered_trend = np.zeros_like(self.prices, dtype=float)
        filtered_trend[0] = self.prices[0]
        
        # Exponential smoothing (simpler Kalman approximation)
        for i in range(1, len(self.prices)):
            filtered_trend[i] = alpha * self.prices[i] + (1 - alpha) * filtered_trend[i - 1]
        
        self.kalman_trend = filtered_trend
        self.noise = self.prices - self.kalman_trend
        
        print(f"✓ Kalman Filter applied (alpha={alpha})")
        return self.kalman_trend, self.noise
    
    def calculate_trend_quality(self):
        """Assess how well Kalman trend fits"""
        rmse = np.sqrt(mean_squared_error(self.prices, self.kalman_trend))
        mae = mean_absolute_error(self.prices, self.kalman_trend)
        noise_std = np.std(self.noise)
        signal_to_noise = np.std(self.kalman_trend) / (noise_std + 1e-6)
        
        metrics = {
            'RMSE': rmse,
            'MAE': mae,
            'Noise Std Dev': noise_std,
            'Signal-to-Noise Ratio': signal_to_noise
        }
        return metrics
    
    def apply_wavelet_analysis(self, wavelet='morl', scales=None):
        """
        Apply Continuous Wavelet Transform to Kalman-filtered prices
        Using filtered trend for cleaner signal
        """
        if scales is None:
            scales = np.arange(1, min(len(self.kalman_trend), 16))
        
        # Apply CWT to the clean trend
        coefficients, frequencies = pywt.cwt(
            self.kalman_trend,
            scales,
            wavelet,
            method='conv'
        )
        
        # Generate trading signals from wavelet
        self.wavelet_signal = self._generate_trading_signals(coefficients)
        
        print(f"✓ Wavelet analysis applied ({len(scales)} scales)")
        return coefficients, frequencies
    
    def _generate_trading_signals(self, coefficients):
        """Generate multi-scale trading signals from wavelet coefficients"""
        signals = []
        
        # Define scale indices for different timeframes
        short_term_idx = 2 if len(coefficients) > 2 else 0
        medium_term_idx = len(coefficients) // 2
        long_term_idx = -1  # Last scale = longest timeframe
        
        for i in range(len(self.kalman_trend)):
            signal_strength = 0
            
            # Short-term trend
            if coefficients[short_term_idx, i] > 0:
                signal_strength += 1
            
            # Medium-term trend
            if coefficients[medium_term_idx, i] > 0:
                signal_strength += 1
            
            # Long-term trend
            if coefficients[long_term_idx, i] > 0:
                signal_strength += 1
            
            signals.append(signal_strength)
        
        return np.array(signals)
    
    def calculate_momentum(self):
        """Calculate momentum from Kalman trend velocity"""
        velocity = np.diff(self.kalman_trend, prepend=self.kalman_trend[0])
        momentum = velocity / (np.std(self.kalman_trend) + 1e-6)  # normalized
        return momentum
    
    def generate_combined_signal(self, wavelet_weight=0.6, momentum_weight=0.4):
        """
        Combine wavelet and momentum signals
        
        Wavelet: 3/3 multi-scale alignment (0-3)
        Momentum: normalized velocity direction (-1 to 1)
        """
        momentum = self.calculate_momentum()
        momentum_signal = (momentum > 0).astype(int) * (np.abs(momentum) / (np.max(np.abs(momentum)) + 1e-6))
        
        # Weighted combination
        combined = (self.wavelet_signal / 3.0) * wavelet_weight + momentum_signal * momentum_weight
        combined = combined * 3  # Scale back to 0-3 range
        
        return combined
    
    def get_report(self):
        """Generate analysis report"""
        trend_metrics = self.calculate_trend_quality()
        current_signal = self.wavelet_signal[-1]
        current_price = self.prices[-1]
        momentum = self.calculate_momentum()[-1]
        
        report = {
            'ticker': self.ticker,
            'data_points': len(self.prices),
            'current_price': current_price,
            'kalman_trend': self.kalman_trend[-1],
            'current_wavelet_signal': current_signal,
            'current_momentum': momentum,
            'price_range': (np.min(self.prices), np.max(self.prices)),
            'trend_metrics': trend_metrics,
            'signal_progression': self.wavelet_signal[-5:]  # Last 5 signals
        }
        
        return report
    
    def print_report(self):
        """Print analysis report"""
        report = self.get_report()
        
        print("\n" + "="*60)
        print(f"KALMAN-WAVELET ANALYSIS: {report['ticker']}")
        print("="*60)
        print(f"\nData Points: {report['data_points']}")
        print(f"Price Range: {report['price_range'][0]:.0f} - {report['price_range'][1]:.0f} IDR")
        print(f"Current Price: {report['current_price']:.0f} IDR")
        print(f"Kalman Trend: {report['kalman_trend']:.0f} IDR")
        print(f"Trend Deviation: {report['current_price'] - report['kalman_trend']:.0f} IDR")
        
        print(f"\nWavelet Signal (3/3 = STRONG BUY): {report['current_wavelet_signal']}/3")
        print(f"Momentum: {report['current_momentum']:+.3f}")
        
        print(f"\nTrend Quality Metrics:")
        for key, val in report['trend_metrics'].items():
            print(f"  {key}: {val:.4f}")
        
        print(f"\nLast 5 Wavelet Signals: {report['signal_progression'].astype(int)}")
        print("="*60)


def main():
    # Initialize analyzer
    analyzer = KalmanWaveletAnalyzer('BUMI')
    
    # Load data
    prices, dates = analyzer.load_data()
    
    # Apply Kalman filter
    kalman_trend, noise = analyzer.apply_kalman_filter(alpha=0.3)
    
    # Apply wavelet analysis to filtered trend
    coefficients, frequencies = analyzer.apply_wavelet_analysis()
    
    # Generate reports
    analyzer.print_report()
    
    # Visualization
    fig, axes = plt.subplots(4, 1, figsize=(14, 10))
    
    # Plot 1: Price and Kalman Trend
    axes[0].plot(dates, prices, 'o-', label='Actual Price', alpha=0.7, markersize=5)
    axes[0].plot(dates, kalman_trend, 'r-', linewidth=2, label='Kalman Trend')
    axes[0].fill_between(range(len(prices)), 
                         kalman_trend - np.std(noise),
                         kalman_trend + np.std(noise),
                         alpha=0.2, color='red', label='Noise Envelope')
    axes[0].set_ylabel('Price (IDR)')
    axes[0].set_title('BUMI: Price vs Kalman-Filtered Trend')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Residual Noise
    axes[1].bar(range(len(noise)), noise, alpha=0.7, color='orange')
    axes[1].axhline(0, color='black', linestyle='-', linewidth=0.5)
    axes[1].set_ylabel('Noise (IDR)')
    axes[1].set_title('Kalman Filter Residuals (Noise Component)')
    axes[1].grid(True, alpha=0.3)
    
    # Plot 3: Wavelet Signal
    colors = ['red' if s == 0 else 'orange' if s == 1 else 'yellow' if s == 2 else 'green' 
              for s in analyzer.wavelet_signal]
    axes[2].bar(range(len(analyzer.wavelet_signal)), analyzer.wavelet_signal, color=colors, alpha=0.7)
    axes[2].set_ylabel('Signal Strength')
    axes[2].set_ylim(0, 3.5)
    axes[2].set_title('Wavelet Multi-Scale Signal (0=SELL, 3=STRONG BUY)')
    axes[2].grid(True, alpha=0.3)
    
    # Plot 4: Momentum
    momentum = analyzer.calculate_momentum()
    axes[3].plot(range(len(momentum)), momentum, 'b-', linewidth=2)
    axes[3].axhline(0, color='black', linestyle='-', linewidth=0.5)
    axes[3].fill_between(range(len(momentum)), 0, momentum, 
                         where=(momentum >= 0), color='green', alpha=0.3, label='Positive')
    axes[3].fill_between(range(len(momentum)), 0, momentum, 
                         where=(momentum < 0), color='red', alpha=0.3, label='Negative')
    axes[3].set_ylabel('Momentum')
    axes[3].set_xlabel('Days')
    axes[3].set_title('Trend Momentum (Velocity of Price Change)')
    axes[3].legend()
    axes[3].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('wavelet_analysis/BUMI/kalman_wavelet_analysis.png', dpi=300, bbox_inches='tight')
    print("\n✓ Visualization saved: wavelet_analysis/BUMI/kalman_wavelet_analysis.png")
    
    return analyzer


if __name__ == '__main__':
    analyzer = main()
