"""
IDX Broker Transaction Data Scraper
Scrapes real broker transaction data from IDX website
"""
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# Configuration
BASE_URL = "https://www.idx.co.id"
BROKER_SUMMARY_URL = f"{BASE_URL}/id/data-pasar/data-saham/broker-summary"
DATA_DIR = os.path.join("data", "IHSGstockdata")
BROKER_DIR = os.path.join(DATA_DIR, "broker")


def ensure_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def init_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Initialize Chrome WebDriver for scraping.
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        Chrome WebDriver instance
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver


def scrape_broker_summary(stock_code: str, date: str, driver: webdriver.Chrome) -> Optional[pd.DataFrame]:
    """
    Scrape broker transaction summary for a specific stock and date.
    
    Args:
        stock_code: Stock ticker (e.g., 'BBRI')
        date: Date in YYYY-MM-DD format
        driver: Selenium WebDriver
        
    Returns:
        DataFrame with broker transactions or None if failed
    """
    try:
        print(f"  Scraping {stock_code} for {date}...")
        
        # Navigate to broker summary page
        driver.get(BROKER_SUMMARY_URL)
        time.sleep(3)
        
        # Find and fill stock code input
        stock_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stockCode"))
        )
        stock_input.clear()
        stock_input.send_keys(stock_code)
        
        # Fill date input
        date_input = driver.find_element(By.ID, "tradeDate")
        date_input.clear()
        date_input.send_keys(date)
        
        # Click search button
        search_btn = driver.find_element(By.ID, "btnSearch")
        search_btn.click()
        
        time.sleep(3)
        
        # Wait for results table
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table-broker"))
        )
        
        # Parse table data
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        data = []
        for row in rows[1:]:  # Skip header
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 6:
                data.append({
                    'date': date,
                    'stock_code': stock_code,
                    'broker_id': cols[0].text.strip(),
                    'broker_name': cols[1].text.strip(),
                    'buy_volume': int(cols[2].text.strip().replace(',', '') or 0),
                    'buy_value': float(cols[3].text.strip().replace(',', '') or 0),
                    'sell_volume': int(cols[4].text.strip().replace(',', '') or 0),
                    'sell_value': float(cols[5].text.strip().replace(',', '') or 0),
                })
        
        if data:
            df = pd.DataFrame(data)
            df['net_volume'] = df['buy_volume'] - df['sell_volume']
            df['net_value'] = df['buy_value'] - df['sell_value']
            df['total_volume'] = df['buy_volume'] + df['sell_volume']
            df['total_value'] = df['buy_value'] + df['sell_value']
            return df
        
        return None
        
    except Exception as e:
        print(f"  ❌ Error scraping {stock_code}: {e}")
        return None


def scrape_broker_data_batch(
    stock_codes: List[str],
    start_date: str,
    end_date: str,
    save: bool = True
) -> Dict[str, pd.DataFrame]:
    """
    Scrape broker data for multiple stocks across date range.
    
    Args:
        stock_codes: List of stock tickers
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        save: Save to CSV files
        
    Returns:
        Dict mapping stock codes to DataFrames
    """
    print("=" * 70)
    print("🔍 IDX Broker Data Scraper")
    print("=" * 70)
    print(f"📊 Stocks: {', '.join(stock_codes)}")
    print(f"📅 Date Range: {start_date} to {end_date}")
    print(f"{'=' * 70}\n")
    
    # Initialize driver
    driver = init_driver(headless=True)
    
    # Generate date range
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    date_range = pd.date_range(start, end, freq='B')  # Business days only
    
    results = {}
    
    try:
        for stock in tqdm(stock_codes, desc="Stocks"):
            stock_data = []
            
            for date in tqdm(date_range, desc=f"  {stock}", leave=False):
                date_str = date.strftime('%Y-%m-%d')
                df = scrape_broker_summary(stock, date_str, driver)
                
                if df is not None:
                    stock_data.append(df)
                
                time.sleep(2)  # Rate limiting
            
            if stock_data:
                combined = pd.concat(stock_data, ignore_index=True)
                results[stock] = combined
                
                # Save to file
                if save:
                    ensure_directory(BROKER_DIR)
                    filename = os.path.join(BROKER_DIR, f"{stock}_broker.csv")
                    combined.to_csv(filename, index=False)
                    print(f"  ✅ Saved {len(combined)} broker records to {filename}")
    
    finally:
        driver.quit()
    
    print(f"\n{'=' * 70}")
    print(f"✅ Scraping complete! Collected data for {len(results)} stocks")
    print(f"{'=' * 70}\n")
    
    return results


def get_top_brokers(broker_data: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Get top N most active brokers by total value.
    
    Args:
        broker_data: Broker transaction data
        top_n: Number of top brokers
        
    Returns:
        DataFrame with top brokers
    """
    broker_summary = broker_data.groupby(['broker_id', 'broker_name']).agg({
        'buy_volume': 'sum',
        'buy_value': 'sum',
        'sell_volume': 'sum',
        'sell_value': 'sum',
        'total_volume': 'sum',
        'total_value': 'sum',
        'net_volume': 'sum',
        'net_value': 'sum'
    }).reset_index()
    
    broker_summary = broker_summary.sort_values('total_value', ascending=False)
    
    return broker_summary.head(top_n)


def identify_smart_money(broker_data: pd.DataFrame, threshold: float = 1e9) -> pd.DataFrame:
    """
    Identify 'smart money' brokers with consistently profitable positions.
    
    Args:
        broker_data: Broker transaction data
        threshold: Minimum transaction value to be considered (IDR)
        
    Returns:
        DataFrame with smart money brokers
    """
    # Filter high-value brokers
    big_players = broker_data[broker_data['total_value'] > threshold]
    
    # Calculate metrics per broker
    smart_money = big_players.groupby(['broker_id', 'broker_name']).agg({
        'net_value': ['sum', 'mean', 'std'],
        'total_value': 'sum',
        'date': 'nunique'
    }).reset_index()
    
    smart_money.columns = ['broker_id', 'broker_name', 'total_net_value', 
                           'avg_net_value', 'std_net_value', 'total_value', 'days_active']
    
    # Smart money = consistent positive net value
    smart_money['consistency_score'] = smart_money['avg_net_value'] / (smart_money['std_net_value'] + 1)
    smart_money = smart_money[smart_money['total_net_value'] > 0]
    smart_money = smart_money.sort_values('consistency_score', ascending=False)
    
    return smart_money


def main():
    """Main scraper entry point."""
    # Example: Scrape BBRI broker data for last 5 days
    stock_codes = ['BBRI', 'BBCA', 'BMRI']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    results = scrape_broker_data_batch(
        stock_codes=stock_codes,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        save=True
    )
    
    # Analyze results
    for stock, data in results.items():
        print(f"\n{'=' * 70}")
        print(f"📊 Analysis for {stock}")
        print(f"{'=' * 70}")
        
        # Top brokers
        top_brokers = get_top_brokers(data, top_n=10)
        print(f"\n🏆 Top 10 Brokers by Value:")
        print(top_brokers[['broker_id', 'broker_name', 'total_value', 'net_value']].to_string(index=False))
        
        # Smart money
        smart = identify_smart_money(data)
        if not smart.empty:
            print(f"\n💰 Smart Money Brokers (Top 5):")
            print(smart.head()[['broker_id', 'broker_name', 'consistency_score', 'total_net_value']].to_string(index=False))


if __name__ == "__main__":
    main()
