"""
Market Manipulation Detection Dashboard
Real-time monitoring and alerting for suspicious trading patterns
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import numpy as np
from glob import glob

DATA_DIR = os.path.join("data", "IHSGstockdata")
MINUTES_DIR = os.path.join(DATA_DIR, "minutes")
BROKER_DIR = os.path.join(DATA_DIR, "broker")
ALERTS_DIR = os.path.join(DATA_DIR, "alerts")


def analyze_broker_summary(date: str) -> Dict:
    """Load aggregated broker summary (no buy/sell split) and compute concentration."""
    summary_file = os.path.join(BROKER_DIR, f"broker_summary_{date}.csv")
    alt_file = os.path.join(BROKER_DIR, f"broker_summary_{date.replace('-', '')}.csv")

    if not os.path.exists(summary_file):
        if os.path.exists(alt_file):
            summary_file = alt_file
        else:
            return {"error": f"Broker summary not found for {date}", "file": summary_file}

    df = pd.read_csv(summary_file)
    if df.empty:
        return {"error": "Broker summary file is empty", "file": summary_file}

    df = df.sort_values("value", ascending=False)
    total_value = df["value"].sum()
    top3 = df.head(3)["value"].sum() / total_value * 100
    top5 = df.head(5)["value"].sum() / total_value * 100
    top10 = df.head(10)["value"].sum() / total_value * 100

    # Tighter thresholds for concentration risk
    risk = "LOW"
    if top3 > 50 or top5 > 70 or top10 > 85:
        risk = "HIGH"
    elif top3 > 40 or top5 > 60 or top10 > 80:
        risk = "MEDIUM"

    top_rows = []
    for row in df.head(10)[["broker_id", "broker_name", "value", "volume", "frequency"]].to_dict("records"):
        top_rows.append({
            "broker_id": row.get("broker_id"),
            "broker_name": row.get("broker_name"),
            "value": int(row.get("value", 0)),
            "volume": int(row.get("volume", 0)),
            "frequency": int(row.get("frequency", 0)),
        })

    return {
        "file": summary_file,
        "total_brokers": int(len(df)),
        "total_value": float(total_value),
        "top3_share": round(top3, 2),
        "top5_share": round(top5, 2),
        "top10_share": round(top10, 2),
        "top10": top_rows,
        "risk_level": risk,
    }


class ManipulationDetector:
    """Real-time manipulation pattern detector."""
    
    def __init__(self):
        self.alerts = []
        self.patterns = {
            'pump_dump': 0,
            'painting_tape': 0,
            'volume_anomaly': 0,
            'coordinated': 0,
            'spoofing': 0
        }
    
    def scan_all_stocks(self, date: str = None) -> Dict:
        """
        Scan all available stocks for manipulation patterns.
        
        Args:
            date: Date to analyze (default: today)
            
        Returns:
            Dict with scan results
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print("=" * 80)
        print(f"🔍 MARKET MANIPULATION SCAN")
        print(f"📅 Date: {date}")
        print("=" * 80)
        
        # Get all stock files
        stock_files = glob(os.path.join(MINUTES_DIR, "*.csv"))
        
        if not stock_files:
            print("\n❌ No stock data found!")
            return {"error": "No data"}
        
        print(f"\n📊 Scanning {len(stock_files)} stocks...\n")
        
        all_alerts = []
        
        for stock_file in stock_files:
            stock_code = os.path.basename(stock_file).replace('.csv', '')
            
            # Load data
            try:
                df = pd.read_csv(stock_file, parse_dates=['timestamp'])
                
                # Filter for date
                df_day = df[df['timestamp'].dt.date == pd.to_datetime(date).date()]
            except Exception as e:
                print(f"❌ Error loading {stock_code}: {e}")
                continue
            
            if df_day.empty:
                continue
            
            # Run detection
            stock_alerts = self._analyze_stock(stock_code, df_day)
            
            if stock_alerts:
                all_alerts.extend(stock_alerts)
                
                # Print summary
                risk_levels = [a['risk_level'] for a in stock_alerts]
                high_risk = risk_levels.count('HIGH')
                medium_risk = risk_levels.count('MEDIUM')
                
                status = "🚨" if high_risk > 0 else "⚠️" if medium_risk > 0 else "✅"
                print(f"{status} {stock_code:6s} | Alerts: {len(stock_alerts):2d} | HIGH: {high_risk} | MEDIUM: {medium_risk}")
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📋 SCAN SUMMARY")
        print("=" * 80)
        print(f"Total Alerts: {len(all_alerts)}")
        
        if all_alerts:
            by_type = {}
            by_risk = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            
            for alert in all_alerts:
                alert_type = alert['pattern']
                risk = alert['risk_level']
                
                by_type[alert_type] = by_type.get(alert_type, 0) + 1
                by_risk[risk] = by_risk.get(risk, 0) + 1
            
            print(f"\n📊 By Pattern Type:")
            for pattern, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
                print(f"  {pattern:25s}: {count}")
            
            print(f"\n⚠️  By Risk Level:")
            for risk, count in by_risk.items():
                emoji = "🚨" if risk == "HIGH" else "⚠️" if risk == "MEDIUM" else "ℹ️"
                print(f"  {emoji} {risk:10s}: {count}")
        else:
            print("✅ No manipulation patterns detected")

        # Broker concentration from daily summary (if available)
        broker_summary = analyze_broker_summary(date)
        if 'error' not in broker_summary:
            print(f"\n🏢 Broker Concentration ({date}):")
            print(f"  Top 3 share : {broker_summary['top3_share']:.2f}%")
            print(f"  Top 5 share : {broker_summary['top5_share']:.2f}%")
            print(f"  Top 10 share: {broker_summary['top10_share']:.2f}%")
            print(f"  Total brokers: {broker_summary['total_brokers']}")
            print(f"  Risk level   : {broker_summary['risk_level']}")
            print("  Top 10 brokers:")
            for row in broker_summary['top10']:
                print(f"    {row['broker_id']:>4s} | {row['broker_name'][:45]:45s} | value {row['value']:,}")
        else:
            print(f"\n🏢 Broker Concentration: {broker_summary['error']}")
            if 'file' in broker_summary:
                print(f"  Missing file: {broker_summary['file']}")
        
        print("=" * 80 + "\n")
        
        return {
            'date': date,
            'stocks_scanned': len(stock_files),
            'total_alerts': len(all_alerts),
            'alerts': all_alerts,
            'broker_concentration': broker_summary
        }
    
    def _analyze_stock(self, stock_code: str, df: pd.DataFrame) -> List[Dict]:
        """Analyze single stock for all manipulation patterns."""
        alerts = []
        
        # 1. Volume Anomaly
        df_vol = self._detect_volume_anomaly(df)
        vol_alerts = df_vol[df_vol['volume_anomaly'] == True]
        
        if len(vol_alerts) > 5:  # Only alert if multiple anomalies
            max_score = vol_alerts['anomaly_score'].max()
            alerts.append({
                'stock_code': stock_code,
                'pattern': 'VOLUME_ANOMALY',
                'count': int(len(vol_alerts)),
                'score': float(round(max_score, 2)),
                'risk_level': 'HIGH' if max_score > 70 else 'MEDIUM',
                'timestamps': vol_alerts['timestamp'].astype(str).tolist()[:3]
            })
        
        # 2. Pump and Dump
        pump_dump = self._detect_pump_dump(df)
        if pump_dump['detected']:
            alerts.append({
                'stock_code': stock_code,
                'pattern': 'PUMP_AND_DUMP',
                'risk_level': pump_dump['risk_level'],
                'confidence': int(pump_dump['confidence']),
                'price_change': float(pump_dump['price_change']),
                'volume_surge': float(pump_dump['volume_surge'])
            })
        
        # 3. Painting Tape
        painting = self._detect_painting(df)
        if painting['detected']:
            alerts.append({
                'stock_code': stock_code,
                'pattern': 'PAINTING_TAPE',
                'risk_level': painting['risk_level'],
                'confidence': int(painting['confidence']),
                'price': float(painting['price']),
                'frequency': float(painting['frequency'])
            })
        
        # 4. End-of-Day Manipulation
        eod_manip = self._detect_eod_manipulation(df)
        if eod_manip['detected']:
            alerts.append({
                'stock_code': stock_code,
                'pattern': 'END_OF_DAY_MANIPULATION',
                'risk_level': eod_manip['risk_level'],
                'price_jump': float(eod_manip['price_jump'])
            })
        
        return alerts
    
    def _detect_volume_anomaly(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect volume spikes."""
        df = df.copy()
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        df['volume_anomaly'] = df['volume_ratio'] > 3.0
        df['anomaly_score'] = np.clip((df['volume_ratio'] - 1) * 20, 0, 100)
        return df
    
    def _detect_pump_dump(self, df: pd.DataFrame, lookback: int = 60) -> Dict:
        """Detect pump and dump pattern."""
        if len(df) < lookback:
            return {"detected": False}
        
        recent = df.tail(lookback)
        price_change = (recent['close'].iloc[-1] / recent['close'].iloc[0] - 1) * 100
        volume_surge = recent['volume'].iloc[-lookback//2:].mean() / recent['volume'].iloc[:lookback//2].mean()
        
        pump_detected = price_change > 10 and volume_surge > 2
        
        if pump_detected:
            mid_point = len(recent) // 2
            dump_detected = recent['close'].iloc[-1] < recent['close'].iloc[mid_point] * 0.95
            
            if dump_detected:
                confidence = min(100, int(abs(price_change) * volume_surge))
                return {
                    "detected": True,
                    "confidence": confidence,
                    "price_change": round(price_change, 2),
                    "volume_surge": round(volume_surge, 2),
                    "risk_level": "HIGH" if confidence > 70 else "MEDIUM"
                }
        
        return {"detected": False}
    
    def _detect_painting(self, df: pd.DataFrame, window: int = 30) -> Dict:
        """Detect painting the tape."""
        if len(df) < window:
            return {"detected": False}
        
        recent = df.tail(window)
        price_counts = recent['close'].value_counts()
        
        if len(price_counts) == 0:
            return {"detected": False}
        
        most_common_price = price_counts.index[0]
        price_frequency = price_counts.iloc[0] / len(recent)
        
        avg_volume_at_price = recent[recent['close'] == most_common_price]['volume'].mean()
        overall_avg_volume = recent['volume'].mean()
        
        detected = (price_frequency > 0.3) and (avg_volume_at_price < overall_avg_volume * 0.5)
        
        if detected:
            return {
                "detected": True,
                "confidence": int(price_frequency * 100),
                "price": most_common_price,
                "frequency": round(price_frequency, 2),
                "risk_level": "MEDIUM"
            }
        
        return {"detected": False}
    
    def _detect_eod_manipulation(self, df: pd.DataFrame) -> Dict:
        """Detect end-of-day price manipulation."""
        if len(df) < 30:
            return {"detected": False}
        
        # Last 30 minutes
        last_30min = df.tail(30)
        
        # Check for sudden price jump in last 10 minutes
        last_10min = df.tail(10)
        earlier = df.tail(40).head(30)
        
        last_10_avg = last_10min['close'].mean()
        earlier_avg = earlier['close'].mean()
        
        price_jump = (last_10_avg / earlier_avg - 1) * 100
        
        # Manipulation if price jumps >2% in last 10 minutes
        if abs(price_jump) > 2:
            return {
                "detected": True,
                "price_jump": round(price_jump, 2),
                "risk_level": "HIGH" if abs(price_jump) > 5 else "MEDIUM"
            }
        
        return {"detected": False}


def analyze_broker_manipulation(stock_code: str, date: str = None) -> Dict:
    """
    Analyze broker-level manipulation for a stock.
    
    Args:
        stock_code: Stock ticker
        date: Date to analyze
        
    Returns:
        Dict with broker manipulation analysis
    """
    broker_file = os.path.join(BROKER_DIR, f"{stock_code}_broker.csv")
    
    if not os.path.exists(broker_file):
        return {"error": f"No broker data found for {stock_code}"}
    
    df = pd.read_csv(broker_file)
    
    if date:
        df = df[df['date'] == date]
    
    if df.empty:
        return {"error": "No data for specified date"}
    
    print(f"\n{'='*70}")
    print(f"🔍 Broker Manipulation Analysis: {stock_code}")
    print(f"{'='*70}\n")
    
    results = {
        'stock_code': stock_code,
        'date': date or 'all',
        'alerts': []
    }
    
    # 1. Concentration Analysis
    total_value = df['total_value'].sum()
    broker_totals = df.groupby('broker_id')['total_value'].sum().sort_values(ascending=False)
    
    top_3_concentration = broker_totals.head(3).sum() / total_value * 100
    top_5_concentration = broker_totals.head(5).sum() / total_value * 100
    
    print(f"📊 Market Concentration:")
    print(f"  Top 3 Brokers: {top_3_concentration:.2f}%")
    print(f"  Top 5 Brokers: {top_5_concentration:.2f}%")
    
    if top_3_concentration > 60:
        results['alerts'].append({
            'type': 'HIGH_CONCENTRATION',
            'risk_level': 'HIGH',
            'concentration': round(top_3_concentration, 2),
            'message': 'Market highly concentrated in few brokers'
        })
        print("  🚨 HIGH CONCENTRATION DETECTED!")
    
    # 2. Aggressive Accumulation
    broker_net = df.groupby('broker_id')['net_value'].sum().sort_values(ascending=False)
    
    for broker_id in broker_net.head(3).index:
        broker_data = df[df['broker_id'] == broker_id]
        net_value = broker_data['net_value'].sum()
        total_value = broker_data['total_value'].sum()
        
        if net_value > 0:
            accumulation_rate = net_value / total_value
            
            if accumulation_rate > 0.5:  # >50% net buying
                results['alerts'].append({
                    'type': 'AGGRESSIVE_ACCUMULATION',
                    'broker_id': broker_id,
                    'risk_level': 'MEDIUM',
                    'accumulation_rate': round(accumulation_rate, 2),
                    'net_value': net_value
                })
                print(f"  ⚠️  {broker_id}: Aggressive accumulation ({accumulation_rate*100:.1f}%)")
    
    # 3. Wash Trading Detection
    broker_balance = df.groupby('broker_id').agg({
        'buy_value': 'sum',
        'sell_value': 'sum'
    })
    
    broker_balance['balance_ratio'] = (
        broker_balance[['buy_value', 'sell_value']].min(axis=1) / 
        broker_balance[['buy_value', 'sell_value']].max(axis=1)
    )
    
    wash_suspects = broker_balance[broker_balance['balance_ratio'] > 0.9]
    
    if len(wash_suspects) > 0:
        print(f"\n⚠️  Possible Wash Trading (Buy=Sell):")
        for broker_id in wash_suspects.head(3).index:
            ratio = wash_suspects.loc[broker_id, 'balance_ratio']
            print(f"  {broker_id}: Balance ratio {ratio:.2%}")
            
            results['alerts'].append({
                'type': 'WASH_TRADING_SUSPECT',
                'broker_id': broker_id,
                'risk_level': 'HIGH',
                'balance_ratio': round(ratio, 2)
            })
    
    print(f"\n{'='*70}\n")
    
    return results


def main():
    """Run comprehensive manipulation scan."""
    detector = ManipulationDetector()
    
    # Scan all stocks
    results = detector.scan_all_stocks(date='2026-01-15')
    
    # Save results
    if results.get('alerts'):
        import json
        report_file = os.path.join(ALERTS_DIR, f"scan_{results['date']}.json")
        
        os.makedirs(ALERTS_DIR, exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Full report saved to: {report_file}\n")


if __name__ == "__main__":
    main()
