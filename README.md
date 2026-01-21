# 📈 Perisai Stock Trading System

**Advanced Day Trading Strategy with Market-Beating Methods**

---

## 🚀 Quick Start

### Daily Market Scan (8:00 AM, Before Open)
```bash
# 1. Check news sentiment for critical risks
python scripts/scrapers/news_sentiment_api.py --stocks ADRO,ASII,UNTR,BBRI

# 2. Run automated trading scanner
python scripts/analysis/flux_daily_scanner_v2.py --output daily_signals.json

# 3. Generate economist-style daily brief
python scripts/analysis/generate_economist_brief.py

# 4. Monitor active trades for exit signals
python scripts/analysis/daily_trading_checklist.py
```

### Analyze Price History
```bash
python scripts/analysis/wavelet_validate_top10.py
```

### View Latest Results
```bash
cat results/elite_strategy_candidates.json
cat data/news_cache/sentiment_20260121_114357.csv
```

---

## 📁 Project Structure

```
perisai/stockscraper/
├── README.md                  # This file
├── .gitignore                 # Version control exclusions
│
├── data/                      # All data files
│   ├── backtest/              # Historical backtest results (backtest_trades.csv)
│   ├── histories/             # Price histories & augmented datasets
│   ├── IHSGstockdata/         # Market data & alerts
│   ├── manual/                # Manual signals & notes
│   └── reference/             # Reference data (business days, broker summaries)
│
├── scripts/                   # Production scripts
│   ├── analysis/              # Trading analysis & signal generation
│   │   ├── flux_daily_scanner_v2.py     # 6-factor automated scanner
│   │   ├── daily_trading_checklist.py   # Active trade monitoring
│   │   └── generate_economist_brief.py  # PDF report generation
│   ├── scrapers/              # Data collection & sentiment
│   │   └── news_sentiment_api.py        # News monitoring & risk alerts
│   ├── utilities/             # Helper functions
│   └── legacy/                # Archive & older scripts
│
├── wavelet_analysis/          # Wavelet analysis per ticker
│   ├── BUMI/, RLCO/, etc.    # Per-symbol CWT visualizations
│   └── generic_wavelet_visualization.py
│
├── REPORTS/                   # Reports & documentation
│   ├── daily-reports/         # Daily trading plans (TRADING_REPORT_20JAN2026.md)
│   ├── elite-strategy/        # Elite strategy Quarto reports
│   ├── market-beating-methods/ # Analysis of trading methods
│   └── logs/                  # Execution logs
│
├── results/                   # Analysis outputs & final picks
│   ├── elite_strategy_candidates.json
│   └── watchlist_final_20stocks.txt
│
├── docs/                      # Documentation & guides
│   ├── START_HERE.txt
│   ├── COMPLETE_OVERVIEW.md
│   ├── ALTERNATIVE_ANALYSIS_METHODS.md
│   ├── WAVELET_ANALYSIS_README.md
│   ├── WAVELET_RESULTS_SUMMARY.md
│   └── [other guides]
│
└── artifacts/                 # Build artifacts (PDFs, LaTeX)
    └── latex/
```

---

## 🎯 Core Trading Strategy

**Strategy:** Institutional Accumulation in Declining Stocks + Technical Reversal  
**Backtest Results:** 9,906 trades | 42.34% win rate | 0.70% avg return | Sharpe 1.90  
**Holding Period:** 5 days mechanical (Entry Day 1, Exit Day 5)  

**Entry Filters (6-Factor Score ≥60/100):**
1. **Broker Concentration** (20%) – Single foreign broker ≥40% of buying (DBR)
2. **Fundamentals** (15%) – Low PER/PBV, positive ROE (MUST PASS)
3. **Technical Reversal** (25%) – -5% to -0.5% decline + +1% intraday bounce (MUST PASS)
4. **Volume** (15%) – Daily volume ≥120% of 5-day average
5. **Sector Momentum** (10%) – Sector gaining MTD
6. **VWAP Entry** (15%) – Current price 9,906 historical trades (Dec 2025 - Jan 2026)
- `data/news_cache/sentiment_*.csv` – Daily sentiment analysis reports
- `data/news_cache/ALERT_*.json` – Critical news alerts by stock

