"""
Selenium scraper for IDX Ringkasan Saham page with date dropdown.
Fetches daily stock summary table for specified date(s) and saves to CSV.
"""
import os
import time
import glob
from datetime import datetime
from typing import List, Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham/"
DATA_DIR = os.path.join("data", "IHSGstockdata")
OUTPUT_DIR = os.path.join(DATA_DIR, "ringkasan_saham")


def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def find_and_click_unduh_button(driver: webdriver.Chrome) -> bool:
    """
    Find and click the 'Unduh' (download) button on the page.
    Uses multiple strategies to bypass overlays.
    
    Args:
        driver: Selenium WebDriver
        
    Returns:
        True if button was found and clicked, False otherwise
    """
    try:
        # First, try to hide any overlays that might be blocking clicks
        try:
            driver.execute_script("""
                // Hide common overlay elements
                var navs = document.querySelectorAll('.nav-container, .navbar, header, [class*="nav-"]');
                navs.forEach(function(nav) {
                    nav.style.visibility = 'hidden';
                });
            """)
            time.sleep(0.3)
        except:
            pass
        
        # Strategy 1: Find button by text content and click with JavaScript
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            btn_text = btn.text.strip().lower()
            if "unduh" in btn_text or "download" in btn_text:
                # Scroll button into view at the center of viewport
                driver.execute_script("""
                    arguments[0].scrollIntoView({behavior: 'instant', block: 'center', inline: 'center'});
                """, btn)
                time.sleep(0.5)
                
                # Try to dispatch Vue event and native click
                driver.execute_script("""
                    // Try multiple event dispatch methods for Vue
                    const button = arguments[0];
                    
                    // Method 1: Native click
                    button.click();
                    
                    // Method 2: Dispatch mouse events
                    ['mousedown', 'mouseup', 'click'].forEach(eventType => {
                        button.dispatchEvent(new MouseEvent(eventType, {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        }));
                    });
                """, btn)
                
                # Restore nav visibility
                try:
                    driver.execute_script("""
                        var navs = document.querySelectorAll('.nav-container, .navbar, header, [class*="nav-"]');
                        navs.forEach(function(nav) {
                            nav.style.visibility = 'visible';
                        });
                    """)
                except:
                    pass
                
                return True
        
        # Strategy 2: Find link by text content
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            link_text = link.text.strip().lower()
            if "unduh" in link_text or "download" in link_text:
                driver.execute_script("""
                    arguments[0].scrollIntoView({behavior: 'instant', block: 'center', inline: 'center'});
                """, link)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", link)
                return True
        
        # Strategy 3: Look for elements with download-related attributes
        download_selectors = [
            "button[class*='download' i]",
            "button[class*='unduh' i]",
            "[class*='btn-download' i]",
            "[aria-label*='unduh' i]",
            "[aria-label*='download' i]",
            "[title*='unduh' i]",
            "[title*='download' i]",
        ]
        for selector in download_selectors:
            try:
                elems = driver.find_elements(By.CSS_SELECTOR, selector)
                if elems:
                    elem = elems[0]
                    driver.execute_script("""
                        arguments[0].scrollIntoView({behavior: 'instant', block: 'center', inline: 'center'});
                    """, elem)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", elem)
                    return True
            except:
                pass
        
        # Restore nav visibility if we didn't return yet
        try:
            driver.execute_script("""
                var navs = document.querySelectorAll('.nav-container, .navbar, header, [class*="nav-"]');
                navs.forEach(function(nav) {
                    nav.style.visibility = 'visible';
                });
            """)
        except:
            pass
        
        return False
    except Exception as e:
        print(f"Error finding unduh button: {e}")
        return False


def wait_for_download(download_dir: str, timeout: int = 10, ignore_before: float = None) -> Optional[str]:
    """
    Wait for a file to be downloaded in the specified directory.
    Supports both CSV and XLSX files.
    
    Args:
        download_dir: Directory where file should appear
        timeout: Maximum seconds to wait
        ignore_before: Ignore files modified before this timestamp
        
    Returns:
        Path to downloaded file or None if timeout
    """
    import time as time_module
    
    start_time = time_module.time()
    while time_module.time() - start_time < timeout:
        # Look for XLSX files (browser downloads as XLSX)
        xlsx_files = glob.glob(os.path.join(download_dir, "*.xlsx"))
        # Filter out any partial downloads (Chrome temp files)
        xlsx_files = [f for f in xlsx_files if not f.endswith(".crdownload")]
        
        # If ignore_before is set, only consider files modified after that time
        if ignore_before:
            xlsx_files = [f for f in xlsx_files if os.path.getmtime(f) > ignore_before]
        
        if xlsx_files:
            # Get the most recently modified file
            latest_file = max(xlsx_files, key=os.path.getmtime)
            # Make sure it's not a temp file by checking if it's still being written
            try:
                with open(latest_file, 'rb') as f:
                    f.read(1)  # Try to read first byte
                return latest_file
            except:
                time_module.sleep(0.5)
                continue
        
        time_module.sleep(0.5)
    
    return None


