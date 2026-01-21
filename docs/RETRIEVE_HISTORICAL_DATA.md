# Historical Stock Data Retrieval Guide
## Challenge: Obtain Data from Previous Days

This guide provides multiple strategies to retrieve historical stock data from previous days.

---

## Overview

Your stock scraper project has three ways to access historical data:

### 📦 **Data Sources Available**

1. **Excel Files** (`histories/` directory)
   - 30+ Excel files from December 2025 to January 2026
   - Format: `Ringkasan Saham-YYYYMMDD.xlsx`
   - Contains complete ringkasan saham (stock summary) data

2. **CSV Files** (`IHSGstockdata/ringkasan_saham/` directory)
   - Recent CSV exports
   - Format: `ringkasan_YYYYMMDD.csv`
   - Quick access to tabular data

3. **Alert Scans** (`IHSGstockdata/alerts/` directory)
   - Daily alert detection results
   - Format: `scan_YYYY-MM-DD.json`
   - Contains detected trading alerts

4. **Real-time Scraping**
   - Use Selenium to scrape latest data from IDX website
   - Supports date-picker for historical dates

---

## Method 1: Fetch Historical Data from Existing Files

### Script: `fetch_previous_days_data.py`

This is the **quickest method** to get historical data.

```bash
# Run the fetcher
python3 fetch_previous_days_data.py
```

**What it does:**
- Scans all available data sources
- Creates a consolidated CSV with all historical data
- Generates statistics and coverage reports
- Detects data gaps (weekends/holidays)
- Exports to `consolidated_stock_history.csv`

**Output includes:**
- Data coverage timeline
- Gap detection
- Sample data overview
- File statistics

---

## Method 2: Scrape Multiple Days (Real-time)

### Script: `scrape_multiple_days.py`

For more recent data or specific dates, use the Selenium scraper.

```bash
# Scrape last 10 business days
python3 scrape_multiple_days.py --days 10

# Scrape last 30 business days (non-headless, recommended)
python3 scrape_multiple_days.py --days 30

# Scrape specific dates
python3 scrape_multiple_days.py --dates 2026-01-14 2026-01-15 2026-01-16

# Scrape with headless browser (faster, may fail with Cloudflare)
python3 scrape_multiple_days.py --days 10 --headless
```

**Options:**
- `--days N`: Scrape last N business days
- `--dates DATE1 DATE2 ...`: Scrape specific dates (YYYY-MM-DD format)
- `--headless`: Run browser in headless mode (faster but less reliable)
- `--delay N`: Delay between requests in seconds (default: 1.5)

**What it produces:**
- CSV files in `IHSGstockdata/ringkasan_saham/`
- Named: `ringkasan_YYYYMMDD.csv`
- Contains full ringkasan saham table

**Requirements:**
- Chrome/Chromium browser installed
- Selenium and dependencies installed
- Network connectivity to idx.co.id

---

## Method 3: Custom Data Analysis

### Script: `fetch_historical_data.py`

Advanced script for detailed analysis and custom exports.

```bash
python3 fetch_historical_data.py
```

**Features:**
- Detailed data source scanning
- Gap detection with business day intelligence
- Stock-level statistics
- Consolidated exports
- Date range filtering

---

## Supported Date Ranges

### Available Historical Data:

```
📅 Excel Files (histories/):
   December 2025:  01, 02, 03, 04, 05, 08, 09, 10, 11, 12, 15, 16, 17, 18, 19, 22, 23, 24, 29, 30
   January 2026:   05, 06, 07, 08, 09, 12, 13, 14, 15

🔍 Most Recent Dates:
   2026-01-15 (Wednesday) - Most recent Excel file
   2026-01-16 (Thursday) - Most recent CSV file
```

### Weekend/Holiday Handling:

The scripts automatically skip:
- Saturdays and Sundays (weekends)
- Indonesian public holidays (detailed list in script)
- Dates with no data available

---

## Data Consolidation Examples

### Example 1: Get Last 30 Days of Data

```bash
# Fetch existing historical data
python3 fetch_previous_days_data.py

# Output: consolidated_stock_history.csv
# Contains: All available ringkasan saham data for last 30 business days
```

### Example 2: Get Latest Data (Scrape)

```bash
# Scrape last 5 business days
python3 scrape_multiple_days.py --days 5

# This will:
# 1. Identify last 5 business days
# 2. Open Chrome browser
# 3. Navigate to IDX website
# 4. Select each date using the date picker
# 5. Extract table data
# 6. Save as CSV files
```

### Example 3: Compare Two Dates

