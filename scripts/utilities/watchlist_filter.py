#!/usr/bin/env python3
"""
IDX Watchlist Board Filter
===========================
Filter and exclude stocks based on IDX Watchlist Board criteria.

Based on IDX Regulation I-X: Securities on Watchlist Board
Reference: Securities on Watchlist Board-20260102-20260119.xlsx

The 11 criteria identify problematic stocks that should be excluded from trading:
1. Low price (<Rp51) + low liquidity (avg daily value <Rp5M, volume <10K for 3 months)
2. Audited Financial Statements with disclaimer opinion
3. No revenue or no change in revenue in latest financial statements
4. Mining companies without core business revenue by 4th fiscal year
5. Negative equity in latest financial statement
6. Non-compliance with listing requirements (except free float)
7. Low liquidity only (avg daily value <Rp5M, volume <10K for 3 months)
8. PKPU, bankruptcy, or homologation cancellation proceedings
9. Material subsidiary facing PKPU/bankruptcy/homologation cancellation
10. Temporary suspension >1 exchange day due to trading activities
11. Other conditions determined by OJK

Author: Trading Analysis System
Date: January 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class SuspensionTracker:
    """Lightweight suspension tracker for integration."""
    
    # Fallback suspension data (updated based on IDX website)
    SUSPENDED_STOCKS = {
        'POLA': '15 Jan 2026',
        'SOTS': '14 Jan 2026',
        'IFSH': '13 Jan 2026',
        'SIPD': '13 Jan 2026',
    }
    
    # Recently reopened (cleared to trade)
    REOPENED_STOCKS = {
        'INDS': '15 Jan 2026',
        'KOCI': '13 Jan 2026',
        'PKPK': '14 Jan 2026',
        'SPRE': '13 Jan 2026',
    }


class WatchlistFilter:
    """
    Filter stocks based on IDX Watchlist Board criteria.
    
    Usage:
        # Initialize with stock data
        filter = WatchlistFilter()
        
        # Check single stock
        is_risky, reasons = filter.check_stock(stock_code, price, volume, value)
        
        # Filter DataFrame
        clean_df = filter.filter_dataframe(df)
        
        # Get detailed analysis
        analysis = filter.analyze_portfolio(['BUMI', 'RLCO', 'BBRI'])
    """
    
    # Thresholds from IDX regulations
    PRICE_THRESHOLD = 51  # Rupiah
    VOLUME_THRESHOLD = 10000  # shares
    VALUE_THRESHOLD = 5000000  # Rupiah (5 million)
    LIQUIDITY_PERIOD_DAYS = 90  # 3 months
    
    def __init__(self, historical_data_path=None):
        """
        Initialize watchlist filter.
        
        Args:
            historical_data_path: Path to historical trading data (CSV)
                                Expected columns: Kode Saham, Penutupan, Volume, Nilai
        """
        self.historical_data = None
        
        if historical_data_path:
            self.load_historical_data(historical_data_path)
    
    def load_historical_data(self, path):
        """Load historical trading data for liquidity analysis."""
        try:
            self.historical_data = pd.read_csv(path)
            if 'SourceDate' in self.historical_data.columns:
                self.historical_data['SourceDate'] = pd.to_datetime(
                    self.historical_data['SourceDate']
                )
            print(f"✓ Loaded {len(self.historical_data)} historical records")
        except Exception as e:
            print(f"✗ Error loading historical data: {e}")
            self.historical_data = None
    
    def check_criteria_1_low_price_liquidity(self, stock_code, price, avg_volume, avg_value):
        """
        Criteria 1: Price < Rp51 AND low liquidity
        
        Returns:
            (bool, str): (is_risky, reason)
        """
        if price < self.PRICE_THRESHOLD:
            if avg_volume < self.VOLUME_THRESHOLD and avg_value < self.VALUE_THRESHOLD:
                return True, f"Low price (Rp{price}) + low liquidity (vol={avg_volume:,.0f}, val=Rp{avg_value:,.0f})"
        
        return False, None
    
    def check_criteria_7_low_liquidity(self, avg_volume, avg_value):
        """
        Criteria 7: Low liquidity only (regardless of price)
        
        Returns:
            (bool, str): (is_risky, reason)
        """
        if avg_volume < self.VOLUME_THRESHOLD and avg_value < self.VALUE_THRESHOLD:
            return True, f"Low liquidity (avg vol={avg_volume:,.0f}, avg val=Rp{avg_value:,.0f})"
        
        return False, None
    
    def calculate_liquidity_metrics(self, stock_code, days=90, end_date=None):
        """
        Calculate average daily volume and value over specified period.
        
        Args:
            stock_code: Stock ticker
            days: Number of days to analyze (default 90 = 3 months)
            end_date: End date for analysis (default: most recent date)
        
        Returns:
            dict: {'avg_volume': float, 'avg_value': float, 'trading_days': int, 'avg_price': float}
        """
        if self.historical_data is None:
            return None
        
        # Filter for specific stock
        stock_data = self.historical_data[
            self.historical_data['Kode Saham'] == stock_code
        ].copy()
        
        if len(stock_data) == 0:
            return None
        
        # Filter by date range
        if end_date is None and 'SourceDate' in stock_data.columns:
            end_date = stock_data['SourceDate'].max()
        
        if 'SourceDate' in stock_data.columns:
            start_date = end_date - timedelta(days=days)
            stock_data = stock_data[
                (stock_data['SourceDate'] >= start_date) & 
                (stock_data['SourceDate'] <= end_date)
            ]
        else:
            # If no date column, use most recent N records
            stock_data = stock_data.tail(days)
        
        if len(stock_data) == 0:
            return None
        
        # Calculate metrics
        metrics = {
            'avg_volume': stock_data['Volume'].mean() if 'Volume' in stock_data.columns else 0,
            'avg_value': stock_data['Nilai'].mean() if 'Nilai' in stock_data.columns else 0,
            'trading_days': len(stock_data),
            'avg_price': stock_data['Penutupan'].mean() if 'Penutupan' in stock_data.columns else 0,
            'latest_price': stock_data['Penutupan'].iloc[-1] if 'Penutupan' in stock_data.columns else 0,
        }
        
        return metrics
    
    def check_stock(self, stock_code, price=None, volume=None, value=None):
        """
        Check if a stock meets watchlist criteria.
        
        Args:
            stock_code: Stock ticker symbol
            price: Current/latest price (optional if historical data loaded)
            volume: Average daily volume (optional if historical data loaded)
            value: Average daily value (optional if historical data loaded)
        
        Returns:
            (bool, list): (is_on_watchlist, [reasons])
        """
        reasons = []
        
        # Check suspension status first (highest priority)
        if stock_code in SuspensionTracker.SUSPENDED_STOCKS:
            susp_date = SuspensionTracker.SUSPENDED_STOCKS[stock_code]
            reasons.append(f"[Criteria 10] Trading suspended since {susp_date}")
            return True, reasons
        
        # If historical data available, calculate metrics
        if self.historical_data is not None:
            metrics = self.calculate_liquidity_metrics(stock_code)
            
            if metrics:
                price = price or metrics['latest_price']
                volume = volume or metrics['avg_volume']
                value = value or metrics['avg_value']
            else:
                # Stock not found in historical data
                reasons.append(f"No historical data found (possibly delisted/new)")
                return True, reasons
        
        # Validate inputs
        if price is None or volume is None or value is None:
            reasons.append("Insufficient data for analysis")
            return True, reasons  # Conservative: flag as risky if can't analyze
        
        # Check Criteria 1: Low price + low liquidity
        is_risky_1, reason_1 = self.check_criteria_1_low_price_liquidity(
            stock_code, price, volume, value
        )
        if is_risky_1:
            reasons.append(f"[Criteria 1] {reason_1}")
        
        # Check Criteria 7: Low liquidity only
        is_risky_7, reason_7 = self.check_criteria_7_low_liquidity(volume, value)
        if is_risky_7 and not is_risky_1:  # Don't double-count
            reasons.append(f"[Criteria 7] {reason_7}")
        
        # Note: Criteria 2-6, 8-11 require fundamental/regulatory data
        # These should be maintained in a separate watchlist CSV file
        
        is_on_watchlist = len(reasons) > 0
        
        return is_on_watchlist, reasons
    
    def filter_dataframe(self, df, stock_col='Kode Saham', price_col='Penutupan', 
                        volume_col='Volume', value_col='Nilai', inplace=False):
        """
        Filter a DataFrame to exclude watchlist stocks.
        
        Args:
            df: DataFrame with stock data
            stock_col: Column name for stock codes
            price_col: Column name for prices
            volume_col: Column name for volumes
            value_col: Column name for values
            inplace: Modify DataFrame in place (default False)
        
        Returns:
            DataFrame: Filtered DataFrame (or None if inplace=True)
            dict: Summary of removed stocks
        """
        if df is None or len(df) == 0:
            return df, {}
        
        original_count = len(df)
        removed_stocks = {}
        
        # Create mask for stocks to keep
        keep_mask = pd.Series([True] * len(df), index=df.index)
        
        for idx, row in df.iterrows():
            stock_code = row[stock_col]
            price = row.get(price_col, None)
            volume = row.get(volume_col, None)
            value = row.get(value_col, None)
            
            is_risky, reasons = self.check_stock(stock_code, price, volume, value)
            
            if is_risky:
                keep_mask[idx] = False
                removed_stocks[stock_code] = reasons
        
        # Filter DataFrame
        if inplace:
            df.drop(df[~keep_mask].index, inplace=True)
            filtered_df = None
        else:
            filtered_df = df[keep_mask].copy()
        
        # Summary
        removed_count = original_count - keep_mask.sum()
        summary = {
            'original_count': original_count,
            'removed_count': removed_count,
            'remaining_count': keep_mask.sum(),
            'removed_stocks': removed_stocks
        }
        
        return filtered_df, summary
    
    def analyze_portfolio(self, stock_list):
        """
        Analyze a list of stocks for watchlist criteria.
        
        Args:
            stock_list: List of stock codes
        
        Returns:
            dict: Analysis results with risks identified per stock
        """
        results = {
            'safe_stocks': [],
            'risky_stocks': {},
            'summary': {}
        }
        
        for stock_code in stock_list:
            is_risky, reasons = self.check_stock(stock_code)
            
            if is_risky:
                results['risky_stocks'][stock_code] = reasons
            else:
                results['safe_stocks'].append(stock_code)
        
        results['summary'] = {
            'total_stocks': len(stock_list),
            'safe_count': len(results['safe_stocks']),
            'risky_count': len(results['risky_stocks']),
            'safe_percentage': len(results['safe_stocks']) / len(stock_list) * 100 if stock_list else 0
        }
        
        return results
    
    def print_analysis(self, analysis_results):
        """Pretty print analysis results."""
        print("\n" + "="*70)
        print("IDX WATCHLIST ANALYSIS")
        print("="*70)
        
        summary = analysis_results['summary']
        print(f"\nTotal Stocks Analyzed: {summary['total_stocks']}")
        print(f"✓ Safe Stocks: {summary['safe_count']} ({summary['safe_percentage']:.1f}%)")
        print(f"⚠ Risky Stocks: {summary['risky_count']} ({100-summary['safe_percentage']:.1f}%)")
        
        if analysis_results['risky_stocks']:
            print("\n" + "-"*70)
            print("RISKY STOCKS (Watchlist Criteria Detected)")
            print("-"*70)
            
            for stock, reasons in analysis_results['risky_stocks'].items():
                print(f"\n{stock}:")
                for reason in reasons:
                    print(f"  ⚠ {reason}")
        
        if analysis_results['safe_stocks']:
            print("\n" + "-"*70)
            print(f"SAFE STOCKS ({len(analysis_results['safe_stocks'])} stocks)")
            print("-"*70)
            print(", ".join(analysis_results['safe_stocks']))
        
        print("\n" + "="*70)


def load_official_watchlist(watchlist_file):
    """
    Load official IDX watchlist from Excel/CSV file.
    
    This supplements the automated checks with regulatory data for
    criteria that can't be detected from price/volume alone.
    
    Args:
        watchlist_file: Path to Excel/CSV with official watchlist
    
    Returns:
        set: Set of stock codes on official watchlist
    """
    try:
        if watchlist_file.endswith('.xlsx'):
            df = pd.read_excel(watchlist_file)
        else:
            df = pd.read_csv(watchlist_file)
        
        # Assuming column with stock codes
        if 'Kode' in df.columns:
            stock_col = 'Kode'
        elif 'Code' in df.columns:
            stock_col = 'Code'
        elif 'Stock' in df.columns:
            stock_col = 'Stock'
        else:
            stock_col = df.columns[0]
        
        watchlist_set = set(df[stock_col].unique())
        print(f"✓ Loaded {len(watchlist_set)} stocks from official watchlist")
        
        return watchlist_set
    
    except Exception as e:
        print(f"✗ Error loading watchlist file: {e}")
        return set()


# Example usage
if __name__ == "__main__":
    # Initialize filter with historical data
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    HIST_FILE = BASE_DIR / "data" / "histories" / "ringkasan_histories_combined.csv"
    
    print("Initializing IDX Watchlist Filter...")
    filter = WatchlistFilter(historical_data_path=str(HIST_FILE))
    
    # Example 1: Check individual stocks
    print("\n" + "="*70)
    print("EXAMPLE 1: Individual Stock Check")
    print("="*70)
    
    test_stocks = ['BUMI', 'BBRI', 'BMRI', 'TLKM']
    
    for stock in test_stocks:
        is_risky, reasons = filter.check_stock(stock)
        status = "⚠ RISKY" if is_risky else "✓ SAFE"
        print(f"\n{stock}: {status}")
        if reasons:
            for reason in reasons:
                print(f"  - {reason}")
    
    # Example 2: Portfolio analysis
    print("\n" + "="*70)
    print("EXAMPLE 2: Portfolio Analysis")
    print("="*70)
    
    portfolio = ['BUMI', 'BBRI', 'BMRI', 'TLKM', 'ACES', 'ARTO']
    analysis = filter.analyze_portfolio(portfolio)
    filter.print_analysis(analysis)
    
    # Example 3: Filter DataFrame
    print("\n" + "="*70)
    print("EXAMPLE 3: DataFrame Filtering")
    print("="*70)
    
    sample_data = {
        'Kode Saham': ['BUMI', 'BBRI', 'ACES'],
        'Penutupan': [48, 5200, 1250],
        'Volume': [5000, 15000000, 850000],
        'Nilai': [240000, 78000000000, 1062500000]
    }
    df = pd.DataFrame(sample_data)
    
    print("\nOriginal DataFrame:")
    print(df)
    
    filtered_df, summary = filter.filter_dataframe(df)
    
    print(f"\nFiltering Results:")
    print(f"  Original: {summary['original_count']} stocks")
    print(f"  Removed: {summary['removed_count']} stocks")
    print(f"  Remaining: {summary['remaining_count']} stocks")
    
    if summary['removed_stocks']:
        print("\n  Removed stocks:")
        for stock, reasons in summary['removed_stocks'].items():
            print(f"    {stock}: {', '.join(reasons)}")
    
    print("\nFiltered DataFrame:")
    print(filtered_df)
