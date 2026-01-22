#!/usr/bin/env python3
"""
Organize scripts and documentation into logical folders.
"""
import os
import shutil
from pathlib import Path

def organize_project():
    root = Path('/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper')
    os.chdir(root)
    
    print("📁 Starting project organization...")
    print("=" * 60)
    
    # Define folder structure and file mappings
    organization = {
        'scripts/trading': [
            'elite_strategy.py',
            'elite_strategy_simple.py',
            'day_trading_scanner.py',
            'day_trading_scanner_enhanced.py',
            'detect_pump_end.py',
            'manipulation_dashboard.py',
            'manipulation_watchlist.py'
        ],
        'scripts/analysis': [
            'analyze_backtest.py',
            'analyze_bumi.py',
            'broker_analysis.py',
            'bumi_analysis_output.txt'
        ],
        'scripts/scrapers': [
            'ringkasan_saham_batch_scraper.py',
            'ringkasan_saham_scraper.py',
            'scrape_multiple_days.py',
            'scraper_yfinance.py',
            'broker_scraper_idx.py'
        ],
        'scripts/utilities': [
            'backtest_day_trading.py',
            'backtest_v2.py',
            'business_days.py',
            'combine_histories.py',
            'fast_backtest.py',
            'fetch_historical_data.py',
            'fetch_previous_days_data.py',
            'final_backtest.py',
            'improved_backtest.py',
            'quick_data_loader.py',
            'simple_backtest.py',
            'simple_data_scanner.py',
            'test.py',
            'vectorized_backtest.py',
            'visualize_bumi_pattern.py',
            'IDX_MAJOR_BROKERS.py'
        ]
    }
    
    # Documentation files to move to docs/
    docs_files = [
        'README_MARKET_BEATING_METHODS.md',
        'PROFESSIONAL_REPORT.md',
        'PROFESSIONAL_REPORT_SIMPLE.md',
        'backtest_output.txt',
        'ORGANIZATION_COMPLETE.md'
    ]
    
    # Data files to move to data/
    data_files = [
        'backtest_summary.csv',
        'backtest_trades.csv'
    ]
    
    # LaTeX artifacts to move to artifacts/
    latex_patterns = ['*.aux', '*.log', '*.tex']
    
    moved_count = 0
    skipped_count = 0
    
    # 1. Create script folders and move files
    print("\n📂 Creating script folders...")
    for folder in organization.keys():
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ Created {folder}/")
    
    print("\n📄 Moving script files...")
    for folder, files in organization.items():
        for file in files:
            src = Path(file)
            dst = Path(folder) / file
            if src.exists():
                shutil.move(str(src), str(dst))
                print(f"   ✓ {file} → {folder}/")
                moved_count += 1
            else:
                print(f"   - {file} (not found)")
                skipped_count += 1
    
    # 2. Move documentation files
    print("\n📚 Moving documentation files to docs/...")
    Path('docs').mkdir(parents=True, exist_ok=True)
    for file in docs_files:
        src = Path(file)
        if src.exists():
            dst = Path('docs') / file
            shutil.move(str(src), str(dst))
            print(f"   ✓ {file} → docs/")
            moved_count += 1
        else:
            print(f"   - {file} (not found)")
    
    # 3. Move data files
    print("\n💾 Moving data files to data/...")
    Path('data').mkdir(parents=True, exist_ok=True)
    for file in data_files:
        src = Path(file)
        if src.exists():
            dst = Path('data') / file
            shutil.move(str(src), str(dst))
            print(f"   ✓ {file} → data/")
            moved_count += 1
    
    # 4. Move LaTeX artifacts
    print("\n📦 Moving LaTeX artifacts to artifacts/...")
    Path('artifacts').mkdir(parents=True, exist_ok=True)
    import glob
    for pattern in latex_patterns:
        for file in glob.glob(pattern):
            src = Path(file)
            dst = Path('artifacts') / file
            shutil.move(str(src), str(dst))
            print(f"   ✓ {file} → artifacts/")
            moved_count += 1
    
    # Move *_files directories
    for folder in glob.glob('*_files'):
        if Path(folder).is_dir():
            shutil.move(folder, f'artifacts/{folder}')
            print(f"   ✓ {folder}/ → artifacts/")
    
    # 5. Move .DS_Store if exists
    if Path('.DS_Store').exists():
        shutil.move('.DS_Store', 'artifacts/.DS_Store')
        print(f"   ✓ .DS_Store → artifacts/")
    
    print("\n" + "=" * 60)
    print(f"✅ Organization complete!")
    print(f"   Files moved: {moved_count}")
    print(f"   Files skipped: {skipped_count}")
    print("\n📊 Final structure:")
    print("   ✓ scripts/trading/      (7 trading scripts)")
    print("   ✓ scripts/analysis/     (4 analysis scripts)")
    print("   ✓ scripts/scrapers/     (5 scraper scripts)")
    print("   ✓ scripts/utilities/    (16 utility scripts)")
    print("   ✓ docs/                 (documentation)")
    print("   ✓ data/                 (data files)")
    print("   ✓ artifacts/            (LaTeX & build files)")
    print("   ✓ REPORTS/              (analysis reports)")
    
if __name__ == '__main__':
    organize_project()