```python
import pandas as pd

# Load data from Excel
jan_14 = pd.read_excel("histories/Ringkasan Saham-20260114.xlsx")
jan_15 = pd.read_excel("histories/Ringkasan Saham-20260115.xlsx")

# Compare data
print(f"Stocks on Jan 14: {len(jan_14)}")
print(f"Stocks on Jan 15: {len(jan_15)}")

# Find new stocks
new_stocks = set(jan_15['Kode Saham']) - set(jan_14['Kode Saham'])
print(f"New stocks: {new_stocks}")

# Find stocks with price changes > 5%
jan_15['Price_Change'] = (jan_15['Harga Penutupan'] / jan_14['Harga Penutupan'] - 1) * 100
big_movers = jan_15[jan_15['Price_Change'].abs() > 5]
print(big_movers[['Kode Saham', 'Price_Change']])
```

---

## Data Structure

### Ringkasan Saham (Stock Summary) Data:

```
Columns typically include:
- Kode Saham (Stock Code)
- Nama Saham (Stock Name)
- Harga Pembukaan (Opening Price)
- Harga Penutupan (Closing Price)
- Harga Tertinggi (Highest Price)
- Harga Terendah (Lowest Price)
- Volume (Trading Volume)
- Nilai Transaksi (Transaction Value)
- Perubahan Harga (Price Change)
```

### Alert Scan Data (JSON):

```json
[
  {
    "date": "2026-01-15",
    "stock": "BBRI",
    "alert_type": "volume_spike",
    "value": 2500000000,
    "threshold": 1800000000
  },
  ...
]
```

---

## Quick Commands Cheatsheet

```bash
# 1️⃣ Consolidate all existing historical data
python3 fetch_previous_days_data.py

# 2️⃣ Scrape last 10 days
python3 scrape_multiple_days.py --days 10

# 3️⃣ Scrape last 30 days (headless, faster)
python3 scrape_multiple_days.py --days 30 --headless

# 4️⃣ Scrape specific dates
python3 scrape_multiple_days.py --dates 2026-01-10 2026-01-11 2026-01-12

# 5️⃣ View Python data
python3 -c "import pandas as pd; df = pd.read_csv('consolidated_stock_history.csv'); print(df.head())"

# 6️⃣ Count total stocks across all dates
python3 -c "import pandas as pd; df = pd.read_csv('consolidated_stock_history.csv'); print(f'Total records: {len(df)}'); print(f'Unique stocks: {df[df.columns[0]].nunique()}')"
```

---

## Troubleshooting

### Problem: "Chrome driver not found"
```bash
# Install chromedriver
pip install webdriver-manager  # Already in requirements
# Or install Chrome browser first
```

### Problem: "Cloudflare blocked the request"
```bash
# Use non-headless mode (more reliable)
python3 scrape_multiple_days.py --days 5  # No --headless flag

# Or reduce speed
python3 scrape_multiple_days.py --days 5 --delay 3
```

### Problem: "Date not found in dropdown"
```bash
# Check if date is a business day
python3 -c "from fetch_previous_days_data import is_business_day; from datetime import date; print(is_business_day(date(2026,1,15)))"

# If False, try an adjacent date
```

### Problem: "No Excel files found"
```bash
# Check if histories directory exists
ls -la histories/

# If not, create it and copy Excel files there
mkdir -p histories
```

---

## Performance Tips

1. **For bulk historical data**: Use `fetch_previous_days_data.py` (reads existing files)
2. **For daily updates**: Use Selenium scraper with `--days 5`
3. **For specific analysis**: Consolidate data first, then process

### Recommended Workflow:

```
Day 1: Consolidate all historical data
   └─> python3 fetch_previous_days_data.py
   └─> Output: consolidated_stock_history.csv

Daily: Scrape new data
   └─> python3 scrape_multiple_days.py --days 1
   └─> Output: ringkasan_20260116.csv

Weekly: Analysis
   └─> Load consolidated data
   └─> Compare with new data
   └─> Generate alerts
```

---

## Next Steps

After retrieving historical data, you can:

1. **Analyze trends**: Compare price movements across days
2. **Detect patterns**: Identify stocks with consistent behavior
3. **Generate alerts**: Find stocks meeting specific criteria
4. **Backtest strategies**: Test trading strategies on historical data
5. **Create dashboards**: Visualize data trends

---

## Files Created

- `fetch_previous_days_data.py` - Main historical data fetcher
- `fetch_historical_data.py` - Advanced fetcher with detailed analysis
- `scrape_multiple_days.py` - CLI tool for scraping multiple dates
- `simple_data_scanner.py` - Quick data source scanner
- `RETRIEVE_HISTORICAL_DATA.md` - This guide

---

**Last Updated**: January 16, 2026
**Status**: ✅ Ready to use
