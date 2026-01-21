#!/usr/bin/env python3
"""
FLUX DAILY TRADER CHECKLIST
Quick reference for 5-day swing trading decisions
Use this BEFORE entering any trade
"""

import json
from datetime import datetime, timedelta

# Active trades to monitor for exit
ACTIVE_TRADES = {
    'ADRO': {
        'entry_date': '2026-01-16',  # Day 1 entry
        'entry_price': 2030,
        'exit_date': '2026-01-23',   # Day 5 exit (5 trading days)
        'entry_reason': 'DBR 50.7% institutional cornering + reversal bounce',
        'target_return': 5.0,
    }
}

# Real data from 21 Jan 2026
TODAY_DATA = {
    'scan_date': '2026-01-21',
    'stocks': {
        'ADRO': {
            'price': 2210,
            'day_change': -1.34,
            '5d_change': 8.87,
            'intraday_bounce': 3.23,
            'volume': 56_365_200,
            'avg_5d_volume': 100_000_000,
            'broker_dbr': 50.7,
            'buy_vwap': 2258,
            'per': 5.65,
            'roe': 10.95,
            'pbv': 0.62,
            'sector': 'Energy',
            'sector_mtd': 19.2,
        },
        'ASII': {
            'price': 6625,
            'day_change': -8.93,
            '5d_change': -5.36,
            'intraday_bounce': -1.02,
            'volume': 164_350_800,
            'avg_5d_volume': 120_000_000,
            'broker_bci': 2.74,
            'buy_vwap': 7233,
            'per': 8.30,
            'roe': 11.28,
            'pbv': 0.94,
            'sector': 'Industrials',
            'sector_mtd': 8.8,
        },
        'BMTR': {
            'price': 163,
            'day_change': -1.81,
            '5d_change': 6.54,
            'intraday_bounce': 1.5,
            'volume': 23_369_100,
            'avg_5d_volume': 20_000_000,
            'per': 4.39,
            'roe': 1.77,
            'pbv': 0.08,
            'sector': 'Industrials',
            'sector_mtd': 8.8,
        },
        'BSIM': {
            'price': 1290,
            'day_change': 0.39,
            '5d_change': -24.56,
            'intraday_bounce': 0.39,
            'per': 54.24,
            'roe': 3.36,
            'pbv': 1.80,
            'sector': 'Financials',
            'sector_mtd': -5.2,
        },
        'BNBR': {
            'price': 230,
            'day_change': 0.0,
            '5d_change': 22.99,
            'intraday_bounce': 0.0,
            'per': -74.15,
            'roe': -7.15,
            'pbv': 5.35,
            'sector': 'Industrials',
            'sector_mtd': 8.8,
        },
    }
}

