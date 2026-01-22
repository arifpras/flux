"""
Historical Stock Data Retriever
Intelligently fetch and consolidate data from previous days.
Supports: Excel files, CSV files, and real-time scraping for missing dates.
"""
import os
import sys
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Configuration
DATA_DIR = os.path.join("data", "IHSGstockdata")
RINGKASAN_SAHAM_DIR = os.path.join(DATA_DIR, "ringkasan_saham")
HISTORIES_DIR = os.path.join("data", "histories")
ALERTS_DIR = os.path.join(DATA_DIR, "alerts")

# Indonesian holidays
INDONESIAN_HOLIDAYS = [
    datetime(2025, 1, 1),
    datetime(2025, 2, 19),
    datetime(2025, 3, 29),
    datetime(2025, 4, 18),
    datetime(2025, 5, 1),
    datetime(2025, 5, 23),
    datetime(2025, 6, 1),
    datetime(2025, 6, 2),
    datetime(2025, 6, 16),
    datetime(2025, 7, 7),
    datetime(2025, 8, 17),
    datetime(2025, 8, 28),
    datetime(2025, 9, 8),
    datetime(2025, 12, 25),
    datetime(2025, 12, 26),
    datetime(2026, 1, 1),
    datetime(2026, 2, 8),
    datetime(2026, 3, 20),
]


def is_business_day(check_date: date) -> bool:
    """Check if date is an Indonesian business day."""
    # Check weekends
    if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Check holidays
    check_datetime = datetime(check_date.year, check_date.month, check_date.day)
    if check_datetime in INDONESIAN_HOLIDAYS:
        return False
    
    return True


def get_previous_business_days(num_days: int = 30) -> List[date]:
    """Get list of previous business days."""
    business_days = []
    current = date.today() - timedelta(days=1)  # Start from yesterday
    
    while len(business_days) < num_days:
        if is_business_day(current):
            business_days.append(current)
        current -= timedelta(days=1)
    
    return sorted(business_days)


