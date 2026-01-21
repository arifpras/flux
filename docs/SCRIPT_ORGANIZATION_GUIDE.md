# 📁 Project Script & Documentation Organization Guide

## Status: READY TO IMPLEMENT

Your project needs organized script folders created. The folder structure has been partially set up, but we need to move the files.

---

## 📂 Target Folder Structure

```
stockscraper/
├── scripts/
│   ├── trading/           (7 files)
│   ├── analysis/          (4 files)
│   ├── scrapers/          (5 files)
│   └── utilities/         (16 files)
├── docs/                  (documentation files)
├── data/                  (CSV data files)
├── artifacts/             (LaTeX build files)
└── REPORTS/               (analysis reports - already organized)
```

---

## 📋 Files to Move - By Category

### 1. scripts/trading/ (TRADING EXECUTION)
**Purpose:** Daily trading and strategy execution scripts

```
elite_strategy.py
elite_strategy_simple.py
day_trading_scanner.py
day_trading_scanner_enhanced.py
detect_pump_end.py
manipulation_dashboard.py
manipulation_watchlist.py
```

### 2. scripts/analysis/ (BACKTESTING & ANALYSIS)
**Purpose:** Performance analysis and metric calculation

```
analyze_backtest.py
analyze_bumi.py
broker_analysis.py
bumi_analysis_output.txt
```

### 3. scripts/scrapers/ (DATA COLLECTION)
**Purpose:** Web scraping and data fetching

```
ringkasan_saham_batch_scraper.py
ringkasan_saham_scraper.py
scrape_multiple_days.py
scraper_yfinance.py
broker_scraper_idx.py
```

### 4. scripts/utilities/ (SUPPORT TOOLS)
**Purpose:** Utility functions and support scripts

```
backtest_day_trading.py
backtest_v2.py
business_days.py
combine_histories.py
fast_backtest.py
fetch_historical_data.py
fetch_previous_days_data.py
final_backtest.py
improved_backtest.py
quick_data_loader.py
simple_backtest.py
simple_data_scanner.py
test.py
vectorized_backtest.py
visualize_bumi_pattern.py
IDX_MAJOR_BROKERS.py
```

### 5. docs/ (DOCUMENTATION)
**Purpose:** Strategy guides, implementation guides, reports

```
README_MARKET_BEATING_METHODS.md
PROFESSIONAL_REPORT.md
PROFESSIONAL_REPORT_SIMPLE.md
backtest_output.txt
ORGANIZATION_COMPLETE.md
```

### 6. data/ (DATA FILES)
**Purpose:** Backtest and trading data

```
backtest_summary.csv
backtest_trades.csv
(+ existing data folder structure: IHSGstockdata/, histories/, manual/, reference/)
```

### 7. artifacts/ (BUILD ARTIFACTS)
**Purpose:** LaTeX and build files

```
ELITE_STRATEGY_IDR.aux
ELITE_STRATEGY_IDR.log
ELITE_STRATEGY_IDR.tex
MARKET_BEATING_METHODS.aux
MARKET_BEATING_METHODS.log
MARKET_BEATING_METHODS.tex
PROFESSIONAL_REPORT.aux
PROFESSIONAL_REPORT.log
PROFESSIONAL_REPORT.tex
ELITE_STRATEGY_IDR_files/
MARKET_BEATING_METHODS_files/
PROFESSIONAL_REPORT_files/
.DS_Store
```

---

## 🔧 How to Implement

### Option 1: VS Code Drag-and-Drop
1. Open stockscraper folder in VS Code
2. Expand scripts/trading/ folder
3. Drag files from root to scripts/trading/
4. Repeat for other folders

### Option 2: Use Finder (macOS)
1. Open Finder to stockscraper folder
2. Create new folders: scripts/trading, scripts/analysis, etc.
3. Drag files from root into appropriate folders
4. Move to Trash: old folders

### Option 3: Terminal Command
```bash
cd ~/Library/CloudStorage/Dropbox/perisai/stockscraper

# Move trading scripts
mv elite_strategy.py elite_strategy_simple.py ... scripts/trading/

# Move analysis scripts
mv analyze_backtest.py analyze_bumi.py ... scripts/analysis/

# Move scraper scripts
mv ringkasan_saham_batch_scraper.py ... scripts/scrapers/

# Move utility scripts
mv backtest_day_trading.py ... scripts/utilities/

# Move documentation
mv *.md backtest_output.txt docs/

# Move data
mv *.csv data/

# Move LaTeX artifacts
mv *.aux *.log *.tex *_files artifacts/
```