def check_stock(stock, data):
    """Run full checklist for a stock"""
    
    print(f"\n{'='*70}")
    print(f"FLUX CHECKLIST: {stock}")
    print(f"{'='*70}\n")
    
    checks = {
        'PASS': 0,
        'FAIL': 0
    }
    
    # CHECK 1: BROKER CONCENTRATION
    print("☐ CHECK 1: BROKER CONCENTRATION")
    dbr = data.get('broker_dbr', 0)
    bci = data.get('broker_bci', 0)
    
    if dbr > 40 or bci > 2.0:
        print(f"  ✅ PASS")
        if dbr > 50:
            print(f"     → Institutional Cornering: DBR {dbr}% (HIGHEST conviction)")
        elif bci > 2.5:
            print(f"     → Broker Alliance: BCI {bci} (MEDIUM-HIGH conviction)")
        else:
            print(f"     → Institutional buying present")
        checks['PASS'] += 1
    else:
        print(f"  ❌ FAIL - No institutional backing (DBR: {dbr}%, BCI: {bci})")
        checks['FAIL'] += 1
    
    # CHECK 2: FUNDAMENTALS
    print("\n☐ CHECK 2: FUNDAMENTALS")
    per = data.get('per', 0)
    roe = data.get('roe', 0)
    pbv = data.get('pbv', 0)
    
    fund_pass = per > 0 and per < 15 and roe > 5 and pbv < 2.0
    
    if fund_pass:
        print(f"  ✅ PASS")
        print(f"     → PER: {per} (Target <15) ✓")
        print(f"     → ROE: {roe}% (Target >5%) ✓")
        print(f"     → PBV: {pbv} (Target <2.0) ✓")
        checks['PASS'] += 1
    else:
        print(f"  ❌ FAIL - Weak fundamentals")
        if per <= 0:
            print(f"     → Negative/loss-making (PER: {per})")
        elif per >= 15:
            print(f"     → Overvalued (PER: {per} > 15)")
        if roe <= 5:
            print(f"     → Low profitability (ROE: {roe}% < 5%)")
        if pbv >= 2.0:
            print(f"     → Trading above book (PBV: {pbv} > 2.0)")
        checks['FAIL'] += 1
    
    # CHECK 3: TECHNICAL REVERSAL (CRITICAL!)
    print("\n☐ CHECK 3: TECHNICAL REVERSAL ⭐ CRITICAL")
    decline_5d = data.get('5d_change', 0)
    bounce = data.get('intraday_bounce', 0)
    
    decline_valid = -5.0 <= decline_5d <= -0.5
    bounce_valid = bounce > 1.0
    
    if decline_valid and bounce_valid:
        print(f"  ✅ PASS - Strong reversal signal")
        print(f"     → 5D Decline: {decline_5d:.2f}% (Target: -5% to -0.5%) ✓")
        print(f"     → Intraday Bounce: +{bounce:.2f}% (Target: >1%) ✓")
        checks['PASS'] += 1
    else:
        print(f"  ❌ FAIL - No reversal confirmation")
        if not decline_valid:
            print(f"     → Decline outside range: {decline_5d:.2f}%")
        if not bounce_valid:
            print(f"     → No intraday bounce: {bounce:.2f}%")
        checks['FAIL'] += 1
    
    # CHECK 4: VOLUME SPIKE
    print("\n☐ CHECK 4: VOLUME SPIKE")
    volume = data.get('volume', 0)
    avg_vol = data.get('avg_5d_volume', 0)
    
    if volume > 0 and avg_vol > 0:
        vol_ratio = (volume / avg_vol) * 100
        if vol_ratio > 120:
            print(f"  ✅ PASS")
            print(f"     → Volume ratio: {vol_ratio:.0f}% (Target: >120%) ✓")
            checks['PASS'] += 1
        else:
            print(f"  ⚠️  WEAK - Below target volume")
            print(f"     → Volume ratio: {vol_ratio:.0f}% (Target: >120%)")
            checks['FAIL'] += 1
    else:
        print(f"  ⚠️  Volume data unavailable")
    
    # CHECK 5: SECTOR MOMENTUM
    print("\n☐ CHECK 5: SECTOR MOMENTUM")
    sector = data.get('sector', 'Unknown')
    sector_mtd = data.get('sector_mtd', 0)
    
    if sector_mtd > 0:
        print(f"  ✅ PASS")
        print(f"     → Sector: {sector} (MTD: +{sector_mtd}%) ✓")
        checks['PASS'] += 1
    else:
        print(f"  ❌ FAIL - Sector in downtrend")
        print(f"     → {sector} MTD: {sector_mtd}% (weak momentum)")
        checks['FAIL'] += 1
    
    # CHECK 6: VWAP ENTRY TIMING
    print("\n☐ CHECK 6: VWAP ENTRY TIMING")
    price = data.get('price', 0)
    vwap = data.get('buy_vwap', 0)
    
    if vwap > 0 and price > 0:
        vwap_diff = ((price - vwap) / vwap) * 100
        if -1.0 <= vwap_diff <= 1.0:
            print(f"  ✅ PASS - Optimal entry price")
            print(f"     → Current: Rp {price:,} vs VWAP: Rp {vwap:,}")
            print(f"     → Diff: {vwap_diff:.2f}% (Target: ±1%) ✓")
            checks['PASS'] += 1
        else:
            print(f"  ❌ FAIL - Outside entry window")
            print(f"     → Diff from VWAP: {vwap_diff:.2f}% (should be ±1%)")
            if vwap_diff < -1.0:
                print(f"     → Too far below (sellers fleeing, weak hands)")
            else:
                print(f"     → Too far above (early movers escaping)")
            checks['FAIL'] += 1
    else:
        print(f"  ⚠️  VWAP data unavailable")
    
    # FINAL DECISION
    print(f"\n{'='*70}")
    print("FINAL DECISION")
    print(f"{'='*70}\n")
    
    passed = checks['PASS']
    failed = checks['FAIL']
    score = (passed / 6) * 100
    
    print(f"Score: {passed}/6 checks ({score:.0f}/100)")
    print(f"Checks: {passed} PASS ✅ | {failed} FAIL ❌\n")
    
    # Mandatory requirement: Technical reversal + Fundamentals
    must_have = ('CHECK 3' in str(checks) and fund_pass)
    
    if failed == 0:
        print(f"🟢 STRONG BUY")
        print(f"   Action: ENTER immediately")
        print(f"   Position Size: 100%")
        print(f"   Expected 5D return: +5% to +8%")
    elif failed == 1 and failed != checks.get('CHECK 3'):
        print(f"🟢 BUY (Minor weakness)")
        print(f"   Action: Enter with caution")
        print(f"   Position Size: 50-75%")
        print(f"   Expected 5D return: +3% to +5%")
    elif failed <= 2 and fund_pass:
        print(f"🟡 HOLD (Wait for confirmation)")
        print(f"   Action: Monitor for Day 2 follow-through")
        print(f"   Position Size: Skip or 25% trial")
        print(f"   Expected 5D return: +1% to +3%")
    else:
        print(f"🔴 SKIP (Too many red flags)")
        print(f"   Action: Do not enter")
        print(f"   Reason: {failed} checks failed")
        print(f"   Review: Come back when more signals align")
    
    # Entry parameters if buying
    if failed <= 2 and fund_pass:
        print(f"\n{'='*70}")
        print("TRADING PARAMETERS (If Entering)")
        print(f"{'='*70}\n")
        
        entry = price
        stop_loss = entry * 0.93  # 7% stop
        target_1 = entry * 1.03  # 3%
        target_2 = entry * 1.05  # 5%
        target_3 = entry * 1.08  # 8%
        
        print(f"Entry Price:  Rp {entry:>10,}")
        print(f"Stop Loss:    Rp {stop_loss:>10,.0f}  (-7%)")
        print(f"Target 1:     Rp {target_1:>10,.0f}  (+3%)")
        print(f"Target 2:     Rp {target_2:>10,.0f}  (+5%)")
        print(f"Target 3:     Rp {target_3:>10,.0f}  (+8%)")
        print(f"\nExit Date:    24 January 2026 (5 trading days)")
    
    print(f"\n{'='*70}\n")
    
    return failed == 0  # Return True if strong buy


