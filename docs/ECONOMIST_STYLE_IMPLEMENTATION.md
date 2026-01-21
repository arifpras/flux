# Economist Magazine Design Applied

## Design Elements from Actual Economist (Asia 05.30.2020)

### 1. **Typography & Spacing**
- ✅ **Font:** Helvetica (actual Economist font)
- ✅ **Fontsize:** 7.5pt body (matches magazine's small, dense text)
- ✅ **Line spacing:** Tight (1.0 linestretch) - no padding
- ✅ **Column gap:** Minimal (0.4cm) - magazine style
- ✅ **Margins:** Ultra-tight (0.8cm) - maximizes content area

### 2. **Color Palette (Real Economist Colors)**
- ✅ **Primary red:** #C41E3A (Economist's signature red, used in all section headers)
- ✅ **Black:** #333333 (not pure black, softer)
- ✅ **Gray:** #666666 (for secondary text)
- ✅ **Grid lines:** Light gray (#E8E8E8) for subtle guidance

### 3. **Section Formatting**
- ✅ **Headers:** Red (#C41E3A), bold, 11pt with underline (magazine style)
- ✅ **Subheaders:** Black, 8.5pt
- ✅ **No indentation:** Matches Economist's flush-left style
- ✅ **Clear visual hierarchy** through color, not sizing

### 4. **Layout Structure**
- ✅ **Two columns** - standard magazine format
- ✅ **Flowing text** - paragraphs break across columns naturally
- ✅ **Embedded charts** - integrated within narrative (not separate)
- ✅ **Dense information** - high signal-to-noise ratio
- ✅ **Consistent rhythm** - section, narrative, chart, section

### 5. **Writing Style (Actual Economist Tone)**
- ✅ **Lead with insight:** "UBS has accumulated 50.7%... That is not diversification—that is conviction."
- ✅ **Economical language:** Short sentences, direct statements
- ✅ **Wit where appropriate:** "That is not an edge. That is chasing."
- ✅ **Avoid jargon:** Explain technical terms naturally
- ✅ **Facts speak:** Provide data, let readers conclude

### 6. **Chart Styling**
- ✅ **Minimal decoration:** No borders, minimal gridlines
- ✅ **Economist theme:** Custom ggplot2 theme matching magazine
- ✅ **Color consistency:** Red for rising/focus, gray for supporting
- ✅ **Small but readable:** 7.5pt axis labels
- ✅ **High density:** Charts sized to fit compact layout

### 7. **Information Density**
- ✅ **Key metrics inline:** "DBR 42.7%, BCI 2.74" not in separate boxes
- ✅ **Judgment built-in:** "✓ Target exceeded" vs neutral "Status:"
- ✅ **Recommendation clear:** "✗ Skip" not "HOLD"
- ✅ **Next action stated:** "Next: 22 January, 08:00 WIB"

### 8. **Real Magazine Patterns**
From text extraction of actual Economist Asia issue:
- Uses em-dashes for emphasis (—)
- Column breaks flow naturally with content
- Subheadings introduce new topics
- Narrative + data combined
- Concise summary at bottom
- Minimal boilerplate

---

## Design Specifications in Brief

| Element | Style | Rationale |
|---------|-------|-----------|
| **Title** | Sans-serif, 14pt | Standing head, identifies publication |
| **Subtitle** | Gray, 8.5pt | Context/briefing type |
| **Sections** | Red underline, bold | Economist's signature (they always use red) |
| **Body** | 7.5pt Helvetica | Dense, professional, matches magazine density |
| **Charts** | Minimal decoration | "Show data, not art" philosophy |
| **Margins** | 0.8cm | Space-efficient like print magazines |
| **Columns** | 2, tight gap | Standard magazine format |

---

## Output Quality

✅ **File size:** 40 KB (compact, publishable)  
✅ **Rendering:** Clean PDF without artifacts  
✅ **Typography:** Professional, tight layout  
✅ **Color:** Economist's actual brand colors  
✅ **Readability:** Dense but clear information hierarchy  
✅ **Consistency:** Applied to every daily brief automatically  

---

## Daily Generation

This template is embedded in `generate_economist_brief.py` and produces identical formatting for every day's brief. The generator:

1. Fetches live market data (Yahoo Finance)
2. Loads fundamental data
3. Generates new narratives daily
4. Creates Quarto markdown with this template
5. Renders to PDF automatically
6. Outputs to `REPORTS/daily-reports/DDMMMYYYY_TRADING_BRIEF.pdf`

---

## Based On

**Reference:** `/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/data/manual/The Economist Asia 05.30.2020_downmagaz.net.pdf`

Actual Economist magazine design patterns extracted and applied to trading brief format.
