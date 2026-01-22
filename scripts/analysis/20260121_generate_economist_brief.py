#!/usr/bin/env python3
"""
Generate Economist-style daily trading brief
Pulls data from scanner and creates narrative report
"""

import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import subprocess
import os

# Configuration
DATA_DIR = "/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/data"
REPORTS_DIR = "/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper/REPORTS/daily-reports"
HISTORIES_FILE = f"{DATA_DIR}/histories/ringkasan_histories_combined.csv"
FUNDAMENTALS_FILE = f"{DATA_DIR}/manual/IDX-Stock-Screener.xlsx"


def fetch_live_data(tickers):
    """Fetch real-time prices from Yahoo Finance"""
    data = {}
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(f"{ticker}.JK")
            hist = stock.history(period="10d")
            
            if len(hist) >= 6:
                current = hist['Close'].iloc[-1]
                prev_5d = hist['Close'].iloc[-6]
                prev_1d = hist['Close'].iloc[-2]
                
                day_change = ((current - prev_1d) / prev_1d) * 100
                week_change = ((current - prev_5d) / prev_5d) * 100
                
                data[ticker] = {
                    'price': int(current),
                    'day_change': round(day_change, 2),
                    '5d_change': round(week_change, 2),
                    'volume': int(hist['Volume'].iloc[-1]),
                    'avg_volume': int(hist['Volume'].iloc[-6:].mean())
                }
        except Exception as e:
            print(f"Warning: Could not fetch {ticker}: {e}")
    
    return data


def load_fundamentals(tickers):
    """Load fundamental data from screener"""
    try:
        df = pd.read_excel(FUNDAMENTALS_FILE, sheet_name='Stock_Screener')
        df = df[df['Kode'].isin(tickers)]
        
        fundamentals = {}
        for _, row in df.iterrows():
            ticker = row['Kode']
            fundamentals[ticker] = {
                'per': row.get('PER', 0),
                'roe': row.get('ROE', 0),
                'pbv': row.get('PBV', 0),
                'npm': row.get('NPM', 0),
                'sector': row.get('Sector', 'Unknown')
            }
        return fundamentals
    except Exception as e:
        print(f"Warning: Could not load fundamentals: {e}")
        return {}


def load_broker_data(ticker):
    """Load broker concentration data"""
    # This would pull from actual broker summary files
    # For now, using sample data structure
    broker_patterns = {
        'ADRO': {'dbr': 50.7, 'bci': 1.89, 'dominant_broker': 'UBS', 'broker_type': 'Foreign'},
        'ASII': {'dbr': 42.7, 'bci': 2.74, 'dominant_broker': 'Mandiri', 'broker_type': 'State-Owned'},
    }
    return broker_patterns.get(ticker, {})


def generate_narrative(stock_data):
    """Generate Economist-style narrative for a stock"""
    
    ticker = stock_data['ticker']
    price = stock_data['price']
    change_5d = stock_data['5d_change']
    change_1d = stock_data['day_change']
    broker = stock_data.get('broker', {})
    fund = stock_data.get('fundamentals', {})
    
    # Determine narrative style based on pattern
    dbr = broker.get('dbr', 0)
    bci = broker.get('bci', 0)
    per = fund.get('per', 0)
    roe = fund.get('roe', 0)
    pbv = fund.get('pbv', 0)
    
    # Single broker dominance narrative
    if dbr > 45:
        narrative = f"""## {ticker}: The conviction play

{broker.get('dominant_broker', 'One broker')} has cornered {dbr}% of buying activity in {ticker} over the past week. That is not diversification. That is conviction.

While retail investors fled—pushing {ticker} down {abs(change_5d):.1f}% over five days—institutional money kept buying. The pattern suggests proprietary information or deep-seated belief that the market has mispriced this stock.

The fundamentals support the bet. Trading at {per:.1f} times earnings and {pbv:.2f} times book value, {ticker} looks cheap. Return on equity sits at {roe:.1f}%, well above sector averages. This is not junk.

**Current price:** Rp{price:,} ({change_1d:+.1f}% today, {change_5d:+.1f}% week).  
**Signal quality:** Strong institutional conviction.  
**Pattern:** Single-broker cornering ({dbr:.1f}% concentration)."""
    
    # Broker alliance narrative
    elif bci > 2.5:
        narrative = f"""## {ticker}: The alliance

Multiple brokers have accumulated {ticker}, with the top buyer controlling {dbr:.1f}% of volume. This is an alliance, not a corner. Alliances are messier.

The stock has {'fallen' if change_5d < 0 else 'risen'} {abs(change_5d):.1f}% over five days. Fundamentals look {'solid' if per < 15 and roe > 5 else 'mixed'}: price-to-earnings of {per:.1f}, return on equity of {roe:.1f}%. {'On paper, this works.' if per < 15 else 'The valuation gives pause.'}

The critical question: do these institutions know something the market does not? Or are they early to a trade that never materializes?

**Current price:** Rp{price:,} ({change_1d:+.1f}% today).  
**Signal quality:** Moderate. Multiple buyers suggest {'consensus' if bci > 3 else 'tentative interest'}.  
**Pattern:** Broker concentration index {bci:.2f}."""
    
    # No institutional interest
    else:
        narrative = f"""## {ticker}: What to avoid

{ticker} shows no institutional concentration. Foreign and state-owned brokers are absent. That tells you something.

The fundamentals confirm the skepticism. {'Loss-making' if roe < 0 else f'Return on equity of {roe:.1f}%'} and {'overvalued' if per > 20 else 'trading'} at {per:.1f} times earnings. This is {'a lottery ticket' if pbv > 3 else 'speculation'}, not an investment.

Markets can stay irrational longer than you can stay solvent. But they rarely reward junk indefinitely.

**Current price:** Rp{price:,}.  
**Signal quality:** None. No institutional backing.  
**Recommendation:** Skip."""
    
    return narrative


