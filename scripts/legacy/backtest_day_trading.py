"""Backtest day-trading pump strategy on historical data."""
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
combined_path = BASE_DIR / 'data' / 'histories' / 'ringkasan_histories_combined.csv'
watchlist_path = BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts' / 'manipulation_watchlist.csv'

df = pd.read_csv(combined_path)
watchlist = pd.read_csv(watchlist_path)

df['SourceDate'] = pd.to_datetime(df['SourceDate'])
watchlist['SourceDate'] = pd.to_datetime(watchlist['SourceDate'])

for col in ['Penutupan', 'Sebelumnya', 'Volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
    if col in watchlist.columns:
        watchlist[col] = pd.to_numeric(watchlist[col], errors='coerce')

df['return'] = (df['Penutupan'] / df['Sebelumnya']) - 1.0

print(f"\n{'='*140}")
print(f"📊 DAY-TRADING BACKTEST: Pump Strategy on Historical Data (Dec 1 - Jan 15)")
print(f"{'='*140}\n")

# Backtesting logic
trades = []
trade_count = 0
win_count = 0
loss_count = 0
total_pnl = 0

# Get unique dates for iteration
unique_dates = sorted(df['SourceDate'].unique())

for date_idx in range(len(unique_dates) - 1):
    current_date = unique_dates[date_idx]
    next_date = unique_dates[date_idx + 1]
    
    # Get flagged stocks on current_date
    today_flagged = watchlist[watchlist['SourceDate'] == current_date]
    
    if len(today_flagged) == 0:
        continue
    
    for ticker in today_flagged['Kode Saham'].unique():
        ticker_watchlist = today_flagged[today_flagged['Kode Saham'] == ticker]
        
        # Get today's close (entry price)
        entry_candidates = df[
            (df['SourceDate'] == current_date) & 
            (df['Kode Saham'] == ticker)
        ]
        
        if len(entry_candidates) == 0:
            continue
        
        entry_price = entry_candidates.iloc[0]['Penutupan']
        entry_vol = entry_candidates.iloc[0]['Volume']
        
        # Get next day's close (exit price)
        exit_candidates = df[
            (df['SourceDate'] == next_date) & 
            (df['Kode Saham'] == ticker)
        ]
        
        if len(exit_candidates) == 0:
            continue
        
        exit_price = exit_candidates.iloc[0]['Penutupan']
        exit_vol = exit_candidates.iloc[0]['Volume']
        
        # Calculate P&L
        pnl = exit_price - entry_price
        pnl_pct = (pnl / entry_price) * 100
        
        # Slippage model: -0.1% entry, -0.1% exit
        slippage_cost = entry_price * 0.002
        net_pnl = pnl - slippage_cost
        net_pnl_pct = (net_pnl / entry_price) * 100
        
        # Stop loss: 2% below entry
        stop_loss = entry_price * 0.98
        
        # Day trading exit: If price goes below stop loss, exit with loss
        if exit_price < stop_loss:
            actual_exit = stop_loss
            actual_pnl = -slippage_cost - (entry_price * 0.02)
            actual_pnl_pct = -2.1
            is_stopout = True
        else:
            actual_exit = exit_price
            actual_pnl = net_pnl
            actual_pnl_pct = net_pnl_pct
            is_stopout = False
        
        # Profit target: 3% above entry (take profit)
        take_profit = entry_price * 1.03
        if exit_price > take_profit:
            actual_exit = take_profit
            actual_pnl = (take_profit - entry_price) - slippage_cost
            actual_pnl_pct = 2.9
            is_target = True
        else:
            is_target = False
        
        trade_count += 1
        total_pnl += actual_pnl_pct
        
        if actual_pnl_pct > 0:
            win_count += 1
        else:
            loss_count += 1
        
        trades.append({
            'entry_date': current_date,
            'exit_date': next_date,
            'ticker': ticker,
            'entry_price': entry_price,
            'exit_price': actual_exit,
            'entry_vol': entry_vol,
            'exit_vol': exit_vol,
            'pnl_pct': actual_pnl_pct,
            'pnl': actual_pnl,
            'stopped_out': is_stopout,
            'took_profit': is_target
        })

# Analysis
trades_df = pd.DataFrame(trades)

if len(trades_df) > 0:
    print(f"📈 BACKTEST RESULTS (Total trades: {trade_count})\n")
    print(f"{'Win Rate:':<20} {win_count}/{trade_count} ({100*win_count/trade_count:.1f}%)")
    print(f"{'Avg P&L per trade:':<20} {trades_df['pnl_pct'].mean():+.2f}%")
    print(f"{'Median P&L:':<20} {trades_df['pnl_pct'].median():+.2f}%")
    print(f"{'Max gain:':<20} {trades_df['pnl_pct'].max():+.2f}%")
    print(f"{'Max loss:':<20} {trades_df['pnl_pct'].min():+.2f}%")
    print(f"{'Std Dev:':<20} {trades_df['pnl_pct'].std():.2f}%")
    print(f"{'Total P&L:':<20} {total_pnl:+.2f}%")
    
    profitable_trades = trades_df[trades_df['pnl_pct'] > 0]
    losing_trades = trades_df[trades_df['pnl_pct'] <= 0]
    
    if len(profitable_trades) > 0:
        print(f"{'Avg win:':<20} {profitable_trades['pnl_pct'].mean():+.2f}%")
    if len(losing_trades) > 0:
        print(f"{'Avg loss:':<20} {losing_trades['pnl_pct'].mean():+.2f}%")
    
    profit_factor = profitable_trades['pnl'].sum() / (abs(losing_trades['pnl'].sum()) + 1e-9)
    print(f"{'Profit factor:':<20} {profit_factor:.2f}x")
    
    print(f"\n{'='*140}\n")
    
    # Best and worst performers
    print("🔥 TOP 10 WINNING TRADES:\n")
    print(f"{'Rank':<5} {'Ticker':<8} {'Entry Date':<12} {'Entry':<10} {'Exit':<10} {'P&L%':<10}")
    print("-" * 70)
    top_wins = trades_df.nlargest(10, 'pnl_pct')
    for idx, (_, trade) in enumerate(top_wins.iterrows(), 1):
        print(f"{idx:<5} {trade['ticker']:<8} {trade['entry_date'].strftime('%Y-%m-%d'):<12} {trade['entry_price']:>9.0f} {trade['exit_price']:>9.0f} {trade['pnl_pct']:>9.2f}%")
    
    print(f"\n❌ TOP 10 LOSING TRADES:\n")
    print(f"{'Rank':<5} {'Ticker':<8} {'Entry Date':<12} {'Entry':<10} {'Exit':<10} {'P&L%':<10}")
    print("-" * 70)
    top_losses = trades_df.nsmallest(10, 'pnl_pct')
    for idx, (_, trade) in enumerate(top_losses.iterrows(), 1):
        print(f"{idx:<5} {trade['ticker']:<8} {trade['entry_date'].strftime('%Y-%m-%d'):<12} {trade['entry_price']:>9.0f} {trade['exit_price']:>9.0f} {trade['pnl_pct']:>9.2f}%")
    
    print(f"\n{'='*140}\n")
    
    # Statistics by ticker
    print("📊 BEST & WORST TICKERS (by avg P&L):\n")
    ticker_stats = trades_df.groupby('ticker').agg({
        'pnl_pct': ['count', 'mean', 'std'],
        'ticker': 'first'
    }).round(2)
    ticker_stats.columns = ['Trades', 'Avg P&L%', 'Std Dev']
    ticker_stats = ticker_stats.sort_values('Avg P&L%', ascending=False)
    
    print("Top 10 best tickers:")
    print(ticker_stats.head(10).to_string())
    
    print("\n\nTop 10 worst tickers:")
    print(ticker_stats.tail(10).to_string())
    
    print(f"\n{'='*140}\n")
    
    # Risk metrics
    print("⚠️  RISK METRICS:\n")
    
    # Max drawdown (daily cumulative)
    trades_df_sorted = trades_df.sort_values('entry_date')
    trades_df_sorted['cumsum'] = trades_df_sorted['pnl_pct'].cumsum()
    trades_df_sorted['running_max'] = trades_df_sorted['cumsum'].expanding().max()
    trades_df_sorted['drawdown'] = trades_df_sorted['cumsum'] - trades_df_sorted['running_max']
    max_dd = trades_df_sorted['drawdown'].min()
    
    print(f"{'Max Drawdown:':<20} {max_dd:.2f}%")
    print(f"{'Sharp Ratio (est):':<20} {total_pnl / (trades_df['pnl_pct'].std() + 0.01):.2f}")
    print(f"{'Winning streak:':<20} {(trades_df['pnl_pct'] > 0).sum()} trades")
    print(f"{'Losing streak:':<20} {(trades_df['pnl_pct'] <= 0).sum()} trades")
    
    print(f"\n{'='*140}\n")
    
    # Export results
    export_path = BASE_DIR / 'data' / 'IHSGstockdata' / 'alerts' / 'backtest_results.csv'
    trades_df.to_csv(export_path, index=False)
    print(f"✅ Detailed backtest saved to: {export_path}\n")
    
    # Verdict
    print("💡 BACKTEST VERDICT:\n")
    if trades_df['pnl_pct'].mean() > 0.5:
        print("✅ STRATEGY IS PROFITABLE: Avg +{:.2f}% per trade (positive edge)".format(trades_df['pnl_pct'].mean()))
        print("   → Confidence: MODERATE (can scale with proper risk management)")
    elif trades_df['pnl_pct'].mean() > 0:
        print("⚠️  MARGINALLY PROFITABLE: Avg +{:.2f}% per trade (needs optimization)".format(trades_df['pnl_pct'].mean()))
        print("   → Confidence: LOW (commissions/slippage could kill profits)")
    else:
        print("❌ UNPROFITABLE: Avg {:.2f}% per trade (negative edge)".format(trades_df['pnl_pct'].mean()))
        print("   → Confidence: VERY LOW (refinement needed)")
    
    print(f"\n{'='*140}\n")
else:
    print("❌ No trades generated - check data quality")
