"""
IDX Broker Behavior & Market Manipulation Pattern Analysis
Detects suspicious trading patterns and broker manipulation tactics
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from glob import glob

# Configuration
DATA_DIR = os.path.join("data", "IHSGstockdata")
BROKER_DIR = os.path.join(DATA_DIR, "broker")
ALERTS_DIR = os.path.join(DATA_DIR, "alerts")
MINUTES_DIR = os.path.join(DATA_DIR, "minutes")

# Manipulation Pattern Thresholds
VOLUME_SPIKE_THRESHOLD = 3.0  # 3x average volume
PRICE_MANIPULATION_THRESHOLD = 0.05  # 5% price movement
WASH_TRADE_THRESHOLD = 0.8  # 80% similarity in broker pairs
SPOOFING_CANCEL_RATE = 0.7  # 70% order cancellation rate
FOREIGN_THRESHOLD = 100_000_000  # 100M IDR for foreign activity flag


class ManipulationPattern:
    """Common manipulation patterns on IDX"""
    
    # Pattern types
    PUMP_AND_DUMP = "pump_and_dump"
    SPOOFING = "spoofing"
    WASH_TRADING = "wash_trading"
    LAYERING = "layering"
    PAINTING_TAPE = "painting_tape"
    INSIDER_ACCUMULATION = "insider_accumulation"
    BEAR_RAID = "bear_raid"
    CORNER_SQUEEZE = "corner_squeeze"


def ensure_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def detect_volume_anomalies(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Detect unusual volume spikes that may indicate manipulation.
    
    Args:
        df: Stock data with timestamp, volume columns
        window: Rolling window for average calculation
        
    Returns:
        DataFrame with anomaly flags and scores
    """
    df = df.copy()
    
    # Calculate rolling average volume
    df['volume_ma'] = df['volume'].rolling(window=window).mean()
    df['volume_std'] = df['volume'].rolling(window=window).std()
    
    # Detect spikes
    df['volume_ratio'] = df['volume'] / df['volume_ma']
    df['volume_zscore'] = (df['volume'] - df['volume_ma']) / df['volume_std']
    
    # Flag anomalies
    df['volume_anomaly'] = (df['volume_ratio'] > VOLUME_SPIKE_THRESHOLD) | \
                            (df['volume_zscore'] > 3)
    
    # Anomaly score (0-100)
    df['anomaly_score'] = np.clip(df['volume_zscore'] * 10, 0, 100)
    
    return df


