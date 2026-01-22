#!/usr/bin/env python3
"""
Strategy 3.10: Industry-Neutral Mean-Reversion with IDX Screener

Signal: Enhanced mean-reversion using sector/industry groupings.
- Load sector classifications from IDX Stock Screener
- Build industry-neutral portfolios (control for sector bias)
- Apply mean-reversion within each sector cluster

Our Implementation:
- Parse sector data from IDX-Stock-Screener-20Jan2026.xlsx
- Group KNN predictions by sector
- Calculate sector-adjusted positions (avoid concentration in one sector)

Inputs:
- data/reference/IDX-Stock-Screener-20Jan2026.xlsx : sector classifications
- results/strategy_3_17_knn_predictions.csv : ML predictions

Outputs:
- results/strategy_3_10_sector_neutral_positions.csv : sector-balanced portfolio
- results/strategy_3_10_report.txt : sector exposure and risk analysis
"""

from pathlib import Path
import pandas as pd
import numpy as np

SCREENER_FILE = Path("data/reference/IDX-Stock-Screener-20Jan2026.xlsx")
PREDICTIONS_FILE = Path("results/strategy_3_17_knn_predictions.csv")
OUTPUT_FILE = Path("results/strategy_3_10_sector_neutral_positions.csv")
REPORT_FILE = Path("results/strategy_3_10_report.txt")

MAX_SECTOR_WEIGHT = 0.35  # No more than 35% in one sector


def load_sector_data(path: Path) -> pd.DataFrame:
    """Load sector classifications from IDX screener."""
    try:
        # Try to read Excel file
        df = pd.read_excel(path, sheet_name=0)
        
        # Common column names in IDX screener
        code_col = None
        sector_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if any(x in col_lower for x in ['code', 'ticker', 'saham', 'kode']):
                code_col = col
            if any(x in col_lower for x in ['sector', 'sektor', 'industry', 'industri']):
                sector_col = col
        
        if code_col is None or sector_col is None:
            print(f"⚠️  Could not identify code/sector columns in screener")
            return pd.DataFrame(columns=["Kode Saham", "Sector"])
        
        # Keep relevant columns
        sectors = df[[code_col, sector_col]].copy()
        sectors.columns = ["Kode Saham", "Sector"]
        sectors = sectors.dropna()
        
        return sectors
        
    except Exception as e:
        print(f"⚠️  Error loading sector data: {e}")
        print("Continuing without sector classifications...")
        return pd.DataFrame(columns=["Kode Saham", "Sector"])


def apply_sector_constraints(predictions: pd.DataFrame, sectors: pd.DataFrame, 
                              total_capital: float) -> pd.DataFrame:
    """Apply sector-neutral constraints to position sizing."""
    # Merge predictions with sectors
    merged = predictions.merge(sectors, on="Kode Saham", how="left")
    
    # Fill missing sectors with "Unknown"
    merged["Sector"] = merged["Sector"].fillna("Unknown")
    
    # Calculate initial weights (from capital allocation)
    merged["initial_weight"] = merged["capital_allocation"] / merged["capital_allocation"].sum()
    
    # Calculate sector exposures
    sector_exposure = merged.groupby("Sector")["initial_weight"].sum()
    
    # Adjust if any sector exceeds max weight
    adjusted = merged.copy()
    
    for sector in sector_exposure.index:
        sector_weight = sector_exposure[sector]
        
        if sector_weight > MAX_SECTOR_WEIGHT:
            # Scale down positions in this sector
            scale_factor = MAX_SECTOR_WEIGHT / sector_weight
            mask = adjusted["Sector"] == sector
            adjusted.loc[mask, "initial_weight"] *= scale_factor
    
    # Renormalize weights to sum to 1
    adjusted["adjusted_weight"] = adjusted["initial_weight"] / adjusted["initial_weight"].sum()
    
    # Recalculate capital allocations
    adjusted["adjusted_capital"] = adjusted["adjusted_weight"] * total_capital
    adjusted["adjusted_shares"] = (adjusted["adjusted_capital"] / adjusted["current_price"]).astype(int)
    
    return adjusted


