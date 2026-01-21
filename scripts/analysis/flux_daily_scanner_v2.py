#!/usr/bin/env python3
"""
FLUX IMPROVED DAILY SCANNER v2.0
Enhanced trading signal generator with technical + fundamental filters
Designed for 5-day swing trading on Indonesian equities
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json

class FluxDailyScanner:
    def __init__(self):
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.stocks_data = {}
        self.signals = []
        
    def fetch_live_prices(self, tickers):
        """Fetch real-time prices from Yahoo Finance"""
        print("📊 Fetching live prices...")
        for ticker in tickers:
            try:
                stock = yf.Ticker(f"{ticker}.JK")
                hist = stock.history(period='10d')
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else latest['Close']
                    
                    # 5-day metrics
                    five_days_ago = hist.iloc[0]['Close'] if len(hist) >= 5 else hist.iloc[0]['Close']
                    five_day_change = ((latest['Close'] - five_days_ago) / five_days_ago * 100)
                    day_change = ((latest['Close'] - prev_close) / prev_close * 100)
                    
                    # Intraday metrics
                    intraday_change = ((latest['Close'] - latest['Open']) / latest['Open'] * 100)
                    high_low_range = ((latest['High'] - latest['Low']) / latest['Low'] * 100)
                    
                    self.stocks_data[ticker] = {
                        'close': latest['Close'],
                        'high': latest['High'],
                        'low': latest['Low'],
                        'open': latest['Open'],
                        'volume': int(latest['Volume']),
                        'day_change_pct': day_change,
                        '5d_change_pct': five_day_change,
                        'intraday_change_pct': intraday_change,
                        'high_low_range_pct': high_low_range,
                        'date': hist.index[-1].date()
                    }
            except Exception as e:
                print(f"  ⚠️  {ticker}: {str(e)}")
    
    def load_broker_data(self, filepath):
        """Load foreign buy data from CSV"""
        print("📋 Loading broker concentration data...")
        try:
            df = pd.read_csv(filepath)
            return df
        except Exception as e:
            print(f"  ⚠️  Could not load {filepath}: {e}")
            return None
    
    def calculate_scores(self, stock, broker_data, fundamentals):
        """
        Calculate comprehensive trading score based on improved checklist
        Returns: score (0-100), passes boolean, detailed breakdown
        """
        
        checks = {
            'broker_concentration': False,
            'fundamentals': False,
            'technical_reversal': False,
            'volume_confirmation': False,
            'sector_momentum': False,
            'vwap_entry': False,
        }
        
        details = {}
        
        # 1. BROKER CONCENTRATION CHECK
        if stock in broker_data:
            dbr = broker_data[stock].get('DBR', 0)
            bci = broker_data[stock].get('BCI', 0)
            
            if dbr > 0.40 or bci > 2.0:
                checks['broker_concentration'] = True
                details['dbr'] = dbr
                details['bci'] = bci
                # Higher weight for institutional cornering
                if dbr > 0.50:
                    details['signal_type'] = 'Institutional Cornering'
                    details['conviction_level'] = 'HIGH'
                elif bci > 2.5:
                    details['signal_type'] = 'Broker Alliance'
                    details['conviction_level'] = 'MEDIUM'
                else:
                    details['signal_type'] = 'Moderate Institutional'
                    details['conviction_level'] = 'LOW-MEDIUM'
        
        # 2. FUNDAMENTALS CHECK
        if stock in fundamentals:
            fund = fundamentals[stock]
            per = fund.get('PER', 0)
            roe = fund.get('ROE', 0)
            pbv = fund.get('PBV', 0)
            
            if per > 0 and per < 15 and roe > 5 and pbv < 2.0:
                checks['fundamentals'] = True
                details['per'] = per
                details['roe'] = roe
                details['pbv'] = pbv
        
        # 3. TECHNICAL REVERSAL CHECK (CRITICAL)
        price_data = self.stocks_data.get(stock, {})
        
        # Intraday bounce detection
        intraday_change = price_data.get('intraday_change_pct', 0)
        five_day_change = price_data.get('5d_change_pct', 0)
        
        # Must have declined 5 days AND bounced intraday
        if -5.0 <= five_day_change <= -0.5:  # Proper decline range
            if intraday_change > 1.0:  # Bounced +1% minimum
                checks['technical_reversal'] = True
                details['intraday_bounce'] = intraday_change
                details['5d_decline'] = five_day_change
        
        # 4. VOLUME CONFIRMATION CHECK
        if 'volume' in price_data and 'avg_volume_5d' in broker_data.get(stock, {}):
            volume = price_data['volume']
            avg_vol = broker_data[stock]['avg_volume_5d']
            volume_ratio = (volume / avg_vol * 100) if avg_vol > 0 else 0
            
            if volume_ratio > 120:  # >120% of average
                checks['volume_confirmation'] = True
                details['volume_ratio'] = volume_ratio
        
        # 5. SECTOR MOMENTUM CHECK
        if stock in broker_data:
            sector_mtd = broker_data[stock].get('sector_mtd_change', 0)
            if sector_mtd > 0:  # Positive sector momentum
                checks['sector_momentum'] = True
                details['sector_mtd'] = sector_mtd
        
        # 6. VWAP ENTRY TIMING CHECK
        if stock in broker_data:
            buy_vwap = broker_data[stock].get('buy_vwap', 0)
            current_price = price_data.get('close', 0)
            
            if buy_vwap > 0 and current_price > 0:
                vwap_diff = ((current_price - buy_vwap) / buy_vwap * 100)
                
                # Within ±1% of institutional VWAP = good entry
                if -1.0 <= vwap_diff <= 1.0:
                    checks['vwap_entry'] = True
                    details['vwap_diff'] = vwap_diff
        
        # SCORING SYSTEM (v2.0)
        score = 0
        max_score = 100
        
        weights = {
            'broker_concentration': 20,
            'fundamentals': 15,
            'technical_reversal': 25,  # MOST CRITICAL
            'volume_confirmation': 15,
            'sector_momentum': 10,
            'vwap_entry': 15,
        }
        
        for check, passed in checks.items():
            if passed:
                score += weights[check]
        
        # MINIMUM REQUIREMENTS (Any fail = SKIP)
        must_pass = ['technical_reversal', 'fundamentals']
        can_skip = score < 60  # Low score even if passes
        
        passed = all(checks[c] for c in must_pass) and score >= 60
        
        return {
            'score': score,
            'passed': passed,
            'checks': checks,
            'details': details,
            'recommendation': self.get_recommendation(score, checks)
        }
    
    def get_recommendation(self, score, checks):
        """Generate trading recommendation based on score and checks"""
        if not checks['technical_reversal']:
            return "⚠️ SKIP - No technical reversal"
        
        if not checks['fundamentals']:
            return "⚠️ SKIP - Weak fundamentals"
        
        if score >= 80:
            return "🟢 STRONG BUY - All signals aligned"
        elif score >= 65:
            return "🟢 BUY - Good signal, proceed carefully"
        elif score >= 50:
            return "🟡 HOLD - Marginal, wait for confirmation"
        else:
            return "🔴 SKIP - Too many red flags"
    
    def scan_stocks(self, stock_list, broker_data, fundamentals):
        """Scan all stocks against improved criteria"""
        print("\n" + "="*80)
        print("FLUX DAILY SCANNER - IMPROVED v2.0")
        print(f"Date: {self.date}")
        print("="*80 + "\n")
        
        results = []
        
        for stock in stock_list:
            result = self.calculate_scores(stock, broker_data, fundamentals)
            result['stock'] = stock
            results.append(result)
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
    
    def print_detailed_report(self, results):
        """Print comprehensive daily trading report"""
        print("📋 DETAILED ANALYSIS\n")
        
        # Filter for actionable signals
        strong_buy = [r for r in results if r['score'] >= 80]
        buy = [r for r in results if 65 <= r['score'] < 80]
        hold = [r for r in results if 50 <= r['score'] < 65]
        skip = [r for r in results if r['score'] < 50]
        
        # STRONG BUY SECTION
        if strong_buy:
            print("🟢 STRONG BUY (Entry Recommended)")
            print("-" * 80)
            for r in strong_buy:
                self.print_stock_detail(r)
            print()
        
        # BUY SECTION
        if buy:
            print("🟢 BUY (Proceed Cautiously)")
            print("-" * 80)
            for r in buy:
                self.print_stock_detail(r)
            print()
        
        # HOLD SECTION
        if hold:
            print("🟡 HOLD (Wait for Confirmation)")
            print("-" * 80)
            for r in hold:
                self.print_stock_detail(r)
            print()
        
        # SKIP SECTION (brief)
        if skip:
            print(f"🔴 SKIP ({len(skip)} stocks) - See detailed results\n")
    
    def print_stock_detail(self, result):
        """Print detailed analysis for single stock"""
        stock = result['stock']
        price_data = self.stocks_data.get(stock, {})
        
        print(f"\n{stock} - Score: {result['score']}/100")
        print(f"  Current Price: Rp {price_data.get('close', 'N/A'):,.0f}")
        print(f"  Recommendation: {result['recommendation']}")
        
        # Show checks
        checks = result['checks']
        details = result['details']
        
        print(f"\n  Checklist:")
        print(f"    ✅ Broker Concentration: {'PASS' if checks['broker_concentration'] else '❌ FAIL'}", end="")
        if checks['broker_concentration']:
            dbr = details.get('dbr', 0)
            print(f" (DBR: {dbr:.1%})" if dbr else "")
        else:
            print()
        
        print(f"    ✅ Fundamentals: {'PASS' if checks['fundamentals'] else '❌ FAIL'}", end="")
        if checks['fundamentals']:
            print(f" (PER: {details.get('per', 'N/A')}, ROE: {details.get('roe', 'N/A')}%)")
        else:
            print()
        
        print(f"    ✅ Technical Reversal: {'PASS' if checks['technical_reversal'] else '❌ FAIL'}", end="")
        if checks['technical_reversal']:
            bounce = details.get('intraday_bounce', 0)
            decline = details.get('5d_decline', 0)
            print(f" (Bounce: +{bounce:.2f}%, Decline: {decline:.2f}%)")
        else:
            print()
        
        print(f"    ✅ Volume Confirmation: {'PASS' if checks['volume_confirmation'] else '❌ FAIL'}", end="")
        if checks['volume_confirmation']:
            vol_ratio = details.get('volume_ratio', 0)
            print(f" (Vol Ratio: {vol_ratio:.0f}%)")
        else:
            print()
        
        print(f"    ✅ Sector Momentum: {'PASS' if checks['sector_momentum'] else '❌ FAIL'}")
        print(f"    ✅ VWAP Entry Timing: {'PASS' if checks['vwap_entry'] else '❌ FAIL'}")
        
        # Trading parameters if passing
        if result['passed']:
            print(f"\n  Trading Parameters:")
            current = price_data.get('close', 0)
            if current > 0:
                stop_loss = current * 0.93  # 7% stop
                target_1 = current * 1.03  # 3% target
                target_2 = current * 1.05  # 5% target
                target_3 = current * 1.08  # 8% target
                
                print(f"    Entry: Rp {current:,.0f}")
                print(f"    Stop Loss: Rp {stop_loss:,.0f} (-7%)")
                print(f"    Target 1: Rp {target_1:,.0f} (+3%)")
                print(f"    Target 2: Rp {target_2:,.0f} (+5%)")
                print(f"    Target 3: Rp {target_3:,.0f} (+8%)")
                print(f"    Exit: 5 trading days (24 Jan 2026)")
    
    def export_results(self, results, filename=None):
        """Export results to JSON for tracking"""
        if not filename:
            filename = f"REPORTS/daily-reports/{datetime.now().strftime('%Y%m%d')}_FLUX_SCAN_RESULTS.json"
        
        export_data = {
            'scan_date': self.date,
            'total_stocks_scanned': len(results),
            'strong_buy_count': len([r for r in results if r['score'] >= 80]),
            'buy_count': len([r for r in results if 65 <= r['score'] < 80]),
            'results': [
                {
                    'stock': r['stock'],
                    'score': r['score'],
                    'passed': r['passed'],
                    'recommendation': r['recommendation'],
                    'checks': r['checks'],
                }
                for r in results
            ]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\n✅ Results exported to {filename}")
        except Exception as e:
            print(f"\n⚠️  Could not export: {e}")


def main():
    """Main execution"""
    
    # Initialize scanner
    scanner = FluxDailyScanner()
    
    # List of Indonesian stocks to scan (5-day traders' favorites)
    stocks_to_scan = ['ADRO', 'ASII', 'BMTR', 'BSIM', 'BNBR', 'AALI', 'BOAT', 'BCIP']
    
    # Fetch live prices
    scanner.fetch_live_prices(stocks_to_scan)
    
    # For now, use sample broker data
    # In production, this would load from daily broker summary CSV
    sample_broker_data = {
        'ADRO': {
            'DBR': 0.507,
            'BCI': 1.89,
            'signal_type': 'Institutional Cornering',
            'buy_vwap': 2258,
            'avg_volume_5d': 100000000,
            'sector_mtd_change': 19.2
        },
        'ASII': {
            'DBR': 0.427,
            'BCI': 2.74,
            'signal_type': 'Broker Alliance',
            'buy_vwap': 7233,
            'avg_volume_5d': 120000000,
            'sector_mtd_change': 8.8
        },
    }
    
    # Sample fundamental data
    fundamentals = {
        'ADRO': {'PER': 5.65, 'ROE': 10.95, 'PBV': 0.62},
        'ASII': {'PER': 8.30, 'ROE': 11.28, 'PBV': 0.94},
        'BMTR': {'PER': 4.39, 'ROE': 1.77, 'PBV': 0.08},
        'BSIM': {'PER': 54.24, 'ROE': 3.36, 'PBV': 1.80},
        'BNBR': {'PER': -74.15, 'ROE': -7.15, 'PBV': 5.35},
    }
    
    # Run scan
    results = scanner.scan_stocks(stocks_to_scan, sample_broker_data, fundamentals)
    
    # Print detailed report
    scanner.print_detailed_report(results)
    
    # Export results
    scanner.export_results(results)
    
    print("\n" + "="*80)
    print("✅ Daily scan complete. Ready for trading decisions.")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
