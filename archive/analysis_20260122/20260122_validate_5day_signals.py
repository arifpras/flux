"""
Live validation of 5-day analysis signals against real-time yfinance data.
Compares recommended stocks from last_5days_analysis.py against today's market reality.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
from pathlib import Path

# Load the most recent 5-day report data
def load_5day_data():
    """Load the last 5 trading days from ringkasan_histories_combined.csv."""
    df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])
    
    # Get last 5 trading days
    dates = sorted(df['SourceDate'].unique())[-5:]
    return df[df['SourceDate'].isin(dates)], dates

def get_yfinance_data(symbols, period='5d'):
    """Fetch 5-day history from yfinance for IDX symbols (fallback method)."""
    # Convert IDX codes to yfinance format (add .JK suffix)
    yf_symbols = [f"{sym}.JK" for sym in symbols]
    
    try:
        data = yf.download(yf_symbols, period=period, progress=False)
        return data
    except Exception as e:
        print(f"⚠️  yfinance not available (many micro-cap IDX stocks not covered): {e}")
        print("   Switching to local ringkasan_histories_combined.csv for validation...")
        return None

def get_local_data(symbols):
    """Use local ringkasan data (more reliable for micro-cap IDX stocks)."""
    df = pd.read_csv("data/histories/ringkasan_histories_combined.csv")
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])
    
    # Get today (or latest available)
    latest_date = df['SourceDate'].max()
    
    local_data = {}
    for sym in symbols:
        sym_df = df[df['Kode Saham'] == sym]
        if not sym_df.empty:
            latest_row = sym_df[sym_df['SourceDate'] == latest_date]
            if not latest_row.empty:
                local_data[sym] = {
                    'today_close': latest_row['Penutupan'].values[0],
                    'today_date': latest_date
                }
    
    return local_data, latest_date

def extract_validators_from_report(report_path):
    """Parse the last report to extract Price Validators (recommended stocks)."""
    validators = {}
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
                        # Extract accum value (format: 🟢 Rp X,XXX,XXX)
                        # This is a simplified parse; more robust would regex
                        if stock and stock[0].isalpha():
                            validators[stock] = True
    except Exception as e:
        print(f"⚠️  Error parsing report: {e}")
    
    return validators

def validate_signals():
    """Main validation routine."""
    print("\n" + "=" * 150)
    print("🔍 LIVE VALIDATION: 5-Day Analysis Signals vs. Real-Time Data")
    print("=" * 150)
    print(f"Validation Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load historical data
    df_hist, dates = load_5day_data()
    print(f"Historical Period: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    
    # Get the Price Validators from the report
    report_path = "last_5days_output.txt"
    validators = extract_validators_from_report(report_path)
    
    if not validators:
        print("⚠️  No Price Validators found in report. Exiting.")
        return
    
    validator_stocks = list(validators.keys())
    print(f"\nValidator Stocks ({len(validator_stocks)}): {', '.join(validator_stocks[:10])}")
    
    # Try yfinance first, fall back to local data
    print("\n📊 Fetching real-time data from yfinance...")
    yf_data = get_yfinance_data(validator_stocks)
    
    if yf_data is None or yf_data.empty:
        print("   Using local ringkasan_histories_combined.csv for validation...")
        local_data, today_date = get_local_data(validator_stocks)
    else:
        local_data = None
    
    # Compare: historical vs. current
    print("\n" + "=" * 150)
    print("📈 SIGNAL VALIDATION: Did prices validate the recommendation?")
    print("=" * 150)
    print(f"{'Stock':<8} {'Last 5d Close':<18} {'Last 5d Perf':<18} {'Today Close':<18} {'Today Perf':<18} {'Status':<20} {'Confidence':<15}")
    print("-" * 150)
    
    # Historical close for comparison (last date in period)
    hist_last_date = dates[-1]
    hist_closes = df_hist[df_hist['SourceDate'] == hist_last_date].set_index('Kode Saham')['Penutupan']
    
    # Historical price start (first date in period)
    hist_first_date = dates[0]
    hist_closes_start = df_hist[df_hist['SourceDate'] == hist_first_date].set_index('Kode Saham')['Penutupan']
    
    results = []
    
    for stock in validator_stocks:
        yf_sym = f"{stock}.JK"
        
        # Get historical perf in last 5 days
        if stock in hist_closes.index and stock in hist_closes_start.index:
            hist_start = hist_closes_start[stock]
            hist_end = hist_closes[stock]
            hist_perf = ((hist_end - hist_start) / hist_start * 100) if hist_start > 0 else 0
        else:
            hist_start = hist_end = hist_perf = None
        
        # Get today's close (from local data or yfinance)
        if local_data and stock in local_data:
            today_close = local_data[stock]['today_close']
        elif yf_data is not None:
            try:
                if 'Close' in yf_data.columns:
                    today_close = yf_data['Close'][yf_sym].iloc[-1]
                else:
                    today_close = yf_data[yf_sym]['Close'].iloc[-1]
            except:
                today_close = None
        else:
            today_close = None
        
        # Calculate today's perf vs. period end
        if hist_end and today_close:
            today_perf = ((today_close - hist_end) / hist_end * 100) if hist_end > 0 else 0
        else:
            today_perf = None
        
        # Determine status
        if hist_perf is not None and today_perf is not None:
            if hist_perf > 0 and today_perf > 0:
                status = "✅ VALIDATED"
                confidence = "High"
            elif hist_perf > 0 and today_perf >= 0:
                status = "✅ HOLDING"
                confidence = "Medium"
            elif hist_perf > 0 and today_perf < 0:
                status = "⚠️  DIVERGING"
                confidence = "Low"
            elif hist_perf > 5 and today_perf < hist_perf:
                status = "🔴 TAKING PROFIT"
                confidence = "Medium"
            else:
                status = "➡️  NEUTRAL"
                confidence = "Low"
        else:
            status = "❓ N/A"
            confidence = "No Data"
        
        hist_close_str = f"Rp {hist_end:,.0f}" if hist_end else "N/A"
        hist_perf_str = f"{hist_perf:+.2f}%" if hist_perf is not None else "N/A"
        today_close_str = f"Rp {today_close:,.0f}" if today_close else "N/A"
        today_perf_str = f"{today_perf:+.2f}%" if today_perf is not None else "N/A"
        
        print(f"{stock:<8} {hist_close_str:<18} {hist_perf_str:<18} {today_close_str:<18} {today_perf_str:<18} {status:<20} {confidence:<15}")
        
        results.append({
            'stock': stock,
            'hist_close': hist_end,
            'hist_perf': hist_perf,
            'today_close': today_close,
            'today_perf': today_perf,
            'status': status,
            'confidence': confidence
        })
    
    # Summary
    print("\n" + "=" * 150)
    print("📊 VALIDATION SUMMARY")
    print("=" * 150)
    
    validated = sum(1 for r in results if r['status'] == "✅ VALIDATED")
    holding = sum(1 for r in results if r['status'] == "✅ HOLDING")
    diverging = sum(1 for r in results if r['status'] == "⚠️  DIVERGING")
    taking_profit = sum(1 for r in results if r['status'] == "🔴 TAKING PROFIT")
    
    print(f"✅ Validated (continuing up):        {validated}/{len(results)}")
    print(f"✅ Holding (not falling):            {holding}/{len(results)}")
    print(f"⚠️  Diverging (price fell):          {diverging}/{len(results)}")
    print(f"🔴 Taking Profit (reversal):        {taking_profit}/{len(results)}")
    
    overall_accuracy = ((validated + holding) / len(results) * 100) if len(results) > 0 else 0
    print(f"\n📈 Signal Accuracy (Validated+Holding): {overall_accuracy:.1f}%")
    
    # High-confidence plays
    high_conf = [r for r in results if r['confidence'] == 'High' and r['today_perf'] is not None and r['today_perf'] > 0]
    if high_conf:
        print(f"\n🟢 HIGH-CONFIDENCE ACTIVE (price up today):")
        for r in sorted(high_conf, key=lambda x: x['today_perf'], reverse=True):
            print(f"   {r['stock']}: +{r['today_perf']:.2f}% (last 5d: {r['hist_perf']:+.2f}%)")
    
    # Risky plays (recommended but falling)
    risky = [r for r in results if r['status'] == "⚠️  DIVERGING"]
    if risky:
        print(f"\n🔴 RISKY DIVERGENCE (recommended but price fell today):")
        for r in sorted(risky, key=lambda x: x['today_perf']):
            print(f"   {r['stock']}: {r['today_perf']:.2f}% (last 5d: {r['hist_perf']:+.2f}%)")
    
    # Exit signals
    reversals = [r for r in results if r['status'] == "🔴 TAKING PROFIT"]
    if reversals:
        print(f"\n⚠️  POTENTIAL REVERSALS (after strong 5d runs):")
        for r in sorted(reversals, key=lambda x: x['hist_perf'], reverse=True):
            print(f"   {r['stock']}: 5d: {r['hist_perf']:+.2f}%, today: {r['today_perf']:+.2f}%")
    
    print("\n" + "=" * 150)
    print("💡 TRADING GUIDANCE")
    print("=" * 150)
    print("""
1. HIGH CONFIDENCE ACTIVE
   → Continue holding; consider adding on dips
   → Risk: Take profit if breaks below 5-day trend line
   
2. DIVERGING (recommended but price fell)
   → Institutional flows may be outdated or data lag
   → Options: (a) Wait for stabilization, (b) Exit if breaks 2-3%
   → Risk: Further weakness; watch for capitulation
   
3. TAKING PROFIT (after strong runs)
   → Natural pullback after 80%+ rallies
   → Risk: May reverse if volume dries up
   → Exit trigger: Close below 50-day MA or break of recent support
    """)
    
    print("=" * 150)

if __name__ == "__main__":
    validate_signals()
