#!/usr/bin/env python3
"""
Daily Top 5 Stock Recommendations for Swing Trading

Objective: Recommend 5 stocks with highest probability of next-day profit, filtered for liquidity.

Inputs:
- results/flow_augmented_momentum_picks.csv : ranked momentum/pullback signals
- results/broker_event_study.txt : dominance event context
- results/flow_regime_clusters.csv : market regime
- data/histories/ringkasan_histories_combined.csv : for liquidity filters

Method:
1. Pull latest date signals from momentum picks
2. Filter by liquidity: avg_20d_volume > 1M shares AND avg_20d_value > 1B IDR
3. Check market regime (cluster) and dominance event status
4. Score stocks: signal_score × liquidity_factor × regime_multiplier
5. Return top 5 with rationale

Output:
- results/daily_top5_recommendations.txt : formatted recommendation with context
"""

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PICKS_FILE = Path("results/flow_augmented_momentum_picks.csv")
CLUSTERS_FILE = Path("results/flow_regime_clusters.csv")
HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
BROKER_FILE = Path("data/reference/ringkasan_broker_combined_20251201_20260121.csv")
OUTPUT_FILE = Path("results/daily_top5_recommendations.txt")

# Filters
MIN_AVG_VOLUME = 1_000_000  # 1M shares
MIN_AVG_VALUE = 1_000_000_000  # 1B IDR
LIQUIDITY_WINDOW = 20  # days


def load_latest_signals(path: Path) -> pd.DataFrame:
    """Get latest date signals from momentum picks."""
    df = pd.read_csv(path)
    df["SourceDate"] = pd.to_datetime(df["SourceDate"])
    latest_date = df["SourceDate"].max()
    signals = df[df["SourceDate"] == latest_date].copy()
    return signals, latest_date


def calculate_liquidity(hist: pd.DataFrame) -> pd.DataFrame:
    """Calculate 20-day average volume and value per stock."""
    df = hist.sort_values(["Kode Saham", "SourceDate"])
    df["avg_20d_volume"] = df.groupby("Kode Saham")["Volume"].transform(
        lambda x: x.rolling(LIQUIDITY_WINDOW, min_periods=10).mean()
    )
    df["avg_20d_value"] = df.groupby("Kode Saham")["Nilai"].transform(
        lambda x: x.rolling(LIQUIDITY_WINDOW, min_periods=10).mean()
    )
    # Get latest liquidity for each stock
    latest = df.sort_values("SourceDate").groupby("Kode Saham").tail(1)
    return latest[["Kode Saham", "avg_20d_volume", "avg_20d_value", "Penutupan", "Volume", "Nilai"]]


def get_regime_context(clusters_path: Path, latest_date: pd.Timestamp) -> dict:
    """Get current market regime and interpretation."""
    df = pd.read_csv(clusters_path)
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Get latest cluster
    latest = df[df["Date"] == latest_date]
    if len(latest) == 0:
        latest = df.sort_values("Date").tail(1)
    
    cluster = int(latest["cluster"].iloc[0])
    top1 = latest["top1_share"].iloc[0]
    hhi = latest["hhi_vol"].iloc[0]
    
    regime_desc = {
        0: "Moderate flow (normal conditions, historically favorable for signals)",
        1: "Low flow/volume (quiet market, reduce position sizes)",
        2: "High concentration (dominant broker activity, elevated risk/opportunity)"
    }
    
    return {
        "cluster": cluster,
        "description": regime_desc.get(cluster, "Unknown"),
        "top1_share": top1,
        "hhi_vol": hhi,
        "date": latest["Date"].iloc[0]
    }


def check_dominance_event(broker_path: Path, latest_date: pd.Timestamp) -> dict:
    """Check if latest date is a dominance event."""
    df = pd.read_csv(broker_path)
    date_col = "Date" if "Date" in df.columns else "date"
    vol_col = "Volume" if "Volume" in df.columns else "volume"
    val_col = "Nilai" if "Nilai" in df.columns else "nilai"
    
    df["Date"] = pd.to_datetime(df[date_col])
    
    # Get daily stats
    df["vol_share"] = df[vol_col] / df.groupby("Date")[vol_col].transform("sum")
    daily = df.groupby("Date").agg(
        total_value=(val_col, "sum"),
        top1_share=("vol_share", lambda x: x.nlargest(1).sum())
    ).reset_index()
    
    # Compute z-scores
    daily["value_z"] = (daily["total_value"] - daily["total_value"].rolling(20, min_periods=5).mean()) / daily["total_value"].rolling(20, min_periods=5).std()
    
    # Check thresholds (80th percentile, value_z >= -0.3)
    top1_threshold = daily["top1_share"].quantile(0.8)
    
    latest = daily[daily["Date"] == latest_date]
    if len(latest) == 0:
        latest = daily.sort_values("Date").tail(1)
    
    is_event = (latest["top1_share"].iloc[0] >= top1_threshold) and (latest["value_z"].iloc[0] >= -0.3)
    
    return {
        "is_event": is_event,
        "top1_share": latest["top1_share"].iloc[0],
        "value_z": latest["value_z"].iloc[0],
        "threshold": top1_threshold
    }


