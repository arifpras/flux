#!/usr/bin/env python3
"""
Strategy 3.9: Mean-Reversion - Single Cluster

Signal: Multiple correlated stocks (cluster) show divergent returns → trade to mean.
- Calculate demeaned returns for cluster: R̃_i = R_i − R̄ (cluster mean)
- Short R̃_i > 0 (outperformers), buy R̃_i < 0 (underperformers)
- Dollar allocation: D_i = −γ·R̃_i (inversely proportional to deviation)

Our Implementation (Long-Only):
- Use top momentum picks as a natural "accumulation cluster"
- Calculate cluster mean return (daily)
- Identify underperformers (below cluster mean) as buy opportunities
- Position size inversely proportional to deviation from mean

Inputs:
- results/strategy_3_4_filtered_picks.csv : low-volatility momentum cluster
- data/histories/ringkasan_histories_combined.csv : for recent returns

Outputs:
- results/strategy_3_9_cluster_positions.csv : position sizing recommendations
- results/strategy_3_9_report.txt : cluster mean-reversion analysis
"""

from pathlib import Path
import pandas as pd
import numpy as np

PICKS_FILE = Path("results/strategy_3_4_filtered_picks.csv")
HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
OUTPUT_FILE = Path("results/strategy_3_9_cluster_positions.csv")
REPORT_FILE = Path("results/strategy_3_9_report.txt")

LOOKBACK_DAYS = 5  # Calculate returns over past 5 days


