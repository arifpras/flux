import shutil
import os
from pathlib import Path
import glob

root = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper')
os.chdir(root)

moves = []

# Trading scripts
for f in ['elite_strategy.py', 'elite_strategy_simple.py', 'day_trading_scanner.py', 'day_trading_scanner_enhanced.py', 'detect_pump_end.py', 'manipulation_dashboard.py', 'manipulation_watchlist.py']:
    if Path(f).exists():
        try:
            shutil.move(f, f'scripts/trading/{f}')
            moves.append(('trading', f))
        except: pass

# Analysis
for f in ['analyze_backtest.py', 'analyze_bumi.py', 'broker_analysis.py', 'bumi_analysis_output.txt']:
    if Path(f).exists():
        try:
            shutil.move(f, f'scripts/analysis/{f}')
            moves.append(('analysis', f))
        except: pass

# Scrapers
for f in ['ringkasan_saham_batch_scraper.py', 'ringkasan_saham_scraper.py', 'scrape_multiple_days.py', 'scraper_yfinance.py', 'broker_scraper_idx.py']:
    if Path(f).exists():
        try:
            shutil.move(f, f'scripts/scrapers/{f}')
            moves.append(('scrapers', f))
        except: pass

# Utilities
for f in ['backtest_day_trading.py', 'backtest_v2.py', 'business_days.py', 'combine_histories.py', 'fast_backtest.py', 'fetch_historical_data.py', 'fetch_previous_days_data.py', 'final_backtest.py', 'improved_backtest.py', 'quick_data_loader.py', 'simple_backtest.py', 'simple_data_scanner.py', 'test.py', 'vectorized_backtest.py', 'visualize_bumi_pattern.py', 'IDX_MAJOR_BROKERS.py']:
    if Path(f).exists():
        try:
            shutil.move(f, f'scripts/utilities/{f}')
            moves.append(('utilities', f))
        except: pass

# Docs
for f in ['README_MARKET_BEATING_METHODS.md', 'PROFESSIONAL_REPORT.md', 'PROFESSIONAL_REPORT_SIMPLE.md', 'backtest_output.txt', 'ORGANIZATION_COMPLETE.md']:
    if Path(f).exists():
        try:
            shutil.move(f, f'docs/{f}')
            moves.append(('docs', f))
        except: pass

# Data
for f in ['backtest_summary.csv', 'backtest_trades.csv']:
    if Path(f).exists():
        try:
            shutil.move(f, f'data/{f}')
            moves.append(('data', f))
        except: pass

# Artifacts
for f in glob.glob('*.aux') + glob.glob('*.log') + glob.glob('*.tex'):
    try:
        shutil.move(f, f'artifacts/{f}')
        moves.append(('artifacts', f))
    except: pass

for folder in glob.glob('*_files'):
    if Path(folder).is_dir():
        try:
            shutil.move(folder, f'artifacts/{folder}')
            moves.append(('artifacts', folder))
        except: pass

if Path('.DS_Store').exists():
    try:
        shutil.move('.DS_Store', 'artifacts/.DS_Store')
        moves.append(('artifacts', '.DS_Store'))
    except: pass

# Save report
with open('ORGANIZATION_REPORT.txt', 'w') as f:
    f.write("Project Organization Report\n")
    f.write("=" * 60 + "\n\n")
    for category, filename in moves:
        f.write(f"{category}: {filename}\n")
    f.write(f"\nTotal files moved: {len(moves)}\n")

print(f"Moved {len(moves)} files")
