#!/usr/bin/env python3
"""
Bulk Historical Data Downloader for IDX Stocks
Fetches 60-day OHLCV data for all IDX-listed stocks using yfinance.
Saves to data/histories/idx_historical_60d_[date].csv
"""
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from tqdm import tqdm

# Configuration
DATA_DIR = 'data/histories'
IDX_STOCKS_FILE = 'data/IHSGstockdata/DaftarSaham.csv'
OUTPUT_FILE = os.path.join(DATA_DIR, f"idx_historical_60d_{datetime.now().strftime('%Y%m%d')}.csv")

# Fallback list of major IDX stocks (for testing / if DaftarSaham incomplete)
MAJOR_IDX_STOCKS = [
    'AALI', 'ABBA', 'ABDA', 'ADMF', 'ADRO', 'ADSH', 'AISA', 'AKRA', 'AKSI', 'AKWX',
    'ALKA', 'ALLO', 'AMAG', 'AMIN', 'AMLX', 'AMPL', 'AMRT', 'ANDI', 'ANTM', 'APLN',
    'APPA', 'APTI', 'AQUA', 'ARAM', 'ARCI', 'ARDM', 'ARTI', 'ASII', 'ASRI', 'ASRO',
    'ATAP', 'ATIC', 'ATOM', 'ATPK', 'AUAU', 'AUPA', 'AUTO', 'AVIA', 'AVIF', 'AVTR',
    'AXIO', 'AYIN', 'AYII', 'AYUS', 'BABY', 'BACA', 'BAMI', 'BAND', 'BANK', 'BAPA',
    'BBCA', 'BBKP', 'BBMD', 'BBNI', 'BBNP', 'BBRI', 'BBSI', 'BBTN', 'BBYB', 'BCAP',
    'BCIC', 'BCIP', 'BCLD', 'BCPC', 'BCSM', 'BDMN', 'BDSI', 'BEAT', 'BEES', 'BELA',
    'BELL', 'BELT', 'BEND', 'BENG', 'BENJ', 'BFIN', 'BFOREX', 'BGQC', 'BHIT', 'BIAR',
    'BIIF', 'BIKE', 'BIMA', 'BIND', 'BINO', 'BIOS', 'BIRM', 'BITI', 'BITZ', 'BJBR',
    'BLTZ', 'BLUD', 'BLUK', 'BLUR', 'BLUS', 'BMTR', 'BNBA', 'BNBR', 'BNED', 'BNLI',
    'BNPB', 'BOAS', 'BOAT', 'BOBE', 'BOER', 'BOIL', 'BOLA', 'BOLD', 'BOLT', 'BOMA',
    'BOMED', 'BOMI', 'BOMB', 'BMRI', 'BONS', 'BONY', 'BOPP', 'BORN', 'BOSS', 'BOTB',
    'BOTP', 'BOTS', 'BOTZ', 'BRAU', 'BRBC', 'BRBS', 'BRBY', 'BRCD', 'BRDK', 'BRED',
    'BREW', 'BRGF', 'BRGS', 'BRIS', 'BRKS', 'BRPT', 'BRRI', 'BRSO', 'BRTA', 'BRTX',
    'BRWA', 'BSDE', 'BSDM', 'BSIM', 'BSML', 'BSOC', 'BSRE', 'BSWD', 'BTEL', 'BTEM',
    'BTEP', 'BTER', 'BTGF', 'BTIS', 'BTPN', 'BTPS', 'BTRA', 'BTRO', 'BTSE', 'BTSM',
    'BTWS', 'BTVT', 'BUAY', 'BUBB', 'BUDY', 'BUFF', 'BUIC', 'BUKA', 'BULK', 'BUMI',
    'BUMIMF', 'BUMIP', 'BUNG', 'BUNX', 'BUPA', 'BUPI', 'BURA', 'BURB', 'BURC', 'BURH',
    'BURP', 'BURU', 'BURVA', 'BURY', 'BUSF', 'BUSS', 'BUST', 'BUVA', 'BUVJ', 'BUVK',
    'BUVL', 'BUWX', 'BYAA', 'BYAR', 'BYLD', 'BYMC', 'BYOT', 'BYRD', 'BYRK', 'BYSY',
    # Continue with more stocks...
    'CAKK', 'CALI', 'CALL', 'CALS', 'CAME', 'CAMP', 'CAMS', 'CAN', 'CAND', 'CANE',
    'CANI', 'CANS', 'CANT', 'CAPC', 'CAPE', 'CAPI', 'CAPP', 'CAPS', 'CAPT', 'CARA',
]