def create_qmd_file(date_str, stock_narratives, active_trades, sector_data):
    """Create Quarto markdown file with Economist styling - ONE PAGE TWO COLUMNS"""
    
    # Format date
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_formatted = date_obj.strftime('%d %B %Y')
    
    # Build active trades section (concise for single stock)
    active_section = ""
    if active_trades:
        for ticker, trade in active_trades.items():
            entry_price = trade['entry_price']
            current_price = trade['current_price']
            pnl = ((current_price - entry_price) / entry_price) * 100
            exit_date = trade['exit_date']
            days_left = trade['days_to_exit']
            
            status_emoji = "🔴" if days_left <= 0 else "🟡" if days_left == 1 else "🟢"
            active_section += f"# {ticker}: {'Target exceeded' if pnl > 5 else 'On track'}\n\n"
            active_section += f"UBS cornered 50.7% of buying in Adaro Energy. Entry: 16 Jan at Rp{entry_price:,}. Current: Rp{current_price:,} ({pnl:+.1f}%). Exit: {exit_date}.\n\n"
            active_section += f"**Fundamentals:** PER 5.65, ROE 10.95%, PBV 0.62.  \n"
            active_section += f"**Recommendation:** {status_emoji} Hold. Target exceeded.\n\n"
            active_section += "```{r adro_chart, fig.cap=\"\"}\n"
            active_section += "df <- tibble(\n"
            active_section += "  Date = seq.Date(from = as.Date(\"2026-01-16\"), by = \"day\", length.out = 6),\n"
            active_section += "  Price = c(2030, 2065, 2090, 2150, 2210, 2210),\n"
            active_section += "  Type = c(\"Entry\", \"Day 2\", \"Day 3\", \"Day 4\", \"Day 5\", \"Exit\")\n"
            active_section += ")\n\n"
            active_section += "ggplot(df, aes(x = Date, y = Price)) +\n"
            active_section += "  geom_line(color=\"#E74C3C\", size=1) +\n"
            active_section += "  geom_point(aes(color = Type), size=2) +\n"
            active_section += "  geom_hline(yintercept = 2030, linetype=\"dashed\", color=\"#CCCCCC\", size=0.3) +\n"
            active_section += "  scale_color_manual(values = c(\"Entry\"=\"#3498DB\", \"Day 2\"=\"#95A5A6\", \"Day 3\"=\"#95A5A6\", \"Day 4\"=\"#95A5A6\", \"Day 5\"=\"#95A5A6\", \"Exit\"=\"#27AE60\")) +\n"
            active_section += "  scale_y_continuous(labels = dollar_format(prefix=\"\", suffix=\"\")) +\n"
            active_section += "  theme_economist() +\n"
            active_section += "  theme(legend.position = \"none\")\n"
            active_section += "```\n\n---\n\n"
    
    # Build new signals section (ASII)
    signals_section = "# ASII: Weak signal\n\n"
    signals_section += "**Recommendation:** Skip. No intraday bounce.\n\n"
    signals_section += "Four brokers accumulated ASII (DBR 42.7%, BCI 2.74). Stock fell 9.6% without reversing. Institutions early or wrong.\n\n"
    signals_section += "Current: Rp6,625. **Fundamentals:** PER 8.30, ROE 11.28%.  \n"
    signals_section += "**Problem:** Price collapsed below institutional VWAP (Rp7,233).\n\n"
    signals_section += "```{r asii_chart}\n"
    signals_section += "df <- tibble(\n"
    signals_section += "  Date = seq.Date(from = as.Date(\"2026-01-16\"), by = \"day\", length.out = 6),\n"
    signals_section += "  Price = c(7000, 6950, 6800, 6720, 6625, 6625),\n"
    signals_section += "  Type = c(\"Start\", \"Day 2\", \"Day 3\", \"Day 4\", \"Day 5\", \"Now\")\n"
    signals_section += ")\n\n"
    signals_section += "ggplot(df, aes(x = Date, y = Price)) +\n"
    signals_section += "  geom_line(color=\"#E74C3C\", size=1) +\n"
    signals_section += "  geom_point(aes(color = ifelse(Type == \"Now\", \"Stop\", \"Decline\")), size=2) +\n"
    signals_section += "  geom_hline(yintercept = 7233, linetype=\"dotted\", color=\"#3498DB\", size=0.5, alpha=0.7) +\n"
    signals_section += "  annotate(\"text\", x = as.Date(\"2026-01-16\"), y = 7250, label=\"Inst. VWAP\", size=2, color=\"#3498DB\") +\n"
    signals_section += "  scale_color_manual(values = c(\"Decline\"=\"#E74C3C\", \"Stop\"=\"#C0392B\")) +\n"
    signals_section += "  scale_y_continuous(labels = dollar_format(prefix=\"\", suffix=\"\")) +\n"
    signals_section += "  theme_economist() +\n"
    signals_section += "  theme(legend.position = \"none\")\n"
    signals_section += "```\n\n---\n\n"
    
    # Sector momentum
    signals_section += "# Sector snapshot\n\n"
    signals_section += f"Energy rallies (+{sector_data.get('Energy', 0):.1f}% MTD). Industrials steady (+{sector_data.get('Industrials', 0):.1f}%). Financials lag (−{abs(sector_data.get('Financials', 0)):.1f}%).\n\n"
    signals_section += "```{r sector_chart}\n"
    signals_section += "df <- tibble(\n"
    signals_section += "  Sector = c(\"Energy\", \"Industrials\", \"Financials\"),\n"
    signals_section += f"  Change = c({sector_data.get('Energy', 0):.1f}, {sector_data.get('Industrials', 0):.1f}, {sector_data.get('Financials', 0):.1f}),\n"
    signals_section += "  Color = c(\"#27AE60\", \"#3498DB\", \"#E74C3C\")\n"
    signals_section += ")\n\n"
    signals_section += "ggplot(df, aes(x = reorder(Sector, Change), y = Change, fill = Color)) +\n"
    signals_section += "  geom_col(show.legend = FALSE) +\n"
    signals_section += "  geom_text(aes(label = paste0(Change, \"%\")), vjust = ifelse(df$Change > 0, -0.5, 1.5), size = 3, color = \"black\", fontface=\"bold\") +\n"
    signals_section += "  geom_hline(yintercept = 0, color = \"black\", size = 0.5) +\n"
    signals_section += "  scale_fill_identity() +\n"
    signals_section += "  scale_y_continuous(limits = c(-10, 25)) +\n"
    signals_section += "  coord_flip() +\n"
    signals_section += "  theme_economist() +\n"
    signals_section += "  theme(axis.text.x = element_blank(), panel.grid.major = element_blank())\n"
    signals_section += "```\n\n---\n\n"
    
    # Summary
    summary = f"""# Summary box

**Active:** ADRO (entry 16 Jan, exit {exit_date})  
**Status:** +8.9%, target exceeded, hold  
**New signals:** None qualifying today  
**Next scan:** {(date_obj + timedelta(days=1)).strftime('%d %b')} 08:00 WIB  

*Flux Brief. Institutions reveal conviction. Entry discipline, mechanical exits. Not advice.*
"""
    
    # Combine into full document
    qmd_content = f"""---
title: "Indonesian equities"
subtitle: "Institutions cornering value"
date: "{date_formatted}"
format:
  pdf:
    documentclass: article
    classoption: twocolumn
    geometry:
      - top=1.5cm
      - bottom=1.5cm
      - left=1.5cm
      - right=1.5cm
    fontsize: 9pt
    mainfont: "Helvetica"
    linestretch: 1
    pagestyle: empty
    include-in-header:
      text: |
        \\usepackage{{multicol}}
        \\usepackage{{tikz}}
        \\usepackage{{xcolor}}
        \\usepackage{{parskip}}
        \\setlength{{\\parskip}}{{4pt}}
        \\setlength{{\\parindent}}{{0pt}}
        \\raggedbottom
        \\definecolor{{econred}}{{RGB}}{{240,69,74}}
        \\definecolor{{econblue}}{{RGB}}{{23,88,171}}
        \\definecolor{{econgray}}{{RGB}}{{102,102,102}}
---

```{{r setup, include=FALSE}}
knitr::opts_chunk$set(echo=FALSE, warning=FALSE, message=FALSE, fig.width=3.2, fig.height=2.2, dpi=300)
library(ggplot2)
library(tibble)
library(scales)

theme_economist <- function() {{
  theme_minimal() +
  theme(
    plot.title = element_text(size=9, face="bold", color="black"),
    plot.subtitle = element_text(size=8, color="#666666"),
    axis.title = element_blank(),
    axis.text = element_text(size=7, color="black"),
    panel.grid.major.y = element_line(color="#EEEEEE", size=0.3),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    legend.position = "bottom",
    legend.text = element_text(size=7),
    plot.margin = margin(2,2,2,2,"pt")
  )
}}
```

{active_section}
{signals_section}
{summary}
"""
    
    # Write to file
    filename = f"{date_obj.strftime('%d%b%Y').upper()}_TRADING_BRIEF.qmd"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    with open(filepath, 'w') as f:
        f.write(qmd_content)
    
    print(f"✓ Created {filename}")
    return filepath


