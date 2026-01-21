# IDX Watchlist Filter Integration Guide

## Overview

The `watchlist_filter.py` module implements automated filtering of risky stocks based on IDX Watchlist Board criteria. It protects your trading strategies from stocks with regulatory red flags.

## Quick Start

```python
from scripts.utilities.watchlist_filter import WatchlistFilter

# Initialize with historical data
filter = WatchlistFilter(
    historical_data_path="data/histories/ringkasan_histories_combined.csv"
)

# Check single stock
is_risky, reasons = filter.check_stock('BUMI')
if is_risky:
    print(f"⚠ BUMI is risky: {reasons}")

# Filter your trading candidates
candidates_df = pd.read_csv('your_candidates.csv')
clean_df, summary = filter.filter_dataframe(candidates_df)
print(f"Filtered {summary['removed_count']} risky stocks")
```

## Integration with Elite Strategy

Add watchlist filtering to your elite strategy:

```python
# In elite_strategy.py or your trading script

from scripts.utilities.watchlist_filter import WatchlistFilter

class EliteStrategy:
    def __init__(self, backtest_file, threshold_return=1.0):
        # ... existing code ...
        
        # Add watchlist filter
        self.watchlist_filter = WatchlistFilter(
            historical_data_path="data/histories/ringkasan_histories_combined.csv"
        )
    
    def get_trading_candidates(self, date):
        """Get elite stocks with watchlist filtering."""
        
        # Get your normal candidates
        candidates = self.elite_stocks.copy()
        
        # Filter out watchlist stocks
        safe_candidates = []
        for stock in candidates.index:
            is_risky, reasons = self.watchlist_filter.check_stock(stock)
            
            if not is_risky:
                safe_candidates.append(stock)
            else:
                print(f"⚠ Excluded {stock}: {reasons[0]}")
        
        return safe_candidates
```

## Criteria Implemented

### Automated Detection (from price/volume data)

✅ **Criteria 1**: Low price (<Rp51) + low liquidity  
✅ **Criteria 7**: Low liquidity (avg daily value <Rp5M, volume <10K for 90 days)

### Requires Manual Data (supplement with official watchlist)

⚠ **Criteria 2**: Disclaimer audit opinion  
⚠ **Criteria 3**: No revenue or flat revenue  
⚠ **Criteria 4**: Mining companies without revenue by year 4  
⚠ **Criteria 5**: Negative equity  
⚠ **Criteria 6**: Listing requirement violations  
⚠ **Criteria 8-9**: PKPU/bankruptcy proceedings  
⚠ **Criteria 10**: Trading suspensions >1 day  
⚠ **Criteria 11**: OJK discretionary conditions

## Methods

### `check_stock(stock_code, price, volume, value)`

Check if a single stock meets watchlist criteria.

**Args:**
- `stock_code`: Stock ticker (e.g., 'BUMI')
- `price`: Current price (optional if historical data loaded)
- `volume`: Average daily volume (optional)
- `value`: Average daily value (optional)

**Returns:**
- `(bool, list)`: (is_on_watchlist, [reasons])

**Example:**
```python
is_risky, reasons = filter.check_stock('BUMI')
if is_risky:
    print(f"Risk factors: {', '.join(reasons)}")
```

### `filter_dataframe(df, ...)`

Filter DataFrame to remove risky stocks.

**Args:**
- `df`: DataFrame with stock data
- `stock_col`: Column with stock codes (default: 'Kode Saham')
- `price_col`: Column with prices (default: 'Penutupan')
- `volume_col`: Column with volumes (default: 'Volume')
- `value_col`: Column with trading values (default: 'Nilai')
- `inplace`: Modify DataFrame in place (default: False)

**Returns:**
- `DataFrame`: Filtered DataFrame
- `dict`: Summary with removed stocks

**Example:**
```python
clean_df, summary = filter.filter_dataframe(candidates_df)
print(f"Removed {summary['removed_count']} stocks:")
for stock, reasons in summary['removed_stocks'].items():
    print(f"  {stock}: {reasons}")
```

### `analyze_portfolio(stock_list)`

Analyze risk profile of a portfolio.

**Args:**
- `stock_list`: List of stock codes

**Returns:**
- `dict`: Analysis with safe/risky stocks categorized

**Example:**
```python
analysis = filter.analyze_portfolio(['BUMI', 'BBRI', 'TLKM'])
filter.print_analysis(analysis)
```