def load_cluster_returns(picks: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
    """Calculate recent returns for cluster stocks."""
    # Get stock codes from picks
    cluster_stocks = picks["Kode Saham"].unique()
    
    # Filter history to cluster stocks only
    df = hist[hist["Kode Saham"].isin(cluster_stocks)].copy()
    df = df.sort_values(["Kode Saham", "SourceDate"])
    
    # Calculate N-day returns
    df["ret_5d"] = df.groupby("Kode Saham")["Penutupan"].pct_change(LOOKBACK_DAYS) * 100
    
    # Get latest returns
    latest = df.sort_values("SourceDate").groupby("Kode Saham").tail(1)
    latest = latest[["Kode Saham", "SourceDate", "Penutupan", "ret_5d"]].copy()
    latest = latest.dropna(subset=["ret_5d"])
    
    return latest


def calculate_mean_reversion_positions(picks: pd.DataFrame, returns: pd.DataFrame, 
                                        capital: float = 100_000_000) -> pd.DataFrame:
    """
    Calculate position sizes using mean-reversion logic.
    
    Position sizing formula:
    - Cluster mean return: R̄ = mean(all returns)
    - Demeaned return: R̃_i = R_i − R̄
    - Position weight: w_i = −γ·R̃_i (negative of deviation, normalized)
    - Dollar allocation: D_i = w_i × Total_Capital
    
    Interpretation:
    - Stocks below cluster mean (R̃_i < 0) get positive weights (buy underperformers)
    - Stocks above cluster mean (R̃_i > 0) get negative weights (fade outperformers in long-only = reduce size)
    """
    # Merge picks with returns
    merged = picks.merge(returns[["Kode Saham", "ret_5d"]], on="Kode Saham", how="left")
    
    # Calculate cluster mean return
    cluster_mean = merged["ret_5d"].mean()
    
    # Demeaned returns
    merged["ret_demeaned"] = merged["ret_5d"] - cluster_mean
    
    # Mean-reversion weights (negative of deviation)
    # In long-only: we overweight underperformers, underweight outperformers
    merged["mr_weight_raw"] = -merged["ret_demeaned"]
    
    # Normalize to positive weights (for long-only portfolio)
    # Shift so minimum weight = 0.5, max weight = 1.5 (range of 0.5 to 1.5x base weight)
    min_raw = merged["mr_weight_raw"].min()
    max_raw = merged["mr_weight_raw"].max()
    range_raw = max_raw - min_raw
    
    if range_raw > 0:
        merged["mr_weight_normalized"] = 0.5 + (merged["mr_weight_raw"] - min_raw) / range_raw
    else:
        merged["mr_weight_normalized"] = 1.0
    
    # Combine with signal score for final weight
    # Final weight = signal_score × mean_reversion_weight
    merged["signal_weight"] = merged["signal_score"] / merged["signal_score"].sum()
    merged["combined_weight"] = merged["signal_weight"] * merged["mr_weight_normalized"]
    
    # Normalize combined weights to sum to 1
    merged["position_weight"] = merged["combined_weight"] / merged["combined_weight"].sum()
    
    # Calculate dollar allocations
    merged["capital_allocation"] = merged["position_weight"] * capital
    merged["shares_to_buy"] = (merged["capital_allocation"] / merged["close"]).astype(int)
    
    # Rank by mean-reversion opportunity (most underperforming = best buy)
    merged = merged.sort_values("ret_demeaned", ascending=True)
    merged["mr_rank"] = range(1, len(merged) + 1)
    
    return merged, cluster_mean


def write_report(positions: pd.DataFrame, cluster_mean: float, capital: float):
    """Write mean-reversion analysis report."""
    lines = []
    lines.append("Strategy 3.9: Cluster Mean-Reversion (Long-Only)")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("CONCEPT:")
    lines.append("  • Stocks in same cluster (momentum picks) should move together")
    lines.append("  • Divergence from cluster mean creates opportunity")
    lines.append("  • BUY underperformers (below mean) expecting catch-up")
    lines.append("  • REDUCE outperformers (above mean) expecting mean-reversion")
    lines.append("")
    
    lines.append(f"CLUSTER STATISTICS:")
    lines.append(f"  Cluster size: {len(positions)} stocks")
    lines.append(f"  Cluster mean return (5d): {cluster_mean:.2f}%")
    lines.append(f"  Best performer: {positions['ret_5d'].max():.2f}%")
    lines.append(f"  Worst performer: {positions['ret_5d'].min():.2f}%")
    lines.append(f"  Range (max - min): {positions['ret_5d'].max() - positions['ret_5d'].min():.2f}%")
    lines.append("")
    
    lines.append(f"POSITION SIZING (Total Capital: Rp {capital/1e6:.0f}M):")
    lines.append("-" * 80)
    lines.append(f"{'Rank':<6}{'Ticker':<8}{'Price':<10}{'5d Ret%':<10}{'Demeaned%':<12}"
                 f"{'MR Weight':<12}{'Capital(M)':<12}{'Shares':<10}")
    lines.append("-" * 80)
    
    for idx, row in positions.iterrows():
        lines.append(f"{row['mr_rank']:<6d}{row['Kode Saham']:<8}{int(row['close']):<10,}"
                     f"{row['ret_5d']:<10.1f}{row['ret_demeaned']:<12.1f}"
                     f"{row['mr_weight_normalized']:<12.2f}{row['capital_allocation']/1e6:<12.1f}"
                     f"{row['shares_to_buy']:<10,}")
    
    lines.append("-" * 80)
    lines.append("")
    
    # Highlight best mean-reversion opportunities
    lines.append("TOP 3 MEAN-REVERSION OPPORTUNITIES (Most Underperforming):")
    top3 = positions.head(3)
    for idx, row in top3.iterrows():
        rank = top3.index.get_loc(idx) + 1
        lines.append(f"  {rank}. {row['Kode Saham']:6s} | Ret: {row['ret_5d']:5.1f}% "
                     f"(Cluster mean: {cluster_mean:.1f}%) | "
                     f"Deviation: {row['ret_demeaned']:+.1f}% → OVERWEIGHT")
    
    lines.append("")
    lines.append("BOTTOM 3 (Most Overperforming → Reduce Exposure):")
    bottom3 = positions.tail(3)
    for idx, row in bottom3.iterrows():
        rank = len(positions) - list(positions.index).index(idx)
        lines.append(f"  {rank}. {row['Kode Saham']:6s} | Ret: {row['ret_5d']:5.1f}% "
                     f"(Cluster mean: {cluster_mean:.1f}%) | "
                     f"Deviation: {row['ret_demeaned']:+.1f}% → UNDERWEIGHT")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("IMPLEMENTATION:")
    lines.append("  • Use 'Capital(M)' column for position sizing")
    lines.append("  • Rebalance daily as returns converge/diverge")
    lines.append("  • Mean-reversion works best in stable regimes (Cluster 0)")
    lines.append("  • Avoid during high volatility or regime shifts")
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    print(f"Report written to {REPORT_FILE}")


def main():
    # Load data
    picks = pd.read_csv(PICKS_FILE)
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    
    print(f"Loaded {len(picks)} low-volatility momentum picks as cluster...")
    
    # Calculate cluster returns
    print("Calculating 5-day returns for cluster stocks...")
    returns = load_cluster_returns(picks, hist)
    
    # Calculate mean-reversion positions
    print("Computing mean-reversion position sizing...")
    capital = 100_000_000  # 100M IDR example capital
    positions, cluster_mean = calculate_mean_reversion_positions(picks, returns, capital)
    
    # Save outputs
    positions.to_csv(OUTPUT_FILE, index=False)
    print(f"Position sizing saved to {OUTPUT_FILE}")
    
    # Write report
    write_report(positions, cluster_mean, capital)
    
    # Console summary
    print(f"\n{'='*60}")
    print(f"CLUSTER MEAN-REVERSION ANALYSIS")
    print(f"{'='*60}")
    print(f"Cluster mean return (5d): {cluster_mean:.2f}%")
    print(f"\nTop 3 BUY Opportunities (Most Underperforming):")
    for idx, row in positions.head(3).iterrows():
        rank = positions.index.get_loc(idx) + 1
        print(f"  {rank}. {row['Kode Saham']:6s} | {row['ret_5d']:5.1f}% vs {cluster_mean:.1f}% mean "
              f"| Allocate: Rp {row['capital_allocation']/1e6:.1f}M")


if __name__ == "__main__":
    main()