def init_driver(headless: bool = False, download_dir: str = None) -> webdriver.Chrome:
    """Initialize Chrome driver with optional download directory."""
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

    # Configure download directory if provided
    if download_dir:
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
        }
        options.add_experimental_option("prefs", prefs)

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
        df.columns = [expected[0]] + expected[1 : len(df.columns)]

    # Convert numeric columns (leave ticker as string)
    numeric_cols = [c for c in df.columns if c != "Kode Saham"]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace("[^0-9-]", "", regex=True)
        df[col] = df[col].replace({"": "0", "-": "0"}).astype(int)

    return df


def select_date_and_scrape(
    driver: webdriver.Chrome, target_date: datetime, download_dir: str = None
) -> Optional[pd.DataFrame]:
    """
    Select a date from dropdown and download the full CSV data.
    
    Args:
        driver: Selenium WebDriver
        target_date: Date to select (datetime object)
        download_dir: Directory to save downloaded file
        
    Returns:
        DataFrame with scraped data or None if failed
    """
    try:
        date_str_iso = target_date.strftime("%Y-%m-%d")
        date_str_alt = target_date.strftime("%d-%m-%Y")
        date_str_filename = target_date.strftime("%Y%m%d")
        print(f"  Selecting date: {date_str_iso}...", end="", flush=True)

        # Find date input
        date_input = None
        selectors = [
            "input[type='date']",
            "input[placeholder*='date' i]",
            "input[name*='date' i]",
            "input[class*='date' i]",
            ".date-input",
            "#date",
        ]

        max_retries = 3
        for attempt in range(max_retries):
            for selector in selectors:
                try:
                    date_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    pass
            
            if date_input:
                break
            
            if attempt < max_retries - 1:
                time.sleep(0.5)

        if date_input is None:
            print(" ❌ (date input not found)")
            return None

        # Set the date
        date_input.clear()
        date_input.send_keys(date_str_iso)
        date_input.send_keys(Keys.RETURN)

        # Fallback if ISO didn't work
        current_val = date_input.get_attribute("value") or ""
        if current_val.replace("/", "-") not in (date_str_iso, date_str_alt):
            date_input.clear()
            date_input.send_keys(date_str_alt)
            date_input.send_keys(Keys.RETURN)
            time.sleep(0.5)

        if current_val.replace("/", "-") not in (date_str_iso, date_str_alt):
            driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change')); arguments[0].dispatchEvent(new Event('input'));",
                date_input,
                date_str_iso,
            )
        
        # Trigger events
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('change')); arguments[0].dispatchEvent(new Event('input')); arguments[0].dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}));",
            date_input,
        )

        # Wait for page to load
        time.sleep(2.0)

        # Try to click the "Unduh" (download) button
        if download_dir:
            print(" Downloading...", end="", flush=True)
            
            # Record time before click to know which file is new
            time_before_download = time.time()
            time.sleep(0.2)
            
            if find_and_click_unduh_button(driver):
                # Wait a bit longer for download to start
                time.sleep(2)
                # Wait for file to download (only look for files modified after click)
                # Increased timeout to 25 seconds for slower downloads
                downloaded_file = wait_for_download(download_dir, timeout=25, ignore_before=time_before_download)
                
                if downloaded_file:
                    # Check if it's an XLSX file that needs conversion
                    target_path = os.path.join(download_dir, f"ringkasan_{date_str_filename}.csv")
                    
                    if downloaded_file.endswith('.xlsx'):
                        # Convert XLSX to CSV
                        try:
                            df = pd.read_excel(downloaded_file)
                            if os.path.exists(target_path):
                                os.remove(target_path)
                            df.to_csv(target_path, index=False)
                            print(f" ✅ ({len(df)} rows from Excel)")
                            return df
                        except Exception as e:
                            print(f" ❌ (Excel read error: {e})")
                            return None
                    else:
                        # It's already a CSV
                        if os.path.exists(target_path):
                            os.remove(target_path)
                        os.rename(downloaded_file, target_path)
                        
                        # Read and validate the CSV
                        try:
                            df = pd.read_csv(target_path)
                            print(f" ✅ ({len(df)} rows)")
                            return df
                        except Exception as e:
                            print(f" ❌ (read error: {e})")
                            return None
                else:
                    print(" ⚠️  (no download, falling back to table)")
            else:
                print(" ⚠️  (button not found, falling back to table)", end="", flush=True)

        # Fallback: Extract table data if download failed
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )

        headers: List[str] = []
        try:
            headers = [
                th.text.strip() for th in table.find_elements(By.CSS_SELECTOR, "thead th")
            ]
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

        # Align headers with data
        if data:
            max_cols = max(len(r) for r in data)
            if len(headers) > max_cols:
                headers = headers[:max_cols]
            elif len(headers) < max_cols:
                headers.extend([f"col_{i+1}" for i in range(len(headers), max_cols)])

        df = pd.DataFrame(data, columns=headers)
        if not df.empty:
            df = clean_dataframe(df)

        print(f" ✅ ({len(df)} rows from table)")
        return df if not df.empty else None

    except Exception as e:
        print(f" ❌ ({e})")
        return None


