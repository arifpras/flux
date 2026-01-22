#!/usr/bin/env python3
"""
Multi-Day Stock Data Scraper
=============================

This script scrapes stock data from IDX for multiple previous days.
Requires: ringkasan_saham_batch_scraper.py

Usage:
    python scrape_multiple_days.py --days 10
    python scrape_multiple_days.py --dates 2026-01-10 2026-01-11 2026-01-12
"""

import os
import sys
import argparse
from datetime import date, datetime, timedelta
from typing import List, Optional
from pathlib import Path

# Import the batch scraper
import importlib.util

INDONESIAN_HOLIDAYS = {
    date(2025, 1, 1), date(2025, 2, 19), date(2025, 3, 29), date(2025, 4, 18),
    date(2025, 5, 1), date(2025, 5, 23), date(2025, 6, 1), date(2025, 6, 2),
    date(2025, 6, 16), date(2025, 7, 7), date(2025, 8, 17), date(2025, 8, 28),
    date(2025, 9, 8), date(2025, 12, 25), date(2025, 12, 26),
    date(2026, 1, 1), date(2026, 2, 8), date(2026, 3, 20),
}


def is_business_day(check_date: date) -> bool:
    """Check if date is an Indonesian business day."""
    if check_date.weekday() >= 5:  # Weekend
        return False
    if check_date in INDONESIAN_HOLIDAYS:
        return False
    return True


def get_previous_n_business_days(num_days: int) -> List[date]:
    """Get N previous business days."""
    days = []
    current = date.today() - timedelta(days=1)
    
    while len(days) < num_days:
        if is_business_day(current):
            days.append(current)
        current -= timedelta(days=1)
    
    return sorted(days)


def load_batch_scraper():
    """Dynamically load the batch scraper module."""
    spec = importlib.util.spec_from_file_location(
        "batch_scraper", 
        "ringkasan_saham_batch_scraper.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scrape_multiple_days(dates: List[date], headless: bool = False) -> dict:
    """Scrape data for multiple days."""
    print("\n" + "="*80)
    print("🚀 MULTI-DAY STOCK SCRAPER")
    print("="*80)
    
    print(f"\n📅 Dates to scrape: {len(dates)}")
    for d in dates:
        print(f"   • {d}")
    
    # Try to load batch scraper
    try:
        scraper = load_batch_scraper()
    except Exception as e:
        print(f"\n❌ Error loading batch scraper: {e}")
        print("   Make sure ringkasan_saham_batch_scraper.py exists in current directory")
        return {"success": 0, "failed": len(dates), "files": []}
    
    print(f"\n🔄 Starting scrape (headless={headless})...\n")
    
    # Call the batch scraper function
    try:
        results = scraper.scrape_date_range(dates, headless=headless, delay=1.5)
        return results
    except Exception as e:
        print(f"\n❌ Scraping error: {e}")
        return {"success": 0, "failed": len(dates), "files": []}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape ringkasan saham data for multiple previous days",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape last 10 business days
  python scrape_multiple_days.py --days 10
  
  # Scrape last 30 business days (headless mode)
  python scrape_multiple_days.py --days 30 --headless
  
  # Scrape specific dates
  python scrape_multiple_days.py --dates 2026-01-10 2026-01-11 2026-01-12
        """
    )
    
    parser.add_argument('--days', type=int, help='Number of previous business days to scrape')
    parser.add_argument('--dates', nargs='+', help='Specific dates to scrape (YYYY-MM-DD format)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--delay', type=float, default=1.5, help='Delay between requests (seconds)')
    
    args = parser.parse_args()
    
    # Determine which dates to scrape
    if args.days:
        dates_to_scrape = get_previous_n_business_days(args.days)
    elif args.dates:
        try:
            dates_to_scrape = [datetime.strptime(d, "%Y-%m-%d").date() for d in args.dates]
            dates_to_scrape = sorted(dates_to_scrape)
        except ValueError as e:
            print(f"❌ Error parsing dates: {e}")
            print("   Use format: YYYY-MM-DD")
            sys.exit(1)
    else:
        # Default: last 5 business days
        dates_to_scrape = get_previous_n_business_days(5)
        print("ℹ️  No dates specified. Using last 5 business days by default.")
    
    # Run scraper
    results = scrape_multiple_days(dates_to_scrape, headless=args.headless)
    
    # Print results
    print("\n" + "="*80)
    print("📊 SCRAPING RESULTS")
    print("="*80)
    print(f"Total dates:    {results['total']}")
    print(f"Successful:     {results['success']}")
    print(f"Failed:         {results['failed']}")
    
    if results['success'] > 0:
        success_rate = (results['success'] / results['total']) * 100
        print(f"Success rate:   {success_rate:.1f}%")
        
        if results['files']:
            print(f"\n✅ Files saved ({len(results['files'])}):")
            for f in results['files'][-5:]:  # Show last 5
                print(f"   • {os.path.basename(f)}")
            
            if len(results['files']) > 5:
                print(f"   ... and {len(results['files']) - 5} more")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
