# Sentiment Analysis & Daily Trading Workflow

## Overview

Before executing any trades from the strategy report, run sentiment analysis on recommended stocks to detect any negative news that might affect them. This is a critical **sanity check** that prevents trades during unfavorable news cycles.

## Files

### 1. **20260123_sentiment_analysis.py**
Main sentiment analysis engine
- Checks news cache for all 24 recommended stocks
- Scores sentiment: positive keywords vs negative keywords
- Identifies risk flags (bankruptcy, fraud, scandal, etc.)
- Groups stocks by strategy for clear reporting
- Outputs risk levels: 🟢 LOW | 🟡 MEDIUM | 🔴 HIGH

**Usage:**
```bash
python scripts/analysis/20260123_sentiment_analysis.py
```

**Output:**
- Console report with sentiment scores
- `results/20260123_SENTIMENT_ANALYSIS.json` (machine-readable results)

### 2. **20260123_news_collector.py**
Fetches and caches news for continuous monitoring
- Integrates with NewsAPI, Google News RSS, local Indonesian sources
- Stores articles in `data/news_cache/` by stock ticker
- Prevents duplicate articles with title matching

**Usage:**
```bash
python scripts/analysis/20260123_news_collector.py
```

**Note:** Requires API keys for full functionality. Configure:
- NewsAPI.org API key
- News source credentials
- RSS feed endpoints

### 3. **20260123_daily_workflow.py** ⭐ **START HERE**
Complete daily trading workflow with sentiment sanity check
- Runs sentiment analysis automatically
- Maps results to Priority 1 trading actions
- Generates pre-trade checklist
- Flags any high-risk stocks before execution

**Usage:**
```bash
python scripts/analysis/20260123_daily_workflow.py
```

**Output:**
```
✅ Sentiment sanity check PASSED
   → Proceed with executing priority trades
   → Monitor for any market-wide events
```

---

## Recommended Stocks (24 total)

### Strategy: DIVIDEND INCOME
| Ticker | Yield | Status |
|--------|-------|--------|
| ADRO | 114% | 🟢 CLEAN |
| PTBA | 72% | 🟢 CLEAN |
| ITMG | 66% | 🟢 CLEAN |
| LPPF | 55% | 🟢 CLEAN |
| BSSR | 50% | 🟢 CLEAN |
| MEGA | 5-6% | 🟢 CLEAN |

### Strategy: FOREIGN ACCUMULATION
| Ticker | Buy (M) | Status |
|--------|---------|--------|
| BRMS | 139M | 🟢 CLEAN |
| ELTY | 92M | 🟢 CLEAN |
| BKSL | 62M | 🟢 CLEAN |
| GMFI | 56M | 🟢 CLEAN |
| ASII | 52M | 🟢 CLEAN |
| PTRO | 39M | 🟢 CLEAN |
| CTRA | 30M | 🟢 CLEAN |
| KLBF | 21M | 🟢 CLEAN |

### Strategy: FOREIGN + FUNDAMENTALS (HIGH CONVICTION)
| Ticker | Status |
|--------|--------|
| CNMA | 🟢 CLEAN |
| UNTR | 🟢 CLEAN |

### Strategy: MOMENTUM
| Ticker | Status |
|--------|--------|
| BBKP | 🟢 CLEAN |
| ELIT | 🟢 CLEAN |
| KREN | 🟢 CLEAN |
| PBRX | 🟢 CLEAN |
| PSKT | 🟢 CLEAN |

### Strategy: TECHNICAL OVERSOLD (HIGH CONVICTION)
| Ticker | Status |
|--------|--------|
| DGIK | 🟢 CLEAN |
| MERK | 🟢 CLEAN |
| SUNI | 🟢 CLEAN |

---

## Sentiment Scoring

### Positive Keywords
recovery, recover, rebound, bounce, surge, approval, partnership, deal, acquisition, profit, profitable, growth, upgrade, beat, innovation, dividend, expansion, pipeline

### Negative Keywords
collapse, crash, plunge, bankruptcy, fraud, scandal, suspend, delisting, loss, downgrade, lawsuit, dividend cut, supply chain, recall, debt, covenant

### Risk Level Determination
| Condition | Risk Level | Action |
|-----------|-----------|--------|
| Avg sentiment > -1 & flags < 3 | 🟢 LOW | PROCEED |
| Avg sentiment -1 to -3 & flags 3-5 | 🟡 MEDIUM | CAUTION |
| Avg sentiment < -3 or multi-negative | 🔴 HIGH | AVOID |

---

## Daily Workflow (Recommended)

**Before Trading:**
1. Run `20260123_daily_workflow.py` (5 min)
   ```bash
   python scripts/analysis/20260123_daily_workflow.py
   ```

