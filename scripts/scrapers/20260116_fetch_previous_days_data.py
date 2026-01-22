#!/usr/bin/env python3
"""
Advanced Historical Data Retriever for Stock Scraper
=====================================================

This script retrieves and consolidates stock data from previous days.
Supports multiple data sources: Excel files, CSV files, and JSON alerts.

Features:
- Scans all available historical data sources
- Consolidates data from multiple formats
- Detects data gaps (weekends/holidays)
- Generates statistical summaries
- Exports consolidated datasets
"""

import os
import json
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration
DATA_DIR = os.path.join("data", "IHSGstockdata")
RINGKASAN_SAHAM_DIR = os.path.join(DATA_DIR, "ringkasan_saham")
HISTORIES_DIR = os.path.join("data", "histories")
ALERTS_DIR = os.path.join(DATA_DIR, "alerts")

# Indonesian holidays (2025-2026)
INDONESIAN_HOLIDAYS = {
    date(2025, 1, 1),   # New Year
    date(2025, 2, 19),  # Isra & Mi'raj
    date(2025, 3, 29),  # Nyepi
    date(2025, 4, 18),  # Good Friday
    date(2025, 5, 1),   # Labour Day
    date(2025, 5, 23),  # Vesak Day
    date(2025, 6, 1),   # Eid al-Fitr
    date(2025, 6, 2),   # Eid al-Fitr
    date(2025, 6, 16),  # Eid al-Adha
    date(2025, 7, 7),   # Islamic New Year
    date(2025, 8, 17),  # Independence Day
    date(2025, 8, 28),  # Mawlid
    date(2025, 9, 8),   # Ascension of Jesus
    date(2025, 12, 25), # Christmas
    date(2025, 12, 26), # Joint Leave
    date(2026, 1, 1),   # New Year
    date(2026, 2, 8),   # Isra & Mi'raj
    date(2026, 3, 20),  # Nyepi
}


class DataSource:
    """Represents a single data source file."""
    
    def __init__(self, filename: str, filepath: str, source_type: str, date_obj: Optional[date] = None):
        self.filename = filename
        self.filepath = filepath
        self.source_type = source_type  # 'excel', 'csv', 'json'
        self.date = date_obj
        self.size = os.path.getsize(filepath)
        self.data = None
    
    def load(self) -> Optional[pd.DataFrame]:
        """Load data from source."""
        try:
            if self.source_type == 'excel':
                self.data = pd.read_excel(self.filepath)
            elif self.source_type == 'csv':
                self.data = pd.read_csv(self.filepath)
            elif self.source_type == 'json':
                with open(self.filepath) as f:
                    self.data = json.load(f)
            return self.data
        except Exception as e:
            print(f"  ⚠️  Failed to load {self.filename}: {e}")
            return None
    
    def __repr__(self) -> str:
        size_str = f"{self.size/1024:.1f}KB" if self.size < 1024*1024 else f"{self.size/(1024*1024):.1f}MB"
        return f"{self.filename:<50} | {str(self.date):<12} | {size_str:>10}"


