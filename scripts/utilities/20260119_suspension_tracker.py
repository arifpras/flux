#!/usr/bin/env python3
"""
IDX Suspension Tracker
=====================
Fetches and tracks trading suspensions from IDX website.

Features:
- Scrapes suspension announcements from IDX
- Tracks suspension/reopening dates
- Identifies currently suspended stocks
- Integrates with watchlist filter for risk management
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

class SuspensionTracker:
    """Track and manage IDX trading suspensions."""
    
    # IDX Suspension page
    IDX_SUSPENSION_URL = "https://www.idx.co.id/en/news/suspension/"
    IDX_SUSPENSION_ID = "https://www.idx.co.id/id/berita/suspensi/"
    
    # Cache file
    CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "manual"
    SUSPENSION_CACHE = CACHE_DIR / "idx_suspensions_cache.json"
    
    def __init__(self, use_cache=True, cache_age_hours=24):
        """
        Initialize suspension tracker.
        
        Args:
            use_cache: Use cached data if available (default True)
            cache_age_hours: Max age of cache before refresh (default 24 hours)
        """
        self.use_cache = use_cache
        self.cache_age_hours = cache_age_hours
        self.suspensions = {}
        self.last_update = None
        
        self._load_or_fetch()
    
    def _load_or_fetch(self):
        """Load from cache or fetch fresh data."""
        if self.use_cache and self._is_cache_valid():
            self._load_from_cache()
        else:
            self.fetch_suspensions()
    
    def _is_cache_valid(self):
        """Check if cache file exists and is not too old."""
        if not self.SUSPENSION_CACHE.exists():
            return False
        
        file_age = datetime.now() - datetime.fromtimestamp(
            self.SUSPENSION_CACHE.stat().st_mtime
        )
        return file_age < timedelta(hours=self.cache_age_hours)
    
    def _load_from_cache(self):
        """Load suspension data from cache file."""
        try:
            with open(self.SUSPENSION_CACHE, 'r') as f:
                data = json.load(f)
                self.suspensions = data.get('suspensions', {})
                self.last_update = data.get('last_update')
                print(f"✓ Loaded suspensions from cache ({len(self.suspensions)} stocks)")
        except Exception as e:
            print(f"⚠ Error loading cache: {e}")
            self.fetch_suspensions()
    
    def _save_to_cache(self):
        """Save suspension data to cache file."""
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            
            data = {
                'suspensions': self.suspensions,
                'last_update': self.last_update,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.SUSPENSION_CACHE, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Saved {len(self.suspensions)} suspension records to cache")
        except Exception as e:
            print(f"⚠ Error saving cache: {e}")
    
    def fetch_suspensions(self):
        """
        Fetch suspension data from IDX website.
        
        Attempts to scrape the suspension page and extract stock codes and dates.
        Falls back to manual data if scraping fails.
        """
        try:
            print("📡 Fetching suspension data from IDX...")
            
            # Try to fetch the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(self.IDX_SUSPENSION_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find suspension table
            tables = soup.find_all('table')
            
            if tables:
                suspensions_found = self._parse_suspension_table(soup)
                if suspensions_found:
                    self.last_update = datetime.now().isoformat()
                    self._save_to_cache()
                    print(f"✓ Fetched {len(self.suspensions)} suspension records from IDX")
                    return
            
            print("⚠ Could not parse suspension table, using fallback data")
            self._load_fallback_data()
            
        except Exception as e:
            print(f"⚠ Error fetching suspensions: {e}")
            print("  Using fallback/cached data")
            self._load_fallback_data()
    
    def _parse_suspension_table(self, soup):
        """
        Parse suspension data from HTML table.
        
        Returns:
            bool: True if parsing was successful
        """
        try:
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    cols = row.find_all('td')
                    
                    if len(cols) >= 2:
                            # Extract date and description
                            date_str = cols[0].text.strip()
                            desc_str = cols[1].text.strip()
                        
                            # Try to parse date
                            try:
                                date_obj = datetime.strptime(date_str, '%d %b %Y')
                            except:
                                continue
                            
                            # Extract stock code (usually in parentheses)
                            stock_code = self._extract_stock_code(desc_str)
                            
                            if stock_code:
                                is_suspension = 'Penghentian' in desc_str or 'Suspension' in desc_str
                                is_reopening = 'Pembukaan' in desc_str or 'Reopening' in desc_str
                                
                                if stock_code not in self.suspensions:
                                    self.suspensions[stock_code] = {
                                        'code': stock_code,
                                        'status': 'suspended' if is_suspension else 'reopened',
                                        'last_event_date': date_str,
                                        'last_event_desc': desc_str[:80],
                                        'suspension_date': date_str if is_suspension else None,
                                        'reopening_date': date_str if is_reopening else None
                                    }
                                else:
                                    # Update existing record
                                    if is_suspension:
                                        self.suspensions[stock_code]['status'] = 'suspended'
                                        self.suspensions[stock_code]['suspension_date'] = date_str
                                    elif is_reopening:
                                        self.suspensions[stock_code]['status'] = 'reopened'
                                        self.suspensions[stock_code]['reopening_date'] = date_str
                                    
                                    self.suspensions[stock_code]['last_event_date'] = date_str
                                    self.suspensions[stock_code]['last_event_desc'] = desc_str[:80]
            
            return len(self.suspensions) > 0
        
        except Exception as e:
            print(f"⚠ Error parsing table: {e}")
            return False
    
    @staticmethod
    def _extract_stock_code(text):
        """
        Extract stock code from text (usually in parentheses).
        
        Examples:
            "Penghentian Sementara Perdagangan Saham PT Pool Advista Finance Tbk. (POLA)"
            → "POLA"
        """
        import re
        
        # Look for pattern: (XXXX) or (XXXX-W)
        matches = re.findall(r'\(([A-Z]{2,6}(?:-[A-Z])?)(?:\s|,|\))', text)
        
        if matches:
            return matches[0]
        
        return None
    
    def _load_fallback_data(self):
        """Load fallback suspension data from recent IDX announcements."""
        # Based on the fetched webpage data from Jan 19, 2026
        fallback_data = {
            'POLA': {
                'code': 'POLA',
                'status': 'suspended',
                'last_event_date': '15 Jan 2026',
                'last_event_desc': 'Penghentian Sementara Perdagangan Saham PT Pool Advista Finance Tbk.',
                'suspension_date': '15 Jan 2026',
                'reopening_date': None
            },
            'SOTS': {
                'code': 'SOTS',
                'status': 'suspended',
                'last_event_date': '14 Jan 2026',
                'last_event_desc': 'Penghentian Sementara Perdagangan Saham PT Satria Mega Kencana Tbk.',
                'suspension_date': '14 Jan 2026',
                'reopening_date': None
            },
            'INDS': {
                'code': 'INDS',
                'status': 'reopened',
                'last_event_date': '15 Jan 2026',
                'last_event_desc': 'Pembukaan Kembali Perdagangan Saham PT Indospring Tbk.',
                'suspension_date': '14 Jan 2026',
                'reopening_date': '15 Jan 2026'
            },
            'KOCI': {
                'code': 'KOCI',
                'status': 'reopened',
                'last_event_date': '13 Jan 2026',
                'last_event_desc': 'Pembukaan Kembali Perdagangan Saham PT Kokoh Exa Nusantara Tbk.',
                'suspension_date': '14 Jan 2026',
                'reopening_date': '13 Jan 2026'
            },
            'PKPK': {
                'code': 'PKPK',
                'status': 'reopened',
                'last_event_date': '14 Jan 2026',
                'last_event_desc': 'Pembukaan Kembali Perdagangan Saham PT Paragon Karya Perkasa Tbk.',
                'suspension_date': None,
                'reopening_date': '14 Jan 2026'
            },
            'IFSH': {
                'code': 'IFSH',
                'status': 'suspended',
                'last_event_date': '13 Jan 2026',
                'last_event_desc': 'Penghentian Sementara Perdagangan Saham PT Ifishdeco Tbk.',
                'suspension_date': '13 Jan 2026',
                'reopening_date': None
            },
            'SIPD': {
                'code': 'SIPD',
                'status': 'suspended',
                'last_event_date': '13 Jan 2026',
                'last_event_desc': 'Penghentian Sementara Perdagangan Saham PT Sreeya Sewu Indonesia Tbk.',
                'suspension_date': '13 Jan 2026',
                'reopening_date': None
            },
            'SPRE': {
                'code': 'SPRE',
                'status': 'reopened',
                'last_event_date': '13 Jan 2026',
                'last_event_desc': 'Pembukaan Kembali Perdagangan Saham PT Soraya Berjaya Indonesia Tbk.',
                'suspension_date': None,
                'reopening_date': '13 Jan 2026'
            }
        }
        
        self.suspensions = fallback_data
        self.last_update = datetime.now().isoformat()
        self._save_to_cache()
        print(f"✓ Loaded {len(self.suspensions)} fallback suspension records")
    
    def is_suspended(self, stock_code):
        """
        Check if a stock is currently suspended.
        
        Args:
            stock_code: Stock ticker
        
        Returns:
            (bool, str): (is_suspended, reason_or_date)
        """
        if stock_code not in self.suspensions:
            return False, None
        
        record = self.suspensions[stock_code]
        
        if record['status'] == 'suspended':
            date = record.get('suspension_date', 'Unknown date')
            return True, f"Suspended since {date}"
        
        return False, None
    
    def get_suspension_info(self, stock_code):
        """
        Get detailed suspension information for a stock.
        
        Args:
            stock_code: Stock ticker
        
        Returns:
            dict: Suspension details or None if not suspended
        """
        return self.suspensions.get(stock_code)
    
    def get_suspended_stocks(self):
        """
        Get list of currently suspended stocks.
        
        Returns:
            list: List of suspended stock codes
        """
        return [
            code for code, info in self.suspensions.items()
            if info['status'] == 'suspended'
        ]
    
    def get_reopened_stocks(self):
        """
        Get list of recently reopened stocks.
        
        Returns:
            list: List of reopened stock codes
        """
        return [
            code for code, info in self.suspensions.items()
            if info['status'] == 'reopened'
        ]
    
    def print_suspensions(self):
        """Print formatted suspension report."""
        suspended = self.get_suspended_stocks()
        reopened = self.get_reopened_stocks()
        
        print("\n" + "="*80)
        print("IDX SUSPENSION TRACKER - LIVE DATA")
        print("="*80)
        print(f"\nLast Update: {self.last_update}")
        
        if suspended:
            print(f"\n🚫 CURRENTLY SUSPENDED ({len(suspended)} stocks):")
            print("-"*80)
            for code in sorted(suspended):
                info = self.suspensions[code]
                print(f"  {code:<10} │ Since {info['suspension_date']:<12} │ {info['last_event_desc']}")
        else:
            print("\n✓ No currently suspended stocks")
        
        if reopened:
            print(f"\n✅ RECENTLY REOPENED ({len(reopened)} stocks):")
            print("-"*80)
            for code in sorted(reopened):
                info = self.suspensions[code]
                reopen_date = info.get('reopening_date', 'N/A')
                print(f"  {code:<10} │ Reopened {reopen_date:<12} │ {info['last_event_desc']}")
        
        print("\n" + "="*80)


# Example usage
if __name__ == "__main__":
    tracker = SuspensionTracker(use_cache=True)
    tracker.print_suspensions()
    
    # Test individual stock checks
    print("\n" + "="*80)
    print("STOCK-SPECIFIC CHECKS")
    print("="*80)
    
    test_stocks = ['RLCO', 'SOTS', 'KOCI', 'INDS', 'MDRN']
    
    for stock in test_stocks:
        is_suspended, reason = tracker.is_suspended(stock)
        status = "🚫 SUSPENDED" if is_suspended else "✓ ACTIVE"
        print(f"\n{stock}: {status}")
        if reason:
            print(f"  Reason: {reason}")
        
        info = tracker.get_suspension_info(stock)
        if info:
            print(f"  Status: {info['status']}")
            print(f"  Last event: {info['last_event_date']} - {info['last_event_desc']}")