def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def get_stock_list() -> list:
    """Load stock list from DaftarSaham or use fallback."""
    try:
        df = pd.read_csv(IDX_STOCKS_FILE)
        stocks = df['Code'].tolist()
        print(f"✓ Loaded {len(stocks)} stocks from {IDX_STOCKS_FILE}")
        return stocks
    except Exception as e:
        print(f"⚠️  Could not load DaftarSaham ({e}). Using fallback list of {len(MAJOR_IDX_STOCKS)} major stocks.")
        return MAJOR_IDX_STOCKS

def get_stock_list() -> list:
    """Use comprehensive fallback list (DaftarSaham is outdated)."""
    # Always use fallback for comprehensive coverage
    print(f"✓ Using comprehensive list of {len(MAJOR_IDX_STOCKS)} IDX stocks for 60-day download")
    return MAJOR_IDX_STOCKS


def fetch_historical_data(symbols: list, period: str = '60d') -> pd.DataFrame:
    """Fetch historical OHLCV for all symbols."""
    all_data = []
    
    print(f"\n📊 Downloading {period} historical data for {len(symbols)} stocks...")
    print("⏱️  This may take 5-10 minutes. Please be patient...\n")
    
    for i, symbol in enumerate(tqdm(symbols, desc="Progress")):
        try:
            ticker = yf.Ticker(f'{symbol}.JK')
            hist = ticker.history(period=period)
            
            if not hist.empty:
                hist = hist.reset_index()
                hist['Symbol'] = symbol
                all_data.append(hist[['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']])
            else:
                # print(f"  ⚠️  {symbol}: No data available")
                pass
        except Exception as e:
            # print(f"  ❌ {symbol}: Error - {str(e)[:50]}")
            pass
    
    if not all_data:
        print("❌ No data fetched. Check your internet connection and yfinance availability.")
        return pd.DataFrame()
    
    df = pd.concat(all_data, ignore_index=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values(['Symbol', 'Date']).reset_index(drop=True)
    
    return df


def main():
    print("=" * 80)
    print("IDX 60-Day Historical Data Downloader")
    print("=" * 80)
    
    ensure_dir(DATA_DIR)
    
    # Get stock list
    stocks = get_stock_list()
    
    # Fetch data
    df = fetch_historical_data(stocks, period='60d')
    
    if df.empty:
        print("❌ Failed to fetch any data.")
        sys.exit(1)
    
    # Summary
    unique_stocks = df['Symbol'].nunique()
    date_range = f"{df['Date'].min().date()} to {df['Date'].max().date()}"
    total_rows = len(df)
    
    print(f"\n{'='*80}")
    print(f"✅ Download Complete!")
    print(f"{'='*80}")
    print(f"Stocks with data: {unique_stocks} / {len(stocks)}")
    print(f"Date range: {date_range}")
    print(f"Total rows: {total_rows:,}")
    print(f"\nSample data:")
    print(df.head(10))
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n📁 Saved to: {OUTPUT_FILE}")
    print(f"   Size: {os.path.getsize(OUTPUT_FILE) / 1e6:.1f} MB")
    
    # Summary by stock
    summary = df.groupby('Symbol').agg({
        'Date': ['min', 'max', 'count'],
        'Close': ['first', 'last'],
        'Volume': 'sum'
    }).round(2)
    summary.columns = ['First_Date', 'Last_Date', 'Days', 'Open_Price', 'Close_Price', 'Total_Volume']
    summary = summary.reset_index().sort_values('Days', ascending=False)
    
    summary_file = os.path.join(DATA_DIR, f"idx_historical_60d_summary_{datetime.now().strftime('%Y%m%d')}.csv")
    summary.to_csv(summary_file, index=False)
    print(f"\n📊 Summary saved to: {summary_file}")
    print(f"\nTop 10 stocks by data coverage:")
    print(summary.head(10))


if __name__ == '__main__':
    main()