def score_and_rank(signals: pd.DataFrame, liquidity: pd.DataFrame, regime: dict, event: dict) -> pd.DataFrame:
    """Combine signals with liquidity and regime to produce final scores."""
    # Merge signals with liquidity
    merged = signals.merge(liquidity, on="Kode Saham", how="left")
    
    # Filter by liquidity
    merged = merged[
        (merged["avg_20d_volume"] >= MIN_AVG_VOLUME) &
        (merged["avg_20d_value"] >= MIN_AVG_VALUE)
    ].copy()
    
    # Liquidity score: normalize volume and value to 0-1 range
    merged["volume_score"] = merged["avg_20d_volume"] / merged["avg_20d_volume"].max()
    merged["value_score"] = merged["avg_20d_value"] / merged["avg_20d_value"].max()
    merged["liquidity_factor"] = (merged["volume_score"] + merged["value_score"]) / 2
    
    # Regime multiplier
    regime_multipliers = {
        0: 1.2,  # Favorable regime
        1: 0.8,  # Quiet market
        2: 1.0 if event["is_event"] else 0.9  # High concentration: good if event, else caution
    }
    regime_mult = regime_multipliers.get(regime["cluster"], 1.0)
    
    # Final score: signal_score × liquidity_factor × regime_multiplier
    merged["final_score"] = merged["signal_score"] * merged["liquidity_factor"] * regime_mult
    
    # Rank and return top 5
    top5 = merged.nlargest(5, "final_score")
    return top5


def write_recommendations(top5: pd.DataFrame, regime: dict, event: dict, signal_date: pd.Timestamp):
    """Write formatted recommendation report."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"DAILY TOP 5 STOCK RECOMMENDATIONS FOR SWING TRADING")
    lines.append(f"Signal Date: {signal_date.strftime('%Y-%m-%d')} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 80)
    lines.append("")
    
    # Market context
    lines.append("MARKET CONTEXT:")
    lines.append(f"  Regime (Cluster {regime['cluster']}): {regime['description']}")
    lines.append(f"  Top-1 Broker Share: {regime['top1_share']:.1%} | HHI: {regime['hhi_vol']:.4f}")
    event_status = "YES (Bullish bias for next day)" if event["is_event"] else "NO"
    lines.append(f"  Dominance Event: {event_status}")
    if event["is_event"]:
        lines.append(f"    → Top-1 share {event['top1_share']:.1%} ≥ threshold {event['threshold']:.1%}, value z-score {event['value_z']:.2f}")
    lines.append("")
    
    # Top 5 recommendations
    lines.append("TOP 5 RECOMMENDATIONS (Ranked by Final Score):")
    lines.append("-" * 80)
    
    for idx, row in top5.iterrows():
        rank = top5.index.get_loc(idx) + 1
        lines.append(f"\n{rank}. {row['Kode Saham']} — Rp {int(row['close']):,}")
        lines.append(f"   Signal Score: {row['signal_score']:.1f} | Final Score: {row['final_score']:.2f}")
        lines.append(f"   Momentum: 3d={row['ret_3d']:.1f}%, 10d={row['ret_10d']:.1f}%")
        lines.append(f"   Liquidity: Avg Vol={row['avg_20d_volume']/1e6:.1f}M shares, Avg Value={row['avg_20d_value']/1e9:.2f}B IDR")
        lines.append(f"   Latest: Vol={row['Volume']/1e6:.1f}M shares, Value={row['Nilai']/1e9:.2f}B IDR")
        
        # Rationale
        if row['ret_3d'] > 20:
            lines.append(f"   🔥 Strong short-term momentum (3d: {row['ret_3d']:.1f}%) - already extended, consider pullback entry")
        elif row['ret_3d'] < 0 and row['ret_10d'] > 10:
            lines.append(f"   💎 Pullback opportunity (3d down but 10d up) - potential mean-reversion play")
        else:
            lines.append(f"   ✅ Balanced momentum - early stage breakout candidate")
    
    lines.append("")
    lines.append("-" * 80)
    lines.append("TRADING GUIDELINES:")
    lines.append("  • Entry: Consider limit orders near current close or wait for intraday pullback")
    lines.append("  • Position Size: Scale by liquidity (higher avg volume = safer for larger positions)")
    lines.append("  • Stop-Loss: Set 2-3% below entry or below recent swing low")
    lines.append("  • Target: 5-10% gain within 1-5 days (swing trade horizon)")
    lines.append("  • Risk: If market regime is Cluster 1 (low flow), reduce position sizes by 50%")
    
    if event["is_event"]:
        lines.append("  • Event Bias: Dominance detected → lean bullish for next-day follow-through")
    
    lines.append("")
    lines.append("LIQUIDITY FILTERS APPLIED:")
    lines.append(f"  • Min Avg Volume: {MIN_AVG_VOLUME/1e6:.1f}M shares (20-day average)")
    lines.append(f"  • Min Avg Value: {MIN_AVG_VALUE/1e9:.1f}B IDR (20-day average)")
    lines.append(f"  • Stocks excluded: Illiquid tickers with low trading activity")
    lines.append("")
    lines.append("=" * 80)
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines))
    print(f"Recommendations written to {OUTPUT_FILE}")


def main():
    # Load data
    signals, signal_date = load_latest_signals(PICKS_FILE)
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    liquidity = calculate_liquidity(hist)
    
    # Get context
    regime = get_regime_context(CLUSTERS_FILE, signal_date)
    event = check_dominance_event(BROKER_FILE, signal_date)
    
    # Score and rank
    top5 = score_and_rank(signals, liquidity, regime, event)
    
    # Write recommendations
    write_recommendations(top5, regime, event, signal_date)
    
    # Also print to console
    print("\nTOP 5 PICKS:")
    for idx, row in top5.iterrows():
        rank = top5.index.get_loc(idx) + 1
        print(f"{rank}. {row['Kode Saham']:6s} Rp {int(row['close']):6,} | Score: {row['final_score']:6.2f} | 3d: {row['ret_3d']:6.1f}% | Vol: {row['avg_20d_volume']/1e6:5.1f}M")


if __name__ == "__main__":
    main()