---

## 📊 Benefits After Organization

### Current State (Before)
- Root directory has 35+ Python files
- Hard to find scripts by purpose
- Mixed documentation, data, code
- No clear separation of concerns

### Target State (After)
- Root is clean (only REPORTS/, scripts/, docs/, data/, artifacts/)
- Scripts grouped by function
- Documentation centralized
- Data files organized
- Build artifacts separate

### File Access
```
# Before
ls *.py | grep elite    # Messy

# After
ls scripts/trading/*.py  # Clear!
```

---

## 🎯 Next Steps

### 1. Move Scripts (32 files)
- [ ] Move 7 files → scripts/trading/
- [ ] Move 4 files → scripts/analysis/
- [ ] Move 5 files → scripts/scrapers/
- [ ] Move 16 files → scripts/utilities/

### 2. Move Documentation (5 files)
- [ ] Move markdown & txt files → docs/

### 3. Move Data (2 files)
- [ ] Move CSV files → data/

### 4. Move Artifacts (12+ items)
- [ ] Move .aux, .log, .tex files → artifacts/
- [ ] Move *_files folders → artifacts/
- [ ] Move .DS_Store → artifacts/

### 5. Verify & Clean
- [ ] Confirm all files moved
- [ ] Verify no duplicates
- [ ] Update any file references if needed

---

## ⚠️ Important Notes

### Files to NOT Move
- `.git/` folder (if using git)
- `REPORTS/` folder (already organized)
- `.gitignore`, `.env`, etc. (keep in root)

### Update File Paths
If any scripts have hardcoded paths like:
```python
data = pd.read_csv('analyze_backtest.py')
```

Update them to:
```python
data = pd.read_csv('scripts/analysis/analyze_backtest.py')
```

Or use relative paths:
```python
import os
script_dir = os.path.dirname(__file__)
data = pd.read_csv(os.path.join(script_dir, '../data/backtest_trades.csv'))
```

---

## 📍 File Structure Reference

After organization, paths will be:

```
scripts/trading/elite_strategy.py
scripts/analysis/analyze_backtest.py
scripts/scrapers/ringkasan_saham_scraper.py
scripts/utilities/business_days.py

docs/README_MARKET_BEATING_METHODS.md
docs/ORGANIZATION_COMPLETE.md

data/backtest_trades.csv
data/backtest_summary.csv

artifacts/ELITE_STRATEGY_IDR.aux
artifacts/MARKET_BEATING_METHODS_files/

REPORTS/README.md (already organized)
REPORTS/market-beating-methods/
REPORTS/elite-strategy/
REPORTS/analysis/
```

---

## ✅ Quick Reference

**Trading Scripts:**
```bash
ls scripts/trading/
# elite_strategy.py
# day_trading_scanner.py
# detect_pump_end.py
# ... (7 total)
```

**Data Location:**
```bash
ls data/
# backtest_trades.csv     (main backtest data)
# backtest_summary.csv    (summary stats)
# IHSGstockdata/          (historical data)
# histories/              (cached histories)
```

**Analysis Tools:**
```bash
ls scripts/analysis/
# analyze_backtest.py
# analyze_bumi.py
# broker_analysis.py
```

**Quick Start After Organization:**
```bash
cd scripts/trading
python3 elite_strategy_simple.py  # Run trading

cd ../analysis  
python3 analyze_backtest.py       # Run analysis

cd ../../docs
cat README_MARKET_BEATING_METHODS.md  # Read guide
```

---

## 🚀 Implementation Priority

**High Priority (Do First):**
1. Move scripts/ files (32 Python files)
2. Move docs/ files (5 documentation files)

**Medium Priority (Do Second):**
3. Move data/ files (2 CSV files)
4. Move artifacts/ files (12+ build files)

**Verification:**
5. Run `ls scripts/trading/ | wc -l` → should show 7
6. Run `ls scripts/analysis/ | wc -l` → should show 4
7. Run `ls docs/ | wc -l` → should show 5+

---

## 📞 Questions?

If you need help with:
- **Specific file paths:** Check the categorized list above
- **Updating Python imports:** Use relative paths from script location
- **Verifying moves:** Run `find scripts/ -type f | wc -l` → should show 32

---

**Total Files to Move:** 56 files
**Total Folders to Create:** 4 subfolders (already created)
**Estimated Time:** 5-10 minutes
**Difficulty:** Easy (drag-and-drop)

Let me know when you've moved the files and I'll help verify the structure!
