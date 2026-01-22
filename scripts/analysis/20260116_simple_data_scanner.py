"""Simple script to scan and retrieve historical stock data."""
import os
import pandas as pd
from datetime import datetime, date
from pathlib import Path

DATA_DIR = os.path.join("data", "IHSGstockdata")
RINGKASAN_SAHAM_DIR = os.path.join(DATA_DIR, "ringkasan_saham")
HISTORIES_DIR = os.path.join("data", "histories")
ALERTS_DIR = os.path.join(DATA_DIR, "alerts")

def scan_data():
    print("\n" + "="*80)
    print("📊 HISTORICAL DATA SCANNER")
    print("="*80)
    
    # Scan Excel files
    print("\n✅ EXCEL FILES (histories/):")
    excel_files = []
    if os.path.exists(HISTORIES_DIR):
        for f in sorted(os.listdir(HISTORIES_DIR)):
            if f.endswith('.xlsx'):
                path = os.path.join(HISTORIES_DIR, f)
                try:
                    df = pd.read_excel(path)
                    excel_files.append((f, len(df)))
                    print(f"  • {f:<50} {len(df):>5} rows")
                except Exception as e:
                    print(f"  • {f:<50} Error: {e}")
    
    # Scan CSV files
    print("\n✅ CSV FILES (data/IHSGstockdata/ringkasan_saham/):")
    csv_files = []
    if os.path.exists(RINGKASAN_SAHAM_DIR):
        for f in sorted(os.listdir(RINGKASAN_SAHAM_DIR)):
            if f.endswith('.csv'):
                path = os.path.join(RINGKASAN_SAHAM_DIR, f)
                try:
                    df = pd.read_csv(path)
                    csv_files.append((f, len(df)))
                    print(f"  • {f:<50} {len(df):>5} rows")
                except Exception as e:
                    print(f"  • {f:<50} Error: {e}")
    
    # Scan Alert files
    print("\n✅ ALERT SCANS (data/IHSGstockdata/alerts/):")
    if os.path.exists(ALERTS_DIR):
        for f in sorted(os.listdir(ALERTS_DIR)):
            if f.endswith('.json'):
                path = os.path.join(ALERTS_DIR, f)
                size = os.path.getsize(path) / 1024
                print(f"  • {f:<50} {size:>8.2f} KB")
    
    print("\n" + "="*80)
    print(f"📈 SUMMARY:")
    print(f"  Excel files:   {len(excel_files)} files")
    print(f"  CSV files:     {len(csv_files)} files")
    print("="*80 + "\n")
    
    return excel_files, csv_files

if __name__ == "__main__":
    excel, csv = scan_data()