def save_csv(df: pd.DataFrame, date_str: str) -> str:
    ensure_dir(OUTPUT_DIR)
    out_path = os.path.join(OUTPUT_DIR, f"ringkasan_{date_str}.csv")
    df.to_csv(out_path, index=False)
    return out_path


def scrape_date_range(
    dates: List[datetime], headless: bool = False, delay: float = 1.0
) -> dict:
    """
    Scrape ringkasan saham for multiple dates with automatic download.
    
    Args:
        dates: List of datetime objects to scrape
        headless: Run browser headless
        delay: Delay between requests (seconds)
        
    Returns:
        Dict with results
    """
    results = {
        "total": len(dates),
        "success": 0,
        "failed": 0,
        "files": [],
    }

    ensure_dir(OUTPUT_DIR)
    driver = init_driver(headless=headless, download_dir=OUTPUT_DIR)

    try:
        # Load page once
        driver.get(BASE_URL)
        time.sleep(3)  # Wait for page load and Cloudflare

        for date in dates:
            date_str = date.strftime("%Y%m%d")
            df = select_date_and_scrape(driver, date, download_dir=OUTPUT_DIR)

            if df is not None and not df.empty:
                file_path = save_csv(df, date_str)
                results["files"].append(file_path)
                results["success"] += 1
            else:
                results["failed"] += 1

            time.sleep(delay)

    finally:
        driver.quit()

    return results


def main(date_list_file: str = "business_days_90.txt", headless: bool = False):
    """Main entry point."""
    # Load dates from file
    if not os.path.exists(date_list_file):
        print(f"❌ File not found: {date_list_file}")
        print("   Run business_days.py first to generate the date list")
        return

    dates = []
    with open(date_list_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    dates.append(datetime.strptime(line, "%Y%m%d"))
                except ValueError:
                    pass

    if not dates:
        print(f"❌ No valid dates found in {date_list_file}")
        return

    print("=" * 80)
    print(f"🔄 Scraping Ringkasan Saham for {len(dates)} dates")
    print(f"📅 From: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    print("=" * 80 + "\n")

    results = scrape_date_range(dates, headless=headless, delay=1.5)

    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    print(f"Total dates:    {results['total']}")
    print(f"Successful:     {results['success']}")
    print(f"Failed:         {results['failed']}")
    print(f"Success rate:   {results['success']/results['total']*100:.1f}%")

    if results["files"]:
        print(f"\n✅ Saved {len(results['files'])} files to {OUTPUT_DIR}")
        print(f"\nFirst file: {os.path.basename(results['files'][0])}")
        print(f"Last file:  {os.path.basename(results['files'][-1])}")
    else:
        print(f"\n❌ No files saved")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    import sys

    # Support CLI argument for date file
    date_file = sys.argv[1] if len(sys.argv) > 1 else "business_days_90.txt"
    main(date_list_file=date_file, headless=False)
