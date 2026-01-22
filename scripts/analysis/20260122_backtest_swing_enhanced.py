#!/usr/bin/env python3
"""
Backtest swing strategies (base vs enhanced) on IDX stocks.
Base: 3.12 (MA), 3.14 (Pivot), 3.4 (Volatility)
Enhanced: + 3.13 (Bollinger Bands), 3.10 (Short-Term Reversal pullback)
Assumptions:
- Entry at close when conditions met
- Exit at target/stop using next day's high/low; fallback to close on day 9
- Stop loss: -3%
- Max holding: 9 trading days
- Volatility gate: 30d stdev of returns under 15%
- Trend filter: 10dma not materially below 30dma (>= -0.5%)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

DATA_FILE = Path('data/histories/ringkasan_histories_combined.csv')
STOCKS = ['PTBA', 'ASII', 'LPPF', 'BBNI', 'BBRI', 'BNGA', 'BSSR', 'HEXA', 'ADRO', 'BMRI', 'BUMI']
MAX_HOLD = 7  # days
MAX_HOLD = 9  # days
STOP_PCT = 0.03
SUPPORT_BUFFER = 0.05  # allow buffer above support/pivot for entries


def load_data():
    df = pd.read_csv(DATA_FILE)
    df['SourceDate'] = pd.to_datetime(df['SourceDate'])
    return df


def prepare_stock(df):
    df = df.sort_values('SourceDate').copy()
    df['close'] = df['Penutupan']
    df['high'] = df['Tertinggi']
    df['low'] = df['Terendah']

    # Moving averages (3.12)
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma30'] = df['close'].rolling(30).mean()

    # Volatility (3.4) on returns
    returns = df['close'].pct_change()
    df['vol_pct'] = returns.rolling(30).std() * 100

    # Pivot points (3.14)
    df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
    df['resistance'] = (2 * df['pivot'] - df['low'])
    df['support'] = (2 * df['pivot'] - df['high'])

    # Bollinger Bands (3.13)
    df['bb_mid'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + 2 * bb_std
    df['bb_lower'] = df['bb_mid'] - 2 * bb_std
    df['bb_pos'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # Short-term reversals (3.10)
    df['ret_1d'] = df['close'].pct_change(1) * 100
    df['ret_3d'] = df['close'].pct_change(3) * 100

    return df


def backtest(df, enhanced=False):
    in_position = False
    entry_price = target = stop = None
    entry_date = None
    trades = []
    days_held = 0

    for idx, row in df.iterrows():
        if not in_position:
            # Entry conditions
            if pd.isna(row['ma30']) or pd.isna(row['vol_pct']):
                continue
            if row['ma10'] < row['ma30'] * 0.995:
                continue
            if row['vol_pct'] >= 15:
                continue

            close = row['close']
            support = row['support']
            resistance = row['resistance']
            bb_pos = row['bb_pos']
            ret_1d = row['ret_1d']
            ret_3d = row['ret_3d']

            # Base entry: price near pivot (support to pivot window)
            if enhanced:
                if pd.isna(bb_pos) or pd.isna(ret_1d) or pd.isna(ret_3d):
                    continue
                pullback_ok = ret_1d <= 0
                bb_ok = bb_pos < 1.05  # allow just above upper band
                entry_ok = pullback_ok and bb_ok
            else:
                entry_ok = False
                if not pd.isna(support) and not pd.isna(row['pivot']):
                    upper_band = row['pivot'] * (1 + SUPPORT_BUFFER)
                    lower_band = support * (1 + SUPPORT_BUFFER)
                    entry_ok = lower_band <= close <= upper_band
            if not entry_ok:
                continue

            in_position = True
            entry_price = close
            target = resistance
            stop = entry_price * (1 - STOP_PCT)
            entry_date = row['SourceDate']
            days_held = 0
            continue

        # In position: check exits using intraday high/low
        days_held += 1
        hit_target = row['high'] >= target
        hit_stop = row['low'] <= stop

        exit_price = None
        reason = None
        if hit_stop and hit_target:
            # If both hit, assume worst case (stop) to be conservative
            exit_price = stop
            reason = 'stop_and_target'
        elif hit_target:
            exit_price = target
            reason = 'target'
        elif hit_stop:
            exit_price = stop
            reason = 'stop'
        elif days_held >= MAX_HOLD:
            exit_price = row['close']
            reason = 'time'

        if exit_price is not None:
            trades.append({
                'entry_date': entry_date,
                'exit_date': row['SourceDate'],
                'entry': entry_price,
                'exit': exit_price,
                'hold_days': days_held,
                'reason': reason,
                'pnl_pct': (exit_price / entry_price - 1) * 100,
            })
            in_position = False
            entry_price = target = stop = None
            entry_date = None
            days_held = 0

    return trades


def summarize(trades):
    if not trades:
        return {'trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0}
    pnl = [t['pnl_pct'] for t in trades]
    wins = [p for p in pnl if p > 0]
    return {
        'trades': len(trades),
        'win_rate': len(wins) / len(trades) * 100,
        'avg_pnl': np.mean(pnl),
        'total_pnl': np.sum(pnl),
    }


def run_backtest(df_all):
    summary_rows = []
    total_base_pnls = []
    total_enh_pnls = []

    for stock in STOCKS:
        df_stock = df_all[df_all['Kode Saham'] == stock]
        if df_stock.empty:
            continue
        prepared = prepare_stock(df_stock)
        base_trades = backtest(prepared, enhanced=False)
        enh_trades = backtest(prepared, enhanced=True)

        base_sum = summarize(base_trades)
        enh_sum = summarize(enh_trades)

        summary_rows.append({
            'stock': stock,
            'base_trades': base_sum['trades'],
            'base_win%': base_sum['win_rate'],
            'base_avg%': base_sum['avg_pnl'],
            'base_total%': base_sum['total_pnl'],
            'enh_trades': enh_sum['trades'],
            'enh_win%': enh_sum['win_rate'],
            'enh_avg%': enh_sum['avg_pnl'],
            'enh_total%': enh_sum['total_pnl'],
        })

        total_base_pnls.extend([t['pnl_pct'] for t in base_trades])
        total_enh_pnls.extend([t['pnl_pct'] for t in enh_trades])

    portfolio_base = summarize([{'pnl_pct': p} for p in total_base_pnls])
    portfolio_enh = summarize([{'pnl_pct': p} for p in total_enh_pnls])

    return summary_rows, portfolio_base, portfolio_enh, total_base_pnls, total_enh_pnls


def print_report(summary_rows, portfolio_base, portfolio_enh, total_base_pnls, total_enh_pnls):
    print("=" * 90)
    print("SWING BACKTEST - BASE vs ENHANCED")
    print("=" * 90)
    print(f"Date: {datetime.now().strftime('%d %B %Y')}")
    print(f"Data: {DATA_FILE}")
    print(f"Stocks: {', '.join(STOCKS)}")
    print("Assumptions: Stop -3%, Max hold 9d, Vol<15%/30d, Trend cushion -0.5%, Support buffer 5% (base), +BB & pullback (enhanced)")
    print("=" * 90)
    print()

    print(f"{'Stock':<6} | {'Base n':>6} {'Win%':>6} {'Avg%':>7} {'Tot%':>7} | {'Enh n':>6} {'Win%':>6} {'Avg%':>7} {'Tot%':>7}")
    print("-" * 90)
    for row in summary_rows:
        print(f"{row['stock']:<6} | {row['base_trades']:6d} {row['base_win%']:6.1f} {row['base_avg%']:7.2f} {row['base_total%']:7.2f} | {row['enh_trades']:6d} {row['enh_win%']:6.1f} {row['enh_avg%']:7.2f} {row['enh_total%']:7.2f}")
    print("-" * 90)
    print(f"PORTF  | {len(total_base_pnls):6d} {portfolio_base['win_rate']:6.1f} {portfolio_base['avg_pnl']:7.2f} {portfolio_base['total_pnl']:7.2f} | {len(total_enh_pnls):6d} {portfolio_enh['win_rate']:6.1f} {portfolio_enh['avg_pnl']:7.2f} {portfolio_enh['total_pnl']:7.2f}")
    print("=" * 90)

if __name__ == "__main__":
    df_all = load_data()
    summary_rows, portfolio_base, portfolio_enh, total_base_pnls, total_enh_pnls = run_backtest(df_all)
    print_report(summary_rows, portfolio_base, portfolio_enh, total_base_pnls, total_enh_pnls)
