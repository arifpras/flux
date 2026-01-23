#!/usr/bin/env python3
"""
Generate the daily text reports for the six requested methods using the
current combined datasets. Outputs are written into results/ with fixed
date-stamped filenames for 2026-01-22.

Methods:
1) Dividend oriented (yield + recency)
2) Foreign net buy + 5-day price decline
3) Net buy at t, price up at t+1
4) Foreign net buy + 5-day decline + fundamental filter
5) Net buy at t, price up at t+1 + fundamental filter
6) Technical enhanced swing (MA crossover + pivots proxy + vol filter + BB + pullback)

Data files used:
- data/histories/ringkasan_histories_combined.csv
- data/reference/ringkasan_broker_combined.csv (not split by foreign/domestic; we use Foreign Buy/Sell from histories)
- data/reference/idx_dividend_history.csv
- data/reference/IDX-Stock-Screener-22Jan2026.xlsx
- data/reference/Financial Data and Ratio - Dec 2025.xlsx
- data/reference/Stock List  - 20260122.xlsx
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


RUN_DATE = "2026-01-22"
GENERATE_INDIVIDUAL_REPORTS = False  # set True if you still want the per-method txt files
HIST_PATH = Path("data/histories/ringkasan_histories_combined.csv")
BROKER_PATH = Path("data/reference/ringkasan_broker_combined.csv")
DIVIDEND_PATH = Path("data/reference/idx_dividend_history.csv")
SCREENER_PATH = Path("data/reference/IDX-Stock-Screener-22Jan2026.xlsx")
FIN_PATH = Path("data/reference/Financial Data and Ratio - Dec 2025.xlsx")
STOCKLIST_PATH = Path("data/reference/Stock List  - 20260122.xlsx")
NEWS_CACHE_DIR = Path("data/news_cache")
TEMPLATE_PATH = Path("docs/STRATEGY_REPORT_CONCISE_TEMPLATE.txt")

# Silence noisy openpyxl default style warning when loading Excel files
warnings.filterwarnings(
    "ignore",
    message="Workbook contains no default style",
    category=UserWarning,
    module="openpyxl",
)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def load_histories() -> pd.DataFrame:
    df = pd.read_csv(HIST_PATH)
    df["SourceDate"] = pd.to_datetime(df["SourceDate"])
    df = df.sort_values(["Kode Saham", "SourceDate"])
    df["net_foreign"] = df.get("Foreign Buy", 0) - df.get("Foreign Sell", 0)
    df["return_pct"] = df.groupby("Kode Saham")["Penutupan"].pct_change() * 100
    return df


def load_dividends() -> pd.DataFrame:
    df = pd.read_csv(DIVIDEND_PATH)
    if "payment_date" in df.columns:
        df["payment_date"] = pd.to_datetime(df["payment_date"])
    return df


def load_fundamentals() -> pd.DataFrame:
    def _load_excel(path: Path) -> pd.DataFrame:
        try:
            df = pd.read_excel(path)
            df.columns = df.columns.str.strip()
            return df
        except Exception:
            return pd.DataFrame()

    fin = _load_excel(FIN_PATH)
    screener = _load_excel(SCREENER_PATH)

    # Normalize ticker column to Code
    if not fin.empty:
        if "Code" not in fin.columns and "Kode Saham" in fin.columns:
            fin = fin.rename(columns={"Kode Saham": "Code"})
        elif "Code" not in fin.columns and "Ticker" in fin.columns:
            fin = fin.rename(columns={"Ticker": "Code"})
        if "Code" not in fin.columns:
            # fallback: if first column looks like a ticker, use it; else drop Code
            first_col = fin.columns[0]
            fin = fin.rename(columns={first_col: "Code"})
        if "Code" in fin.columns:
            fin["Code"] = fin["Code"].astype(str).str.strip()
    if not screener.empty:
        if "Code" not in screener.columns and "Kode Saham" in screener.columns:
            screener = screener.rename(columns={"Kode Saham": "Code"})
        if "Code" not in screener.columns:
            first_col = screener.columns[0]
            screener = screener.rename(columns={first_col: "Code"})
        if "Code" in screener.columns:
            screener["Code"] = screener["Code"].astype(str).str.strip()

    merged: pd.DataFrame
    if not fin.empty and not screener.empty:
        merged = fin.merge(screener, on="Code", how="outer", suffixes=("_fin", "_scr"))
    elif not fin.empty:
        merged = fin.copy()
    elif not screener.empty:
        merged = screener.copy()
    else:
        merged = pd.DataFrame()

    if not merged.empty and "Code" in merged.columns:
        merged["Code"] = merged["Code"].astype(str).str.strip()
    return merged


def load_stocklist() -> pd.DataFrame:
    try:
        df = pd.read_excel(STOCKLIST_PATH)
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return pd.DataFrame()


def latest_prices(hist: pd.DataFrame) -> pd.DataFrame:
    latest = hist.sort_values("SourceDate").groupby("Kode Saham").tail(1)
    return latest[["Kode Saham", "Penutupan", "SourceDate"]].rename(columns={"Penutupan": "last_close"})


def compute_5d_change(hist: pd.DataFrame) -> pd.Series:
    def _chg(s: pd.Series) -> float:
        if len(s) < 6:
            return 0.0
        tail = s.tail(6)
        start, end = tail.iloc[0], tail.iloc[-1]
        if start == 0:
            return 0.0
        return (end - start) / start * 100

    return hist.groupby("Kode Saham", group_keys=False)["Penutupan"].apply(_chg)


def net_foreign_5d(hist: pd.DataFrame) -> pd.Series:
    def _net(s: pd.Series) -> float:
        return s.tail(5).sum()

    return hist.groupby("Kode Saham", group_keys=False)["net_foreign"].apply(_net)


def next_day_return(hist: pd.DataFrame) -> pd.DataFrame:
    g = hist.copy()
    g["next_return_pct"] = g.groupby("Kode Saham")["Penutupan"].pct_change(-1) * 100
    latest = g.groupby("Kode Saham").tail(1)
    return latest[["Kode Saham", "next_return_pct", "SourceDate"]]


def passes_basic_fundamentals(row: pd.Series) -> bool:
    # Screener columns we care about
    val = lambda c: row[c] if c in row.index and pd.notna(row[c]) else None
    roe = val("ROE %")
    npm = val("NPM %")
    der = val("DER")
    per = val("PER")

    roe_ok = roe is None or roe > 8
    npm_ok = npm is None or npm > 5
    der_ok = der is None or der < 200
    per_ok = per is None or (0 < per < 25)
    return roe_ok and npm_ok and der_ok and per_ok


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_lines(path: Path, lines: List[str]) -> None:
    ensure_dir(path)
    path.write_text("\n".join(lines))
    print(f"✓ Wrote {path}")


def method_dividend(hist: pd.DataFrame, dividends: pd.DataFrame, fundamentals: pd.DataFrame) -> None:
    latest = latest_prices(hist)
    recent_divs = dividends.copy()
    if "dividend_year" in recent_divs.columns:
        recent_divs = recent_divs[recent_divs["dividend_year"] >= 2023]
    grouped = recent_divs.groupby("stock_code").agg({"dividend_amount_numeric": "sum", "dividend_year": "count"}).rename(columns={"dividend_amount_numeric": "total_div", "dividend_year": "payouts"}).reset_index()
    merged = grouped.merge(latest, left_on="stock_code", right_on="Kode Saham", how="left")
    merged["yield_pct"] = (merged["total_div"] / merged["last_close"]).fillna(0) * 100
    merged["consistency"] = merged["payouts"].fillna(0) / 3
    merged = merged.sort_values("yield_pct", ascending=False)
    lines = ["MONTHLY DIVIDEND INCOME STRATEGY", f"Run date: {RUN_DATE}", ""]
    lines.append(f"Top {min(15, len(merged))} dividend yielders (3Y sum):")
    lines.append("Ticker  Yield%  Payouts  LastClose")
    for _, row in merged.head(15).iterrows():
        lines.append(f"{row['stock_code']:6s} {row['yield_pct']:6.2f} {int(row['payouts']):7d} {row['last_close']:10,.0f}")
    write_lines(RESULTS_DIR / f"{RUN_DATE.replace('-', '')}_MONTHLY_DIVIDEND_INCOME_STRATEGY.txt", lines)


def method_foreign_buy_decline(hist: pd.DataFrame, fundamentals: Optional[pd.DataFrame] = None, with_fundamental: bool = False) -> None:
    net5 = net_foreign_5d(hist)
    chg5 = compute_5d_change(hist)
    latest = latest_prices(hist)
    df = (
        pd.DataFrame({"Kode Saham": net5.index, "net_foreign_5d": net5.values})
        .merge(chg5.rename("chg5_pct"), left_on="Kode Saham", right_index=True)
        .merge(latest, on="Kode Saham", how="left")
    )
    df = df[(df["net_foreign_5d"] > 0) & (df["chg5_pct"] < 0)]
    df = df.sort_values("net_foreign_5d", ascending=False)
    if with_fundamental and fundamentals is not None and not fundamentals.empty:
        fund = fundamentals.copy()
        fund["Code"] = fund["Code"].astype(str).str.strip()
        df = df.merge(fund, left_on="Kode Saham", right_on="Code", how="left")
        df["fund_ok"] = df.apply(passes_basic_fundamentals, axis=1)
        df = df[df["fund_ok"]]
    title = "FOREIGN NET BUY + 5D DECLINE"
    fname = f"{RUN_DATE.replace('-', '')}_FOREIGN_BUY_DECLINE_5D"
    if with_fundamental:
        title += " + FUNDAMENTALS"
        fname += "_FUNDAMENTAL"
    lines = [title, f"Run date: {RUN_DATE}", "", "Ticker  NetForeign5D  Chg5%  LastClose"]
    for _, row in df.head(25).iterrows():
        lines.append(
            f"{row['Kode Saham']:6s} {row['net_foreign_5d']/1e6:12.1f}M {row['chg5_pct']:6.2f}% {row['last_close']:10,.0f}"
        )
    lines.append("")
    lines.append(f"Total matches: {len(df)}")
    write_lines(RESULTS_DIR / f"{fname}.txt", lines)


def method_buy_then_up(hist: pd.DataFrame, fundamentals: Optional[pd.DataFrame] = None, with_fundamental: bool = False) -> None:
    g = hist.copy()
    g = g.sort_values(["Kode Saham", "SourceDate"])
    g["next_return"] = g.groupby("Kode Saham")["Penutupan"].pct_change(-1) * 100
    # use the most recent row that has a defined next_return (second-to-last per ticker)
    rows = []
    for _, grp in g.groupby("Kode Saham"):
        rows.append(grp.iloc[-2] if len(grp) >= 2 else grp.iloc[-1])
    signals = pd.DataFrame(rows)
    signals = signals[(signals["net_foreign"] > 0) & (signals["next_return"] > 0)]
    signals = signals.sort_values("net_foreign", ascending=False)
    if with_fundamental and fundamentals is not None and not fundamentals.empty:
        fund = fundamentals.copy()
        fund["Code"] = fund["Code"].astype(str).str.strip()
        signals = signals.merge(fund, left_on="Kode Saham", right_on="Code", how="left")
        signals["fund_ok"] = signals.apply(passes_basic_fundamentals, axis=1)
        signals = signals[signals["fund_ok"]]
    title = "NET BUY AT T THEN PRICE UP T+1"
    fname = f"{RUN_DATE.replace('-', '')}_INST_BUY_THEN_UP_T1"
    if with_fundamental:
        title += " + FUNDAMENTALS"
        fname += "_FUNDAMENTAL"
    lines = [title, f"Run date: {RUN_DATE}", "", "Ticker  NetForeignT  NextRet%  Close"]
    for _, row in signals.head(25).iterrows():
        lines.append(
            f"{row['Kode Saham']:6s} {row['net_foreign']/1e6:12.1f}M {row['next_return']:7.2f}% {row['Penutupan']:10,.0f}"
        )
    lines.append("")
    lines.append(f"Total matches: {len(signals)}")
    write_lines(RESULTS_DIR / f"{fname}.txt", lines)


def method_technical(hist: pd.DataFrame, fundamentals: Optional[pd.DataFrame] = None, with_fundamental: bool = False) -> None:
    df = hist.copy()
    df["ma10"] = df.groupby("Kode Saham")["Penutupan"].rolling(10, min_periods=10).mean().reset_index(0, drop=True)
    df["ma30"] = df.groupby("Kode Saham")["Penutupan"].rolling(30, min_periods=30).mean().reset_index(0, drop=True)
    df["ret_pct"] = df.groupby("Kode Saham")["Penutupan"].pct_change()
    df["vol20"] = df.groupby("Kode Saham")["ret_pct"].rolling(20, min_periods=20).std().reset_index(0, drop=True)
    df["bb_mid"] = df["ma20"] = df.groupby("Kode Saham")["Penutupan"].rolling(20, min_periods=20).mean().reset_index(0, drop=True)
    df["bb_std"] = df.groupby("Kode Saham")["Penutupan"].rolling(20, min_periods=20).std().reset_index(0, drop=True)
    df["bb_low"] = df["bb_mid"] - 2 * df["bb_std"]
    df["bb_high"] = df["bb_mid"] + 2 * df["bb_std"]
    latest = df.groupby("Kode Saham").tail(1).copy()
    latest.loc[:, "bb_pos"] = (latest["Penutupan"] - latest["bb_low"]) / (
        latest["bb_high"] - latest["bb_low"]
    )
    candidates = latest[
        (latest["ma10"] > latest["ma30"])
        & (latest["bb_pos"] <= 0.3)
        & (latest["vol20"].between(0.005, 0.08))
    ].copy()
    
    if with_fundamental and fundamentals is not None and not fundamentals.empty:
        fund = fundamentals.copy()
        fund["Code"] = fund["Code"].astype(str).str.strip()
        candidates = candidates.merge(fund, left_on="Kode Saham", right_on="Code", how="left")
        candidates["fund_ok"] = candidates.apply(passes_basic_fundamentals, axis=1)
        candidates = candidates[candidates["fund_ok"]]
    
    candidates = candidates.sort_values(["bb_pos", "vol20"], ascending=[True, True])
    
    title = "TECHNICAL ENHANCED SWING (3.12, 3.14, 3.4 + 3.13, 3.10)"
    fname = f"{RUN_DATE.replace('-', '')}_TECHNICAL_ENHANCED_SWING"
    if with_fundamental:
        title += " + FUNDAMENTALS"
        fname += "_FUNDAMENTAL"
    
    lines = [
        title,
        f"Run date: {RUN_DATE}",
        "",
        "Ticker  Close  MA10  MA30  BB%  Vol20%"
    ]
    for _, row in candidates.head(40).iterrows():
        vol_pct = (row["vol20"] or 0) * 100 if pd.notna(row["vol20"]) else 0
        bb_pct = row["bb_pos"] * 100 if pd.notna(row["bb_pos"]) else 0
        lines.append(
            f"{row['Kode Saham']:6s} {row['Penutupan']:7,.0f} {row['ma10']:7.0f} {row['ma30']:7.0f} {bb_pct:6.1f}% {vol_pct:7.2f}%"
        )
    lines.append("")
    lines.append(f"Total matches: {len(candidates)}")
    write_lines(RESULTS_DIR / f"{fname}.txt", lines)


# --- Sentiment sanity check (news cache based) ---------------------------------

def collect_all_recommended_tickers(
    hist: pd.DataFrame,
    dividends: pd.DataFrame,
    fundamentals: pd.DataFrame
) -> set:
    """Collect all tickers recommended by any method."""
    tickers = set()
    
    # Method 1: Dividend
    latest = latest_prices(hist)
    recent_divs = dividends.copy()
    if "dividend_year" in recent_divs.columns:
        recent_divs = recent_divs[recent_divs["dividend_year"] >= 2023]
    grouped = recent_divs.groupby("stock_code").agg({"dividend_amount_numeric": "sum"}).reset_index()
    merged = grouped.merge(latest, left_on="stock_code", right_on="Kode Saham", how="left")
    merged["yield_pct"] = (merged["dividend_amount_numeric"] / merged["last_close"]).fillna(0) * 100
    merged = merged.sort_values("yield_pct", ascending=False)
    tickers.update(merged.head(15)["stock_code"].tolist())
    
    # Method 2: Foreign buy + decline
    net5 = net_foreign_5d(hist)
    chg5 = compute_5d_change(hist)
    df = pd.DataFrame({"Kode Saham": net5.index, "net_foreign_5d": net5.values}).merge(
        chg5.rename("chg5_pct"), left_on="Kode Saham", right_index=True
    )
    df = df[(df["net_foreign_5d"] > 0) & (df["chg5_pct"] < 0)]
    tickers.update(df.head(25)["Kode Saham"].tolist())
    
    # Method 3: Buy then up
    g = hist.copy().sort_values(["Kode Saham", "SourceDate"])
    g["next_return"] = g.groupby("Kode Saham")["Penutupan"].pct_change(-1) * 100
    signals = g.groupby("Kode Saham").apply(
        lambda x: x.iloc[-2] if len(x) >= 2 else x.iloc[-1]
    ).reset_index(drop=True)
    signals = signals[(signals["net_foreign"] > 0) & (signals["next_return"] > 0)]
    tickers.update(signals.head(25)["Kode Saham"].tolist())
    
    # Method 4 & 5: Same as 2 & 3 but with fundamentals
    if not fundamentals.empty:
        fund = fundamentals.copy()
        fund["Code"] = fund["Code"].astype(str).str.strip()
        
        # Method 4
        df_fund = df.merge(fund, left_on="Kode Saham", right_on="Code", how="left")
        df_fund["fund_ok"] = df_fund.apply(passes_basic_fundamentals, axis=1)
        tickers.update(df_fund[df_fund["fund_ok"]].head(25)["Kode Saham"].tolist())
        
        # Method 5
        signals_fund = signals.merge(fund, left_on="Kode Saham", right_on="Code", how="left")
        signals_fund["fund_ok"] = signals_fund.apply(passes_basic_fundamentals, axis=1)
        tickers.update(signals_fund[signals_fund["fund_ok"]].head(25)["Kode Saham"].tolist())
    
    # Method 6 & 7: Technical
    df_tech = hist.copy()
    df_tech["ma10"] = df_tech.groupby("Kode Saham")["Penutupan"].rolling(10, min_periods=10).mean().reset_index(0, drop=True)
    df_tech["ma30"] = df_tech.groupby("Kode Saham")["Penutupan"].rolling(30, min_periods=30).mean().reset_index(0, drop=True)
    df_tech["ret_pct"] = df_tech.groupby("Kode Saham")["Penutupan"].pct_change()
    df_tech["vol20"] = df_tech.groupby("Kode Saham")["ret_pct"].rolling(20, min_periods=20).std().reset_index(0, drop=True)
    df_tech["bb_mid"] = df_tech.groupby("Kode Saham")["Penutupan"].rolling(20, min_periods=20).mean().reset_index(0, drop=True)
    df_tech["bb_std"] = df_tech.groupby("Kode Saham")["Penutupan"].rolling(20, min_periods=20).std().reset_index(0, drop=True)
    df_tech["bb_low"] = df_tech["bb_mid"] - 2 * df_tech["bb_std"]
    df_tech["bb_high"] = df_tech["bb_mid"] + 2 * df_tech["bb_std"]
    latest_tech = df_tech.groupby("Kode Saham").tail(1)
    latest_tech["bb_pos"] = (latest_tech["Penutupan"] - latest_tech["bb_low"]) / (latest_tech["bb_high"] - latest_tech["bb_low"])
    candidates = latest_tech[
        (latest_tech["ma10"] > latest_tech["ma30"]) &
        (latest_tech["bb_pos"] <= 0.3) &
        (latest_tech["vol20"].between(0.005, 0.08))
    ]
    tickers.update(candidates.head(40)["Kode Saham"].tolist())
    
    return tickers

NEGATIVE_KEYWORDS = [
    "bankruptcy", "fraud", "scandal", "corruption", "investigation",
    "suspend", "halt", "delisting", "lawsuit", "downgrade",
    "dividend cut", "default", "debt covenant", "negative outlook",
]

POSITIVE_KEYWORDS = [
    "recovery", "rebound", "upgrade", "profit", "growth",
    "partnership", "contract", "dividend", "approval", "expansion",
]

SENTIMENT_TICKERS = {
    "DGIK", "ASII", "BBKP", "ADRO", "PTBA", "BSSR", "MEGA", "GMFI",
    "KLBF", "UNTR", "MERK", "SUNI", "CNMA", "CTRA", "PTRO", "BKSL",
    "BRMS", "ELTY", "PBRX", "ELIT", "PSKT", "KREN", "ITMG", "LPPF",
}


def load_news_cache() -> List[Dict[str, str]]:
    articles: List[Dict[str, str]] = []
    if not NEWS_CACHE_DIR.exists():
        return articles
    for path in NEWS_CACHE_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    articles.extend(data)
                elif isinstance(data, dict):
                    articles.append(data)
        except Exception:
            continue
    return articles


def score_sentiment(text: str) -> int:
    text_l = text.lower()
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_l)
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_l)
    return pos - neg


def method_sentiment_sanity() -> None:
    articles = load_news_cache()
    lines = ["SENTIMENT SANITY CHECK (NEWS CACHE)", f"Run date: {RUN_DATE}", ""]
    if not articles:
        lines.append("No news cache found; defaulting to CLEAN for all tracked tickers.")
        write_lines(RESULTS_DIR / f"{RUN_DATE.replace('-', '')}_SENTIMENT_CHECK.txt", lines)
        return

    per_ticker: Dict[str, List[int]] = {t: [] for t in SENTIMENT_TICKERS}
    for item in articles:
        ticker = str(item.get("ticker", "")).upper()
        if ticker not in per_ticker:
            continue
        text = f"{item.get('title', '')} {item.get('content', '')}"
        per_ticker[ticker].append(score_sentiment(text))

    clean = []
    caution = []
    risk = []
    for ticker in sorted(SENTIMENT_TICKERS):
        scores = per_ticker.get(ticker, [])
        if not scores:
            clean.append(ticker)
            continue
        avg = sum(scores) / len(scores)
        if avg < -1:
            risk.append((ticker, avg))
        elif avg < 0:
            caution.append((ticker, avg))
        else:
            clean.append(ticker)

    lines.append(f"Clean: {', '.join(clean) if clean else 'None'}")
    if caution:
        lines.append("Caution:")
        for t, s in caution:
            lines.append(f"  - {t} | sentiment {s:.1f}")
    if risk:
        lines.append("High risk:")
        for t, s in risk:
            lines.append(f"  - {t} | sentiment {s:.1f}")
    write_lines(RESULTS_DIR / f"{RUN_DATE.replace('-', '')}_SENTIMENT_CHECK.txt", lines)


def compile_concise_report() -> None:
    """Write the concise report using the curated template style."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Missing concise report template: {TEMPLATE_PATH}")

    content = TEMPLATE_PATH.read_text()
    out_path = RESULTS_DIR / f"{RUN_DATE.replace('-', '')}_STRATEGY_REPORT_CONCISE.txt"
    ensure_dir(out_path)
    out_path.write_text(content)
    print(f"✓ Wrote {out_path} from template {TEMPLATE_PATH}")


