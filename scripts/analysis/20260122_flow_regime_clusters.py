#!/usr/bin/env python3
"""
Regime/cluster analysis on market flow and volatility.

Inputs:
- data/reference/ringkasan_broker_combined_20251201_20260121.csv : broker-level daily volume/value (no buy/sell breakdown).
- data/histories/ringkasan_histories_combined.csv : daily OHLCV per stock.
- (Optional) data/reference/IDX-Stock-Screener-20Jan2026.xlsx : not used directly; can be merged later for regime descriptors.

Method:
- Build daily flow features: total value/volume, top-1/3 share, HHI, broker count.
- Build market features from price histories: equal-weight return, 20d volatility of returns, 20d volume ratio.
- Standardize features and cluster days with a simple k-means (k=3).
- Build a basic pullback/momentum signal at the stock level and evaluate next-5d returns conditioned on regimes.

Outputs:
- results/flow_regime_clusters.txt : summary of cluster centers and signal performance per cluster.
- results/flow_regime_clusters.csv : per-day cluster assignments and key features.

Limitations:
- Broker data lacks direction; regimes capture concentration/size, not net-buy vs net-sell.
- Short sample (only two dates in current broker file) will make clustering trivial; still produced for structure.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BROKER_FILE = Path("data/reference/ringkasan_broker_combined_20251201_20260121.csv")
HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
REPORT_FILE = Path("results/flow_regime_clusters.txt")
CLUSTERS_FILE = Path("results/flow_regime_clusters.csv")

K = 3  # clusters
HOLD_DAYS = 5


def simple_kmeans(X, k=3, iters=20, seed=42):
    rng = np.random.default_rng(seed)
    centroids = X[rng.choice(len(X), size=k, replace=False)] if len(X) >= k else np.tile(X.mean(axis=0, keepdims=True), (k, 1))
    for _ in range(iters):
        dists = ((X[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        labels = dists.argmin(axis=1)
        new_centroids = np.array([X[labels == j].mean(axis=0) if np.any(labels == j) else centroids[j] for j in range(k)])
        if np.allclose(new_centroids, centroids, atol=1e-6):
            break
        centroids = new_centroids
    return labels, centroids


def load_broker_features(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    date_col = "Date" if "Date" in df.columns else "date"
    vol_col = "Volume" if "Volume" in df.columns else "volume"
    val_col = "Nilai" if "Nilai" in df.columns else "nilai"
    code_col = "kode_perusahaan" if "kode_perusahaan" in df.columns else "No" if "No" in df.columns else "no"

    df["Date"] = pd.to_datetime(df[date_col])
    df["vol_share"] = df[vol_col] / df.groupby("Date")[vol_col].transform("sum")

    daily = (
        df.groupby("Date")
        .agg(
            total_value=(val_col, "sum"),
            total_volume=(vol_col, "sum"),
            broker_count=(code_col, "nunique"),
        )
        .reset_index()
    )

    ranked = df.sort_values(["Date", "vol_share"], ascending=[True, False]).groupby("Date")
    top1 = ranked.head(1).groupby("Date")["vol_share"].sum().rename("top1_share")
    top3 = ranked.head(3).groupby("Date")["vol_share"].sum().rename("top3_share")
    hhi = df.groupby("Date")["vol_share"].apply(lambda x: np.sum(np.square(x))).rename("hhi_vol")

    out = daily.merge(top1, on="Date", how="left").merge(top3, on="Date", how="left").merge(hhi, on="Date", how="left")
    return out


def load_market_features(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["SourceDate"] = pd.to_datetime(df["SourceDate"])
    df = df.sort_values(["Kode Saham", "SourceDate"])
    df["ret1"] = df.groupby("Kode Saham")["Penutupan"].pct_change()
    mkt = df.groupby("SourceDate").agg(mkt_ret=("ret1", "mean"), mkt_value=("Nilai", "sum"), mkt_volume=("Volume", "sum"))
    mkt["mkt_vol_ratio"] = mkt["mkt_volume"] / mkt["mkt_volume"].rolling(20, min_periods=5).mean()
    mkt["mkt_vol_ratio"] = mkt["mkt_vol_ratio"].fillna(1.0)
    # volatility of returns
    mkt["mkt_ret_vol20"] = mkt["mkt_ret"].rolling(20, min_periods=5).std()
    return mkt.reset_index().rename(columns={"SourceDate": "Date"})


def prepare_clusters(broker: pd.DataFrame, market: pd.DataFrame):
    df = broker.merge(market, on="Date", how="left")
    features = ["total_value", "total_volume", "top1_share", "top3_share", "hhi_vol", "broker_count", "mkt_ret_vol20", "mkt_vol_ratio"]
    feat_df = df[features].copy()
    feat_df = feat_df.fillna(feat_df.median())
    # z-score
    feat_z = (feat_df - feat_df.mean()) / feat_df.std(ddof=0)
    X = feat_z.values
    labels, centroids = simple_kmeans(X, k=K)
    df["cluster"] = labels
    centers_df = pd.DataFrame(centroids, columns=features)
    return df, centers_df


def build_signals(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist.sort_values(["Kode Saham", "SourceDate"]).copy()
    df["ret_5d"] = df.groupby("Kode Saham")["Penutupan"].pct_change(5) * 100
    df["ret_20d"] = df.groupby("Kode Saham")["Penutupan"].pct_change(20) * 100
    df["fwd_5d_ret"] = df.groupby("Kode Saham")["Penutupan"].shift(-HOLD_DAYS) / df["Penutupan"] - 1
    df["fwd_5d_ret"] = df["fwd_5d_ret"] * 100
    signal = ((df["ret_5d"] < -2) & (df["ret_20d"] < 5)) | (df["ret_20d"] > 3)
    df["signal_long"] = signal
    return df


def evaluate_by_cluster(signals: pd.DataFrame, clusters: pd.DataFrame):
    sig = signals[signals["signal_long"]].copy()
    sig = sig.merge(clusters[["Date", "cluster"]], left_on="SourceDate", right_on="Date", how="left")
    sig = sig.dropna(subset=["fwd_5d_ret", "cluster"])
    perf = sig.groupby("cluster")["fwd_5d_ret"].agg(["count", "mean", "median"])
    return perf


def write_report(clustered: pd.DataFrame, centers: pd.DataFrame, perf: pd.DataFrame):
    lines = []
    lines.append("Flow regime clusters (k=3) and signal performance")
    lines.append(f"Days clustered: {len(clustered)}")
    lines.append("")
    lines.append("Cluster centers (z-scored feature space):")
    lines.append(centers.to_string(index=True, float_format=lambda x: f"{x:6.2f}"))
    lines.append("")
    lines.append("Signal performance by cluster (basic pullback/momentum, next-5d %):")
    if len(perf):
        lines.append(perf.to_string(float_format=lambda x: f"{x:6.2f}"))
    else:
        lines.append("No signals available in sample.")
    lines.append("")
    lines.append("Recent cluster assignments (latest 10 days):")
    tail = clustered.sort_values("Date").tail(10)[["Date", "cluster", "top1_share", "hhi_vol", "mkt_ret_vol20", "mkt_vol_ratio"]]
    lines.append(tail.to_string(index=False, formatters={"Date": lambda x: x.strftime('%Y-%m-%d')}))

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    clustered.to_csv(CLUSTERS_FILE, index=False)
    print(f"Report written to {REPORT_FILE}")
    print(f"Clusters written to {CLUSTERS_FILE}")


def main():
    broker = load_broker_features(BROKER_FILE)
    market = load_market_features(HIST_FILE)
    clustered, centers = prepare_clusters(broker, market)
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    signals = build_signals(hist)
    perf = evaluate_by_cluster(signals, clustered)
    write_report(clustered, centers, perf)


if __name__ == "__main__":
    main()
