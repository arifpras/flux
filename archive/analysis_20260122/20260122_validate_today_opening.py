"""
Validate 5-day analysis recommendations against today's (22 Jan 2026) opening prices.
Compares Price Validators from last report (ending 21 Jan) vs. today's opening.
Uses IDX ringkasan scraper for reliable real-time data.
"""

import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts', 'scrapers'))

# Import the ringkasan batch scraper
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available. Install with: pip install selenium webdriver-manager")

def load_21jan_closes():
    """Load yesterday's (21 Jan) closing prices from local data."""
    df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])
    
    # Get 21 Jan 2026
    target_date = pd.to_datetime('2026-01-21')
    df_21jan = df[df['SourceDate'] == target_date]
    
    closes = {}
    for _, row in df_21jan.iterrows():
        closes[row['Kode Saham']] = float(row['Penutupan'])
    
    return closes

def extract_validators_from_report(report_path):
    """Parse the last report to extract Price Validators (recommended stocks)."""
    validators = []
    try:
        with open(report_path, 'r') as f:
            in_validators = False
            for line in f:
                if 'PRICE VALIDATORS' in line:
                    in_validators = True
                    continue
                if in_validators and line.startswith('==='):
                    break
                if in_validators and line.strip() and not line.startswith('-') and not line.startswith('Stock'):
                    parts = line.split()
                    if len(parts) >= 2:
                        stock = parts[0]
                        if stock and stock[0].isalpha() and len(stock) <= 4:
                            validators.append(stock)
    except Exception as e:
        print(f"⚠️  Error parsing report: {e}")
    
    return validators

def fetch_today_opening_yfinance(symbols):
    """Fetch today's opening prices from yfinance."""
    openings = {}
    print(f"\n📊 Fetching today's opening prices for {len(symbols)} stocks...")
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(f"{symbol}.JK")
            # Get today's data
            hist = ticker.history(period='1d', interval='1m')
            
            if not hist.empty:
                # Opening is the first price of the day
                opening = float(hist.iloc[0]['Open'])
                openings[symbol] = opening
                print(f"  ✓ {symbol}: Rp {opening:,.0f}")
            else:
                openings[symbol] = None
                print(f"  ⚠️  {symbol}: No data")
        except Exception as e:
            print(f"  ⚠️  {symbol}: Error - {e}")
            openings[symbol] = None
        
        # Rate limit
        time.sleep(0.5)
    
    return openings

def fetch_today_opening_idx_scraper():
    """Fetch today's data using the proven IDX ringkasan scraper."""
    if not SELENIUM_AVAILABLE:
        print("  ⚠️  Selenium not available. Cannot scrape IDX.")
        return None
    
    try:
        print("  🌐 Launching browser to scrape IDX Ringkasan...")
        
        # Set up Chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Navigate to IDX ringkasan page
        url = "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham/"
        driver.get(url)
        time.sleep(3)
        
        # Wait for table to load
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Find the data table
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        if not tables:
            print("  ⚠️  No table found on page")
            driver.quit()
            return None
        
        # Parse the first table (main stock summary)
        table = tables[0]
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        data = []
        headers = []
        
        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text.strip() for cell in cells]
            
            if i == 0:
                headers = row_data
            else:
                if len(row_data) > 0:
                    data.append(row_data)
        
        driver.quit()
        
        if not data:
            print("  ⚠️  No data extracted from table")
            return None
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers if headers else None)
        
        # Map columns (IDX uses Indonesian names)
        column_mapping = {
            'Kode Saham': 'Kode Saham',
            'Nama Perusahaan': 'Nama Perusahaan',
            'Pembukaan': 'Pembukaan',  # Opening price
            'Tertinggi': 'Tertinggi',
            'Terendah': 'Terendah',
            'Penutupan': 'Penutupan',
            'Volume': 'Volume'
        }
        
        # Extract opening prices
        openings = {}
        for _, row in df.iterrows():
            try:
                stock_code = row.get('Kode Saham', '').strip()
                opening_str = row.get('Pembukaan', '0')
                
                # Clean and convert opening price
                if isinstance(opening_str, str):
                    opening_str = opening_str.replace(',', '').replace('.', '')
                opening = float(opening_str) if opening_str else None
                
                if stock_code and opening:
                    openings[stock_code] = opening
            except Exception as e:
                continue
        
        print(f"  ✓ Scraped {len(openings)} stocks from IDX")
        return openings
        
    except Exception as e:
        print(f"  ⚠️  Scraper error: {e}")
        try:
            driver.quit()
        except:
            pass
        return None

