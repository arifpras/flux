#!/usr/bin/env python3
import os
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
HIST_DIR = os.path.join(DATA_DIR, 'histories')

BACKTEST_TRADES = os.path.join(BASE_DIR, 'backtest_trades.csv')
RINGKASAN_19JAN = os.path.join(HIST_DIR, 'Ringkasan Saham-20260119.xlsx')
OUTPUT_CSV = os.path.join(HIST_DIR, 'augmented_prices_5stocks.csv')

TICKERS = ['CANI', 'EURO', 'KDTN', 'RICY', 'RLCO']

def load_backtest_series(symbol: str) -> pd.DataFrame:
    df = pd.read_csv(BACKTEST_TRADES)
    df = df[df['Kode Saham'] == symbol].copy()
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])
    df = df.sort_values('SourceDate')
    # Use EntryPrice as proxy for that day's price
    return df[['SourceDate', 'EntryPrice']].rename(columns={'EntryPrice': 'Price'})

def load_ringkasan_19jan_prices() -> pd.Series:
    # Try robust read of the Excel: first normal, then headerless
    try:
        df = pd.read_excel(RINGKASAN_19JAN)
    except Exception:
        df = pd.read_excel(RINGKASAN_19JAN, header=None)
    # Detect code and closing columns
    code_col = None
    close_col = None
    for c in df.columns:
        s = str(c).strip().lower()
        if 'kode' in s or 'code' in s:
            code_col = c
        if 'penutupan' in s or 'close' in s or 'harga penutupan' in s:
            close_col = c
    # Fallback for headerless
    if code_col is None:
        # Find column with many 4-letter uppercase codes
        for col in df.columns:
            vals = df[col].astype(str).head(200)
            if sum((len(v) == 4 and v.isalpha() and v.upper() == v) for v in vals) > 10:
                code_col = col
                break
    if close_col is None:
        # Heuristic: last numeric-looking column
        for col in reversed(df.columns):
            vals = pd.to_numeric(df[col], errors='coerce')
            if vals.notna().sum() > 50:
                close_col = col
                break

    sub = df[[code_col, close_col]].dropna()
    sub.iloc[:, 0] = sub.iloc[:, 0].astype(str).str.upper()
    sub = sub.rename(columns={code_col: 'Code', close_col: 'Close'})
    # Build series mapping code -> close
    return pd.Series(sub['Close'].values, index=sub['Code'].values)

def main():
    print('Augmenting price dataset with 19 Jan 2026 closes...')
    prices_19 = load_ringkasan_19jan_prices()
    rows = []
    for sym in TICKERS:
        bt = load_backtest_series(sym)
        # Append Jan 19 if available
        if sym in prices_19.index:
            jan19 = pd.DataFrame({
                'SourceDate': [pd.Timestamp('2026-01-19')],
                'Price': [prices_19[sym]]
            })
            bt = pd.concat([bt, jan19], ignore_index=True)
        bt['Symbol'] = sym
        rows.append(bt[['SourceDate', 'Symbol', 'Price']])

    out = pd.concat(rows, ignore_index=True).sort_values(['Symbol', 'SourceDate'])
    out.to_csv(OUTPUT_CSV, index=False)
    # Summary
    summary = out.groupby('Symbol').agg(
        points=('Price', 'count'),
        start=('SourceDate', 'min'),
        end=('SourceDate', 'max')
    )
    print('Saved:', OUTPUT_CSV)
    print(summary.to_string())

if __name__ == '__main__':
    main()
