#!/usr/bin/env python3
"""
Flow-augmented momentum/contrarian scaffold.

Datasets used:
- data/histories/ringkasan_histories_combined.csv : daily OHLCV per stock.
- data/reference/ringkasan_broker_combined_20251201_20260121.csv : daily broker volumes/values (market-level, no stock breakdown).
- data/reference/IDX-Stock-Screener-20Jan2026.xlsx : optional fundamentals (not needed for the base signal, but can be merged for filters).

Idea:
- Build a market flow factor from broker file: total traded value and concentration (HHI) across brokers.
- Join that daily market factor to each stock's price history.
- Generate signals that require both a price condition (momentum or pullback) and supportive flow regime (flow factor z-score above threshold).
- Evaluate next-5-day forward returns as a quick cross-sectional backtest.

Limitations:
- Broker file is aggregated by broker, not by stock, so flow factor is market-level (not stock-specific buy/sell). It is used as a regime filter rather than a per-stock directional flow.
"""

from pathlib import Path
import pandas as pd
import numpy as np

HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
BROKER_FILE = Path("data/reference/ringkasan_broker_combined_20251201_20260121.csv")
HOLD_DAYS = 5
OUTPUT_FILE = Path("results/flow_augmented_momentum_report.txt")
PICKS_FILE = Path("results/flow_augmented_momentum_picks.csv")

# Signal parameters (more selective than the prior broad version)
FLOW_Z_MIN = -0.3
HHI_Z_MIN = -0.3
PULLBACK_3D_MAX = -0.5  # % return threshold
PULLBACK_10D_MAX = 6.0
MOMENTUM_10D_MIN = 2.0
TOP_N = 20


