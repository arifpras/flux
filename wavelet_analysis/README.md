# Wavelet Analysis for Stock Trading

This directory contains wavelet analysis implementations for Indonesian stock trading, using Continuous Wavelet Transform (CWT) and Discrete Wavelet Decomposition (DWT) to identify multi-scale trading signals.

## Directory Structure

```
wavelet_analysis/
├── RLCO/                          # RLCO stock analysis
│   ├── wavelet_analysis_rlco.py
│   ├── wavelet_visualization_rlco.py
│   ├── generate_professional_report.py
│   ├── RLCO_wavelet_analysis.png
│   ├── RLCO_Wavelet_Report.pdf
│   └── README.md
│
├── BUMI/                          # BUMI stock analysis
│   ├── analyze_bumi_wavelet.py
│   └── README.md
│
├── WAVELET_ANALYSIS_README.md     # Complete methodology guide
├── WAVELET_RESULTS_SUMMARY.md     # Detailed technical analysis
├── QUICK_START_WAVELET.md         # Trading rules & quick reference
└── README.md                      # This file
```

## Quick Comparison: RLCO vs BUMI

| Stock | Signal | Price Move | Entropy | Volatility | Entry Quality | Verdict |
|-------|--------|-----------|---------|------------|---------------|---------|
| **RLCO** | STRONG BUY (3/3) | +2,134% | 4.51 (HIGH) | HIGH | LATE | ⚠️ Risky |
| **BUMI** | STRONG BUY (3/3) | +87.80% | 2.24 (LOW) | LOW | EARLY | ✅ IDEAL |

## Key Insights

### RLCO Analysis
- **Status:** Late-stage parabolic move
- **Risk:** HIGH volatility and entropy
- **Assessment:** Technically valid but poor risk/reward
- **Recommendation:** Wait for pullback

### BUMI Analysis  
- **Status:** Fresh breakout (just reached 3/3)
- **Risk:** LOW volatility with organized trend
- **Assessment:** SUPERIOR setup - early entry, institutional backing
- **Recommendation:** STRONG BUY - Execute with 75-100% position

## Methodology

**Wavelet Type:** Morlet (gold standard for financial markets)  
**Analysis Method:** Continuous Wavelet Transform (CWT)  
**Signal Generation:** Multi-scale alignment across 3 timeframes:
- Short-term (Scale ~8): Daily entry/exit
- Medium-term (Scale ~16): 3-5 day momentum
- Long-term (Scale ~24): Weekly trend direction

**Confidence Metric:**
- 3/3 = STRONG BUY (all timeframes aligned)
- 2/3 = BUY (moderate confidence)
- 1/3 = NEUTRAL (mixed signals)
- 0/3 = SELL (all timeframes bearish)

## Key Differentiator: Entropy

**Shannon Entropy** measures signal complexity and predictability:

- **< 2.5 (LOW)** - Organized, predictable trend (BUMI: 2.24)
  - Lower risk
  - Institutional accumulation
  - Suitable for larger positions

- **2.5 - 3.5 (MODERATE)** - Normal market volatility
  - Moderate risk
  - Standard position sizing

- **> 3.5 (HIGH)** - Chaotic, unpredictable (RLCO: 4.51)
  - Higher risk
  - Reduce position size
  - Wait for consolidation

## Usage

### RLCO Analysis
```bash
cd wavelet_analysis/RLCO
python wavelet_analysis_rlco.py        # Run analysis
python wavelet_visualization_rlco.py   # Generate charts
python generate_professional_report.py # Create PDF report
```

### BUMI Analysis
```bash
cd wavelet_analysis/BUMI
python analyze_bumi_wavelet.py         # Run analysis
```

## Documentation

- **WAVELET_ANALYSIS_README.md** - Complete methodology, integration guide
- **WAVELET_RESULTS_SUMMARY.md** - Technical details, signal interpretation
- **QUICK_START_WAVELET.md** - Trading rules, quick reference

## Dependencies

```bash
pip install pywavelets numpy scipy matplotlib pandas reportlab
```

## Trading Integration

Wavelet analysis works best when combined with:
1. **Elite Strategy** - Fundamental quality scoring
2. **Broker Signals** - Institutional accumulation tracking (Stockbit)
3. **Wavelet Signals** - Multi-timeframe technical confirmation

**Example: BUMI Perfect Setup**
- Elite Score: 9.4/12.0 ✓
- Broker Signal: +27B IDR accumulation ✓
- Wavelet: Fresh 3/3 STRONG BUY ✓
- Entropy: 2.24 (LOW volatility) ✓
- **Result: Maximum confidence STRONG BUY**

## Next Steps

1. Monitor BUMI daily for signal degradation (3/3 → 2/3 = exit)
2. Apply wavelet analysis to remaining top 10 elite stocks
3. Build automated daily wavelet scanning system
4. Backtest wavelet-enhanced returns vs baseline elite strategy

## Date
January 19, 2026