### Daily Trading Scripts
- `scripts/analysis/flux_daily_scanner_v2.py` – Automated 6-factor signal scanner
- `scripts/analysis/daily_trading_checklist.py` – Active position monitoring + exit alerts
- `scripts/analysis/generate_economist_brief.py` – Economist-style PDF brief generator
- `scripts/scrapers/news_sentiment_api.py` – News risk monitoring (Google News RSS)

### Reports & Signals
- `REPORTS/daily-reports/` – Daily economist-style briefs (e.g., 21JAN2026_TRADING_BRIEF.pdf)
- `results/watchlist_final_20stocks.txt` – Current watchlist

### Analysis (Historical)
- `data/histories/wavelet_scores_top10.json` – Wavelet momentum validation
- `results/elite_strategy_candidates.json` – Confluence screening results
- `scripts/analysis/augment_prices_19jan.py` – Update price series with latest closes
- `scripts/analysis/wavelet_validate_top10.py` – Run wavelet analysis on candidates
- `wavelet_analysis/generic_wavelet_visualization.py` – Generate CWT plots

### Reports
- `REPORTS/daily-reports/TRADING_REPORT_20JAN2026.md` – Tomorrow's trading plan
- `REPORTS/TRADING_REPORT_20JAN2026.qmd` – Quarto version for PDF rendering
- `REPORTS/elite-strategy/ELITE_STRATEGY_IDR.qmd` – Elite strategy deep-dive

### Results
- `results/elite_strategy_candidates.json` – Top candidates by confluence
- `results/watchlist_final_20stocks.txt` – Final watchlist

---

## 🔬 Analysis Methods

### Wavelet Analysis
Mult1. Flux Trading System (Current Production)
**Foreign Institutional Accumulation + Technical Reversal**

Identifies stocks where:
- Single foreign broker ("dominant buyer") accumulates ≥40% of volume
- Stock declined 5% but bounced >1% intraday (reversal confirmation)
- Fundamentals attractive (low multiples, positive ROE)
- Volume confirms institutional conviction

**Real-World Validation (21 Jan 2026):**
- ✅ **ADRO** recommendation: Entry Rp 2,030 → Current Rp 2,210 (+8.87%)
- ❌ **ASII** rejected: Score 60/100 but no technical bounce → Fell -8.93%
- Key insight: Technical reversal filter prevented false signal

### 2. News Sentiment Monitor (New - 21 Jan 2026)
**Real-time regulatory & corporate risk detection**

Monitors Google News RSS for:
- Regulatory keywords: "dicabut" (permit revoked), "pencabutan izin", "suspend", "sanksi"
- Operational crises: "bencana", "shutdown", "force majeure"
- Corporate scandals: "korupsi", "fraud", "default"

**Detected Signals:**
- ASII: -6.1 sentiment score | 23 critical alerts | Agincourt permit revoked ← Prevented trade
- UNTR: -14.8 sentiment score | 43 critical alerts | Subsidiary risk exposure
- News break at 11:26 AM today, triggered crash immediately
Pre-Market (8:00 AM)
```bash
# 1. Check for critical news (30 seconds)
python scripts/scrapers/news_sentiment_api.py --stocks ADRO,ASII,UNTR,BBRI

# 2. Run signal scanner (2 minutes)
python scripts/analysis/flux_daily_scanner_v2.py

# 3. Generate economist brief (1 minute)
python scripts/analysis/generate_economist_brief.py

# 4. Review active positions (2 minutes)
python scripts/analysis/daily_trading_checklist.py
```