def write_report(portfolio: pd.DataFrame, sectors: pd.DataFrame):
    """Write sector-neutral portfolio report."""
    lines = []
    lines.append("Strategy 3.10: Industry-Neutral Portfolio Construction")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("CONCEPT:")
    lines.append("  • Avoid concentration risk by limiting exposure to any single sector")
    lines.append(f"  • Maximum sector weight: {MAX_SECTOR_WEIGHT:.0%}")
    lines.append("  • Sector-balanced portfolio reduces systematic risk")
    lines.append("")
    
    if len(sectors) == 0:
        lines.append("⚠️  Sector data not available - portfolio not sector-adjusted")
        lines.append("")
    
    # Sector exposure
    sector_exp = portfolio.groupby("Sector").agg(
        weight=("adjusted_weight", "sum"),
        count=("Kode Saham", "count"),
        avg_pred_return=("predicted_return_1d", "mean")
    ).sort_values("weight", ascending=False)
    
    lines.append("SECTOR EXPOSURE:")
    lines.append("-" * 80)
    lines.append(f"{'Sector':<30}{'Weight%':<12}{'Stocks':<10}{'Avg Pred Ret%':<15}")
    lines.append("-" * 80)
    
    for sector, row in sector_exp.iterrows():
        lines.append(f"{sector:<30}{row['weight']*100:<12.1f}{int(row['count']):<10d}{row['avg_pred_return']:<15.2f}")
    
    lines.append("-" * 80)
    lines.append("")
    
    # Final positions
    lines.append("SECTOR-BALANCED POSITIONS (Ranked by Predicted Return):")
    lines.append("-" * 80)
    lines.append(f"{'Rank':<6}{'Ticker':<8}{'Sector':<20}{'Pred%':<10}{'Weight%':<10}"
                 f"{'Capital(M)':<12}{'Shares':<10}")
    lines.append("-" * 80)
    
    sorted_port = portfolio.sort_values("predicted_return_1d", ascending=False)
    for idx, row in sorted_port.iterrows():
        rank = sorted_port.index.get_loc(idx) + 1
        lines.append(f"{rank:<6d}{row['Kode Saham']:<8}{row['Sector'][:18]:<20}"
                     f"{row['predicted_return_1d']:<10.2f}{row['adjusted_weight']*100:<10.1f}"
                     f"{row['adjusted_capital']/1e6:<12.1f}{row['adjusted_shares']:<10,}")
    
    lines.append("-" * 80)
    lines.append("")
    
    # Risk analysis
    max_sector_exp = sector_exp["weight"].max()
    lines.append("RISK ANALYSIS:")
    lines.append(f"  Max sector exposure: {max_sector_exp:.1%}")
    lines.append(f"  Number of sectors: {len(sector_exp)}")
    lines.append(f"  Diversification score: {1 - max_sector_exp:.1%} (higher = more diversified)")
    
    if max_sector_exp > MAX_SECTOR_WEIGHT:
        lines.append(f"  ⚠️  WARNING: Sector constraint violated (max allowed: {MAX_SECTOR_WEIGHT:.0%})")
    else:
        lines.append(f"  ✓ Portfolio meets sector constraints")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("IMPLEMENTATION:")
    lines.append("  • Use 'Capital(M)' and 'Shares' columns for execution")
    lines.append("  • Monitor sector exposure as new opportunities arise")
    lines.append("  • Rebalance if sector weights drift beyond limits")
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    print(f"Report written to {REPORT_FILE}")


def main():
    # Load data
    predictions = pd.read_csv(PREDICTIONS_FILE)
    sectors = load_sector_data(SCREENER_FILE)
    
    print(f"Loaded {len(predictions)} KNN predictions...")
    if len(sectors) > 0:
        print(f"Loaded sector classifications for {len(sectors)} stocks")
    
    # Apply sector constraints
    total_capital = predictions["capital_allocation"].sum()
    print("Applying sector-neutral constraints...")
    
    portfolio = apply_sector_constraints(predictions, sectors, total_capital)
    
    # Save outputs
    portfolio.to_csv(OUTPUT_FILE, index=False)
    print(f"Sector-neutral portfolio saved to {OUTPUT_FILE}")
    
    # Write report
    write_report(portfolio, sectors)
    
    # Console summary
    print(f"\n{'='*60}")
    print(f"SECTOR-NEUTRAL PORTFOLIO")
    print(f"{'='*60}")
    
    sector_exp = portfolio.groupby("Sector")["adjusted_weight"].sum().sort_values(ascending=False)
    print("Sector Exposure:")
    for sector, weight in sector_exp.items():
        print(f"  {sector[:25]:<25s} {weight*100:>6.1f}%")
    
    print(f"\nTop 3 Holdings:")
    top3 = portfolio.sort_values("predicted_return_1d", ascending=False).head(3)
    for idx, row in top3.iterrows():
        rank = top3.index.get_loc(idx) + 1
        print(f"  {rank}. {row['Kode Saham']:6s} ({row['Sector'][:15]}) | "
              f"Pred: {row['predicted_return_1d']:+.2f}% | "
              f"Weight: {row['adjusted_weight']*100:.1f}%")


if __name__ == "__main__":
    main()
