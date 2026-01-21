# 🔍 IDX Market Manipulation Detection System

Comprehensive toolkit for detecting and analyzing market manipulation patterns in Indonesian Stock Exchange (IDX) stocks.

## 📋 Overview

This system helps traders identify suspicious trading activities and manipulation patterns through:
- Real-time volume anomaly detection
- Pump & dump pattern recognition
- Price manipulation detection
- Broker concentration analysis
- Coordinated trading detection
- Smart money tracking

## 🎯 Key Features

### 1. **Volume Anomaly Detection**
- Identifies unusual volume spikes (>3x average)
- Z-score analysis for statistical outliers
- Anomaly severity scoring (0-100)

### 2. **Pump and Dump Detection**
- Detects rapid price increase + volume surge
- Identifies subsequent price collapse
- Confidence scoring based on magnitude

### 3. **Painting the Tape**
- Detects artificial price support/resistance
- Identifies repeated trades at same price
- Low volume but high frequency pattern

### 4. **End-of-Day Manipulation**
- Detects last-minute price manipulation
- Monitors closing price anomalies
- Flags >2% price jumps in final 10 minutes

### 5. **Broker Analysis**
- Market concentration metrics (HHI index)
- Top broker identification
- Aggressive accumulation detection
- Wash trading detection (buy ≈ sell)
- Coordinated trading patterns

## 📁 File Structure

```
stockscraper/
├── broker_analysis.py           # Core manipulation detection algorithms
├── manipulation_dashboard.py    # Real-time scanning dashboard
├── broker_scraper_idx.py       # IDX broker data scraper
├── scraper_yfinance.py         # Stock price data collector
└── IHSGstockdata/
    ├── minutes/                # Minute-level OHLCV data
    ├── broker/                 # Broker transaction data
    └── alerts/                 # Manipulation detection reports
```

## 🚀 Quick Start

### 1. Collect Stock Data
```bash
python scraper_yfinance.py
```

### 2. Run Manipulation Scan
```bash
python manipulation_dashboard.py
```

### 3. Analyze Specific Stock
```bash
python broker_analysis.py
```

### 4. Scrape Broker Data (Optional)
```bash
python broker_scraper_idx.py
```

## 📊 Detection Patterns

### High Risk Patterns 🚨

1. **Pump and Dump**
   - Price increase >10% with 2x volume surge
   - Followed by >5% decline
   - Common in low-cap stocks

2. **Volume Anomaly**
   - Volume >3x rolling average
   - Z-score >3 standard deviations
   - Often precedes major moves

3. **Broker Concentration**
   - Top 3 brokers >60% market share
   - HHI index >2500
   - Indicates potential collusion

4. **Wash Trading**
   - Broker buy ≈ sell values (>90% match)
   - Creates false liquidity impression
   - Illegal market manipulation

### Medium Risk Patterns ⚠️

1. **Painting the Tape**
   - Price appears at same level >30% of time
   - Low volume at those levels
   - Usually near market close

2. **Aggressive Accumulation**
   - Single broker >50% net buying
   - May indicate insider information
   - Monitor for price breakout

3. **Coordinated Trading**
   - 3+ brokers moving simultaneously
   - Same direction (all buy or all sell)
   - Within 5-minute window

## 📈 Usage Examples

### Example 1: Daily Scan
```python
from manipulation_dashboard import ManipulationDetector

detector = ManipulationDetector()
results = detector.scan_all_stocks(date='2026-01-15')

print(f"Total alerts: {results['total_alerts']}")
for alert in results['alerts']:
    if alert['risk_level'] == 'HIGH':
        print(f"🚨 {alert['stock_code']}: {alert['pattern']}")
```

### Example 2: Broker Analysis
```python
from broker_analysis import analyze_broker_concentration

# Load broker data
broker_data = pd.read_csv('IHSGstockdata/broker/BBRI_broker.csv')

# Analyze concentration
analysis = analyze_broker_concentration(broker_data)
print(f"HHI: {analysis['hhi']}")
print(f"Level: {analysis['concentration_level']}")
```

### Example 3: Smart Money Tracking
```python
from broker_scraper_idx import identify_smart_money

smart = identify_smart_money(broker_data, threshold=1e9)
print(smart[['broker_id', 'consistency_score', 'total_net_value']])
```

## 📋 Recent Scan Results (2026-01-15)

| Stock | Alerts | Pattern | Risk |
|-------|--------|---------|------|
| BUMI  | 1 | Volume Anomaly (27 occurrences) | HIGH |
| BMRI  | 1 | Volume Anomaly (27 occurrences) | HIGH |
| ASII  | 1 | Volume Anomaly (20 occurrences) | HIGH |
| AALI  | 1 | Volume Anomaly (14 occurrences) | HIGH |
| BBCA  | 1 | Volume Anomaly (19 occurrences) | HIGH |
| UNVR  | 2 | Volume Anomaly + Painting Tape | HIGH/MEDIUM |
| BBRI  | 1 | Volume Anomaly (18 occurrences) | HIGH |
| INDF  | 1 | Volume Anomaly (17 occurrences) | HIGH |