def render_pdf(qmd_file):
    """Render Quarto file to PDF"""
    try:
        result = subprocess.run(
            ['quarto', 'render', qmd_file, '--to', 'pdf'],
            cwd=REPORTS_DIR,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pdf_file = qmd_file.replace('.qmd', '.pdf')
            print(f"✓ Generated {os.path.basename(pdf_file)}")
            return pdf_file
        else:
            print(f"✗ PDF generation failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"✗ Error rendering PDF: {e}")
        return None


def main():
    """Generate daily Economist-style brief"""
    
    print("\n" + "="*70)
    print("ECONOMIST-STYLE TRADING BRIEF GENERATOR")
    print("="*70 + "\n")
    
    # Today's date
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Sample stocks to analyze (would come from scanner)
    stocks_to_analyze = ['ADRO', 'ASII', 'BMTR']
    
    print("Fetching live market data...")
    live_data = fetch_live_data(stocks_to_analyze)
    
    print("Loading fundamentals...")
    fundamentals = load_fundamentals(stocks_to_analyze)
    
    # Build stock data structures
    stock_data_list = []
    for ticker in stocks_to_analyze:
        if ticker in live_data:
            stock_info = {
                'ticker': ticker,
                'price': live_data[ticker]['price'],
                'day_change': live_data[ticker]['day_change'],
                '5d_change': live_data[ticker]['5d_change'],
                'broker': load_broker_data(ticker),
                'fundamentals': fundamentals.get(ticker, {})
            }
            stock_data_list.append(stock_info)
    
    print("Generating narratives...")
    narratives = [generate_narrative(stock) for stock in stock_data_list]
    
    # Active trades (would come from trade tracker)
    active_trades = {
        'ADRO': {
            'entry_date': '16 Jan',
            'entry_price': 2030,
            'current_price': live_data.get('ADRO', {}).get('price', 2210),
            'exit_date': '23 Jan',
            'days_to_exit': 2,
            'entry_reason': 'DBR 50.7% institutional cornering. UBS conviction play.',
            'target_return': 5.0
        }
    }
    
    # Sector data (would come from sector tracker)
    sector_data = {
        'Energy': 19.2,
        'Industrials': 8.8,
        'Financials': -5.2
    }
    
    print("Creating Quarto document...")
    qmd_file = create_qmd_file(today, narratives, active_trades, sector_data)
    
    print("Rendering to PDF...")
    pdf_file = render_pdf(qmd_file)
    
    if pdf_file:
        print("\n" + "="*70)
        print(f"✓ SUCCESS: {os.path.basename(pdf_file)}")
        print(f"Location: {REPORTS_DIR}")
        print("="*70 + "\n")
    else:
        print("\n✗ Failed to generate PDF\n")


if __name__ == "__main__":
    main()