### `calculate_liquidity_metrics(stock_code, days=90)`

Calculate average liquidity metrics over specified period.

**Returns:**
- `dict`: {'avg_volume', 'avg_value', 'trading_days', 'avg_price', 'latest_price'}

## Using Official Watchlist

For criteria that can't be automated (fundamentals, regulatory issues), maintain a CSV/Excel with officially flagged stocks:

```python
from scripts.utilities.watchlist_filter import load_official_watchlist

# Load official watchlist
official_list = load_official_watchlist(
    "data/manual/idx_watchlist_official.csv"
)

# Check against official list
if stock_code in official_list:
    print(f"⚠ {stock_code} is on official IDX watchlist")
```

## Integration Examples

### 1. Pre-filter Trade Candidates

```python
# Before generating signals
raw_candidates = get_broker_accumulation_signals()
clean_candidates, _ = watchlist_filter.filter_dataframe(raw_candidates)

# Now generate signals only from clean candidates
signals = generate_trading_signals(clean_candidates)
```

### 2. Validate Backtest Results

```python
# After backtest
results = run_backtest()

# Check which trades involved risky stocks
risky_trades = []
for _, trade in results.iterrows():
    is_risky, reasons = filter.check_stock(trade['Kode Saham'])
    if is_risky:
        risky_trades.append({
            'stock': trade['Kode Saham'],
            'return': trade['NetPnL'],
            'risks': reasons
        })

print(f"⚠ {len(risky_trades)} trades involved watchlist stocks")
```

### 3. Daily Screening Workflow

```python
# Daily screening script
def screen_daily_candidates(date):
    # Get candidates from various sources
    broker_signals = get_broker_accumulation()
    momentum_stocks = get_momentum_breakouts()
    elite_stocks = get_elite_winners()
    
    # Combine and deduplicate
    all_candidates = pd.concat([
        broker_signals, momentum_stocks, elite_stocks
    ]).drop_duplicates(subset='Kode Saham')
    
    # Apply watchlist filter
    clean_candidates, summary = filter.filter_dataframe(all_candidates)
    
    # Report
    print(f"📊 Daily Screening Results for {date}")
    print(f"   Raw candidates: {summary['original_count']}")
    print(f"   Watchlist filtered: {summary['removed_count']}")
    print(f"   Clean candidates: {summary['remaining_count']}")
    
    if summary['removed_stocks']:
        print(f"\n   ⚠ Excluded stocks:")
        for stock, reasons in summary['removed_stocks'].items():
            print(f"      {stock}: {reasons[0]}")
    
    return clean_candidates
```

## Performance Considerations

- **First-time load**: ~1-2 seconds for 27K+ historical records
- **Per-stock check**: ~0.001 seconds (sub-millisecond)
- **DataFrame filtering**: ~0.1 seconds for 100 stocks

Memory usage: ~10MB for full historical dataset.

## Best Practices

1. **Initialize once**: Create filter instance at startup, reuse throughout session
2. **Update regularly**: Refresh historical data daily for accurate liquidity metrics
3. **Combine approaches**: Use both automated checks + official watchlist CSV
4. **Log exclusions**: Track which stocks are filtered and why
5. **Review periodically**: Stocks can move on/off watchlist - review quarterly

## Thresholds (Configurable)

```python
WatchlistFilter.PRICE_THRESHOLD = 51          # Rupiah
WatchlistFilter.VOLUME_THRESHOLD = 10000      # shares/day
WatchlistFilter.VALUE_THRESHOLD = 5000000     # Rupiah/day (5M)
WatchlistFilter.LIQUIDITY_PERIOD_DAYS = 90    # 3 months
```

## Testing

Run the module directly to test with examples:

```bash
cd /Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper
python scripts/utilities/watchlist_filter.py
```

## Further Development

Consider adding:

1. **API integration**: Fetch live watchlist from IDX
2. **Alert system**: Notify when portfolio stock hits watchlist
3. **Historical tracking**: Log when stocks enter/exit watchlist
4. **ML-based prediction**: Predict stocks likely to hit watchlist
5. **Fundamental checks**: Auto-fetch financial statements for criteria 2-6

## References

- IDX Regulation I-X: Securities on Watchlist Board
- Data source: Securities on Watchlist Board-20260102-20260119.xlsx
- IDX website: https://www.idx.co.id/
