"""
Backtesting Framework for Foreign Buy + Declining Stocks Strategy
===================================================================

Time Series Backtesting with Walk-Forward Analysis

Strategy Rules:
1. Identify stocks with net foreign buy in last N days (default: 5)
2. Filter for declining prices (-5% to -0.5%)
3. Apply fundamental quality filters (optional)
4. Calculate forward returns

Metrics Calculated:
- Win rate
- Average return (winners vs losers)
- Sharpe ratio
- Maximum drawdown
- Profit factor
- Total return vs benchmark (market average)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
RESULTS_DIR = Path(__file__).parent.parent.parent / 'data' / 'backtest'
RESULTS_DIR.mkdir(exist_ok=True)

# Strategy Parameters
LOOKBACK_DAYS = 5  # Foreign buy lookback period
DECLINE_MIN = -0.05  # -5%
DECLINE_MAX = -0.005  # -0.5%
FOREIGN_BUY_MIN = 0  # Minimum net foreign buy (shares)
HOLDING_PERIODS = [5, 10, 20]  # Forward return periods (days)

# Quality Filters (optional)
USE_QUALITY_FILTERS = True
MIN_MARKET_CAP = 5e12  # 5 Trillion IDR
MAX_PER = 20
MIN_ROE = 5  # 5%


class ForeignBuyBacktester:
    """Backtesting engine for foreign buy strategy"""
    
    def __init__(self, start_date=None, end_date=None):
        """Initialize backtester with date range"""
        self.start_date = start_date
        self.end_date = end_date
        self.load_data()
        
    def load_data(self):
        """Load all required datasets"""
        print("Loading data...")
        
        # 1. Foreign flow data
        self.foreign_data = pd.read_csv(
            DATA_DIR / 'histories' / 'ringkasan_histories_combined.csv'
        )
        self.foreign_data['SourceDate'] = pd.to_datetime(self.foreign_data['SourceDate'])
        self.foreign_data['NetForeignBuy'] = (
            self.foreign_data['Foreign Buy'] - self.foreign_data['Foreign Sell']
        )
        print(f"  Foreign data: {len(self.foreign_data):,} rows, "
              f"{self.foreign_data['SourceDate'].min()} to {self.foreign_data['SourceDate'].max()}")
        
        # 2. Price data
        self.price_data = pd.read_csv(
            DATA_DIR / 'histories' / 'idx_historical_60d_20260120.csv'
        )
        self.price_data['Date'] = pd.to_datetime(self.price_data['Date'])
        self.price_data = self.price_data.rename(columns={'Symbol': 'Ticker'})
        print(f"  Price data: {len(self.price_data):,} rows, "
              f"{self.price_data['Date'].min()} to {self.price_data['Date'].max()}")
        
        # 3. Fundamental data (optional)
        try:
            self.fundamental_data = pd.read_excel(
                DATA_DIR / 'manual' / 'IDX-Stock-Screener-20Jan2026.xlsx',
                engine='openpyxl'
            )
            # Clean column names
            self.fundamental_data.columns = self.fundamental_data.columns.str.strip()
            print(f"  Fundamental data: {len(self.fundamental_data):,} stocks")
            self.has_fundamentals = True
        except Exception as e:
            print(f"  Warning: Could not load fundamentals: {e}")
            self.has_fundamentals = False
        
        # Get all unique dates in price data for iteration
        self.all_dates = sorted(self.price_data['Date'].unique())
        print(f"  Total trading days: {len(self.all_dates)}")
        
    def calculate_foreign_buy_signal(self, date, lookback_days=5):
        """
        Calculate net foreign buy for each stock over lookback period
        
        Args:
            date: Analysis date (pd.Timestamp)
            lookback_days: Number of days to look back
            
        Returns:
            DataFrame with stock, net_foreign_buy, avg_price
        """
        # Get data for lookback period (must be BEFORE the analysis date)
        end_date = date - timedelta(days=1)
        start_date = end_date - timedelta(days=lookback_days * 2)  # Buffer for weekends
        
        mask = (
            (self.foreign_data['SourceDate'] > start_date) &
            (self.foreign_data['SourceDate'] <= end_date)
        )
        period_data = self.foreign_data[mask].copy()
        
        if len(period_data) == 0:
            return pd.DataFrame()
        
        # Get most recent N trading days
        recent_dates = sorted(period_data['SourceDate'].unique())[-lookback_days:]
        period_data = period_data[period_data['SourceDate'].isin(recent_dates)]
        
        # Aggregate by stock
        agg = period_data.groupby('Kode Saham').agg({
            'NetForeignBuy': 'sum',
            'Penutupan': 'last',  # Last closing price in period
            'Volume': 'sum'
        }).reset_index()
        
        agg.columns = ['Ticker', 'NetForeignBuy', 'LastPrice', 'TotalVolume']
        
        # Filter for net buyers only
        agg = agg[agg['NetForeignBuy'] > FOREIGN_BUY_MIN]
        
        return agg
    
    def calculate_price_change(self, date, lookback_days=5):
        """
        Calculate price change over lookback period
        
        Args:
            date: Analysis date
            lookback_days: Number of days to look back
            
        Returns:
            DataFrame with stock, price_change_pct, current_price
        """
        # Get price data up to analysis date
        mask = self.price_data['Date'] <= date
        hist_prices = self.price_data[mask].copy()
        
        if len(hist_prices) == 0:
            return pd.DataFrame()
        
        # Get lookback period
        available_dates = sorted(hist_prices['Date'].unique())
        if len(available_dates) < lookback_days + 1:
            return pd.DataFrame()
        
        current_date = available_dates[-1]
        start_date = available_dates[-(lookback_days + 1)]
        
        # Get start and end prices
        start_prices = hist_prices[hist_prices['Date'] == start_date][['Ticker', 'Close']].copy()
        start_prices.columns = ['Ticker', 'StartPrice']
        
        end_prices = hist_prices[hist_prices['Date'] == current_date][['Ticker', 'Close']].copy()
        end_prices.columns = ['Ticker', 'CurrentPrice']
        
        # Merge and calculate change
        price_change = pd.merge(start_prices, end_prices, on='Ticker')
        price_change['PriceChangePct'] = (
            (price_change['CurrentPrice'] - price_change['StartPrice']) / 
            price_change['StartPrice']
        )
        
        return price_change
    
    def calculate_forward_returns(self, date, tickers, holding_days=5):
        """
        Calculate forward returns for given stocks
        
        Args:
            date: Entry date
            tickers: List of stock tickers
            holding_days: Holding period in days
            
        Returns:
            DataFrame with ticker, entry_price, exit_price, forward_return
        """
        # Get future price data (AFTER entry date)
        future_mask = self.price_data['Date'] > date
        future_prices = self.price_data[future_mask].copy()
        
        if len(future_prices) == 0:
            return pd.DataFrame()
        
        # Get entry prices (at analysis date)
        entry_mask = self.price_data['Date'] == date
        entry_prices = self.price_data[entry_mask & self.price_data['Ticker'].isin(tickers)].copy()
        entry_prices = entry_prices[['Ticker', 'Close']].copy()
        entry_prices.columns = ['Ticker', 'EntryPrice']
        
        if len(entry_prices) == 0:
            return pd.DataFrame()
        
        # Get exit prices (holding_days trading days later)
        future_dates = sorted(future_prices['Date'].unique())
        if len(future_dates) < holding_days:
            exit_date = future_dates[-1] if future_dates else None
            actual_holding_days = len(future_dates)
        else:
            exit_date = future_dates[holding_days - 1]
            actual_holding_days = holding_days
        
        if exit_date is None:
            return pd.DataFrame()
        
        exit_prices = future_prices[
            (future_prices['Date'] == exit_date) & 
            (future_prices['Ticker'].isin(tickers))
        ].copy()
        exit_prices = exit_prices[['Ticker', 'Close']].copy()
        exit_prices.columns = ['Ticker', 'ExitPrice']
        
        # Merge and calculate returns
        returns = pd.merge(entry_prices, exit_prices, on='Ticker', how='left')
        returns['ForwardReturn'] = (
            (returns['ExitPrice'] - returns['EntryPrice']) / returns['EntryPrice']
        )
        returns['HoldingDays'] = actual_holding_days
        returns['ExitDate'] = exit_date
        
        return returns
    
    def apply_fundamental_filters(self, tickers):
        """
        Apply quality filters based on fundamentals
        
        Args:
            tickers: List of stock tickers
            
        Returns:
            Filtered list of tickers
        """
        if not self.has_fundamentals or not USE_QUALITY_FILTERS:
            return tickers
        
        # Filter fundamentals
        fund = self.fundamental_data[
            self.fundamental_data['Code'].isin(tickers)
        ].copy()
        
        # Apply filters
        filtered = fund[
            (fund['PER'].notna()) & 
            (fund['PER'] > 0) & 
            (fund['PER'] < MAX_PER) &
            (fund['ROE (%)'].notna()) & 
            (fund['ROE (%)'] > MIN_ROE)
        ]
        
        return filtered['Code'].tolist()
    
    def run_backtest(self, lookback_days=5, holding_days=5):
        """
        Run complete backtest with walk-forward analysis
        
        Args:
            lookback_days: Foreign buy lookback period
            holding_days: Forward return holding period
            
        Returns:
            DataFrame with all trades
        """
        print(f"\nRunning backtest: {lookback_days}D lookback, {holding_days}D holding period")
        print("=" * 80)
        
        all_trades = []
        
        # Walk forward through dates
        # Start from date where we have enough lookback data
        valid_dates = [d for d in self.all_dates if d >= self.all_dates[lookback_days + 5]]
        
        # End before we run out of forward data
        valid_dates = valid_dates[:-holding_days]
        
        print(f"Backtesting period: {valid_dates[0]} to {valid_dates[-1]}")
        print(f"Total test dates: {len(valid_dates)}\n")
        
        for i, analysis_date in enumerate(valid_dates):
            # Progress
            if (i + 1) % 5 == 0:
                print(f"  Processing {i+1}/{len(valid_dates)}: {analysis_date.date()}", end='\r')
            
            # Step 1: Get foreign buy stocks
            foreign_buy = self.calculate_foreign_buy_signal(analysis_date, lookback_days)
            if len(foreign_buy) == 0:
                continue
            
            # Step 2: Get price changes
            price_change = self.calculate_price_change(analysis_date, lookback_days)
            if len(price_change) == 0:
                continue
            
            # Step 3: Merge signals
            signals = pd.merge(foreign_buy, price_change, on='Ticker', how='inner')
            
            # Step 4: Filter for declining stocks
            signals = signals[
                (signals['PriceChangePct'] >= DECLINE_MIN) &
                (signals['PriceChangePct'] <= DECLINE_MAX)
            ]
            
            if len(signals) == 0:
                continue
            
            # Step 5: Apply fundamental filters
            candidate_tickers = signals['Ticker'].tolist()
            if USE_QUALITY_FILTERS and self.has_fundamentals:
                filtered_tickers = self.apply_fundamental_filters(candidate_tickers)
                signals = signals[signals['Ticker'].isin(filtered_tickers)]
            
            if len(signals) == 0:
                continue
            
            # Step 6: Calculate forward returns
            forward_returns = self.calculate_forward_returns(
                analysis_date, signals['Ticker'].tolist(), holding_days
            )
            
            if len(forward_returns) == 0:
                continue
            
            # Step 7: Combine all data
            trades = pd.merge(signals, forward_returns, on='Ticker', how='left')
            trades['AnalysisDate'] = analysis_date
            trades['Lookback'] = lookback_days
            trades['HoldingTarget'] = holding_days
            
            all_trades.append(trades)
        
        print("\n")
        
        if not all_trades:
            print("WARNING: No trades generated!")
            return pd.DataFrame()
        
        # Combine all trades
        results = pd.concat(all_trades, ignore_index=True)
        
        # Remove trades with missing forward returns
        results = results.dropna(subset=['ForwardReturn'])
        
        print(f"Total trades generated: {len(results)}")
        print(f"Unique stocks traded: {results['Ticker'].nunique()}")
        print(f"Unique entry dates: {results['AnalysisDate'].nunique()}")
        
        return results
    
    def calculate_metrics(self, trades):
        """Calculate performance metrics"""
        if len(trades) == 0:
            return {}
        
        returns = trades['ForwardReturn'].dropna()
        
        # Basic stats
        total_trades = len(returns)
        winners = returns[returns > 0]
        losers = returns[returns <= 0]
        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        
        # Return stats
        avg_return = returns.mean()
        median_return = returns.median()
        avg_winner = winners.mean() if len(winners) > 0 else 0
        avg_loser = losers.mean() if len(losers) > 0 else 0
        
        # Risk metrics
        std_return = returns.std()
        sharpe = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        # Cumulative returns
        cum_returns = (1 + returns).cumprod()
        total_return = cum_returns.iloc[-1] - 1
        max_drawdown = (cum_returns / cum_returns.cummax() - 1).min()
        
        # Profit factor
        gross_profit = winners.sum() if len(winners) > 0 else 0
        gross_loss = abs(losers.sum()) if len(losers) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
        
        metrics = {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'median_return': median_return,
            'avg_winner': avg_winner,
            'avg_loser': avg_loser,
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'std_return': std_return
        }
        
        return metrics
    
    def print_metrics(self, metrics, label="Strategy"):
        """Print metrics in formatted table"""
        print(f"\n{label} Performance Metrics")
        print("=" * 60)
        print(f"Total Trades:        {metrics['total_trades']:>8}")
        print(f"Win Rate:            {metrics['win_rate']:>8.2%}")
        print(f"Avg Return:          {metrics['avg_return']:>8.2%}")
        print(f"Median Return:       {metrics['median_return']:>8.2%}")
        print(f"Avg Winner:          {metrics['avg_winner']:>8.2%}")
        print(f"Avg Loser:           {metrics['avg_loser']:>8.2%}")
        print(f"Total Return:        {metrics['total_return']:>8.2%}")
        print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:>8.2f}")
        print(f"Max Drawdown:        {metrics['max_drawdown']:>8.2%}")
        print(f"Profit Factor:       {metrics['profit_factor']:>8.2f}")
        print("=" * 60)
    
    def run_multiple_periods(self):
        """Run backtest for multiple holding periods"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE BACKTEST: Multiple Holding Periods")
        print("=" * 80)
        
        all_results = {}
        summary = []
        
        for holding_days in HOLDING_PERIODS:
            trades = self.run_backtest(
                lookback_days=LOOKBACK_DAYS, 
                holding_days=holding_days
            )
            
            if len(trades) > 0:
                metrics = self.calculate_metrics(trades)
                self.print_metrics(metrics, f"{holding_days}-Day Holding Period")
                
                # Save trades
                output_file = RESULTS_DIR / f'backtest_trades_{holding_days}d.csv'
                trades.to_csv(output_file, index=False)
                print(f"\nTrades saved to: {output_file}")
                
                all_results[holding_days] = {
                    'trades': trades,
                    'metrics': metrics
                }
                
                summary.append({
                    'holding_days': holding_days,
                    **metrics
                })
        
        # Create summary table
        if summary:
            summary_df = pd.DataFrame(summary)
            summary_file = RESULTS_DIR / 'backtest_summary.csv'
            summary_df.to_csv(summary_file, index=False)
            print(f"\n\nSummary saved to: {summary_file}")
            
            # Print comparison
            print("\n" + "=" * 80)
            print("SUMMARY: Holding Period Comparison")
            print("=" * 80)
            print(summary_df.to_string(index=False))
        
        return all_results, summary_df


def main():
    """Main execution"""
    print("=" * 80)
    print("BACKTESTING: Foreign Buy + Declining Stocks Strategy")
    print("=" * 80)
    print(f"\nStrategy Parameters:")
    print(f"  Foreign buy lookback: {LOOKBACK_DAYS} days")
    print(f"  Price decline range: {DECLINE_MIN:.1%} to {DECLINE_MAX:.1%}")
    print(f"  Minimum foreign buy: {FOREIGN_BUY_MIN:,} shares")
    print(f"  Holding periods: {HOLDING_PERIODS}")
    print(f"  Quality filters: {USE_QUALITY_FILTERS}")
    if USE_QUALITY_FILTERS:
        print(f"    - Max PER: {MAX_PER}")
        print(f"    - Min ROE: {MIN_ROE}%")
    
    # Initialize backtester
    backtester = ForeignBuyBacktester()
    
    # Run comprehensive backtest
    results, summary = backtester.run_multiple_periods()
    
    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {RESULTS_DIR}")


if __name__ == '__main__':
    main()
