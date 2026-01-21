# 📈 Perisai Stock Trading System

**Advanced Day Trading Strategy with Market-Beating Methods**

---

## 🚀 Quick Start

### Run Wavelet Analysis
```bash
python scripts/analysis/wavelet_validate_top10.py
```

### Generate Daily Trading Report
```bash
quarto render REPORTS/TRADING_REPORT_20JAN2026.qmd
```

### View Latest Results
```bash
cat results/elite_strategy_candidates.json
cat data/histories/wavelet_scores_top10.json
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
│   ├── analysis/              # Active analysis tools (augment_prices, wavelet_validate)
│   ├── analysis-archive/      # Archived one-off analysis scripts
│   ├── scrapers/              # Data collection
│   ├── trading/               # Trading strategies & execution
│   └── utilities/             # Helper functions
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

**Proven Method:** 2–3 day momentum with +5% target, -2% stop  
**Position Sizing:** 25% per stock, 3 positions max  
**Entry:** Break above prior day high, volume ≥ 1.5× MA20  
**Exit:** +5% or end of day 3, whichever comes first  

---

## 📊 Key Files

### Data
- `data/backtest/backtest_trades.csv` – Historical trades with entry/exit prices
- `data/histories/augmented_prices_5stocks.csv` – Price series with latest closes
- `data/histories/wavelet_scores_top10.json` – Wavelet validation scores
- `data/reference/Ringkasan Broker-20260119.xlsx` – Broker turnover summary

### Scripts
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
Multi-scale momentum detection using Continuous Wavelet Transform (Morlet wavelet, scales 1–31).

**Strength Classification:**
- **STRONG:** Alignment > 0.6, Total Energy > 0.5
- **MODERATE:** Alignment > 0.4, Total Energy > 0.2
- **WEAK:** Below moderate thresholds

**Validated Top 4 (as of 19 Jan 2026):**
1. INCO (1.050) – STRONG + UP trend
2. MDKA (1.050) – STRONG + UP trend
3. ADRO (1.050) – STRONG + UP trend
4. ANTM (1.050) – STRONG + UP trend

### Confluence Screening
Stocks appearing across multiple strong technical screens:
- Foreign Flow Uptrend
- 1-Month Net Foreign Flow
- Big Accumulation
- Price Breakout MA20/MA10
- Almost 52-Week High

---

## 📈 Daily Workflow

### Morning (Pre-Market)
1. Run wavelet validation: `python scripts/analysis/wavelet_validate_top10.py`
2. Review daily report: `REPORTS/daily-reports/TRADING_REPORT_[DATE].md`
3. Check broker activity: `data/reference/Ringkasan Broker-[DATE].xlsx`

### Market Hours
1. Monitor breakouts on watchlist (Tier 1 priority)
2. Enter on volume confirmation (≥1.5× MA20)
3. Set stops immediately (-2% or below MA10)

### Post-Market
1. Log trades and outcomes
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
