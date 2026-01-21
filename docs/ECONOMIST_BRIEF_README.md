# FLUX Daily Trading Brief - Automated Setup

## Overview

Automated Economist-style daily trading brief that generates every morning before market open.

## Components

### 1. Generator Script
**Location:** `scripts/analysis/generate_economist_brief.py`

**What it does:**
- Fetches live prices from Yahoo Finance
- Loads fundamental data from stock screener
- Pulls broker concentration metrics
- Generates Economist-style narratives
- Creates Quarto markdown file
- Renders to professional PDF

**Output:** `REPORTS/daily-reports/[DATE]_TRADING_BRIEF.pdf`

### 2. Shell Runner
**Location:** `scripts/utilities/run_daily_brief.sh`

**What it does:**
- Runs generator script daily
- Logs output to `REPORTS/logs/`
- Handles errors gracefully

### 3. Cron Job (Optional)
Run automatically every trading day at 8:00 AM WIB.

## Manual Execution

```bash
# Generate today's brief
cd /Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper
.venv/bin/python3 scripts/analysis/generate_economist_brief.py

# Or use the shell script
./scripts/utilities/run_daily_brief.sh
```

## Automated Execution (Cron Setup)

### Step 1: Edit crontab
```bash
crontab -e
```

### Step 2: Add this line (runs Mon-Fri at 8:00 AM)
```bash
0 8 * * 1-5 /Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/scripts/utilities/run_daily_brief.sh
```

### Step 3: Verify cron job
```bash
crontab -l
```

### Alternative: Using launchd (macOS recommended)

Create file: `~/Library/LaunchAgents/com.flux.dailybrief.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.flux.dailybrief</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/scripts/utilities/run_daily_brief.sh</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>1</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/REPORTS/logs/launchd_out.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/REPORTS/logs/launchd_err.log</string>
</dict>
</plist>
```

Load the job:
```bash
launchctl load ~/Library/LaunchAgents/com.flux.dailybrief.plist
launchctl start com.flux.dailybrief
```

## Economist Style Guidelines

The brief follows The Economist Group brand marketing style guide (Dec 2018):

### Writing Principles
- **Clarity**: Clear thinking leads to clear writing
- **Brevity**: Short words. Short sentences. Short paragraphs.
- **Wit**: Never po-faced. Provocative and rewarding.
- **Everyday speech**: Criminals "break" the law, not "violate" it
- **Active voice**: Direct statements, not passive construction

### Headlines
- Clever wordplay, puns, cultural references
- Wit. Intelligence. Boldness.
- Full-points used in marketing materials

### Structure
- Lead with the most important fact
- Inverted pyramid (key finding → evidence → implication)
- 3-4 sentences per paragraph maximum

### Tone
- Confident, authoritative
- Slightly witty, never boring
- Sophisticated but accessible

## Output Structure

Each brief contains:

1. **Active Positions** - Trades to exit
   - Entry/current prices, P&L
   - Days held, days remaining
   - Exit timing and status

2. **New Signals** - Today's opportunities
   - Institutional conviction plays
   - Broker alliance patterns
   - Stocks to avoid

3. **Market Context** - Sector momentum
   - Energy, Industrials, Financials
   - Month-to-date performance

4. **Summary** - Quick reference
   - Active positions count
   - New signals count
   - Next scan date

## Customization

### Add More Stocks
Edit `stocks_to_analyze` in `generate_economist_brief.py`:
```python
stocks_to_analyze = ['ADRO', 'ASII', 'BMTR', 'TLKM', 'BBCA']
```

### Change Time
Modify cron schedule:
```bash
# 7:30 AM instead of 8:00 AM
30 7 * * 1-5 /path/to/run_daily_brief.sh
```

### Add Email Notification
Add to `run_daily_brief.sh`:
```bash
# Send email on completion
if [ $? -eq 0 ]; then
    echo "Brief generated" | mail -s "Daily Trading Brief Ready" your@email.com
fi
```

## Logs

**Location:** `REPORTS/logs/economist_brief_YYYYMMDD.log`

**What's logged:**
- Start/end timestamps
- Data fetch results
- PDF generation status
- Errors and warnings

**Check logs:**
```bash
tail -f REPORTS/logs/economist_brief_$(date +%Y%m%d).log
```

## Integration with Scanner

The brief generator can integrate with `flux_daily_scanner_v2.py`:

```python
# In generate_economist_brief.py
from scripts.analysis.flux_daily_scanner_v2 import FluxDailyScanner

scanner = FluxDailyScanner()
results = scanner.scan_all_stocks()
# Use results for narratives
```

## Troubleshooting

### PDF not generating
```bash
# Check Quarto installation
which quarto

# Test manually
cd REPORTS/daily-reports
quarto render 21JAN2026_TRADING_BRIEF.qmd --to pdf
```

### Yahoo Finance errors
```bash
# Test data fetch
python3 -c "import yfinance as yf; print(yf.Ticker('ADRO.JK').history(period='5d'))"
```

### Cron not running
```bash
# Check cron logs
grep CRON /var/log/system.log

# Test script manually
./scripts/utilities/run_daily_brief.sh
```

## Future Enhancements

1. **Real broker data integration** - Pull from IDX daily files
2. **Sector momentum calculation** - Auto-fetch sector indices
3. **Email distribution** - Send PDF to subscribers
4. **WhatsApp/Telegram alerts** - Push notifications for strong signals
5. **Multi-language support** - Generate Bahasa Indonesia version
6. **Historical archive** - Track brief accuracy over time

## Files Generated

```
REPORTS/
├── daily-reports/
│   ├── 21JAN2026_TRADING_BRIEF.qmd  (source)
│   ├── 21JAN2026_TRADING_BRIEF.pdf  (output)
│   ├── 22JAN2026_TRADING_BRIEF.qmd
│   └── 22JAN2026_TRADING_BRIEF.pdf
└── logs/
    ├── economist_brief_20260121.log
    └── economist_brief_20260122.log
```

## License

Internal use only. The Economist brand guidelines used for styling reference only.
