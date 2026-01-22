#!/usr/bin/env python3
"""
Foreign Accumulation Pattern Filter

Strategy: Filter stocks showing institutional buying patterns
Pattern 1: Foreign accumulation at time t AND declining price at t
Pattern 2: Foreign accumulation at time t AND increasing price at t+1

Rationale:
- Pattern 1: Institutional buy-the-dip (contrarian accumulation)
- Pattern 2: Institutional front-running (momentum confirmation)

Inputs:
- data/histories/foreign_buy_stocks_last5days.csv : foreign flow (5-day net)
- data/histories/ringkasan_histories_combined.csv : price data
- results/strategy_3_17_knn_predictions.csv : ML-filtered candidates

Outputs:
- results/foreign_accumulation_filter.csv : stocks meeting criteria
- results/foreign_accumulation_report.txt : pattern analysis
"""

from pathlib import Path
import pandas as pd
import numpy as np

FOREIGN_FILE = Path("data/histories/foreign_buy_stocks_last5days.csv")
HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
CANDIDATES_FILE = Path("results/strategy_3_17_knn_predictions.csv")
OUTPUT_FILE = Path("results/foreign_accumulation_filter.csv")
REPORT_FILE = Path("results/foreign_accumulation_report.txt")

MIN_FOREIGN_BUY = 1_000_000  # Minimum 1M shares net foreign buy


def load_foreign_data(path: Path) -> pd.DataFrame:
    """Load 5-day foreign accumulation data."""
    df = pd.read_csv(path)
    # Clean column names
    df.columns = df.columns.str.strip()
    # Filter positive net foreign buy only
    df = df[df["Net Foreign Buy"] > MIN_FOREIGN_BUY].copy()
    df = df[["Kode Saham", "Net Foreign Buy", "Foreign Buy", "Foreign Sell"]].copy()
    return df


def calculate_price_changes(hist: pd.DataFrame, stocks: list) -> pd.DataFrame:
    """Calculate price changes at t and t+1 for each stock."""
    df = hist[hist["Kode Saham"].isin(stocks)].copy()
    df = df.sort_values(["Kode Saham", "SourceDate"])
    
    # Price change at time t (current day vs previous day)
    df["price_change_t"] = df.groupby("Kode Saham")["Penutupan"].pct_change() * 100
    
    # Price change at t+1 (next day vs current day)
    df["price_change_t1"] = df.groupby("Kode Saham")["Penutupan"].pct_change().shift(-1) * 100
    
    # Get latest observation for each stock
    latest = df.sort_values("SourceDate").groupby("Kode Saham").tail(1)
    
    return latest[["Kode Saham", "SourceDate", "Penutupan", "price_change_t", "price_change_t1"]]


def identify_patterns(candidates: pd.DataFrame, foreign: pd.DataFrame, 
                      prices: pd.DataFrame) -> pd.DataFrame:
    """Identify stocks matching accumulation patterns."""
    # Merge all data
    merged = candidates.merge(foreign, on="Kode Saham", how="inner")
    merged = merged.merge(prices, on="Kode Saham", how="left")
    
    # Pattern 1: Foreign accumulation + declining price at t (buy the dip)
    merged["pattern_1_dip"] = (
        (merged["Net Foreign Buy"] > 0) & 
        (merged["price_change_t"] < 0)
    )
    
    # Pattern 2: Foreign accumulation + increasing price at t+1 (momentum confirmation)
    # Note: For t+1, we need to check if next day increased (predictive)
    # Since we don't have actual t+1 yet, we'll use ML prediction as proxy
    merged["pattern_2_momentum"] = (
        (merged["Net Foreign Buy"] > 0) & 
        (merged["predicted_return_1d"] > 0)
    )
    
    # Combined pattern: meets either criteria
    merged["meets_criteria"] = merged["pattern_1_dip"] | merged["pattern_2_momentum"]
    
    # Filter to matches only
    matches = merged[merged["meets_criteria"]].copy()
    
    # Add pattern labels
    matches["pattern_type"] = "None"
    matches.loc[matches["pattern_1_dip"] & matches["pattern_2_momentum"], "pattern_type"] = "Both"
    matches.loc[matches["pattern_1_dip"] & ~matches["pattern_2_momentum"], "pattern_type"] = "Dip"
    matches.loc[~matches["pattern_1_dip"] & matches["pattern_2_momentum"], "pattern_type"] = "Momentum"
    
    # Rank by combined score: foreign accumulation × ML prediction
    matches["foreign_ml_score"] = matches["Net Foreign Buy"] * matches["predicted_return_1d"]
    matches = matches.sort_values("foreign_ml_score", ascending=False)
    
    return matches


