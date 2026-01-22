#!/usr/bin/env python3
"""
Strategy 3.4: Low-Volatility Anomaly

Signal: Low-volatility stocks outperform high-volatility stocks (counter-intuitive).
- Calculate historical volatility σ_i over 60 days
- Buy bottom decile (low volatility), short top decile (high volatility)
- Holding period: 6 months to 1 year

Our Implementation (Long-Only):
- Calculate 60-day rolling volatility for each stock
- Filter momentum picks: only trade stocks with below-median volatility
- Output: volatility-filtered picks and stability rankings

Inputs:
- data/histories/ringkasan_histories_combined.csv : price histories
- results/flow_augmented_momentum_picks.csv : existing momentum signals

Outputs:
- results/strategy_3_4_low_volatility_filter.csv : volatility metrics per stock
- results/strategy_3_4_filtered_picks.csv : momentum picks filtered by low volatility
- results/strategy_3_4_report.txt : summary statistics
"""

from pathlib import Path
import pandas as pd
import numpy as np

HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
PICKS_FILE = Path("results/flow_augmented_momentum_picks.csv")
OUTPUT_VOL_FILE = Path("results/strategy_3_4_low_volatility_filter.csv")
OUTPUT_PICKS_FILE = Path("results/strategy_3_4_filtered_picks.csv")
REPORT_FILE = Path("results/strategy_3_4_report.txt")

VOLATILITY_WINDOW = 60  # days
MIN_PERIODS = 30  # minimum data points


def calculate_volatility(hist: pd.DataFrame) -> pd.DataFrame:
    """Calculate 60-day rolling volatility of returns."""
    df = hist.sort_values(["Kode Saham", "SourceDate"]).copy()
    
    # Daily returns
    df["ret_1d"] = df.groupby("Kode Saham")["Penutupan"].pct_change()
    
    # 60-day volatility (annualized)
    df["volatility_60d"] = df.groupby("Kode Saham")["ret_1d"].transform(
        lambda x: x.rolling(VOLATILITY_WINDOW, min_periods=MIN_PERIODS).std() * np.sqrt(252)
    )
    
    # Get latest volatility for each stock
    latest = df.sort_values("SourceDate").groupby("Kode Saham").tail(1)
    latest = latest[["Kode Saham", "SourceDate", "Penutupan", "volatility_60d"]].copy()
    latest = latest.dropna(subset=["volatility_60d"])
    
    # Calculate percentile ranks
    latest["vol_percentile"] = latest["volatility_60d"].rank(pct=True) * 100
    
    return latest


def filter_picks_by_volatility(picks: pd.DataFrame, volatility: pd.DataFrame) -> pd.DataFrame:
    """Filter momentum picks to only low-volatility stocks (below median)."""
    # Get latest signal date
    picks["SourceDate"] = pd.to_datetime(picks["SourceDate"])
    latest_date = picks["SourceDate"].max()
    latest_picks = picks[picks["SourceDate"] == latest_date].copy()
    
    # Merge with volatility
    merged = latest_picks.merge(volatility[["Kode Saham", "volatility_60d", "vol_percentile"]], 
                                  on="Kode Saham", how="left")
    
    # Filter: only stocks with below-median volatility (percentile < 50)
    median_vol = merged["volatility_60d"].median()
    filtered = merged[merged["volatility_60d"] <= median_vol].copy()
    
    # Re-rank by signal_score among filtered set
    filtered = filtered.sort_values("signal_score", ascending=False)
    
    return filtered, median_vol, latest_date


def write_report(volatility: pd.DataFrame, filtered: pd.DataFrame, all_picks: pd.DataFrame, 
                 median_vol: float, signal_date):
    """Write summary report."""
    lines = []
    lines.append("Strategy 3.4: Low-Volatility Anomaly Filter")
    lines.append(f"Signal Date: {signal_date.strftime('%Y-%m-%d')}")
    lines.append("=" * 80)
    lines.append("")
    
    # Overall volatility distribution
    lines.append("VOLATILITY DISTRIBUTION (All Stocks):")
    lines.append(f"  Total stocks with 60d volatility: {len(volatility)}")
    lines.append(f"  Mean volatility: {volatility['volatility_60d'].mean():.2%}")
    lines.append(f"  Median volatility: {median_vol:.2%}")
    lines.append(f"  10th percentile: {volatility['volatility_60d'].quantile(0.1):.2%}")
    lines.append(f"  90th percentile: {volatility['volatility_60d'].quantile(0.9):.2%}")
    lines.append("")
    
    # Filter impact
    lines.append("FILTER IMPACT ON MOMENTUM PICKS:")
    lines.append(f"  Original picks (latest date): {len(all_picks)}")
    lines.append(f"  After low-volatility filter: {len(filtered)}")
    lines.append(f"  Filtered out: {len(all_picks) - len(filtered)} ({(1 - len(filtered)/len(all_picks))*100:.1f}%)")
    lines.append("")
    
    # Top 10 low-volatility picks
    lines.append("TOP 10 LOW-VOLATILITY MOMENTUM PICKS:")
    lines.append("-" * 80)
    if len(filtered) > 0:
        top10 = filtered.head(10)
        for idx, row in top10.iterrows():
            rank = top10.index.get_loc(idx) + 1
            lines.append(f"{rank:2d}. {row['Kode Saham']:6s} | Score: {row['signal_score']:6.1f} | "
                        f"Vol: {row['volatility_60d']:5.1%} (p{row['vol_percentile']:4.1f}) | "
                        f"Price: Rp {int(row['close']):,}")
    else:
        lines.append("No picks available after filtering.")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("INTERPRETATION:")
    lines.append("  • Low-volatility stocks tend to have more stable returns")
    lines.append("  • Combining momentum + low volatility = quality momentum")
    lines.append("  • Use this filter to avoid volatile/manipulated stocks")
    lines.append("  • Below-median volatility = safer swing trades")
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    print(f"Report written to {REPORT_FILE}")


def main():
    # Load data
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    picks = pd.read_csv(PICKS_FILE)
    
    # Calculate volatility
    print("Calculating 60-day volatility for all stocks...")
    volatility = calculate_volatility(hist)
    
    # Filter picks
    print("Filtering momentum picks by low volatility...")
    filtered, median_vol, signal_date = filter_picks_by_volatility(picks, volatility)
    
    # Get all latest picks for comparison
    picks["SourceDate"] = pd.to_datetime(picks["SourceDate"])
    latest_date = picks["SourceDate"].max()
    all_latest = picks[picks["SourceDate"] == latest_date]
    
    # Save outputs
    volatility.to_csv(OUTPUT_VOL_FILE, index=False)
    filtered.to_csv(OUTPUT_PICKS_FILE, index=False)
    print(f"Volatility data saved to {OUTPUT_VOL_FILE}")
    print(f"Filtered picks saved to {OUTPUT_PICKS_FILE}")
    
    # Write report
    write_report(volatility, filtered, all_latest, median_vol, signal_date)
    
    # Console summary
    print(f"\n{'='*60}")
    print(f"LOW-VOLATILITY FILTER APPLIED")
    print(f"{'='*60}")
    print(f"Original picks: {len(all_latest)}")
    print(f"Low-vol picks: {len(filtered)} (below median {median_vol:.1%})")
    print(f"\nTop 5 Low-Vol Picks:")
    for idx, row in filtered.head(5).iterrows():
        rank = filtered.index.get_loc(idx) + 1
        print(f"  {rank}. {row['Kode Saham']:6s} Score: {row['signal_score']:6.1f} | Vol: {row['volatility_60d']:5.1%}")


if __name__ == "__main__":
    main()
