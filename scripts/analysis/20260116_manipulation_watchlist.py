"""Generate a watchlist for potential broker/price manipulation.

Reads the combined daily file and computes simple rule-based flags:
- Volume/Nilai/Frequency z-scores (vs 20-day history per ticker)
- Return vs previous close
- Non-regular trade ratio
- Order book imbalance (Bid/Offer volumes)
- Foreign flow divergence

Outputs a filtered CSV with rows that trip any flag.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "data" / "histories" / "ringkasan_histories_combined.csv"
ALERTS_DIR = BASE_DIR / "data" / "IHSGstockdata" / "alerts"
OUTPUT_CSV = ALERTS_DIR / "manipulation_watchlist.csv"

ROLLING_WINDOW = 20
EPS = 1e-9


def zscore(series: pd.Series, window: int) -> pd.Series:
    """Rolling z-score helper (per ticker)."""
    mean = series.rolling(window, min_periods=5).mean()
    std = series.rolling(window, min_periods=5).std()
    return (series - mean) / (std + EPS)


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing input CSV: {INPUT_CSV}")

    ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])

    # Basic numeric conversions
    for col in [
        'Sebelumnya', 'Penutupan', 'Volume', 'Nilai', 'Frekuensi',
        'Offer Volume', 'Bid Volume', 'Non Regular Volume', 'Non Regular Value',
        'Foreign Buy', 'Foreign Sell'
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df.sort_values(['Kode Saham', 'SourceDate'], inplace=True)

    # Per-ticker rolling metrics
    df['return'] = (df['Penutupan'] / df['Sebelumnya']) - 1.0

    df['volume_z'] = df.groupby('Kode Saham')['Volume'].transform(lambda s: zscore(s, ROLLING_WINDOW))
    df['nilai_z'] = df.groupby('Kode Saham')['Nilai'].transform(lambda s: zscore(s, ROLLING_WINDOW))
    df['freq_z'] = df.groupby('Kode Saham')['Frekuensi'].transform(lambda s: zscore(s, ROLLING_WINDOW))

    df['non_regular_ratio'] = df['Non Regular Volume'] / (df['Volume'] + EPS)
    df['foreign_net'] = df['Foreign Buy'] - df['Foreign Sell']
    df['foreign_ratio'] = df['foreign_net'] / (df['Volume'] + EPS)
    df['book_imbalance'] = (df['Bid Volume'] - df['Offer Volume']) / (
        (df['Bid Volume'] + df['Offer Volume']) + EPS
    )

    # Flags
    flags = {
        'vol_spike_up': (df['volume_z'] > 3) & (df['return'] > 0.05),
        'vol_spike_down': (df['volume_z'] > 3) & (df['return'] < -0.05),
        'non_regular_heavy': (df['non_regular_ratio'] > 0.2) & (df['return'].abs() < 0.01),
        'book_buy_imbalance': (df['book_imbalance'] > 0.6) & (df['return'] > 0),
        'book_sell_imbalance': (df['book_imbalance'] < -0.6) & (df['return'] < 0),
        'foreign_div_up': (df['foreign_ratio'] > 0.1) & (df['return'] < 0),
        'foreign_div_down': (df['foreign_ratio'] < -0.1) & (df['return'] > 0),
    }

    for name, series in flags.items():
        df[name] = series

    # Repeat pattern: 3+ flags in last 5 days per ticker
    flag_cols = list(flags.keys())
    df['flag_count'] = df[flag_cols].sum(axis=1)
    df['repeat_pattern'] = df.groupby('Kode Saham')['flag_count'].transform(
        lambda s: s.rolling(5, min_periods=3).sum() >= 3
    )

    all_flags = flag_cols + ['repeat_pattern']
    df['any_flag'] = df[all_flags].any(axis=1)

    watchlist = df[df['any_flag']].copy()
    if watchlist.empty:
        OUTPUT_CSV.write_text("")
        print("No flags triggered; wrote empty file.")
        return

    # Prepare concise flag summary
    def flag_labels(row):
        return [name for name in all_flags if row.get(name, False)]

    watchlist['flags'] = watchlist.apply(flag_labels, axis=1)

    cols = [
        'SourceDate', 'Kode Saham', 'Nama Perusahaan', 'Penutupan', 'Sebelumnya', 'return',
        'Volume', 'Nilai', 'Frekuensi', 'volume_z', 'nilai_z', 'freq_z',
        'non_regular_ratio', 'foreign_ratio', 'book_imbalance', 'flags'
    ]
    existing_cols = [c for c in cols if c in watchlist.columns]
    output_df = watchlist[existing_cols].sort_values(['SourceDate', 'Kode Saham'])

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {len(output_df)} flagged rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