class HistoricalDataCollector:
    """Collector for historical stock data from multiple sources."""
    
    def __init__(self):
        self.data_sources = {}
        self.collected_data = {}
        self.missing_dates = []
        self.excel_files = []
        self.csv_files = []
        self.scan_data = {}
        
    def scan_all_sources(self) -> Dict[str, any]:
        """Scan all available data sources."""
        print("\n" + "=" * 80)
        print("🔍 SCANNING DATA SOURCES")
        print("=" * 80)
        
        # Scan Excel files in histories directory
        self._scan_excel_files()
        
        # Scan CSV files in ringkasan_saham directory
        self._scan_csv_files()
        
        # Scan alert/scan data
        self._scan_alerts()
        
        # Print summary
        self._print_source_summary()
        
        return {
            "excel_files": self.excel_files,
            "csv_files": self.csv_files,
            "scan_data": self.scan_data,
        }
    
    def _scan_excel_files(self):
        """Scan Excel files in histories directory."""
        print("\n📊 Excel Files in histories/:")
        print("-" * 60)
        
        if not os.path.exists(HISTORIES_DIR):
            print("   ℹ️  Directory not found")
            return
        
        excel_files = sorted([f for f in os.listdir(HISTORIES_DIR) if f.endswith('.xlsx')])
        
        if not excel_files:
            print("   ℹ️  No Excel files found")
            return
        
        for filename in excel_files:
            filepath = os.path.join(HISTORIES_DIR, filename)
            try:
                # Extract date from filename (e.g., "Ringkasan Saham-20251201.xlsx")
                date_str = filename.split('-')[-1].replace('.xlsx', '')
                
                # Try to parse the date
                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                except:
                    file_date = None
                
                # Get file size
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                # Get row count
                df = pd.read_excel(filepath)
                row_count = len(df)
                
                self.excel_files.append({
                    "filename": filename,
                    "date": file_date,
                    "date_str": date_str,
                    "path": filepath,
                    "rows": row_count,
                    "size_mb": size_mb,
                })
                
                print(f"   ✅ {filename:45} | {file_date} | {row_count:5} rows | {size_mb:.2f} MB")
                
            except Exception as e:
                print(f"   ⚠️  {filename:45} | Error: {str(e)[:30]}")
        
        print(f"\n   📈 Total: {len(self.excel_files)} files")
    
    def _scan_csv_files(self):
        """Scan CSV files in ringkasan_saham directory."""
        print("\n📊 CSV Files in data/IHSGstockdata/ringkasan_saham/:")
        print("-" * 60)
        
        if not os.path.exists(RINGKASAN_SAHAM_DIR):
            print("   ℹ️  Directory not found")
            return
        
        csv_files = sorted([f for f in os.listdir(RINGKASAN_SAHAM_DIR) if f.endswith('.csv')])
        
        if not csv_files:
            print("   ℹ️  No CSV files found")
            return
        
        for filename in csv_files:
            filepath = os.path.join(RINGKASAN_SAHAM_DIR, filename)
            try:
                # Extract date from filename (e.g., "ringkasan_20260116.csv")
                date_str = filename.split('_')[-1].replace('.csv', '')
                
                # Try to parse the date
                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d").date()
                except:
                    file_date = None
                
                # Get file size
                size_kb = os.path.getsize(filepath) / 1024
                
                # Get row count
                df = pd.read_csv(filepath)
                row_count = len(df)
                
                self.csv_files.append({
                    "filename": filename,
                    "date": file_date,
                    "date_str": date_str,
                    "path": filepath,
                    "rows": row_count,
                    "size_kb": size_kb,
                })
                
                print(f"   ✅ {filename:40} | {file_date} | {row_count:5} rows | {size_kb:.2f} KB")
                
            except Exception as e:
                print(f"   ⚠️  {filename:40} | Error: {str(e)[:30]}")
        
        print(f"\n   📈 Total: {len(self.csv_files)} files")
    
    def _scan_alerts(self):
        """Scan alert/scan data."""
        print("\n📊 Alert Scan Files in data/IHSGstockdata/alerts/:")
        print("-" * 60)
        
        if not os.path.exists(ALERTS_DIR):
            print("   ℹ️  Directory not found")
            return
        
        json_files = sorted([f for f in os.listdir(ALERTS_DIR) if f.endswith('.json')])
        
        if not json_files:
            print("   ℹ️  No JSON alert files found")
            return
        
        for filename in json_files:
            filepath = os.path.join(ALERTS_DIR, filename)
            try:
                # Extract date from filename (e.g., "scan_2026-01-15.json")
                date_str = filename.split('_')[-1].replace('.json', '')
                
                # Try to parse the date
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except:
                    file_date = None
                
                # Get file size
                size_kb = os.path.getsize(filepath) / 1024
                
                # Read JSON to get alert count
                with open(filepath) as f:
                    data = json.load(f)
                    alert_count = len(data) if isinstance(data, list) else 1
                
                self.scan_data[file_date] = {
                    "filename": filename,
                    "path": filepath,
                    "alerts": alert_count,
                    "size_kb": size_kb,
                }
                
                print(f"   ✅ {filename:40} | {file_date} | {alert_count:3} alerts | {size_kb:.2f} KB")
                
            except Exception as e:
                print(f"   ⚠️  {filename:40} | Error: {str(e)[:30]}")
        
        print(f"\n   📈 Total: {len(self.scan_data)} files")
    
    def _print_source_summary(self):
        """Print summary of all data sources."""
        print("\n" + "=" * 80)
        print("📊 DATA SOURCE SUMMARY")
        print("=" * 80)
        
        # Extract unique dates
        excel_dates = set(f["date"] for f in self.excel_files if f["date"])
        csv_dates = set(f["date"] for f in self.csv_files if f["date"])
        alert_dates = set(self.scan_data.keys())
        all_dates = excel_dates | csv_dates | alert_dates
        
        print(f"\n📅 Date Coverage:")
        print(f"   Excel files:  {len(excel_dates)} unique dates")
        print(f"   CSV files:    {len(csv_dates)} unique dates")
        print(f"   Alert scans:  {len(alert_dates)} unique dates")
        print(f"   Total:        {len(all_dates)} unique dates")
        
        if all_dates:
            date_list = sorted(all_dates)
            print(f"\n📅 Date Range:")
            print(f"   From: {date_list[0]}")
            print(f"   To:   {date_list[-1]}")
            
            # Find gaps
            gaps = []
            for i in range(len(date_list) - 1):
                days_diff = (date_list[i + 1] - date_list[i]).days
                if days_diff > 1:
                    # Check if gap is due to weekends/holidays
                    missing_dates = []
                    current = date_list[i] + timedelta(days=1)
                    while current < date_list[i + 1]:
                        if is_business_day(current):
                            missing_dates.append(current)
                        current += timedelta(days=1)
                    
                    if missing_dates:
                        gaps.append({
                            "from": date_list[i],
                            "to": date_list[i + 1],
                            "missing_business_days": missing_dates
                        })
            
            if gaps:
                print(f"\n⚠️  Data Gaps Detected: {len(gaps)} gap(s)")
                for gap in gaps[:5]:  # Show first 5 gaps
                    print(f"   • {gap['from']} to {gap['to']}: {len(gap['missing_business_days'])} business days missing")
    
    def get_consolidated_data(self, date: date) -> Optional[pd.DataFrame]:
        """Get consolidated data for a specific date from available sources."""
        
        # Try Excel first (highest priority)
        for file_info in self.excel_files:
            if file_info["date"] == date:
                try:
                    return pd.read_excel(file_info["path"])
                except:
                    pass
        
        # Try CSV second
        for file_info in self.csv_files:
            if file_info["date"] == date:
                try:
                    return pd.read_csv(file_info["path"])
                except:
                    pass
        
        return None
    
    def get_date_range(self, start_date: date, end_date: date, include_weekends: bool = False) -> Dict[date, pd.DataFrame]:
        """Get consolidated data for a date range."""
        print("\n" + "=" * 80)
        print("📥 RETRIEVING DATA FOR DATE RANGE")
        print("=" * 80)
        print(f"\n📅 From: {start_date} to {end_date}")
        
        data_dict = {}
        current = start_date
        business_days_count = 0
        found_count = 0
        
        with tqdm(total=(end_date - start_date).days + 1, desc="Processing dates") as pbar:
            while current <= end_date:
                pbar.update(1)
                
                if include_weekends or is_business_day(current):
                    business_days_count += 1
                    df = self.get_consolidated_data(current)
                    
                    if df is not None:
                        data_dict[current] = df
                        found_count += 1
                
                current += timedelta(days=1)
        
        print(f"\n✅ Retrieved: {found_count}/{business_days_count} business days")
        
        return data_dict


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("🚀 HISTORICAL STOCK DATA RETRIEVER")
    print("=" * 80)
    
    collector = HistoricalDataCollector()
    
    # Scan all sources
    sources = collector.scan_all_sources()
    
    # Get data for last 30 days
    print("\n" + "=" * 80)
    print("📥 RETRIEVING DATA FOR LAST 30 DAYS")
    print("=" * 80)
    
    last_30_days = get_previous_business_days(30)
    print(f"\n📅 Business days to retrieve: {len(last_30_days)}")
    print(f"   From: {last_30_days[0]}")
    print(f"   To:   {last_30_days[-1]}")
    
    # Retrieve data
    data_range = collector.get_date_range(last_30_days[0], last_30_days[-1])
    
    # Print detailed results
    print("\n" + "=" * 80)
    print("📊 RETRIEVAL RESULTS")
    print("=" * 80)
    
    if data_range:
        print(f"\n✅ Successfully retrieved data for {len(data_range)} dates\n")
        
        for dt in sorted(data_range.keys()):
            df = data_range[dt]
            print(f"   {dt}: {len(df):5} stocks | Cols: {len(df.columns)}")
        
        # Get statistics
        print("\n" + "=" * 80)
        print("📈 DATA STATISTICS")
        print("=" * 80)
        
        total_stocks = {}
        for dt, df in data_range.items():
            for stock in df.get('Kode Saham', df.get('Ticker', df.get('Stock', []))):
                total_stocks[stock] = total_stocks.get(stock, 0) + 1
        
        print(f"\n📊 Top Stocks by Data Points:")
        sorted_stocks = sorted(total_stocks.items(), key=lambda x: x[1], reverse=True)
        for stock, count in sorted_stocks[:10]:
            print(f"   {stock}: {count} days")
        
        print(f"\n📈 Average Rows per Day: {sum(len(df) for df in data_range.values()) / len(data_range):.1f}")
        
        # Save consolidated data
        print("\n" + "=" * 80)
        print("💾 SAVING CONSOLIDATED DATA")
        print("=" * 80)
        
        output_file = "historical_data_last30days.csv"
        all_data = []
        
        for dt, df in sorted(data_range.items()):
            df_copy = df.copy()
            df_copy['Date'] = dt
            all_data.append(df_copy)
        
        if all_data:
            consolidated = pd.concat(all_data, ignore_index=True)
            consolidated.to_csv(output_file, index=False)
            print(f"\n✅ Saved consolidated data to: {output_file}")
            print(f"   Total rows: {len(consolidated)}")
            print(f"   Total columns: {len(consolidated.columns)}")
    else:
        print("\n❌ No data retrieved. Check data sources.")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
