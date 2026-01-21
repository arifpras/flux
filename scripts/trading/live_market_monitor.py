#!/usr/bin/env python3
"""
Live Market Monitor for IDX Stocks
Real-time price tracking with entry/stop alerts for trading picks.
Polls yfinance every 10 seconds during market hours.
"""
import os
import time
import json
from datetime import datetime, time as dt_time
from typing import Dict, List
import pandas as pd
import yfinance as yf
from collections import defaultdict

# Configuration
WATCHLIST = {
    'INCO': {'entry': 5000, 'stop': 4900, 'target': 5250, 'tier': 1},
    'MDKA': {'entry': 7500, 'stop': 7350, 'target': 7875, 'tier': 1},
    'ADRO': {'entry': 4800, 'stop': 4704, 'target': 5040, 'tier': 1},
    'ANTM': {'entry': 2500, 'stop': 2450, 'target': 2625, 'tier': 1},
    'ASII':  {'entry': 6500, 'stop': 6370, 'target': 6825, 'tier': 2},
    'UNTR':  {'entry': 8200, 'stop': 8036, 'target': 8610, 'tier': 2},
    'ISAT':  {'entry': 3800, 'stop': 3724, 'target': 3990, 'tier': 2},
    'BBNI':  {'entry': 3900, 'stop': 3822, 'target': 4095, 'tier': 2},
}

POLL_INTERVAL = 10  # seconds
OUTPUT_DIR = 'data/live_tracking'
DATA_DIR = os.path.join(OUTPUT_DIR, datetime.now().strftime('%Y%m%d_%H%M%S'))

# Market hours (IDX: 09:00-16:00 WIB)
MARKET_OPEN = dt_time(9, 0)
MARKET_CLOSE = dt_time(16, 0)


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def is_market_open() -> bool:
    """Check if IDX market is currently open (09:00-16:00 WIB)."""
    now = datetime.now().time()
    return MARKET_OPEN <= now <= MARKET_CLOSE


def fetch_prices(symbols: List[str]) -> Dict[str, dict]:
    """Fetch current prices from yfinance."""
    prices = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(f'{symbol}.JK')
            # Get current price and info
            hist = ticker.history(period='1d', interval='1m')
            if not hist.empty:
                latest = hist.iloc[-1]
                prices[symbol] = {
                    'price': float(latest['Close']),
                    'volume': int(latest['Volume']) if 'Volume' in latest else 0,
                    'timestamp': hist.index[-1],
                }
            else:
                prices[symbol] = {'price': None, 'volume': 0, 'timestamp': None}
        except Exception as e:
            print(f"  ⚠️  Error fetching {symbol}: {e}")
            prices[symbol] = {'price': None, 'volume': 0, 'timestamp': None}
    return prices


def format_price(price: float) -> str:
    """Format price with proper IDR notation."""
    if price is None:
        return "N/A"
    if price >= 1000:
        return f"Rp {price:,.0f}"
    return f"Rp {price:.2f}"


def calculate_pnl(entry: float, current: float) -> str:
    """Calculate P&L % and format."""
    if entry is None or current is None:
        return "N/A"
    pnl_pct = ((current - entry) / entry) * 100
    color = "🟢" if pnl_pct >= 0 else "🔴"
    return f"{color} {pnl_pct:+.2f}%"


def check_alerts(symbol: str, price: float, prior_state: Dict) -> List[str]:
    """Check for entry, stop, and target alerts."""
    alerts = []
    config = WATCHLIST[symbol]
    
    if price is None:
        return alerts
    
    curr_state = {
        'above_entry': price >= config['entry'],
        'below_stop': price <= config['stop'],
        'above_target': price >= config['target'],
    }
    
    # Entry alert (breakout above entry level)
    if curr_state['above_entry'] and not prior_state.get('above_entry', False):
        alerts.append(f"🚀 {symbol} BREAKOUT! Price {format_price(price)} > Entry {format_price(config['entry'])}")
    
    # Stop loss hit
    if curr_state['below_stop'] and not prior_state.get('below_stop', False):
        alerts.append(f"🛑 {symbol} STOP HIT! Price {format_price(price)} < Stop {format_price(config['stop'])}")
    
    # Target reached
    if curr_state['above_target'] and not prior_state.get('above_target', False):
        alerts.append(f"✅ {symbol} TARGET! Price {format_price(price)} > Target {format_price(config['target'])}")
    
    # Update state for next iteration
    prior_state[symbol] = curr_state
    return alerts


