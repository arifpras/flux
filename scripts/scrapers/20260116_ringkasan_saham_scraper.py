"""
Selenium scraper for IDX Ringkasan Saham page
Fetches daily stock summary table and saves to CSV.
"""
import os
import time
from datetime import datetime
from typing import List

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham/"
DATA_DIR = os.path.join("data", "IHSGstockdata")
OUTPUT_DIR = os.path.join(DATA_DIR, "ringkasan_saham")


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def init_driver(headless: bool = False) -> webdriver.Chrome:
    """Initialize Chrome driver. Use non-headless to avoid Cloudflare blocks."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,900")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean scraped table: rename columns and convert numeric fields."""
    # Drop unnamed columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")].copy()

    # Normalize column names (strip sort hints)
    new_cols: List[str] = []
    for col in df.columns:
        base = col.split("\n")[0].strip()
        new_cols.append(base)
    df.columns = new_cols

    # Fix typical IDX ringkasan order (ticker + 7 numeric columns)
    expected = [
        "Kode Saham",
        "Tertinggi",
        "Terendah",
        "Penutupan",
        "Selisih",
        "Volume",
        "Nilai",
        "Frekuensi",
    ]
    if len(df.columns) == len(expected):
        df.columns = expected
    elif df.columns[0].startswith("Unnamed"):
        # Rename first to ticker and shift others left if misaligned
        df.columns = [expected[0]] + expected[1:len(df.columns)]

    # Convert numeric columns (leave ticker as string)
    numeric_cols = [c for c in df.columns if c != "Kode Saham"]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace("[^0-9-]", "", regex=True)
        df[col] = df[col].replace({"": "0", "-": "0"}).astype(int)

    return df


def scrape_table(driver: webdriver.Chrome) -> pd.DataFrame:
    """Wait for the stock summary table and return as DataFrame."""
    driver.get(BASE_URL)

    # Wait for table to appear
    table = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
    )

    # Extract headers
    headers: List[str] = []
    try:
        headers = [th.text.strip() for th in table.find_elements(By.CSS_SELECTOR, "thead th")]
    except Exception:
        headers = []

    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    data: List[List[str]] = []
    for row in rows:
        cols = [c.text.strip() for c in row.find_elements(By.TAG_NAME, "td")]
        if cols:
            data.append(cols)

    if not headers and data:
        headers = [f"col_{i+1}" for i in range(len(data[0]))]

    # Align headers with data width to avoid mismatch
    if data:
        max_cols = max(len(r) for r in data)
        if len(headers) > max_cols:
            headers = headers[:max_cols]
        elif len(headers) < max_cols:
            headers.extend([f"col_{i+1}" for i in range(len(headers), max_cols)])

    df = pd.DataFrame(data, columns=headers)
    return clean_dataframe(df)


def save_csv(df: pd.DataFrame, date_str: str) -> str:
    ensure_dir(OUTPUT_DIR)
    out_path = os.path.join(OUTPUT_DIR, f"ringkasan_{date_str}.csv")
    df.to_csv(out_path, index=False)
    return out_path


def main(headless: bool = False) -> None:
    date_str = datetime.now().strftime("%Y%m%d")
    driver = init_driver(headless=headless)
    try:
        df = scrape_table(driver)
        if df.empty:
            print("❌ No data scraped. Table may not have loaded.")
            return
        out_path = save_csv(df, date_str)
        print(f"✅ Saved {len(df)} rows to {out_path}")
    finally:
        driver.quit()


if __name__ == "__main__":
    # If Cloudflare blocks headless, rerun with headless=False
    main(headless=False)