**Summary**: 9 total alerts detected across 8 stocks. All stocks showed volume anomalies on Jan 15, indicating unusually active trading day.

## 🎓 Understanding Manipulation Patterns

### What is Market Manipulation?
Market manipulation involves artificially inflating or deflating security prices through deceptive practices. Common tactics include:

1. **Pump and Dump**: Artificially inflate price then sell at peak
2. **Spoofing**: Place fake orders to move price, then cancel
3. **Layering**: Multiple orders at different prices to create false depth
4. **Wash Trading**: Buy and sell to yourself to create fake volume
5. **Painting the Tape**: Execute trades to create specific price levels

### Why Detect Manipulation?

- **Protect Capital**: Avoid buying pumped stocks
- **Follow Smart Money**: Identify institutional accumulation
- **Time Entries**: Enter after manipulation clears
- **Legal Compliance**: Report suspicious activities
- **Market Fairness**: Contribute to market integrity

### Trading Strategies

#### 1. **Anti-Manipulation Strategy**
- Avoid stocks with HIGH risk alerts
- Wait for volume to normalize
- Enter after pattern completion

#### 2. **Smart Money Following**
- Identify consistent net buyers
- Monitor broker concentration
- Follow institutional accumulation

#### 3. **Manipulation Fade**
- Short after pump detected
- Target return to pre-pump levels
- Use strict stop-loss

## ⚙️ Configuration

Edit thresholds in `broker_analysis.py`:

```python
# Manipulation thresholds
VOLUME_SPIKE_THRESHOLD = 3.0  # 3x average volume
PRICE_MANIPULATION_THRESHOLD = 0.05  # 5% price movement
WASH_TRADE_THRESHOLD = 0.8  # 80% buy/sell similarity
SPOOFING_CANCEL_RATE = 0.7  # 70% order cancellation
```

## 📊 Data Sources

### Current Implementation
- **Price Data**: Yahoo Finance (yfinance library)
- **Broker Data**: IDX Website (requires scraping)
- **Frequency**: 1-minute intervals
- **Timezone**: Asia/Jakarta (WIB)

### Alternative Data Sources
1. **RTI Business**: Real-time broker data subscription
2. **IDX Data**: Official data feed (paid)
3. **Third-party APIs**: Bloomberg, Reuters, etc.

## 🛠️ Technical Details

### Dependencies
```
pandas
numpy
yfinance
selenium
webdriver_manager
tqdm
requests
```

### Performance
- Scans 8 stocks in ~2-3 seconds
- Processes ~10,000 data points
- Generates JSON reports
- Memory efficient (streaming)

### Algorithms

1. **Volume Anomaly**: Rolling window + Z-score
2. **Pump & Dump**: Price momentum + volume surge
3. **Concentration**: Herfindahl-Hirschman Index (HHI)
4. **Wash Trading**: Balance ratio calculation
5. **Coordination**: Time-bin grouping + correlation

## 🚨 Risk Disclaimer

**This tool is for educational and research purposes only.**

- Not financial advice
- Past patterns don't predict future results
- Always conduct your own due diligence
- Manipulation detection has false positives
- Use in conjunction with other analysis methods
- Comply with local securities regulations

## 📝 Contributing

To add new detection patterns:

1. Add pattern to `ManipulationPattern` class
2. Implement detection function in `broker_analysis.py`
3. Add to scanning logic in `manipulation_dashboard.py`
4. Update thresholds in configuration
5. Test with historical data

## 📞 Support

For questions or issues:
- Check existing alerts in `IHSGstockdata/alerts/`
- Review detection scores and confidence levels
- Adjust thresholds for your risk tolerance
- Combine with fundamental analysis

## 🔄 Future Enhancements

- [ ] Real-time streaming analysis
- [ ] Machine learning pattern detection
- [ ] Telegram/Discord alert notifications
- [ ] Web dashboard with charts
- [ ] Historical pattern backtesting
- [ ] Multi-timeframe analysis
- [ ] Order book depth analysis
- [ ] Cross-stock correlation detection

## 📜 License

MIT License - Use at your own risk

## 🎯 Key Takeaways

1. **Volume Anomalies** = First sign of manipulation
2. **Broker Concentration** = Follow the smart money
3. **Pattern Confirmation** = Wait for multiple signals
4. **Risk Management** = Always use stop-loss
5. **Market Context** = Consider overall market conditions

---

**Remember**: The best defense against manipulation is knowledge. Stay informed, stay cautious, and always verify before trading.