def validate_against_today():
    """Main validation routine."""
    print("\n" + "=" * 150)
    print("🔍 TODAY'S OPENING VALIDATION: 22 January 2026")
    print("=" * 150)
    print(f"Validation Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load yesterday's closes (21 Jan)
    print("\n📊 Loading yesterday's (21 Jan) closing prices...")
    closes_21jan = load_21jan_closes()
    print(f"  Loaded {len(closes_21jan)} stocks from 21 Jan data")
    
    # Get Price Validators from report
    report_path = "20260122_last_5days_output.txt"
    validators = extract_validators_from_report(report_path)
    
    if not validators:
        print("⚠️  No Price Validators found in report. Exiting.")
        return
    
    print(f"\n📋 Price Validators ({len(validators)} stocks): {', '.join(validators[:10])}")
    
    # Try IDX scraper first (most reliable for Indonesian stocks)
    print("\n🌐 Attempting to fetch today's data from IDX...")
    openings_today = fetch_today_opening_idx_scraper()
    
    # Fallback to yfinance if IDX scraper fails
    if not openings_today or len(openings_today) == 0:
        print("\n📊 IDX scraper unavailable. Trying yfinance...")
        openings_today = fetch_today_opening_yfinance(validators)
    
    # Final check
    if not openings_today or all(v is None for v in openings_today.values()):
        print("\n⚠️  Unable to fetch today's data from any source.")
        print("  💡 Possible reasons:")
        print("     - Market not yet opened (before 09:00 WIB)")
        print("     - Internet connection issue")
        print("     - IDX website temporarily unavailable")
        print("\n  🔄 Try again after market opens or check your connection.")
        return
    
    # Compare and validate
    print("\n" + "=" * 150)
    print("📈 OPENING VALIDATION: Did recommendations perform at today's open?")
    print("=" * 150)
    print(f"{'Stock':<8} {'21 Jan Close':<18} {'22 Jan Open':<18} {'Gap %':<15} {'Status':<20} {'Signal':<30}")
    print("-" * 150)
    
    results = []
    
    for stock in validators:
        if stock not in closes_21jan or stock not in openings_today:
            continue
        
        close_21 = closes_21jan[stock]
        open_22 = openings_today[stock]
        
        if open_22 is None or close_21 is None:
            continue
        
        # Calculate gap (opening vs. yesterday's close)
        gap_pct = ((open_22 - close_21) / close_21 * 100) if close_21 > 0 else 0
        
        # Determine status
        if gap_pct > 2:
            status = "✅ STRONG GAP UP"
            signal = "Continue holding, momentum strong"
        elif gap_pct > 0.5:
            status = "✅ GAP UP"
            signal = "Positive validation"
        elif gap_pct >= -0.5:
            status = "➡️  FLAT"
            signal = "Watch for direction"
        elif gap_pct >= -2:
            status = "⚠️  GAP DOWN"
            signal = "Minor weakness, monitor"
        else:
            status = "🔴 STRONG GAP DOWN"
            signal = "Exit signal, weakness confirmed"
        
        close_str = f"Rp {close_21:,.0f}"
        open_str = f"Rp {open_22:,.0f}"
        gap_str = f"{gap_pct:+.2f}%"
        
        print(f"{stock:<8} {close_str:<18} {open_str:<18} {gap_str:<15} {status:<20} {signal:<30}")
        
        results.append({
            'stock': stock,
            'close_21': close_21,
            'open_22': open_22,
            'gap_pct': gap_pct,
            'status': status,
            'signal': signal
        })
    
    # Summary
    print("\n" + "=" * 150)
    print("📊 VALIDATION SUMMARY")
    print("=" * 150)
    
    strong_gap_up = sum(1 for r in results if r['gap_pct'] > 2)
    gap_up = sum(1 for r in results if 0.5 < r['gap_pct'] <= 2)
    flat = sum(1 for r in results if -0.5 <= r['gap_pct'] <= 0.5)
    gap_down = sum(1 for r in results if -2 <= r['gap_pct'] < -0.5)
    strong_gap_down = sum(1 for r in results if r['gap_pct'] < -2)
    
    print(f"✅ Strong Gap Up (>+2%):        {strong_gap_up}/{len(results)}")
    print(f"✅ Gap Up (+0.5% to +2%):       {gap_up}/{len(results)}")
    print(f"➡️  Flat (-0.5% to +0.5%):      {flat}/{len(results)}")
    print(f"⚠️  Gap Down (-2% to -0.5%):   {gap_down}/{len(results)}")
    print(f"🔴 Strong Gap Down (<-2%):     {strong_gap_down}/{len(results)}")
    
    validation_rate = ((strong_gap_up + gap_up) / len(results) * 100) if len(results) > 0 else 0
    print(f"\n📈 Opening Validation Rate (Gap Up): {validation_rate:.1f}%")
    
    # High-confidence plays
    strong_plays = [r for r in results if r['gap_pct'] > 2]
    if strong_plays:
        print(f"\n🟢 STRONG OPENING MOMENTUM (>+2%):")
        for r in sorted(strong_plays, key=lambda x: x['gap_pct'], reverse=True):
            print(f"   {r['stock']}: {r['gap_pct']:+.2f}% gap (Rp {r['close_21']:,.0f} → Rp {r['open_22']:,.0f})")
    
    # Exit signals
    weak_plays = [r for r in results if r['gap_pct'] < -2]
    if weak_plays:
        print(f"\n🔴 EXIT SIGNALS (strong gap down <-2%):")
        for r in sorted(weak_plays, key=lambda x: x['gap_pct']):
            print(f"   {r['stock']}: {r['gap_pct']:.2f}% gap (Rp {r['close_21']:,.0f} → Rp {r['open_22']:,.0f})")
    
    print("\n" + "=" * 150)
    print("💡 TRADING GUIDANCE (22 Jan Opening)")
    print("=" * 150)
    print("""
1. STRONG GAP UP (>+2%)
   → Momentum validated; institutions following through
   → Action: Hold or add on minor pullbacks
   → Risk: Take profit if opens >5% up (may reverse)

2. GAP UP (+0.5% to +2%)
   → Positive confirmation
   → Action: Continue holding; monitor for sustained follow-through
   → Risk: Watch for fade if volume weak

3. FLAT (-0.5% to +0.5%)
   → Neutral; awaiting direction
   → Action: Wait for breakout confirmation (above/below yesterday's high/low)
   → Risk: Could move either way; use tight stops

4. GAP DOWN (-2% to -0.5%)
   → Minor weakness; caution
   → Action: Reduce position or tighten stops
   → Risk: May continue down if no support

5. STRONG GAP DOWN (<-2%)
   → EXIT SIGNAL; recommendation invalidated
   → Action: Exit at open or first bounce
   → Risk: Cascading selling if institutions exiting
    """)
    
    print("=" * 150)

if __name__ == "__main__":
    validate_against_today()