def check_active_trades():
    """Monitor active trades for exit signals"""
    
    if not ACTIVE_TRADES:
        return
    
    print("\n" + "="*70)
    print("ACTIVE TRADES - EXIT MONITORING")
    print("="*70 + "\n")
    
    scan_date = datetime.strptime(TODAY_DATA['scan_date'], '%Y-%m-%d')
    
    for stock, trade_info in ACTIVE_TRADES.items():
        entry_date = datetime.strptime(trade_info['entry_date'], '%Y-%m-%d')
        exit_date = datetime.strptime(trade_info['exit_date'], '%Y-%m-%d')
        days_held = (scan_date - entry_date).days
        days_to_exit = (exit_date - scan_date).days
        
        # Get current price
        current_data = TODAY_DATA['stocks'].get(stock, {})
        current_price = current_data.get('price', 0)
        entry_price = trade_info['entry_price']
        
        # Calculate P&L
        if current_price > 0:
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            pnl_idr = current_price - entry_price
            
            print(f"📊 {stock}")
            print(f"   Entry: {entry_date.strftime('%d %b')} @ Rp {entry_price:,}")
            print(f"   Current: Rp {current_price:,}")
            print(f"   P&L: {pnl_idr:+,} IDR ({pnl_pct:+.2f}%)")
            print(f"   Days Held: {days_held}")
            print(f"   Target Return: {trade_info['target_return']}%")
            
            # Exit decision
            if days_to_exit <= 0:
                print(f"   🔴 EXIT TODAY - Day 5 reached")
                print(f"      Reason: Mechanical 5-day exit rule")
            elif days_to_exit == 1:
                print(f"   🟡 EXIT TOMORROW ({exit_date.strftime('%d %b')})")
                print(f"      Prepare sell order")
            else:
                print(f"   🟢 HOLD until {exit_date.strftime('%d %b')} ({days_to_exit} days)")
            
            # Performance assessment
            if pnl_pct >= trade_info['target_return']:
                print(f"   ✅ TARGET REACHED (+{pnl_pct:.2f}% vs +{trade_info['target_return']}% target)")
            elif pnl_pct > 0:
                print(f"   ⚠️  Profitable but below target (+{pnl_pct:.2f}% vs +{trade_info['target_return']}%)")
            else:
                print(f"   ❌ LOSING TRADE ({pnl_pct:.2f}%)")
                if pnl_pct <= -7:
                    print(f"   🚨 STOP LOSS HIT - EXIT IMMEDIATELY")
            
            print(f"   Entry Reason: {trade_info['entry_reason']}")
            print()


def main():
    """Run checklist for all stocks"""
    
    print("\n" + "="*70)
    print("FLUX DAILY TRADING CHECKLIST - 21 JANUARY 2026")
    print("Improved v2.0 with Technical + Fundamental + Institutional Filters")
    print("="*70)
    
    # Check active trades first
    check_active_trades()
    
    # Scan for new entries
    print("\n" + "="*70)
    print("NEW ENTRY SIGNALS - TODAY'S SCAN")
    print("="*70)
    
    results = {}
    
    for stock, data in TODAY_DATA['stocks'].items():
        results[stock] = check_stock(stock, data)
    
    # Summary
    strong_buys = [s for s, passed in results.items() if passed]
    
    print("\n" + "="*70)
    print("TODAY'S SUMMARY")
    print("="*70 + "\n")
    
    if strong_buys:
        print(f"🟢 STRONG BUY signals: {', '.join(strong_buys)}")
    else:
        print("🟡 No strong buy signals today. Review borderline candidates.")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
