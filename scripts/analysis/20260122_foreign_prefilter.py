#!/usr/bin/env python3
"""
Foreign Accumulation Pre-Filter

Apply foreign accumulation filter at the START of strategy cascade.
This ensures we only analyze stocks with institutional interest.

Pattern 1: Foreign accumulation + declining price (buy-the-dip)
Pattern 2: Foreign accumulation + positive momentum (confirmation)

Inputs:
- data/histories/foreign_buy_stocks_last5days.csv : foreign flow
- data/histories/ringkasan_histories_combined.csv : price data
- results/flow_augmented_momentum_picks.csv : initial momentum signals

Outputs:
- results/foreign_filtered_picks.csv : momentum picks with foreign accumulation
- results/foreign_filter_report.txt : filtering summary
"""

from pathlib import Path
import pandas as pd
import numpy as np

FOREIGN_FILE = Path("data/histories/foreign_buy_stocks_last5days.csv")
HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
MOMENTUM_FILE = Path("results/flow_augmented_momentum_picks.csv")
OUTPUT_FILE = Path("results/foreign_filtered_picks.csv")
REPORT_FILE = Path("results/foreign_filter_report.txt")

MIN_FOREIGN_BUY = 500_000  # Minimum 500K shares (lowered threshold)


def load_foreign_data(path: Path) -> pd.DataFrame:
    """Load foreign accumulation data."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    # Filter positive net foreign buy
    df = df[df["Net Foreign Buy"] > MIN_FOREIGN_BUY].copy()
    return df[["Kode Saham", "Net Foreign Buy", "Foreign Buy", "Foreign Sell"]]


def calculate_price_patterns(hist: pd.DataFrame, stocks: list) -> pd.DataFrame:
    """Calculate price change patterns."""
    df = hist[hist["Kode Saham"].isin(stocks)].copy()
    df = df.sort_values(["Kode Saham", "SourceDate"])
    
    # Today's change vs yesterday
    df["price_change_1d"] = df.groupby("Kode Saham")["Penutupan"].pct_change() * 100
    
    # 5-day momentum
    df["price_change_5d"] = df.groupby("Kode Saham")["Penutupan"].pct_change(5) * 100
    
    # Get latest
    latest = df.sort_values("SourceDate").groupby("Kode Saham").tail(1)
    return latest[["Kode Saham", "Penutupan", "price_change_1d", "price_change_5d"]]


def apply_foreign_filter(momentum: pd.DataFrame, foreign: pd.DataFrame, 
                          prices: pd.DataFrame) -> pd.DataFrame:
    """Filter momentum picks by foreign accumulation patterns."""
    # Get latest date momentum signals
    momentum["SourceDate"] = pd.to_datetime(momentum["SourceDate"])
    latest_date = momentum["SourceDate"].max()
    latest_momentum = momentum[momentum["SourceDate"] == latest_date].copy()
    
    # Merge with foreign data
    merged = latest_momentum.merge(foreign, on="Kode Saham", how="inner")
    
    # Merge with prices
    merged = merged.merge(prices, on="Kode Saham", how="left")
    
    if len(merged) == 0:
        return merged
    
    # Classify patterns
    merged["pattern_1_dip"] = merged["price_change_1d"] < 0
    merged["pattern_2_momentum"] = merged["price_change_5d"] > 0
    
    merged["pattern_type"] = "Unknown"
    merged.loc[merged["pattern_1_dip"] & merged["pattern_2_momentum"], "pattern_type"] = "Both (Buy-Dip & Momentum)"
    merged.loc[merged["pattern_1_dip"] & ~merged["pattern_2_momentum"], "pattern_type"] = "Buy-the-Dip Only"
    merged.loc[~merged["pattern_1_dip"] & merged["pattern_2_momentum"], "pattern_type"] = "Momentum Confirmation"
    merged.loc[~merged["pattern_1_dip"] & ~merged["pattern_2_momentum"], "pattern_type"] = "Neutral"
    
    # Score: signal_score × foreign accumulation
    merged["foreign_score"] = merged["signal_score"] * (merged["Net Foreign Buy"] / 1e6)
    merged = merged.sort_values("foreign_score", ascending=False)
    
    return merged


def write_report(filtered: pd.DataFrame, total_momentum: int, total_foreign: int):
    """Write filtering report."""
    lines = []
    lines.append("Foreign Accumulation Pre-Filter (Applied to Momentum Picks)")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("OBJECTIVE:")
    lines.append("  Filter momentum signals to only stocks with foreign institutional interest")
    lines.append("")
    
    lines.append("PATTERNS:")
    lines.append("  Buy-the-Dip: Foreign buying + Price declined today (contrarian)")
    lines.append("  Momentum: Foreign buying + 5-day uptrend (following strength)")
    lines.append("  Both: Best of both worlds (buy dips in uptrending stocks)")
    lines.append("")
    
    lines.append(f"FILTER STATS:")
    lines.append(f"  Momentum picks (latest date): {total_momentum}")
    lines.append(f"  Stocks with foreign accumulation (>500K): {total_foreign}")
    lines.append(f"  Overlap (foreign + momentum): {len(filtered)}")
    if total_momentum > 0:
        lines.append(f"  Filter pass rate: {len(filtered)/total_momentum*100:.1f}%")
    lines.append("")
    
    if len(filtered) == 0:
        lines.append("⚠️  NO OVERLAP between momentum picks and foreign accumulation")
        lines.append("")
        lines.append("Recommendations:")
        lines.append("  1. Lower MIN_FOREIGN_BUY threshold (currently 500K)")
        lines.append("  2. Check if foreign data is updated")
        lines.append("  3. Momentum picks may be in small-caps without foreign interest")
        lines.append("  4. Consider running foreign filter FIRST, then momentum on that subset")
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text("\n".join(lines))
        return
    
    # Pattern breakdown
    pattern_counts = filtered["pattern_type"].value_counts()
    lines.append("PATTERN DISTRIBUTION:")
    for pattern, count in pattern_counts.items():
        lines.append(f"  {pattern}: {count} stocks")
    lines.append("")
    
    # Top picks
    lines.append("TOP 10 FOREIGN-BACKED MOMENTUM PICKS:")
    lines.append("-" * 80)
    lines.append(f"{'Rank':<6}{'Ticker':<8}{'Price':<10}{'Pattern':<28}{'Foreign(M)':<12}"
                 f"{'1d%':<10}{'5d%':<10}")
    lines.append("-" * 80)
    
    for idx, row in filtered.head(10).iterrows():
        rank = filtered.index.get_loc(idx) + 1
        lines.append(f"{rank:<6d}{row['Kode Saham']:<8}{int(row['close']):<10,}"
                     f"{row['pattern_type']:<28}{row['Net Foreign Buy']/1e6:<12.1f}"
                     f"{row['price_change_1d']:<10.2f}{row['price_change_5d']:<10.2f}")
    
    lines.append("-" * 80)
    lines.append("")
    
    # Best patterns
    best_both = filtered[filtered["pattern_type"] == "Both (Buy-Dip & Momentum)"]
    if len(best_both) > 0:
        lines.append(f"⭐ BEST PATTERN - Both Buy-Dip & Momentum ({len(best_both)} stocks):")
        for idx, row in best_both.head(3).iterrows():
            lines.append(f"    {row['Kode Saham']:6s} | Foreign: {row['Net Foreign Buy']/1e6:5.1f}M | "
                        f"1d: {row['price_change_1d']:+.2f}% | 5d: {row['price_change_5d']:+.2f}% | "
                        f"Score: {row['signal_score']:.1f}")
        lines.append("")
    
    dip_only = filtered[filtered["pattern_type"] == "Buy-the-Dip Only"]
    if len(dip_only) > 0:
        lines.append(f"💎 BUY-THE-DIP ({len(dip_only)} stocks):")
        for idx, row in dip_only.head(3).iterrows():
            lines.append(f"    {row['Kode Saham']:6s} | Foreign: {row['Net Foreign Buy']/1e6:5.1f}M | "
                        f"1d: {row['price_change_1d']:+.2f}% | Score: {row['signal_score']:.1f}")
        lines.append("")
    
    momentum_only = filtered[filtered["pattern_type"] == "Momentum Confirmation"]
    if len(momentum_only) > 0:
        lines.append(f"🚀 MOMENTUM CONFIRMATION ({len(momentum_only)} stocks):")
        for idx, row in momentum_only.head(3).iterrows():
            lines.append(f"    {row['Kode Saham']:6s} | Foreign: {row['Net Foreign Buy']/1e6:5.1f}M | "
                        f"5d: {row['price_change_5d']:+.2f}% | Score: {row['signal_score']:.1f}")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("NEXT STEPS:")
    lines.append("  1. Run low-volatility filter on these foreign-backed picks")
    lines.append("  2. Apply mean-reversion and MA filters")
    lines.append("  3. Use KNN ML for final ranking")
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    print(f"Report written to {REPORT_FILE}")


def main():
    # Load data
    print("Loading foreign accumulation data...")
    foreign = load_foreign_data(FOREIGN_FILE)
    print(f"Found {len(foreign)} stocks with foreign accumulation >500K shares")
    
    print("Loading momentum picks...")
    momentum = pd.read_csv(MOMENTUM_FILE)
    momentum_latest = momentum[momentum["SourceDate"] == momentum["SourceDate"].max()]
    print(f"Momentum picks (latest date): {len(momentum_latest)}")
    
    print("Loading price data...")
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    
    # Get foreign stock prices
    foreign_stocks = foreign["Kode Saham"].tolist()
    prices = calculate_price_patterns(hist, foreign_stocks)
    
    # Apply filter
    print("Filtering momentum picks by foreign accumulation...")
    filtered = apply_foreign_filter(momentum, foreign, prices)
    
    # Save and report
    if len(filtered) > 0:
        filtered.to_csv(OUTPUT_FILE, index=False)
        print(f"Foreign-filtered picks saved to {OUTPUT_FILE}")
        
        write_report(filtered, len(momentum_latest), len(foreign))
        
        # Console summary
        print(f"\n{'='*60}")
        print(f"FOREIGN ACCUMULATION FILTER")
        print(f"{'='*60}")
        print(f"Overlap: {len(filtered)} stocks (momentum + foreign)")
        print(f"\nTop 5 Foreign-Backed Picks:")
        for idx, row in filtered.head(5).iterrows():
            rank = filtered.index.get_loc(idx) + 1
            print(f"  {rank}. {row['Kode Saham']:6s} | Foreign: {row['Net Foreign Buy']/1e6:5.1f}M | "
                  f"Pattern: {row['pattern_type']}")
    else:
        print(f"\n⚠️  No overlap between momentum picks and foreign accumulation")
        write_report(filtered, len(momentum_latest), len(foreign))


if __name__ == "__main__":
    main()