def main() -> None:
    print("Loading datasets...")
    hist = load_histories()
    dividends = load_dividends()
    fundamentals = load_fundamentals()
    stocklist = load_stocklist()
    _ = stocklist  # currently unused, but kept for future enrichment

    if GENERATE_INDIVIDUAL_REPORTS:
        print("Running Method 1 (Dividend oriented)...")
        method_dividend(hist, dividends, fundamentals)

        print("Running Method 2 (Foreign buy + 5D decline)...")
        method_foreign_buy_decline(hist, fundamentals=None, with_fundamental=False)

        print("Running Method 3 (Net buy then up t+1)...")
        method_buy_then_up(hist, fundamentals=None, with_fundamental=False)

        print("Running Method 4 (Foreign buy + 5D decline + fundamentals)...")
        method_foreign_buy_decline(hist, fundamentals=fundamentals, with_fundamental=True)

        print("Running Method 5 (Net buy then up t+1 + fundamentals)...")
        method_buy_then_up(hist, fundamentals=fundamentals, with_fundamental=True)

        print("Running Method 6 (Technical enhanced swing)...")
        method_technical(hist, fundamentals=None, with_fundamental=False)

        print("Running Method 7 (Technical enhanced swing + fundamentals)...")
        method_technical(hist, fundamentals=fundamentals, with_fundamental=True)

        print("Running Method 8 (Sentiment sanity check)...")
        method_sentiment_sanity()
    else:
        print("Skipping individual per-strategy reports (GENERATE_INDIVIDUAL_REPORTS=False)...")

    print("Compiling consolidated strategy report...")
    compile_concise_report()

    print("All reports generated.")


if __name__ == "__main__":
    main()
