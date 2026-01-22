#!/usr/bin/env python3
"""
Event study: broker dominance vs next-day market response.

Data:
- data/reference/ringkasan_broker_combined_20251201_20260121.csv : broker-level volume/value per day (no per-stock direction).
- data/histories/ringkasan_histories_combined.csv : daily OHLCV per stock.

Method (direction-agnostic due to data limits):
- Compute market concentration per day: top-1 share, top-3 share, and HHI on broker volume.
- Define dominance events: days where top-1 share is in the 90th percentile AND total traded value z-score > 0.
- Measure next-day market reaction: equal-weight market return (average of all stocks' next-day returns) and aggregate volume vs 20-day average.

Output:
- results/broker_event_study.txt : summary stats and recent event samples.

Limitations:
- Broker file lacks buy/sell direction; we treat dominance as a proxy for aggressive presence, but cannot label net-buy vs net-sell.
- Results are market-level, not per-stock trades.
"""

from pathlib import Path
import pandas as pd
import numpy as np

BROKER_FILE = Path("data/reference/ringkasan_broker_combined_20251201_20260121.csv")
HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
OUTPUT_FILE = Path("results/broker_event_study.txt")


def load_broker_daily(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    date_col = "Date" if "Date" in df.columns else "date"
    vol_col = "Volume" if "Volume" in df.columns else "volume"
    val_col = "Nilai" if "Nilai" in df.columns else "nilai"
    df["Date"] = pd.to_datetime(df[date_col])
    # total per day
    daily = df.groupby("Date").agg(total_value=(val_col, "sum"), total_volume=(vol_col, "sum")).reset_index()
    # shares
    df["vol_share"] = df[vol_col] / df.groupby("Date")[vol_col].transform("sum")
    ranks = df.sort_values(["Date", "vol_share"], ascending=[True, False]).groupby("Date")
    top1 = ranks.head(1).groupby("Date")["vol_share"].sum().rename("top1_share")
    top3 = ranks.head(3).groupby("Date")["vol_share"].sum().rename("top3_share")
    hhi = df.groupby("Date")["vol_share"].apply(lambda x: np.sum(np.square(x))).rename("hhi_vol")
    out = daily.merge(top1, on="Date").merge(top3, on="Date").merge(hhi, on="Date")
    # z-scores (shorter window to accommodate limited history)
    for col in ["total_value", "total_volume", "hhi_vol", "top1_share", "top3_share"]:
        mean = out[col].rolling(20, min_periods=5).mean()
        std = out[col].rolling(20, min_periods=5).std()
        out[f"{col}_z"] = (out[col] - mean) / std
        out[f"{col}_z"] = out[f"{col}_z"].fillna(0)
    return out


def load_market_returns(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["SourceDate"] = pd.to_datetime(df["SourceDate"])
    df = df.sort_values(["Kode Saham", "SourceDate"])
    df["ret1"] = df.groupby("Kode Saham")["Penutupan"].pct_change()
    # Equal-weight market return by averaging across stocks each day
    mkt = df.groupby("SourceDate").agg(mkt_ret=("ret1", "mean"), mkt_value=("Nilai", "sum"), mkt_volume=("Volume", "sum"))
    # next-day returns/volume ratio for event alignment
    mkt["mkt_ret_fwd1"] = mkt["mkt_ret"].shift(-1)
    mkt["mkt_vol_ratio"] = mkt["mkt_volume"] / mkt["mkt_volume"].rolling(20, min_periods=5).mean()
    mkt["mkt_vol_ratio_fwd1"] = mkt["mkt_vol_ratio"].shift(-1)
    return mkt.reset_index().rename(columns={"SourceDate": "Date"})


def define_events(broker_daily: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    # Looser filter: 80th percentile dominance and allow mildly below-average value
    top1_threshold = broker_daily["top1_share"].quantile(0.8)
    value_z_floor = -0.3
    events = broker_daily[
        (broker_daily["top1_share"] >= top1_threshold)
        & (broker_daily["total_value_z"] >= value_z_floor)
    ].copy()
    events["event"] = "dominance_high"
    return events, {"top1_threshold": top1_threshold, "value_z_floor": value_z_floor}


def evaluate_events(events: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    ev = events.merge(market, on="Date", how="left")
    # Exclude last available date where fwd data is unavailable
    last_date = market["Date"].max()
    ev = ev[ev["Date"] < last_date]
    ev["fwd_ret1_pct"] = ev["mkt_ret_fwd1"] * 100
    summary = {
        "event_count": len(ev),
        "mean_fwd_ret1_pct": ev["fwd_ret1_pct"].mean() if len(ev) else 0,
        "median_fwd_ret1_pct": ev["fwd_ret1_pct"].median() if len(ev) else 0,
        "hit_rate_pos": (ev["fwd_ret1_pct"] > 0).mean() * 100 if len(ev) else 0,
        "mean_fwd_vol_ratio": ev["mkt_vol_ratio_fwd1"].mean() if len(ev) else 0,
    }
    return ev, summary


def write_report(events: pd.DataFrame, summary: dict, event_params: dict):
    lines = []
    lines.append("Broker dominance event study (market-level, direction-agnostic)")
    lines.append(
        "Filters: top1_share >= "
        f"{event_params['top1_threshold']:.3f}, total_value_z >= {event_params['value_z_floor']:.1f}"
    )
    lines.append(
        "Interpretation: dominance events are days where one broker controls much of the flow; "
        "we check the next-day market response. Positive mean/median return and hit-rate >50% "
        "hint at short-term bullish follow-through; volume ratio >1.0 suggests elevated activity."
    )
    lines.append(
        "Caveats: data lacks buy vs sell direction, so signals are unsigned; sample size may be small."
    )
    lines.append(f"Events: {summary['event_count']}")
    lines.append(f"Mean next-day market return: {summary['mean_fwd_ret1_pct']:.3f}%")
    lines.append(f"Median next-day market return: {summary['median_fwd_ret1_pct']:.3f}%")
    lines.append(f"Hit-rate (next-day > 0): {summary['hit_rate_pos']:.1f}%")
    lines.append(f"Mean next-day volume ratio (vs 20d avg): {summary['mean_fwd_vol_ratio']:.3f}x")
    lines.append("")
    lines.append("Recent events (latest 10):")
    if len(events):
        tail = events.sort_values("Date").tail(10)[["Date", "top1_share", "top3_share", "hhi_vol", "fwd_ret1_pct", "mkt_vol_ratio_fwd1"]]
        lines.append(tail.to_string(index=False, formatters={"Date": lambda x: x.strftime('%Y-%m-%d')}))
    else:
        lines.append("No events detected; consider lowering the dominance threshold.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines))
    print(f"Report written to {OUTPUT_FILE}")


def main():
    broker_daily = load_broker_daily(BROKER_FILE)
    market = load_market_returns(HIST_FILE)
    events, event_params = define_events(broker_daily)
    ev_with_resp, summary = evaluate_events(events, market)
    write_report(ev_with_resp, summary, event_params)


if __name__ == "__main__":
    main()