def load_histories(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["SourceDate"] = pd.to_datetime(df["SourceDate"])
    # Keep only needed columns to reduce memory
    cols = ["SourceDate", "Kode Saham", "Penutupan", "Tertinggi", "Terendah", "Volume", "Nilai"]
    df = df[cols].copy()
    df = df.rename(columns={"Penutupan": "close", "Tertinggi": "high", "Terendah": "low", "Volume": "volume", "Nilai": "value"})
    return df


def load_broker_flow(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    date_col = "Date" if "Date" in df.columns else "date"
    df["Date"] = pd.to_datetime(df[date_col])
    # Aggregate market-level stats per day
    agg = df.groupby("Date").agg(
        total_value=("nilai", "sum"),
        total_volume=("volume", "sum"),
    ).reset_index()
    # Concentration via HHI on volume share
    df["vol_share"] = df["volume"] / df.groupby("Date")["volume"].transform("sum")
    hhi = df.groupby("Date")["vol_share"].apply(lambda x: np.sum(np.square(x))).reset_index(name="hhi_vol")
    agg = agg.merge(hhi, on="Date", how="left")
    # Z-scores for regime classification
    for col in ["total_value", "total_volume", "hhi_vol"]:
        mean = agg[col].rolling(60, min_periods=5).mean()
        std = agg[col].rolling(60, min_periods=5).std()
        agg[f"{col}_z"] = (agg[col] - mean) / std
        agg[f"{col}_z"] = agg[f"{col}_z"].fillna(0)
    agg = agg.rename(columns={"Date": "SourceDate"})
    return agg


def attach_features(hist: pd.DataFrame, flow: pd.DataFrame) -> pd.DataFrame:
    df = hist.sort_values(["Kode Saham", "SourceDate"]).copy()
    # Price-based features
    df["ret_3d"] = df.groupby("Kode Saham")["close"].pct_change(3) * 100
    df["ret_5d"] = df.groupby("Kode Saham")["close"].pct_change(5) * 100
    df["ret_10d"] = df.groupby("Kode Saham")["close"].pct_change(10) * 100
    df["vol_20d"] = df.groupby("Kode Saham")["close"].pct_change().rolling(20).std() * 100
    # Forward 5-day return for evaluation
    df["fwd_5d_ret"] = df.groupby("Kode Saham")["close"].shift(-HOLD_DAYS) / df["close"] - 1
    df["fwd_5d_ret"] = df["fwd_5d_ret"] * 100

    # Join market flow regime
    df = df.merge(flow, on="SourceDate", how="left")
    return df


def build_signals(df: pd.DataFrame) -> pd.DataFrame:
    # Regime: high value and concentration supportive for momentum; low/neutral for contrarian
    flow_ok = (df["total_value_z"].fillna(0) > FLOW_Z_MIN) & (df["hhi_vol_z"].fillna(0) > HHI_Z_MIN)
    pullback = (df["ret_3d"].fillna(0) < PULLBACK_3D_MAX) & (df["ret_10d"].fillna(0) < PULLBACK_10D_MAX)
    momentum = (df["ret_10d"].fillna(0) > MOMENTUM_10D_MIN)
    # Long signal: either pullback with supportive flow, or momentum with supportive flow
    df["signal_long"] = (pullback | momentum) & flow_ok
    # Score for ranking: prefer stronger momentum; for pullbacks use depth of 3d drop
    df["signal_score"] = np.where(pullback, -df["ret_3d"].fillna(0), df["ret_10d"].fillna(0))
    return df


def evaluate_cross_section(df: pd.DataFrame) -> pd.DataFrame:
    # Daily cross-sectional performance: average next-5d return of signaled names
    signals = df[df["signal_long"]].copy()
    signals = signals.dropna(subset=["fwd_5d_ret"])  # require forward return to evaluate
    perf = signals.groupby("SourceDate")["fwd_5d_ret"].mean().reset_index(name="cs_mean_fwd5d")
    perf["cs_count"] = signals.groupby("SourceDate")["fwd_5d_ret"].size().values
    perf["cs_mean_fwd5d_cum"] = (1 + perf["cs_mean_fwd5d"] / 100).cumprod() - 1
    return perf


def generate_picks(df: pd.DataFrame, top_n: int = TOP_N) -> pd.DataFrame:
    picks = []
    signals = df[df["signal_long"]].copy()
    for date, group in signals.groupby("SourceDate"):
        grp = group.sort_values("signal_score", ascending=False).head(top_n)
        picks.append(grp[[
            "SourceDate", "Kode Saham", "close", "ret_3d", "ret_10d", "total_value_z", "hhi_vol_z", "signal_score", "fwd_5d_ret"
        ]])
    if not picks:
        return pd.DataFrame(columns=["SourceDate", "Kode Saham", "close", "ret_3d", "ret_10d", "total_value_z", "hhi_vol_z", "signal_score", "fwd_5d_ret"])
    return pd.concat(picks, ignore_index=True)


def main():
    hist = load_histories(HIST_FILE)
    flow = load_broker_flow(BROKER_FILE)
    df = attach_features(hist, flow)
    df = build_signals(df)
    perf = evaluate_cross_section(df)
    picks = generate_picks(df)

    lines = []
    lines.append("Flow-augmented momentum/contrarian (long-only) summary")
    lines.append(f"Coverage stocks: {df['Kode Saham'].nunique()}")
    lines.append(f"Sample dates: {df['SourceDate'].min().date()} to {df['SourceDate'].max().date()}")
    lines.append("")
    lines.append("Signal days with counts and next-5d average return (%):")
    lines.append(perf.tail(15).to_string(index=False))
    lines.append("")
    lines.append("Overall stats:")
    lines.append(f"Total signal days: {len(perf)}")
    if len(perf):
        lines.append(f"Mean daily next-5d: {perf['cs_mean_fwd5d'].mean():.2f}%")
        lines.append(f"Median daily next-5d: {perf['cs_mean_fwd5d'].median():.2f}%")
        lines.append(f"Cumulative (compounded): {perf['cs_mean_fwd5d_cum'].iloc[-1]*100:.2f}%")
    else:
        lines.append("No signals generated; consider loosening thresholds.")

    lines.append("")
    lines.append("How to read this:")
    lines.append("- Each signal day count is how many tickers met the pullback/momentum + flow regime filters that day.")
    lines.append("- cs_mean_fwd5d is the average forward 5-day return of all signaled names on that day (not a PnL curve).")
    lines.append("- cs_mean_fwd5d_cum is a compounded curve of those daily averages; it is not a tradeable equity curve.")
    lines.append("- Use results/flow_augmented_momentum_picks.csv for the top-ranked tickers per day (signal_score).")
    lines.append("- Broker flow here is market-level and undirected; no split by institutional vs retail or foreign vs domestic is available in the input.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines))
    picks.to_csv(PICKS_FILE, index=False)
    print(f"Report written to {OUTPUT_FILE}")
    print(f"Picks written to {PICKS_FILE}")


if __name__ == "__main__":
    main()
