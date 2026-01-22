#!/usr/bin/env python3
"""
Strategy 3.12: Two Moving Averages (Dual MA Crossover)

Signal: Fast MA crosses slow MA
- Fast MA (10-day) crosses above Slow MA (30-day) → Bullish
- Fast MA (10-day) crosses below Slow MA (30-day) → Bearish
- Stop-loss: 2% below previous day (long) or 2% above (short)

Our Implementation (Long-Only):
- Calculate 10-day and 30-day SMA for each stock
- Filter momentum picks: only trade if MA(10) > MA(30) at signal date
- Add stop-loss levels for risk management

Inputs:
- results/strategy_3_9_cluster_positions.csv : mean-reversion positioned stocks
- data/histories/ringkasan_histories_combined.csv : for MA calculation

Outputs:
- results/strategy_3_12_ma_filtered_positions.csv : positions with MA confirmation
- results/strategy_3_12_report.txt : MA analysis and entry/stop levels
"""

from pathlib import Path
import pandas as pd
import numpy as np

POSITIONS_FILE = Path("results/strategy_3_9_cluster_positions.csv")
HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
OUTPUT_FILE = Path("results/strategy_3_12_ma_filtered_positions.csv")
REPORT_FILE = Path("results/strategy_3_12_report.txt")

FAST_MA = 10  # days
SLOW_MA = 30  # days
STOP_LOSS_PCT = 2.0  # percent


def calculate_moving_averages(hist: pd.DataFrame, stocks: list) -> pd.DataFrame:
    """Calculate 10-day and 30-day SMA for stocks."""
    df = hist[hist["Kode Saham"].isin(stocks)].copy()
    df = df.sort_values(["Kode Saham", "SourceDate"])
    
    # Calculate MAs
    df["ma_10"] = df.groupby("Kode Saham")["Penutupan"].transform(
        lambda x: x.rolling(FAST_MA, min_periods=FAST_MA).mean()
    )
    df["ma_30"] = df.groupby("Kode Saham")["Penutupan"].transform(
        lambda x: x.rolling(SLOW_MA, min_periods=SLOW_MA).mean()
    )
    
    # Get latest values
    latest = df.sort_values("SourceDate").groupby("Kode Saham").tail(1)
    latest = latest[["Kode Saham", "SourceDate", "Penutupan", "ma_10", "ma_30"]].copy()
    
    # MA status
    latest["ma_bullish"] = latest["ma_10"] > latest["ma_30"]
    latest["ma_distance_pct"] = ((latest["ma_10"] - latest["ma_30"]) / latest["ma_30"]) * 100
    
    return latest


def calculate_stop_loss(positions: pd.DataFrame) -> pd.DataFrame:
    """Calculate stop-loss levels (2% below entry)."""
    positions["stop_loss"] = positions["close"] * (1 - STOP_LOSS_PCT / 100)
    positions["stop_loss"] = positions["stop_loss"].round(0).astype(int)
    return positions


def filter_by_ma(positions: pd.DataFrame, ma_data: pd.DataFrame) -> pd.DataFrame:
    """Filter positions to only stocks with bullish MA alignment."""
    # Merge positions with MA data
    merged = positions.merge(ma_data[["Kode Saham", "ma_10", "ma_30", "ma_bullish", "ma_distance_pct"]], 
                              on="Kode Saham", how="left")
    
    # Filter: only bullish MA (MA10 > MA30)
    bullish = merged[merged["ma_bullish"] == True].copy()
    
    # Calculate stop-loss
    bullish = calculate_stop_loss(bullish)
    
    return bullish, merged


