#!/usr/bin/env python3
"""
Quick Historical Data Loader
=============================
Rapidly loads and displays all available historical stock data.
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_DIRS = {
    'excel': BASE_DIR / 'data' / 'histories',
    'csv': BASE_DIR / 'data' / 'IHSGstockdata' / 'ringkasan_saham',
    'alerts': BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts'
}

class QuickLoader:
    def __init__(self):
        self.data = {}
        self.files = {}
    
    def load_all(self):
        """Load all available data."""
        print("\n" + "="*70)
        print("⚡ QUICK DATA LOADER")
        print("="*70)
        
        self._load_excel()
        self._load_csv()
        self._summarize()
    
    def _load_excel(self):
        """Load Excel files."""
        print("\n📊 Loading Excel files...")
        excel_dir = DATA_DIRS['excel']
        
        if not os.path.exists(excel_dir):
            print(f"   ❌ Directory not found: {excel_dir}")
            return
        
        count = 0
        for filename in sorted(os.listdir(excel_dir)):
            if filename.endswith('.xlsx'):
                try:
                    path = os.path.join(excel_dir, filename)
                    df = pd.read_excel(path)
                    self.data[filename] = df
                    count += 1
                except Exception as e:
                    print(f"   ⚠️  Error loading {filename}: {e}")
        
        print(f"   ✅ Loaded {count} Excel files")
    
    def _load_csv(self):
        """Load CSV files."""
        print("\n📊 Loading CSV files...")
        csv_dir = DATA_DIRS['csv']
        
        if not os.path.exists(csv_dir):
            print(f"   ❌ Directory not found: {csv_dir}")
            return
        
        count = 0
        for filename in sorted(os.listdir(csv_dir)):
            if filename.endswith('.csv'):
                try:
                    path = os.path.join(csv_dir, filename)
                    df = pd.read_csv(path)
                    self.data[filename] = df
                    count += 1
                except Exception as e:
                    print(f"   ⚠️  Error loading {filename}: {e}")
        
        print(f"   ✅ Loaded {count} CSV files")
    
    def _summarize(self):
        """Print summary of loaded data."""
        print("\n" + "="*70)
        print("📈 DATA SUMMARY")
        print("="*70)
        
        if not self.data:
            print("❌ No data loaded")
            return
        
        total_rows = 0
        print(f"\n📂 Files loaded: {len(self.data)}\n")
        
        for filename, df in sorted(self.data.items()):
            base_dir = DATA_DIRS['excel'] if filename.endswith('.xlsx') else DATA_DIRS['csv']
            size_mb = os.path.getsize(base_dir / filename) / (1024*1024)
            rows = len(df)
            cols = len(df.columns)
            total_rows += rows
            
            # Extract date if possible
            date_str = filename.split('-')[-1].replace('.xlsx', '').replace('.csv', '')
            date_info = f"[{date_str}]" if len(date_str) == 8 and date_str.isdigit() else ""
            
            print(f"✓ {filename:<50} {rows:>6} rows | {cols:>3} cols | {size_mb:>6.2f}MB {date_info}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total files: {len(self.data)}")
        print(f"   Total rows:  {total_rows:,}")
        
        # Try to estimate date range
        dates = []
        for filename in self.data.keys():
            date_str = filename.split('-')[-1].replace('.xlsx', '').replace('.csv', '')
            if len(date_str) == 8 and date_str.isdigit():
                try:
                    d = datetime.strptime(date_str, "%Y%m%d").date()
                    dates.append(d)
                except:
                    pass
        
        if dates:
            dates_sorted = sorted(dates)
            print(f"   Date range:  {dates_sorted[0]} to {dates_sorted[-1]}")
            print(f"   Days span:   {(dates_sorted[-1] - dates_sorted[0]).days} days")
        
        print("\n" + "="*70)
        print("✅ Ready for analysis!")
        print("="*70 + "\n")
    
    def get_dataframe(self, key=None):
        """Get a specific dataframe or first available."""
        if key:
            return self.data.get(key)
        if self.data:
            return list(self.data.values())[0]
        return None
    
    def consolidate(self, output_file='consolidated_all.csv'):
        """Consolidate all data into one file."""
        if not self.data:
            print("❌ No data to consolidate")
            return
        
        print(f"\n💾 Consolidating to {output_file}...")
        
        all_dfs = []
        for filename, df in self.data.items():
            df_copy = df.copy()
            df_copy['_source'] = filename
            all_dfs.append(df_copy)
        
        consolidated = pd.concat(all_dfs, ignore_index=True)
        consolidated.to_csv(output_file, index=False)
        
        print(f"✅ Saved {len(consolidated)} rows to {output_file}")
        print(f"   File size: {os.path.getsize(output_file) / (1024*1024):.2f} MB")


if __name__ == "__main__":
    loader = QuickLoader()
    loader.load_all()
    
    # Optional: consolidate
    print("\n🔄 Would you like to consolidate? (y/n)")
    response = input("> ").strip().lower()
    if response == 'y':
        loader.consolidate()