class HistoricalDataFetcher:
    """Main fetcher for historical stock data."""
    
    def __init__(self):
        self.excel_sources: List[DataSource] = []
        self.csv_sources: List[DataSource] = []
        self.json_sources: List[DataSource] = []
        self.all_dates: set = set()
    
    def scan_sources(self) -> None:
        """Scan all data sources."""
        print("\n" + "="*90)
        print("🔍 SCANNING DATA SOURCES")
        print("="*90)
        
        self._scan_excel()
        self._scan_csv()
        self._scan_json()
        self._print_coverage()
    
    def _scan_excel(self) -> None:
        """Scan Excel files in histories directory."""
        print("\n📊 EXCEL FILES (histories/):")
        print("-"*90)
        
        if not os.path.exists(HISTORIES_DIR):
            print("   [Directory not found]")
            return
        
        for filename in sorted(os.listdir(HISTORIES_DIR)):
            if not filename.endswith('.xlsx'):
                continue
            
            filepath = os.path.join(HISTORIES_DIR, filename)
            date_obj = self._extract_date_from_filename(filename)
            
            if date_obj:
                self.all_dates.add(date_obj)
            
            source = DataSource(filename, filepath, 'excel', date_obj)
            self.excel_sources.append(source)
            print(f"   ✅ {source}")
    
    def _scan_csv(self) -> None:
        """Scan CSV files in ringkasan_saham directory."""
        print("\n📊 CSV FILES (data/IHSGstockdata/ringkasan_saham/):")
        print("-"*90)
        
        if not os.path.exists(RINGKASAN_SAHAM_DIR):
            print("   [Directory not found]")
            return
        
        for filename in sorted(os.listdir(RINGKASAN_SAHAM_DIR)):
            if not filename.endswith('.csv'):
                continue
            
            filepath = os.path.join(RINGKASAN_SAHAM_DIR, filename)
            date_obj = self._extract_date_from_filename(filename)
            
            if date_obj:
                self.all_dates.add(date_obj)
            
            source = DataSource(filename, filepath, 'csv', date_obj)
            self.csv_sources.append(source)
            print(f"   ✅ {source}")
    
    def _scan_json(self) -> None:
        """Scan JSON alert files."""
        print("\n📊 JSON ALERT SCANS (data/IHSGstockdata/alerts/):")
        print("-"*90)
        
        if not os.path.exists(ALERTS_DIR):
            print("   [Directory not found]")
            return
        
        for filename in sorted(os.listdir(ALERTS_DIR)):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(ALERTS_DIR, filename)
            date_obj = self._extract_date_from_filename(filename)
            
            if date_obj:
                self.all_dates.add(date_obj)
            
            source = DataSource(filename, filepath, 'json', date_obj)
            self.json_sources.append(source)
            print(f"   ✅ {source}")
    
    def _extract_date_from_filename(self, filename: str) -> Optional[date]:
        """Extract date from filename."""
        # Try YYYYMMDD format
        for i in range(len(filename) - 7):
            substr = filename[i:i+8]
            if substr.isdigit():
                try:
                    return datetime.strptime(substr, "%Y%m%d").date()
                except:
                    pass
        
        # Try YYYY-MM-DD format
        for i in range(len(filename) - 9):
            substr = filename[i:i+10]
            if substr[4] == '-' and substr[7] == '-':
                try:
                    return datetime.strptime(substr, "%Y-%m-%d").date()
                except:
                    pass
        
        return None
    
    def _print_coverage(self) -> None:
        """Print data coverage summary."""
        if not self.all_dates:
            print("\n⚠️  No data found")
            return
        
        print("\n" + "="*90)
        print("📈 DATA COVERAGE")
        print("="*90)
        
        sorted_dates = sorted(self.all_dates)
        print(f"\n📅 Date Range: {sorted_dates[0]} to {sorted_dates[-1]}")
        print(f"   Total unique dates: {len(sorted_dates)}")
        print(f"   Excel sources: {len(self.excel_sources)}")
        print(f"   CSV sources: {len(self.csv_sources)}")
        print(f"   JSON sources: {len(self.json_sources)}")
        
        # Detect data gaps
        self._detect_gaps(sorted_dates)
    
    def _detect_gaps(self, dates: List[date]) -> None:
        """Detect gaps in data coverage."""
        gaps = []
        current = dates[0]
        
        while current <= dates[-1]:
            if current not in self.all_dates and self._is_business_day(current):
                gap_start = current
                while current in self.all_dates or not self._is_business_day(current):
                    if current in self.all_dates:
                        break
                    current += timedelta(days=1)
                    if current > dates[-1]:
                        break
                
                if gap_start < current and current in self.all_dates:
                    gaps.append((gap_start, current - timedelta(days=1)))
            
            current += timedelta(days=1)
        
        if gaps:
            print(f"\n⚠️  Data Gaps Found: {len(gaps)} gap(s)")
            for start, end in gaps[:5]:
                print(f"   • {start} to {end}")
    
    @staticmethod
    def _is_business_day(check_date: date) -> bool:
        """Check if date is a business day."""
        if check_date.weekday() >= 5:  # Weekend
            return False
        if check_date in INDONESIAN_HOLIDAYS:
            return False
        return True
    
    def get_date_data(self, target_date: date) -> Dict[str, any]:
        """Get all available data for a specific date."""
        result = {
            'date': target_date,
            'excel': None,
            'csv': None,
            'json': None,
            'status': '⚠️  Not found'
        }
        
        # Check Excel
        for source in self.excel_sources:
            if source.date == target_date:
                data = source.load()
                result['excel'] = data
                break
        
        # Check CSV
        for source in self.csv_sources:
            if source.date == target_date:
                data = source.load()
                result['csv'] = data
                break
        
        # Check JSON
        for source in self.json_sources:
            if source.date == target_date:
                data = source.load()
                result['json'] = data
                break
        
        # Determine status
        if result['excel'] is not None or result['csv'] is not None:
            result['status'] = '✅ Complete'
        elif result['json'] is not None:
            result['status'] = '⚠️  Partial (alerts only)'
        
        return result
    
    def export_consolidated(self, output_file: str = "consolidated_history.csv") -> None:
        """Export all available data to a single CSV."""
        print("\n" + "="*90)
        print(f"💾 EXPORTING CONSOLIDATED DATA")
        print("="*90)
        
        all_dfs = []
        
        print("\n📥 Loading data...")
        for source in self.excel_sources + self.csv_sources:
            if source.date:
                df = source.load()
                if df is not None and isinstance(df, pd.DataFrame):
                    df['_source_date'] = source.date
                    df['_source_file'] = source.filename
                    all_dfs.append(df)
        
        if not all_dfs:
            print("   ❌ No data to export")
            return
        
        # Concatenate all data
        consolidated = pd.concat(all_dfs, ignore_index=True)
        consolidated.to_csv(output_file, index=False)
        
        print(f"✅ Saved to: {output_file}")
        print(f"   Total rows: {len(consolidated):,}")
        print(f"   Total columns: {len(consolidated.columns)}")
        print(f"   Unique dates: {consolidated['_source_date'].nunique()}")
        print(f"   File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")
    
    def print_summary(self) -> None:
        """Print a comprehensive summary."""
        print("\n" + "="*90)
        print("📊 COMPLETE DATA SUMMARY")
        print("="*90)
        
        if not self.all_dates:
            print("\n❌ No data sources found")
            return
        
        sorted_dates = sorted(self.all_dates)
        print(f"\n📅 Date Coverage:")
        print(f"   From: {sorted_dates[0]}")
        print(f"   To:   {sorted_dates[-1]}")
        print(f"   Total dates: {len(sorted_dates)}")
        
        print(f"\n📦 Data Sources:")
        print(f"   Excel files: {len(self.excel_sources)}")
        print(f"   CSV files: {len(self.csv_sources)}")
        print(f"   JSON files: {len(self.json_sources)}")
        
        # Sample data overview
        print(f"\n📋 Recent Data (Last 5 available dates):")
        for target_date in sorted_dates[-5:]:
            data_dict = self.get_date_data(target_date)
            status = data_dict['status']
            excel_info = f"{len(data_dict['excel'])} rows" if isinstance(data_dict['excel'], pd.DataFrame) else "N/A"
            csv_info = f"{len(data_dict['csv'])} rows" if isinstance(data_dict['csv'], pd.DataFrame) else "N/A"
            print(f"   {target_date}: {status} | Excel: {excel_info:<15} CSV: {csv_info}")
        
        print("\n" + "="*90 + "\n")


def main():
    """Main entry point."""
    print("\n")
    print("╔" + "="*88 + "╗")
    print("║" + "  HISTORICAL STOCK DATA FETCHER".center(88) + "║")
    print("║" + "  Retrieves & consolidates data from previous days".center(88) + "║")
    print("╚" + "="*88 + "╝")
    
    fetcher = HistoricalDataFetcher()
    
    # Scan all sources
    fetcher.scan_sources()
    
    # Print summary
    fetcher.print_summary()
    
    # Export consolidated data
    fetcher.export_consolidated("consolidated_stock_history.csv")


if __name__ == "__main__":
    main()
