"""
Indonesian Stock Exchange (IDX) Data Scraper - yfinance Edition
Uses yfinance for reliable real-time IDX stock data (no Selenium needed)
"""
import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, Tuple, List

import pandas as pd
import yfinance as yf
from tqdm import tqdm

# Configuration
pd.options.mode.chained_assignment = None
DATA_DIR = os.path.join("data", "IHSGstockdata")
MINUTES_DATA_DIR = os.path.join(DATA_DIR, "minutesdata")
MINUTES_DIR = os.path.join(DATA_DIR, "minutes")
STOCK_LIST_FILE = os.path.join(DATA_DIR, "DaftarSaham.csv")

# List of major IDX stocks (verified available on yfinance)
IDX_STOCKS = {
    "BBRI": {"name": "Bank Rakyat Indonesia", "sector": "Banking"},
    "BBCA": {"name": "Bank Central Asia", "sector": "Banking"},
    "BMRI": {"name": "Bank Mandiri", "sector": "Banking"},
    "AALI": {"name": "Astra Agro Lestari", "sector": "Plantation"},
    "UNVR": {"name": "Unilever Indonesia", "sector": "Consumer"},
    "INDF": {"name": "Indofood Sukses Makmur", "sector": "Consumer"},
    "ASII": {"name": "Astra International", "sector": "Automotive"},
    "BUMI": {"name": "Bumi Resources", "sector": "Mining"},
}


def ensure_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def get_date() -> Tuple[str, str]:
    """
    Get the last business day date range (5 business days).
    Returns dates in YYYY_MM_DD format.
    """
    today = date.today()
    
    # Get last business day (accounting for weekends)
    if date.weekday(today) == 5:  # Saturday
        last_business_day = today - timedelta(days=1)
    elif date.weekday(today) == 6:  # Sunday
        last_business_day = today - timedelta(days=2)
    else:
        last_business_day = today
    
    # Get 5 business days before last business day
    first_day = (last_business_day - pd.tseries.offsets.BDay(4)).date()
    
    return (first_day.strftime("%Y_%m_%d"), last_business_day.strftime("%Y_%m_%d"))


def get_stock_list() -> pd.DataFrame:
    """
    Get list of major IDX stocks.
    Returns DataFrame with stock information.
    """
    print("Loading IDX stock list...")
    
    stocks_data = []
    for code, info in IDX_STOCKS.items():
        stocks_data.append({
            "Code": code,
            "Name": info["name"],
            "Sector": info["sector"],
            "ListingDate": "2000-01-01",  # Approximate
            "Shares": 1000000,  # Placeholder
            "ListingBoard": "Reguler"
        })
    
    df = pd.DataFrame(stocks_data)
    df = df.sort_values(by='Code').reset_index(drop=True)
    
    # Merge with existing data if available
    if os.path.exists(STOCK_LIST_FILE):
        existing_df = pd.read_csv(STOCK_LIST_FILE)
        new_stocks = df[~df['Code'].isin(existing_df['Code'])]
        if not new_stocks.empty:
            result_df = pd.concat([existing_df, new_stocks], ignore_index=True)
            return result_df.sort_values(by='Code').reset_index(drop=True)
        return existing_df
    
    return df


def get_stock_data(
    stock_df: pd.DataFrame,
    start_date: str,
    end_date: str
) -> Tuple[List[str], List[str]]:
    """
    Scrape minute-level stock data using yfinance.
    Returns (successful_stocks, error_stocks).
    """
    success_list = []
    error_list = []
    
    date_range_path = os.path.join(MINUTES_DATA_DIR, f"{start_date}-{end_date}")
    ensure_directory(date_range_path)
    
    # Convert date format
    start_dt = datetime.strptime(start_date, "%Y_%m_%d").date()
    end_dt = datetime.strptime(end_date, "%Y_%m_%d").date()
    
    print(f"Fetching data from {start_dt} to {end_dt}...")
    
    for stock_code in tqdm(stock_df['Code'], desc="Downloading from yfinance"):
        try:
            # Add .JK suffix for IDX stocks
            ticker = f"{stock_code}.JK"
            
            # Fetch minute-level data
            df = yf.download(
                ticker,
                start=start_dt,
                end=end_dt + timedelta(days=1),
                interval='1m',
                progress=False,
                timeout=10
            )
            
            if df.empty:
                error_list.append(stock_code)
                continue
            
            # Handle MultiIndex columns (when downloading single ticker)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Prepare data
            df = df.reset_index()
            
            # Rename columns
            df.columns = df.columns.str.lower()
            df = df.rename(columns={
                'datetime': 'timestamp',
                'open': 'open',
                'low': 'low',
                'high': 'high',
                'close': 'close',
                'volume': 'volume'
            }, inplace=False)
            
            # Ensure correct columns and types
            required_cols = ['timestamp', 'open', 'low', 'high', 'close', 'volume']
            df = df[required_cols]
            df.fillna(0, inplace=True)
            # Convert to Indonesian time (UTC+7)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            # Check if already has timezone info
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Jakarta').dt.strftime('%Y-%m-%d %H:%M:%S')
            df[['open', 'low', 'high', 'close', 'volume']] = df[['open', 'low', 'high', 'close', 'volume']].astype('float64').astype('int64')
            
            # Save to CSV
            output_file = os.path.join(date_range_path, f"{stock_code}.csv")
            df.to_csv(output_file, index=False)
            success_list.append(stock_code)
            
        except Exception as e:
            error_list.append(stock_code)
            # Continue with next stock instead of failing
            continue
    
    return (success_list, error_list)