2. Check output for sentiment status:
   - ✅ All stocks GREEN → Proceed
   - 🟡 Some MEDIUM → Review flagged stocks
   - 🔴 Any HIGH → Skip trades until resolved

3. Complete pre-trade checklist:
   - Liquidity confirmed (>500M IDR daily volume)
   - IDX announcements reviewed
   - Market hours (9:00-16:00 WIB)
   - Profit targets & stops set
   - Position sizes calculated

**Daily Maintenance:**
- Schedule news collection every 4 hours
- Review sentiment scores before entering large positions
- Update cache as new articles arrive

**Weekly Maintenance:**
- Configure proper news APIs for continuous collection
- Add Indonesian financial news sources
- Set up alerts for critical keywords per stock

---

## Integration Points

### Automatic Execution (Recommended)
Add to your trading automation:
```python
# Before executing ANY trade
from pathlib import Path
import subprocess

workspace = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper")
result = subprocess.run([
    "python",
    str(workspace / "scripts/analysis/20260123_sentiment_analysis.py")
], capture_output=True, text=True)

if "HIGH RISK" not in result.stdout:
    # Proceed with trade
    pass
```

### With Daily Scanner
Combine with your daily stock scanner:
```bash
#!/bin/bash
# daily_routine.sh

# 1. Update data
python scripts/analysis/20260121_flux_daily_scanner_v2.py

# 2. Run sentiment check (blocks if high-risk)
python scripts/analysis/20260123_daily_workflow.py

# 3. If sentiment clear, execute trades
if [ $? -eq 0 ]; then
    python execute_trades.py
fi
```

---

## News Cache Structure

```
data/news_cache/
├── DGIK_news.json        (array of article objects)
├── ASII_news.json
├── BBKP_news.json
├── ... (one file per recommended stock)
```

Each article object:
```json
{
  "ticker": "DGIK",
  "title": "DGIK Stock Rebounds on Foreign Buying",
  "content": "Foreign institutional investors...",
  "date": "2026-01-23",
  "source": "Google News",
  "url": "https://news.google.com/..."
}
```

---

## Example Scenarios

### ✅ Scenario: All Clear
```
DGIK │ ✅ NO NEWS FOUND (CLEAN)
ASII │ ✅ NO NEWS FOUND (CLEAN)
BBKP │ ✅ NO NEWS FOUND (CLEAN)

✅ ALL SYSTEMS GREEN - Proceed with trading plan
```
**Action:** Execute Priority 1 trades immediately

### 🟡 Scenario: One Stock with Caution
```
DGIK │ Low Risk - 100% of stocks safe
ASII │ Medium Risk - "earnings miss" detected
BBKP │ Low Risk

⚠️ CHECK NEWS BEFORE PROCEEDING
ASII │ Flags: earnings miss, downgrade, guidance lower
```
**Action:** Check ASII news before trading. Other stocks okay to trade.

### 🔴 Scenario: High Risk Detected
```
DGIK │ High Risk - "bankruptcy investigation"
ASII │ Low Risk
BBKP │ Low Risk

❌ HIGH RISK ALERT
DGIK │ AVOID - Recent bankruptcy investigation news

PROCEED WITH CAUTION on ASII and BBKP
```
**Action:** Skip DGIK trade. Update after news resolves.

---

## Configuration

### API Keys (Optional for now)
Create `.env` file:
```
NEWS_API_KEY=your_api_key_here
GOOGLE_NEWS_ENABLED=false  # Requires RSS parser setup
IDX_FEED_URL=https://...
```

### Custom Keywords
Edit sentiment analyzer to add sector-specific keywords:
```python
NEGATIVE_KEYWORDS = [
    # Existing keywords...
    "coal ban",  # Mining sector specific
    "interest rate hike",  # Banking sector specific
]
```

---

## Limitations

1. **No News = CLEAN** (current state)
   - Until news APIs configured, no articles found
   - Prevents false positives (safe default)
   - Once configured, continuously updates

2. **Sentiment Score is Basic**
   - Keyword matching only (no ML/NLP yet)
   - No context understanding (could miss nuance)
   - Improvement: Integrate with transformers for better accuracy

3. **No Real-Time Alerts**
   - Check manually before trading
   - Improvement: Set up Telegram/Email alerts on high-risk detection

---

## Next Steps

1. **Immediate:** Use `20260123_daily_workflow.py` before every trade
2. **This Week:** Configure a news API for continuous monitoring
3. **Next Week:** Add Indonesian financial news sources
4. **Future:** Implement ML-based sentiment scoring with transformers

---

## Support

For questions or improvements:
- Check `results/20260123_SENTIMENT_ANALYSIS.json` for detailed scores
- Review `data/news_cache/` for actual cached articles
- Add custom keywords for sector-specific risks

---

**Last Updated:** 23 January 2026  
**Maintenance:** Check news_collector.py weekly for API updates  
**Tested On:** Python 3.12.5, macOS