def write_report(filtered: pd.DataFrame, all_positions: pd.DataFrame, 
                 ma_data: pd.DataFrame):
    """Write MA confirmation report."""
    lines = []
    lines.append("Strategy 3.12: Dual Moving Average Confirmation")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("CONCEPT:")
    lines.append("  • Fast MA (10d) > Slow MA (30d) = Bullish trend confirmation")
    lines.append("  • Only enter positions when MA alignment is bullish")
    lines.append("  • Stop-loss at 2% below entry to limit downside")
    lines.append("")
    
    lines.append(f"FILTER RESULTS:")
    lines.append(f"  Total positions (after mean-reversion): {len(all_positions)}")
    lines.append(f"  Bullish MA alignment: {len(filtered)}")
    lines.append(f"  Filtered out (bearish MA): {len(all_positions) - len(filtered)}")
    lines.append(f"  Pass rate: {len(filtered)/len(all_positions)*100:.1f}%")
    lines.append("")
    
    # MA-confirmed positions
    lines.append("MA-CONFIRMED POSITIONS (Ranked by Mean-Reversion Opportunity):")
    lines.append("-" * 80)
    lines.append(f"{'Rank':<6}{'Ticker':<8}{'Price':<10}{'MA10':<10}{'MA30':<10}"
                 f"{'MA Dist%':<12}{'Stop-Loss':<12}{'Capital(M)':<12}")
    lines.append("-" * 80)
    
    if len(filtered) > 0:
        for idx, row in filtered.iterrows():
            lines.append(f"{row['mr_rank']:<6d}{row['Kode Saham']:<8}{int(row['close']):<10,}"
                         f"{int(row['ma_10']):<10,}{int(row['ma_30']):<10,}"
                         f"{row['ma_distance_pct']:<12.1f}{int(row['stop_loss']):<12,}"
                         f"{row['capital_allocation']/1e6:<12.1f}")
    else:
        lines.append("No positions pass MA filter.")
    
    lines.append("-" * 80)
    lines.append("")
    
    # Rejected positions
    rejected = all_positions[~all_positions["Kode Saham"].isin(filtered["Kode Saham"])]
    if len(rejected) > 0:
        lines.append("REJECTED POSITIONS (Bearish MA: MA10 < MA30):")
        for idx, row in rejected.iterrows():
            ma_row = ma_data[ma_data["Kode Saham"] == row["Kode Saham"]]
            if len(ma_row) > 0:
                ma10 = ma_row["ma_10"].iloc[0]
                ma30 = ma_row["ma_30"].iloc[0]
                dist = ma_row["ma_distance_pct"].iloc[0]
                lines.append(f"  {row['Kode Saham']:6s} | Price: {int(row['close']):5,} | "
                             f"MA10: {int(ma10):5,} < MA30: {int(ma30):5,} | "
                             f"Dist: {dist:+.1f}% → WAIT")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("TRADING RULES:")
    lines.append("  ✅ ENTER: Only when MA10 > MA30 (bullish alignment)")
    lines.append("  🛑 STOP-LOSS: Exit if price falls 2% below entry")
    lines.append("  ⏳ WAIT: If MA10 < MA30, wait for crossover before entering")
    lines.append("  📊 MONITOR: Check MA alignment daily; exit if MA10 crosses below MA30")
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    print(f"Report written to {REPORT_FILE}")


def main():
    # Load data
    positions = pd.read_csv(POSITIONS_FILE)
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    
    print(f"Loaded {len(positions)} mean-reversion positions...")
    
    # Calculate MAs
    print("Calculating 10-day and 30-day moving averages...")
    stocks = positions["Kode Saham"].unique().tolist()
    ma_data = calculate_moving_averages(hist, stocks)
    
    # Filter by MA
    print("Filtering positions by MA alignment...")
    filtered, all_with_ma = filter_by_ma(positions, ma_data)
    
    # Save outputs
    filtered.to_csv(OUTPUT_FILE, index=False)
    print(f"MA-filtered positions saved to {OUTPUT_FILE}")
    
    # Write report
    write_report(filtered, positions, all_with_ma)
    
    # Console summary
    print(f"\n{'='*60}")
    print(f"DUAL MA FILTER RESULTS")
    print(f"{'='*60}")
    print(f"Positions with bullish MA (MA10 > MA30): {len(filtered)}/{len(positions)}")
    
    if len(filtered) > 0:
        print(f"\nTop 3 MA-Confirmed Entries:")
        for idx, row in filtered.head(3).iterrows():
            rank = filtered.index.get_loc(idx) + 1
            print(f"  {rank}. {row['Kode Saham']:6s} | Price: {int(row['close']):5,} | "
                  f"MA10: {int(row['ma_10']):5,} > MA30: {int(row['ma_30']):5,} | "
                  f"Stop: {int(row['stop_loss']):5,}")
    else:
        print("\n⚠️  No positions pass MA filter - all stocks in bearish MA alignment")


if __name__ == "__main__":
    main()