### Market Hours (9:30 AM - 4:00 PM)
1. Monitor STRONG BUY signals for entry (check volume confirmation)
2. Monitor active trades for exit signals (Day 5 = automatic exit)
Key guides and references:

- **ECONOMIST_BRIEF_README.md** – How to set up automated daily report generation
- **ECONOMIST_STYLE_IMPLEMENTATION.md** – Design decisions & style guide
- **Complete Overview:** `docs/COMPLETE_OVERVIEW.md`
- **Project Structure:** `docs/PROJECT_STRUCTURE.md`
- **Historical Methods:** `docs/WAVELET_ANALYSIS_READM
3. Review sentiment alerts for overnight research

---

## 📝 News Sentiment Monitor

**Command:**
```bash
python scripts/scrapers/news_sentiment_api.py --stocks STOCKS --hours 24
```

**Output:**
- CSV summary with sentiment scores
- JSON alerts for critical news
- Recommendation: IMMEDIATE EXIT (critical), REDUCE POSITION (negative), or HOLD

**Critical Keywords (Trigger Immediate Exit):**
- Regulatory: dicrequests, feedparser, beautifulsoup4
- Quarto 1.5+ (for PDF reports)
- TinyTeX/xelatex (for LaTeX rendering)

### Installation
```bash
# Python packages
pip install pandas numpy requests feedparser beautifulsoup4 openpyxl pywavelets

# Quarto & LaTeX (macOS)
brew install quarto
quarto install tinytex
```

### Optional
- Jupyter for interactive analysis
- R (ggplot2, tibble, scales) for advanced charting +10: POSITIVE (monitor for entry)-reports/TRADING_REPORT_[DATE].md`
3. Check broker activity: `data/reference/Ringkasan Broker-[DATE].xlsx`

### Market Hours
1. Monitor breakouts on watchlist (Tier 1 priority)
2. Enter on volume confirmation (≥1.5× MA20)
3. Set stops immediately (-2% or below MA10)
## 📊 Performance Tracking

**Backtest Validation (Dec 2025 - Jan 2026):**
- Total signals: 9,906
- Win rate: 42.34%
- Average return: +0.70%
- Sharpe ratio: 1.90
- Best week: +12.4% (week of Jan 6)

**Live Trading (Jan 2026):**
- Active position: ADRO (+8.87%, Exit Day 5: Jan 23)
- Rejected: ASII (-8.93%, prevented by technical reversal filter)
- News alerts: 15 monitored, 2 genuine critical (ASII/UNTR)

---

**Last Updated:** 21 January 2026  
**Project Status:** Production Trading + Research  
**Repository:** https://github.com/arifpras/flux
2. Update price series if needed
3. Review wavelet signals for next day

---

## 📚 Documentation

- **START_HERE:** `docs/START_HERE.txt`
- **Complete Overview:** `docs/COMPLETE_OVERVIEW.md`
- **Wavelet Guide:** `docs/WAVELET_ANALYSIS_README.md`
- **Alternative Methods:** `docs/ALTERNATIVE_ANALYSIS_METHODS.md`
- **Project Structure:** `docs/PROJECT_STRUCTURE.md`

---

## 🛠️ Tools & Dependencies

### Required
- Python 3.12+
- pandas, numpy, pywt, matplotlib
- Quarto 1.5+ (for PDF reports)
- TinyTeX (for LaTeX rendering)

### Installation
```bash
pip install pandas numpy pywavelets matplotlib openpyxl
brew install quarto  # macOS
quarto install tinytex
```

---

## 📝 Notes

- All dates in ISO format (YYYY-MM-DD)
- Prices in IDR unless specified
- Volume in shares, Value in Rupiah
- Wavelet scales: 1–31 (short to long-term patterns)
- Reports auto-generated via Quarto; edit .qmd sources, not PDFs

---

**Last Updated:** 20 January 2026  
**Project Status:** Active Trading  
**Next Review:** Daily pre-market analysis