def write_report(matches: pd.DataFrame, total_candidates: int):
    """Write foreign accumulation filter report."""
    lines = []
    lines.append("Foreign Accumulation Pattern Filter")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("FILTERING CRITERIA:")
    lines.append("  Pattern 1: Foreign accumulation (>1M shares) + Price declining today")
    lines.append("             → Institutional buy-the-dip (contrarian)")
    lines.append("  Pattern 2: Foreign accumulation (>1M shares) + ML predicts up tomorrow")
    lines.append("             → Institutional momentum confirmation")
    lines.append("")
    
    lines.append(f"FILTER RESULTS:")
    lines.append(f"  Input candidates (ML-filtered): {total_candidates}")
    lines.append(f"  Stocks with foreign accumulation: {len(matches)}")
    if total_candidates > 0:
        lines.append(f"  Pass rate: {len(matches)/total_candidates*100:.1f}%")
    lines.append("")
    
    if len(matches) == 0:
        lines.append("⚠️  No stocks meet foreign accumulation criteria")
        lines.append("Possible reasons:")
        lines.append("  - ML candidates may not overlap with foreign accumulation stocks")
        lines.append("  - Try loosening MIN_FOREIGN_BUY threshold")
        lines.append("  - Check if foreign data is recent/up-to-date")
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text("\n".join(lines))
        return
    
    # Pattern breakdown
    pattern_counts = matches["pattern_type"].value_counts()
    lines.append("PATTERN BREAKDOWN:")
    for pattern, count in pattern_counts.items():
        lines.append(f"  {pattern}: {count} stocks")
    lines.append("")
    
    # Top matches
    lines.append("TOP FOREIGN ACCUMULATION PICKS:")
    lines.append("-" * 80)
    lines.append(f"{'Rank':<6}{'Ticker':<8}{'Price':<10}{'Pattern':<12}{'Foreign(M)':<12}"
                 f"{'Price Δ%':<12}{'ML Pred%':<12}")
    lines.append("-" * 80)
    
    for idx, row in matches.iterrows():
        rank = matches.index.get_loc(idx) + 1
        lines.append(f"{rank:<6d}{row['Kode Saham']:<8}{int(row['current_price']):<10,}"
                     f"{row['pattern_type']:<12}{row['Net Foreign Buy']/1e6:<12.1f}"
                     f"{row['price_change_t']:<12.2f}{row['predicted_return_1d']:<12.2f}")
    
    lines.append("-" * 80)
    lines.append("")
    
    # Detailed analysis
    lines.append("DETAILED ANALYSIS:")
    lines.append("")
    
    dip_stocks = matches[matches["pattern_1_dip"]]
    if len(dip_stocks) > 0:
        lines.append(f"PATTERN 1 - BUY THE DIP ({len(dip_stocks)} stocks):")
        lines.append("  Foreign investors accumulating despite price decline")
        lines.append("  Interpretation: Institutional conviction, contrarian opportunity")
        for idx, row in dip_stocks.head(3).iterrows():
            lines.append(f"    {row['Kode Saham']:6s} | Foreign: {row['Net Foreign Buy']/1e6:6.1f}M shares | "
                        f"Price today: {row['price_change_t']:+.2f}% | ML pred: {row['predicted_return_1d']:+.2f}%")
        lines.append("")
    
    momentum_stocks = matches[matches["pattern_2_momentum"]]
    if len(momentum_stocks) > 0:
        lines.append(f"PATTERN 2 - MOMENTUM CONFIRMATION ({len(momentum_stocks)} stocks):")
        lines.append("  Foreign investors buying + ML predicts further upside")
        lines.append("  Interpretation: Institutional front-running, momentum play")
        for idx, row in momentum_stocks.head(3).iterrows():
            lines.append(f"    {row['Kode Saham']:6s} | Foreign: {row['Net Foreign Buy']/1e6:6.1f}M shares | "
                        f"Price today: {row['price_change_t']:+.2f}% | ML pred: {row['predicted_return_1d']:+.2f}%")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("TRADING STRATEGY:")
    lines.append("  Dip Pattern: Enter on weakness, follow institutional accumulation")
    lines.append("  Momentum Pattern: Enter on strength, ride institutional momentum")
    lines.append("  Both Patterns: Highest conviction - institutional buy + ML confirmation")
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    print(f"Report written to {REPORT_FILE}")


def main():
    # Load data
    print("Loading foreign accumulation data...")
    foreign = load_foreign_data(FOREIGN_FILE)
    print(f"Found {len(foreign)} stocks with foreign accumulation >1M shares")
    
    print("Loading ML candidates...")
    candidates = pd.read_csv(CANDIDATES_FILE)
    
    print("Loading price data...")
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    
    # Calculate price changes
    print("Calculating price changes...")
    stocks = candidates["Kode Saham"].tolist()
    prices = calculate_price_changes(hist, stocks)
    
    # Identify patterns
    print("Identifying accumulation patterns...")
    matches = identify_patterns(candidates, foreign, prices)
    
    # Save outputs
    if len(matches) > 0:
        matches.to_csv(OUTPUT_FILE, index=False)
        print(f"Foreign accumulation picks saved to {OUTPUT_FILE}")
        
        # Write report
        write_report(matches, len(candidates))
        
        # Console summary
        print(f"\n{'='*60}")
        print(f"FOREIGN ACCUMULATION FILTER")
        print(f"{'='*60}")
        print(f"Stocks passing filter: {len(matches)}/{len(candidates)}")
        print(f"\nTop 5 Foreign Accumulation Picks:")
        for idx, row in matches.head(5).iterrows():
            rank = matches.index.get_loc(idx) + 1
            print(f"  {rank}. {row['Kode Saham']:6s} | Pattern: {row['pattern_type']:10s} | "
                  f"Foreign: {row['Net Foreign Buy']/1e6:5.1f}M | "
                  f"ML: {row['predicted_return_1d']:+.2f}%")
    else:
        print("\n⚠️  No stocks meet foreign accumulation criteria")
        write_report(pd.DataFrame(), len(candidates))


if __name__ == "__main__":
    main()
