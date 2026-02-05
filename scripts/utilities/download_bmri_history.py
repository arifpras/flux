#!/usr/bin/env python3
"""
Download daily historical data for BMRI.JK from Yahoo Finance.
Default range: 2022-01-01 through today.
Saves CSV to data/histories.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download BMRI.JK daily data from Yahoo Finance"
    )
    parser.add_argument(
        "--start",
        default="2022-01-01",
        help="Start date (YYYY-MM-DD). Default: 2022-01-01",
    )
    parser.add_argument(
        "--end",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date (YYYY-MM-DD). Default: today",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path. Default: data/histories/BMRI_JK_daily_2022_to_<YYYYMMDD>.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    start = args.start
    end = args.end

    data_dir = Path("data/histories")
    data_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = data_dir / f"BMRI_JK_daily_2022_to_{datetime.now().strftime('%Y%m%d')}.csv"

    print(f"Downloading BMRI.JK daily data from {start} to {end}...")
    df = yf.download(
        "BMRI.JK",
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if df.empty:
        raise SystemExit("No data returned from Yahoo Finance.")

    df = df.reset_index()
    df.rename(columns={"Date": "date"}, inplace=True)

    def normalize_column(col: object) -> str:
        if isinstance(col, tuple):
            col = col[0]
        return str(col).lower()

    df.columns = [normalize_column(c) for c in df.columns]

    df.to_csv(output_path, index=False)
    print(f"Saved {len(df):,} rows to {output_path}")


if __name__ == "__main__":
    main()