def append_data(start_date: str, end_date: str) -> None:
    """
    Merge new scraped data with existing historical data.
    Removes duplicates and maintains chronological order.
    """
    from glob import glob
    
    date_range_path = os.path.join(MINUTES_DATA_DIR, f"{start_date}-{end_date}")
    stock_files = glob(os.path.join(date_range_path, "*.csv"))
    ensure_directory(MINUTES_DIR)
    
    for filepath in tqdm(stock_files, desc="Appending to history"):
        stock_code = os.path.basename(filepath)[:-4]
        new_df = pd.read_csv(filepath)
        output_file = os.path.join(MINUTES_DIR, f"{stock_code}.csv")
        
        if os.path.exists(output_file):
            existing_df = pd.read_csv(output_file)
            result = pd.concat([new_df, existing_df], ignore_index=True)
            result.drop_duplicates(subset=['timestamp'], keep='first', inplace=True)
            result = result.sort_values(by=['timestamp']).fillna(0).reset_index(drop=True)
        else:
            result = new_df
        
        result.to_csv(output_file, index=False)


def add_extra_columns() -> None:
    """Add extra columns to stock list (last price, market cap, update dates)."""
    from glob import glob
    
    stock_df = pd.read_csv(STOCK_LIST_FILE)
    stock_files = glob(os.path.join(MINUTES_DIR, "*.csv"))
    available_stocks = {os.path.basename(f)[:-4] for f in stock_files}
    
    last_prices = []
    market_caps = []
    first_added_dates = []
    last_updated_dates = []
    
    for stock_code in tqdm(stock_df['Code'], desc="Calculating metrics"):
        if stock_code in available_stocks:
            df = pd.read_csv(os.path.join(MINUTES_DIR, f"{stock_code}.csv"))
            if len(df) > 0:
                first_added_dates.append(df['timestamp'].iloc[0])
                last_updated_dates.append(df['timestamp'].iloc[-1])
                last_price = float(df['close'].iloc[-1])
                last_prices.append(last_price)
                shares = float(stock_df[stock_df['Code'] == stock_code]['Shares'].values[0])
                market_cap = last_price * shares
                market_caps.append(round(market_cap, 2) if market_cap < 1e15 else market_cap)
            else:
                last_prices.append('')
                market_caps.append('')
                first_added_dates.append('')
                last_updated_dates.append('')
        else:
            last_prices.append('')
            market_caps.append('')
            first_added_dates.append('')
            last_updated_dates.append('')
    
    stock_df['LastPrice'] = last_prices
    stock_df['MarketCap'] = market_caps
    stock_df['MinutesFirstAdded'] = first_added_dates
    stock_df['MinutesLastUpdated'] = last_updated_dates
    stock_df.to_csv(STOCK_LIST_FILE, index=False)


def cleanup_temp_files(start_date: str, end_date: str) -> None:
    """Remove temporary dated folders after processing."""
    import shutil
    temp_path = os.path.join(MINUTES_DATA_DIR, f"{start_date}-{end_date}")
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


def main() -> None:
    """Main execution pipeline for real-time IDX stock data scraping."""
    print("=" * 75)
    print(" 📊 IDX Stock Data Scraper - Real-time Edition (yfinance)")
    print("=" * 75)
    
    # Get date range
    start_date, end_date = get_date()
    print(f"\n📅 Scraping data for period: {start_date} to {end_date}")
    
    # Get stock list and save it
    print("\n[1/5] Loading stock list...")
    stock_list = get_stock_list()
    ensure_directory(DATA_DIR)
    stock_list.to_csv(STOCK_LIST_FILE, index=False)
    print(f"✓ Loaded {len(stock_list)} stocks")
    print(f"  Stocks: {', '.join(stock_list['Code'].tolist())}")
    
    # Scrape stock data
    print("\n[2/5] Downloading real-time minute-level data...")
    success_stocks, error_stocks = get_stock_data(stock_list, start_date, end_date)
    
    if success_stocks:
        print(f"✓ Successfully downloaded: {len(success_stocks)} stocks")
    if error_stocks:
        print(f"⚠ Failed to download: {len(error_stocks)} stocks: {error_stocks}")
    
    if not success_stocks:
        print("✗ No data was downloaded. Exiting...")
        return
    
    # Append to historical data
    print("\n[3/5] Merging with historical data...")
    append_data(start_date, end_date)
    print("✓ Data merged")
    
    # Add extra metrics
    print("\n[4/5] Calculating metrics...")
    add_extra_columns()
    print("✓ Metrics calculated")
    
    # Cleanup
    print("\n[5/5] Cleaning up temporary files...")
    cleanup_temp_files(start_date, end_date)
    print("✓ Cleanup complete")
    
    # Summary
    print("\n" + "=" * 75)
    print("✅ Scraping completed successfully!")
    print("=" * 75)
    
    # Show results
    final_df = pd.read_csv(STOCK_LIST_FILE)
    print(f"\n📊 Stock List with Real-time Data:")
    print(final_df[['Code', 'Name', 'Sector', 'LastPrice', 'MarketCap']].to_string(index=False))
    
    print(f"\n📁 Data Location:")
    print(f"   • Stock list: {STOCK_LIST_FILE}")
    print(f"   • Minute data: {MINUTES_DIR}/")
    
    # Statistics
    from glob import glob
    total_rows = 0
    stock_count = 0
    for csv_file in glob(os.path.join(MINUTES_DIR, "*.csv")):
        rows = len(pd.read_csv(csv_file))
        if rows > 0:
            total_rows += rows
            stock_count += 1
    
    if stock_count > 0:
        print(f"\n📈 Data Statistics:")
        print(f"   • Stocks with data: {stock_count}")
        print(f"   • Total data points: {total_rows:,}")
        print(f"   • Average per stock: {total_rows // stock_count:,}")


if __name__ == "__main__":
    main()
