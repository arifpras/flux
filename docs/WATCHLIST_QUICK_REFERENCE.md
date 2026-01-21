# 📋 IDX WATCHLIST FILTER - QUICK REFERENCE

## ⚡ Quick Start

```python
from scripts.utilities.watchlist_filter import WatchlistFilter

# Initialize once
filter = WatchlistFilter("data/histories/ringkasan_histories_combined.csv")

# Check stock
is_risky, reasons = filter.check_stock('BUMI')

# Filter DataFrame
clean_df, summary = filter.filter_dataframe(candidates_df)
```

## 🎯 Integration Points

### 1. Elite Strategy (Already Integrated)
```python
strategy = EliteStrategy('backtest_trades.csv', enable_watchlist_filter=True)
is_safe, reasons = strategy.is_stock_safe('BBRI')
```

### 2. Daily Screening
```python
# Before generating signals
raw_signals = get_your_signals()
clean_signals, summary = filter.filter_dataframe(raw_signals)
print(f"Excluded {summary['removed_count']} risky stocks")
```

### 3. Portfolio Review
```python
portfolio = ['BUMI', 'BBRI', 'TLKM']
analysis = filter.analyze_portfolio(portfolio)
filter.print_analysis(analysis)
```

## 🚫 Watchlist Criteria (11 Total)

### Automated Detection ✅
- **#1**: Price <Rp51 + Low liquidity (value <Rp5M, vol <10K/day)
- **#7**: Low liquidity only (value <Rp5M, vol <10K/day for 90 days)

### Manual Updates Required ⚠️
- **#2**: Disclaimer audit opinion
- **#3**: No revenue / flat revenue
- **#4**: Mining co. without revenue by year 4
- **#5**: Negative equity
- **#6**: Listing violations
- **#8-9**: PKPU/bankruptcy
- **#10**: Trading suspension >1 day
- **#11**: OJK discretionary

## 📁 Files

```
stockscraper/
├── scripts/utilities/
│   └── watchlist_filter.py         # Main filter module
├── data/manual/
│   ├── idx_watchlist_official.csv  # Official watchlist (update weekly)
│   └── idx_watchlist_official_template.txt  # Template
└── docs/
    └── WATCHLIST_FILTER_GUIDE.md   # Full documentation
```

## 🔄 Weekly Maintenance

1. **Check IDX website** for watchlist updates
2. **Update** `idx_watchlist_official.csv` with new entries
3. **Refresh** historical data: `ringkasan_histories_combined.csv`
4. **Re-run** portfolio analysis to catch new flags

## 📊 Thresholds

```python
WatchlistFilter.PRICE_THRESHOLD = 51          # Rp
WatchlistFilter.VOLUME_THRESHOLD = 10000      # shares/day
WatchlistFilter.VALUE_THRESHOLD = 5000000     # Rp/day (5M)
WatchlistFilter.LIQUIDITY_PERIOD_DAYS = 90    # days
```

## 💡 Pro Tips

1. **Initialize once** - Reuse filter instance across checks (~10MB memory)
2. **Check before entry** - Filter candidates before generating signals
3. **Monitor holdings** - Weekly scan of existing positions
4. **Log exclusions** - Track which stocks are filtered and why
5. **Review false positives** - Some high-volatility stocks may trigger wrongly

## ⚠️ Common Issues

### "No historical data found"
→ Update `ringkasan_histories_combined.csv` or disable filter

### "Error loading watchlist file"
→ Check CSV format (no comment lines in data section)

### False positives
→ Adjust thresholds or use official list only

## 🔗 Resources

- IDX Watchlist: https://www.idx.co.id/
- Full docs: [WATCHLIST_FILTER_GUIDE.md](WATCHLIST_FILTER_GUIDE.md)
- Code: [watchlist_filter.py](../scripts/utilities/watchlist_filter.py)

---
**Last Updated**: January 19, 2026
