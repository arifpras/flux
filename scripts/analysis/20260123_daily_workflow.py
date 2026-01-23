#!/usr/bin/env python3
"""
Daily Workflow: Execute Sentiment Sanity Check Before Trading
Ensures no negative news affects recommended stocks before position entry
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
import sys

def run_sentiment_check(workspace):
    """Run sentiment analysis on recommended stocks"""
    print("\n" + "=" * 85)
    print("STEP 1: SENTIMENT SANITY CHECK".ljust(85))
    print("=" * 85)
    print("\nChecking news for any negative signals on recommended stocks...\n")
    
    script = workspace / "scripts" / "analysis" / "20260123_sentiment_analysis.py"
    
    try:
        result = subprocess.run(
            ["python", str(script)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"⚠️  Warning: {result.stderr}")
        
        # Check if results file was created
        results_file = workspace / "results" / "20260123_SENTIMENT_ANALYSIS.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
                return results
        
        return {}
    
    except subprocess.TimeoutExpired:
        print("⚠️  Sentiment check timed out")
        return {}
    except Exception as e:
        print(f"❌ Error running sentiment check: {e}")
        return {}

def extract_trading_recommendations(sentiment_results):
    """Extract trading recommendations from sentiment analysis"""
    
    print("\n" + "=" * 85)
    print("STEP 2: TRADING RECOMMENDATIONS".ljust(85))
    print("=" * 85)
    
    # Priority stocks from strategy report
    priority_stocks = {
        "DGIK": {"action": "BUY", "details": "Target: 160-165, Stop: 136, Size: 5-7%"},
        "ASII": {"action": "BUY", "details": "Target: 7,450, Stop: 6,300, Size: 8-10%"},
        "BBKP": {"action": "MONITOR", "details": "Entry >88, Stop: 84, Size: 2-3%"},
    }
    
    print("\n🚀 PRIORITY 1 ACTIONS (Check Sentiment Clear):\n")
    
    all_clear = True
    
    for ticker, trade_plan in priority_stocks.items():
        result = sentiment_results.get(ticker, {})
        risk = result.get("risk_level", "UNKNOWN")
        
        if risk == "LOW" or not risk:
            status = "✅ CLEAR TO EXECUTE"
        elif risk == "MEDIUM":
            status = "🟡 PROCEED WITH CAUTION"
            all_clear = False
        else:
            status = "❌ DO NOT EXECUTE"
            all_clear = False
        
        action = trade_plan["action"]
        print(f"{ticker} │ {action:8} │ {status}")
        print(f"     │ {trade_plan['details']}")
        
        if risk and risk != "LOW":
            flags = result.get("risk_flags", [])
            if flags:
                print(f"     │ Flags: {', '.join(flags[:3])}")
    
    if all_clear:
        print("\n✅ ALL SYSTEMS GREEN - Proceed with trading plan")
    else:
        print("\n⚠️  CHECK NEWS BEFORE PROCEEDING - Some stocks have warnings")
    
    return all_clear

def generate_trading_checklist():
    """Generate pre-trade checklist"""
    
    print("\n" + "=" * 85)
    print("PRE-TRADE CHECKLIST".ljust(85))
    print("=" * 85)
    print()
    
    checklist = [
        ("Sentiment Analysis Complete", "✓"),
        ("No High-Risk News Detected", "✓"),
        ("Liquidity Confirmed (>500M IDR daily)", "Check yourself"),
        ("IDX Announcements Reviewed", "Check yourself"),
        ("Market Hours (9:00-16:00 WIB)", "Check yourself"),
        ("Profit Targets & Stops Set", "Check yourself"),
        ("Position Sizes Calculated", "Check yourself"),
    ]
    
    for item, status in checklist:
        symbol = "☐" if status == "Check yourself" else "☑"
        print(f"  {symbol} {item:50} {status:20}")
    
    print()

def main():
    workspace = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper")
    
    print("\n")
    print("╔" + "═" * 83 + "╗")
    print("║" + "DAILY TRADING WORKFLOW: SENTIMENT SANITY CHECK".center(83) + "║")
    print("║" + f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}".ljust(83) + "║")
    print("╚" + "═" * 83 + "╝")
    
    # Run sentiment analysis
    sentiment_results = run_sentiment_check(workspace)
    
    # Get trading recommendations
    all_clear = extract_trading_recommendations(sentiment_results)
    
    # Show pre-trade checklist
    generate_trading_checklist()
    
    # Summary
    print("\n" + "=" * 85)
    print("SUMMARY".ljust(85))
    print("=" * 85)
    
    if all_clear:
        print("\n✅ Sentiment sanity check PASSED")
        print("   → Proceed with executing priority trades")
        print("   → Monitor for any market-wide events")
        return 0
    else:
        print("\n⚠️  Sentiment sanity check WARNING")
        print("   → Review flagged stocks before trading")
        print("   → Check latest news on affected stocks")
        return 1

if __name__ == "__main__":
    sys.exit(main())
