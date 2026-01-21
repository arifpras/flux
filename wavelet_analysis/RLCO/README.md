# RLCO Wavelet Analysis

This folder contains all wavelet analysis files for RLCO stock.

## Contents

### Analysis Scripts
- **wavelet_analysis_rlco.py** - Core wavelet analysis engine (293 lines)
  - Continuous Wavelet Transform (CWT)
  - Discrete Wavelet Decomposition (DWT)
  - Multi-scale signal generation
  - Shannon entropy calculation
  
- **wavelet_visualization_rlco.py** - Visualization generator (160 lines)
  - 5-panel professional charts
  - CWT heatmap, decomposition, energy distribution

### Output Files
- **RLCO_wavelet_analysis.png** - 5-panel visualization (853 KB, 4134×3537 @ 300 DPI)
- **RLCO_Wavelet_Report.pdf** - Professional PDF report (913 KB, 4 pages)

### Report Generation
- **generate_professional_report.py** - ReportLab PDF generator (294 lines)
- **RLCO_Wavelet_Report.qmd** - Quarto markdown (not used, switched to ReportLab)
- **RLCO_Wavelet_Report.tex** - LaTeX output (auto-generated)
- **RLCO_Wavelet_Report.aux** - LaTeX auxiliary
- **RLCO_Wavelet_Report.log** - Build logs

## Key Results

**Signal:** STRONG BUY (3/3)  
**Current Price:** 5,050 IDR  
**60-Day Return:** +2,134.51%  
**Volatility:** HIGH (entropy 4.51)  
**Signal Duration:** 4 consecutive days  

**Assessment:** Technically valid STRONG BUY signal, but late-stage parabolic move. High volatility indicates unpredictable behavior. Recommended to wait for pullback before entry.

## Usage

```bash
# Run analysis
python wavelet_analysis_rlco.py

# Generate visualization
python wavelet_visualization_rlco.py

# Generate PDF report
python generate_professional_report.py
```

## Date Range
December 8, 2025 - January 14, 2026 (23 trading days)