def display_header():
    """Print header."""
    print("\n" + "="*110)
    print(f"{'SYMBOL':<8} {'PRICE':<15} {'CHANGE':<10} {'ENTRY':<15} {'STOP':<15} {'TARGET':<15} {'VOL':<12} {'TIER':<5}")
    print("="*110)


def display_row(symbol: str, price: float, entry: float, stop: float, target: float, volume: int, tier: int):
    """Print a single stock row."""
    if price is None:
        print(f"{symbol:<8} {'N/A':<15} {'--':<10} {format_price(entry):<15} {format_price(stop):<15} {format_price(target):<15} {'--':<12} {tier:<5}")
        return
    
    change_pct = ((price - entry) / entry) * 100
    change_color = "🟢" if change_pct >= 0 else "🔴"
    vol_str = f"{volume/1e6:.1f}M" if volume >= 1e6 else f"{volume/1e3:.0f}K"
    
    print(f"{symbol:<8} {format_price(price):<15} {change_color} {change_pct:+6.2f}%   {format_price(entry):<15} {format_price(stop):<15} {format_price(target):<15} {vol_str:<12} {tier:<5}")


def save_snapshot(prices: Dict[str, dict], alerts: List[str]):
    """Save current snapshot to CSV and alerts to JSON."""
    ensure_dir(DATA_DIR)
    
    # Save prices
    rows = []
    for symbol in WATCHLIST:
        if symbol in prices and prices[symbol]['price']:
            config = WATCHLIST[symbol]
            p = prices[symbol]['price']
            rows.append({
                'timestamp': prices[symbol]['timestamp'],
                'symbol': symbol,
                'price': p,
                'entry': config['entry'],
                'stop': config['stop'],
                'target': config['target'],
                'pnl_pct': ((p - config['entry']) / config['entry']) * 100,
                'volume': prices[symbol]['volume'],
            })
    
    if rows:
        df = pd.DataFrame(rows)
        csv_file = os.path.join(DATA_DIR, f"prices_{datetime.now().strftime('%H%M%S')}.csv")
        df.to_csv(csv_file, index=False)
    
    # Save alerts
    if alerts:
        alerts_file = os.path.join(DATA_DIR, 'alerts.json')
        existing = []
        if os.path.exists(alerts_file):
            with open(alerts_file, 'r') as f:
                existing = json.load(f)
        existing.extend([{'timestamp': datetime.now().isoformat(), 'alert': a} for a in alerts])
        with open(alerts_file, 'w') as f:
            json.dump(existing, f, indent=2)


def main():
    """Main monitoring loop."""
    print("📊 IDX Live Market Monitor - Starting...")
    print(f"⏰ Market hours: 09:00-16:00 WIB")
    print(f"⏱️  Poll interval: {POLL_INTERVAL}s")
    print(f"📁 Output directory: {DATA_DIR}")
    
    ensure_dir(DATA_DIR)
    prior_state = defaultdict(dict)
    
    # Warm-up: fetch initial prices
    print("\n🔄 Fetching initial prices...")
    symbols = list(WATCHLIST.keys())
    prices = fetch_prices(symbols)
    
    iteration = 0
    while True:
        iteration += 1
        now = datetime.now()
        
        # Check if market is open
        if not is_market_open():
            print(f"⏹️  Market closed ({now.strftime('%H:%M:%S')}). Exiting.")
            break
        
        # Fetch prices
        prices = fetch_prices(symbols)
        
        # Clear screen and display
        os.system('clear' if os.name != 'nt' else 'cls')
        print(f"\n⏰ {now.strftime('%Y-%m-%d %H:%M:%S')} | Iteration {iteration}")
        
        display_header()
        for symbol in symbols:
            if symbol in prices:
                config = WATCHLIST[symbol]
                p = prices[symbol]['price']
                display_row(symbol, p, config['entry'], config['stop'], config['target'], prices[symbol]['volume'], config['tier'])
        
        # Check alerts
        all_alerts = []
        for symbol in symbols:
            if symbol in prices and prices[symbol]['price']:
                alerts = check_alerts(symbol, prices[symbol]['price'], prior_state)
                all_alerts.extend(alerts)
        
        # Display alerts
        if all_alerts:
            print("\n🔔 ALERTS:")
            for alert in all_alerts:
                print(f"  {alert}")
        
        # Save snapshot
        save_snapshot(prices, all_alerts)
        
        # Wait for next poll
        print(f"\n⏳ Next update in {POLL_INTERVAL}s... (Ctrl+C to stop)")
        try:
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n✅ Monitor stopped.")
            break


if __name__ == '__main__':
    main()