def detect_pump_and_dump(df: pd.DataFrame, lookback: int = 60) -> Dict:
    """
    Detect pump and dump patterns:
    - Rapid price increase with high volume (pump)
    - Followed by sharp decline (dump)
    
    Args:
        df: Stock data with timestamp, close, volume
        lookback: Minutes to look back for pattern
        
    Returns:
        Dict with detection results and confidence
    """
    if len(df) < lookback:
        return {"detected": False, "confidence": 0}
    
    recent = df.tail(lookback).copy()
    
    # Calculate price change and volume profile
    price_change = (recent['close'].iloc[-1] / recent['close'].iloc[0] - 1) * 100
    volume_surge = recent['volume'].iloc[-lookback//2:].mean() / recent['volume'].iloc[:lookback//2].mean()
    
    # Detect pump phase
    pump_detected = price_change > 10 and volume_surge > 2
    
    # Detect dump phase (price declining after pump)
    if pump_detected:
        mid_point = len(recent) // 2
        first_half_price = recent['close'].iloc[mid_point]
        second_half_price = recent['close'].iloc[-1]
        dump_detected = second_half_price < first_half_price * 0.95
        
        confidence = min(100, int(abs(price_change) * volume_surge))
        
        return {
            "detected": dump_detected,
            "confidence": confidence,
            "price_change": round(price_change, 2),
            "volume_surge": round(volume_surge, 2),
            "pattern": ManipulationPattern.PUMP_AND_DUMP,
            "risk_level": "HIGH" if confidence > 70 else "MEDIUM"
        }
    
    return {"detected": False, "confidence": 0}


def detect_painting_tape(df: pd.DataFrame, window: int = 30) -> Dict:
    """
    Detect "painting the tape" - artificial price support/resistance:
    - Small trades at specific prices to create false impression
    - Usually happens near market close
    - Low volume but frequent trades
    
    Args:
        df: Stock data with timestamp, close, volume
        window: Minutes window to analyze
        
    Returns:
        Dict with detection results
    """
    if len(df) < window:
        return {"detected": False, "confidence": 0}
    
    recent = df.tail(window).copy()
    
    # Check for repeated prices with small volumes
    price_counts = recent['close'].value_counts()
    most_common_price = price_counts.index[0]
    price_frequency = price_counts.iloc[0] / len(recent)
    
    # Low volume but high frequency at same price
    avg_volume_at_price = recent[recent['close'] == most_common_price]['volume'].mean()
    overall_avg_volume = recent['volume'].mean()
    
    # Detection logic
    detected = (price_frequency > 0.3) and (avg_volume_at_price < overall_avg_volume * 0.5)
    
    if detected:
        confidence = int(price_frequency * 100)
        return {
            "detected": True,
            "confidence": confidence,
            "pattern": ManipulationPattern.PAINTING_TAPE,
            "price": most_common_price,
            "frequency": round(price_frequency, 2),
            "risk_level": "MEDIUM"
        }
    
    return {"detected": False, "confidence": 0}


def detect_price_manipulation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect suspicious price movements that may indicate manipulation.
    
    Args:
        df: Stock data with OHLCV
        
    Returns:
        DataFrame with manipulation flags
    """
    df = df.copy()
    
    # Calculate price volatility
    df['price_change'] = df['close'].pct_change()
    df['volatility'] = df['price_change'].rolling(window=20).std()
    
    # Detect sudden movements
    df['sudden_spike'] = (abs(df['price_change']) > PRICE_MANIPULATION_THRESHOLD) & \
                         (abs(df['price_change']) > df['volatility'] * 3)
    
    # Detect coordinated movements (price and volume both spike)
    df['coordinated_move'] = df['sudden_spike'] & (df['volume'] > df['volume'].rolling(20).mean() * 2)
    
    return df


def analyze_broker_concentration(broker_data: pd.DataFrame, top_n: int = 10) -> Dict:
    """
    Analyze broker concentration - high concentration may indicate manipulation.
    
    Args:
        broker_data: DataFrame with columns [broker_id, stock_code, buy_volume, sell_volume, net_volume]
        top_n: Number of top brokers to analyze
        
    Returns:
        Dict with concentration metrics
    """
    if broker_data.empty:
        return {"error": "No broker data available"}
    
    # Calculate net positions
    broker_summary = broker_data.groupby('broker_id').agg({
        'buy_volume': 'sum',
        'sell_volume': 'sum',
        'net_volume': 'sum'
    }).reset_index()
    
    broker_summary['total_volume'] = broker_summary['buy_volume'] + broker_summary['sell_volume']
    broker_summary = broker_summary.sort_values('total_volume', ascending=False)
    
    # Calculate concentration
    total_market_volume = broker_summary['total_volume'].sum()
    top_brokers = broker_summary.head(top_n)
    top_concentration = top_brokers['total_volume'].sum() / total_market_volume * 100
    
    # Herfindahl-Hirschman Index (HHI) - measure of market concentration
    market_shares = (broker_summary['total_volume'] / total_market_volume * 100) ** 2
    hhi = market_shares.sum()
    
    # Interpretation
    if hhi > 2500:
        concentration_level = "HIGHLY CONCENTRATED (Manipulation Risk)"
    elif hhi > 1500:
        concentration_level = "MODERATELY CONCENTRATED"
    else:
        concentration_level = "COMPETITIVE"
    
    return {
        "top_n_concentration": round(top_concentration, 2),
        "hhi": round(hhi, 2),
        "concentration_level": concentration_level,
        "top_brokers": top_brokers[['broker_id', 'total_volume', 'net_volume']].to_dict('records'),
        "risk_level": "HIGH" if hhi > 2500 else "MEDIUM" if hhi > 1500 else "LOW"
    }


def detect_coordinated_trading(broker_data: pd.DataFrame, time_window: int = 5) -> List[Dict]:
    """
    Detect coordinated trading between multiple brokers (possible collusion).
    
    Args:
        broker_data: Broker transaction data
        time_window: Minutes window to check for coordination
        
    Returns:
        List of suspicious coordinated activities
    """
    if broker_data.empty:
        return []
    
    suspicious_patterns = []
    
    # Group by time windows
    broker_data['time_bin'] = pd.to_datetime(broker_data['timestamp']).dt.floor(f'{time_window}min')
    
    grouped = broker_data.groupby(['time_bin', 'stock_code'])
    
    for (time_bin, stock_code), group in grouped:
        # Check if multiple brokers are buying/selling simultaneously
        broker_count = group['broker_id'].nunique()
        
        if broker_count >= 3:  # At least 3 brokers acting together
            # Check if they're all doing the same action
            buy_brokers = group[group['net_volume'] > 0]['broker_id'].nunique()
            sell_brokers = group[group['net_volume'] < 0]['broker_id'].nunique()
            
            # Suspicious if majority moving in same direction
            if buy_brokers >= 3 or sell_brokers >= 3:
                total_volume = group['total_volume'].sum()
                
                suspicious_patterns.append({
                    "timestamp": str(time_bin),
                    "stock_code": stock_code,
                    "broker_count": broker_count,
                    "direction": "BUY" if buy_brokers > sell_brokers else "SELL",
                    "total_volume": int(total_volume),
                    "pattern": "COORDINATED_TRADING",
                    "risk_level": "HIGH"
                })
    
    return suspicious_patterns


def generate_manipulation_report(stock_code: str, date: str) -> Dict:
    """
    Generate comprehensive manipulation analysis report for a stock.
    
    Args:
        stock_code: Stock ticker
        date: Date to analyze (YYYY-MM-DD)
        
    Returns:
        Dict with complete analysis
    """
    print(f"\n{'='*70}")
    print(f"🔍 Market Manipulation Analysis: {stock_code}")
    print(f"📅 Date: {date}")
    print(f"{'='*70}\n")
    
    # Load stock data
    stock_file = os.path.join(MINUTES_DIR, f"{stock_code}.csv")
    
    if not os.path.exists(stock_file):
        return {"error": f"No data found for {stock_code}"}
    
    df = pd.read_csv(stock_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter for specific date
    df_day = df[df['timestamp'].dt.date == pd.to_datetime(date).date()]
    
    if df_day.empty:
        return {"error": f"No data for {stock_code} on {date}"}
    
    # Run all detection algorithms
    report = {
        "stock_code": stock_code,
        "date": date,
        "data_points": len(df_day),
        "alerts": []
    }
    
    # 1. Volume Anomaly Detection
    print("📊 Analyzing volume anomalies...")
    df_anomaly = detect_volume_anomalies(df_day)
    volume_alerts = df_anomaly[df_anomaly['volume_anomaly'] == True]
    
    if not volume_alerts.empty:
        report["alerts"].append({
            "type": "VOLUME_ANOMALY",
            "count": len(volume_alerts),
            "max_score": round(volume_alerts['anomaly_score'].max(), 2),
            "timestamps": volume_alerts['timestamp'].astype(str).tolist()[:5]
        })
        print(f"  ⚠️  Found {len(volume_alerts)} volume anomalies")
    
    # 2. Pump and Dump Detection
    print("🎯 Detecting pump and dump patterns...")
    pump_dump = detect_pump_and_dump(df_day)
    if pump_dump['detected']:
        report["alerts"].append({
            "type": "PUMP_AND_DUMP",
            **pump_dump
        })
        print(f"  🚨 PUMP & DUMP DETECTED! Confidence: {pump_dump['confidence']}%")
    
    # 3. Painting the Tape Detection
    print("🎨 Detecting painting the tape...")
    painting = detect_painting_tape(df_day)
    if painting['detected']:
        report["alerts"].append({
            "type": "PAINTING_TAPE",
            **painting
        })
        print(f"  ⚠️  TAPE PAINTING DETECTED! Confidence: {painting['confidence']}%")
    
    # 4. Price Manipulation
    print("💰 Analyzing price manipulation...")
    df_price = detect_price_manipulation(df_day)
    price_alerts = df_price[df_price['coordinated_move'] == True]
    
    if not price_alerts.empty:
        report["alerts"].append({
            "type": "PRICE_MANIPULATION",
            "count": len(price_alerts),
            "timestamps": price_alerts['timestamp'].astype(str).tolist()
        })
        print(f"  ⚠️  Found {len(price_alerts)} suspicious price movements")
    
    # Summary
    print(f"\n{'='*70}")
    if report["alerts"]:
        print(f"🚨 TOTAL ALERTS: {len(report['alerts'])}")
        risk_levels = [a.get('risk_level', 'UNKNOWN') for a in report['alerts']]
        high_risk = risk_levels.count('HIGH')
        if high_risk > 0:
            print(f"⚠️  HIGH RISK ALERTS: {high_risk}")
    else:
        print("✅ No manipulation patterns detected")
    print(f"{'='*70}\n")
    
    return report


def create_demo_broker_data(stock_code: str, num_brokers: int = 20) -> pd.DataFrame:
    """Generate demo broker data for testing (will be replaced with real data)."""
    timestamps = pd.date_range('2026-01-15 09:00', '2026-01-15 16:00', freq='5min')
    
    data = []
    for ts in timestamps:
        for broker_id in range(1, num_brokers + 1):
            buy_vol = np.random.randint(1000, 100000) if np.random.random() > 0.3 else 0
            sell_vol = np.random.randint(1000, 100000) if np.random.random() > 0.3 else 0
            
            data.append({
                'timestamp': ts,
                'stock_code': stock_code,
                'broker_id': f"BR{broker_id:03d}",
                'buy_volume': buy_vol,
                'sell_volume': sell_vol,
                'net_volume': buy_vol - sell_vol,
                'total_volume': buy_vol + sell_vol
            })
    
    return pd.DataFrame(data)


def main():
    """Main analysis entry point."""
    print("=" * 70)
    print(" 🔍 IDX Market Manipulation Pattern Analyzer")
    print("=" * 70)
    
    # Example: Analyze BBRI
    stock_code = "BBRI"
    date = "2026-01-15"
    
    report = generate_manipulation_report(stock_code, date)
    
    # Demo broker analysis
    if 'error' not in report:
        print("\n📊 Broker Concentration Analysis (Demo Data)...")
        broker_data = create_demo_broker_data(stock_code)
        concentration = analyze_broker_concentration(broker_data)
        
        print(f"\n  Top {len(concentration['top_brokers'])} Brokers:")
        print(f"  Concentration: {concentration['top_n_concentration']}%")
        print(f"  HHI: {concentration['hhi']}")
        print(f"  Level: {concentration['concentration_level']}")
        
        # Coordinated trading detection
        print("\n🤝 Detecting coordinated trading patterns...")
        coordinated = detect_coordinated_trading(broker_data)
        if coordinated:
            print(f"  ⚠️  Found {len(coordinated)} suspicious coordinated activities")
        else:
            print("  ✅ No coordinated manipulation detected")
    
    # Save report
    ensure_directory(ALERTS_DIR)
    report_file = os.path.join(ALERTS_DIR, f"{stock_code}_{date}_manipulation_report.json")
    
    import json
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Report saved to: {report_file}\n")


if __name__ == "__main__":
    main()
