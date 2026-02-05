"""Combine all Ringkasan Saham XLSX files in histories/ into one CSV.
Adds a SourceDate column from the filename (YYYYMMDD) for traceability.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
HIST_DIR = BASE_DIR / "data" / "histories"
OUTPUT_CSV = HIST_DIR / "ringkasan_histories_combined.csv"


def parse_date_from_filename(path: Path) -> datetime:
    """Extract YYYYMMDD date from a filename like 'Ringkasan Saham-20251201.xlsx'."""
    try:
        return datetime.strptime(path.stem.split("-")[-1], "%Y%m%d")
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Cannot parse date from {path.name}") from exc


def main() -> None:
    files = sorted(HIST_DIR.glob("Ringkasan Saham-*.xlsx"), key=parse_date_from_filename)
    if not files:
        print("No XLSX files found in histories/", file=sys.stderr)
        sys.exit(1)

    frames = []
    for path in files:
        dt = parse_date_from_filename(path)
        df = pd.read_excel(path)
        df.insert(0, "SourceDate", dt.strftime("%Y-%m-%d"))
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(OUTPUT_CSV, index=False)

    print(f"Wrote {len(combined):,} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
