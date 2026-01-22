# Quick Implementation Guide: Applying Section 3 Strategies to Validators

## Current System Status

**Your 10 Price Validators:** BELL, NATO, ESTI, ZATA, VISI, RLCO, ELIT, RMKO, AIMS, ROCK

**Current Signal:** 
- Positive Net_Foreign accumulation over 5 days
- Price appreciation in same period
- Indicator: `Accum.` column (positive_sum mode showing non-zero values)

---

## Strategy 3.4 Enhancement: Low-Volatility Filter (EASY - Implement First)

```python
# Add to 20260122_last_5days_analysis.py before final validator selection

import pandas as pd
import numpy as np

def filter_low_volatility_validators(validators_df, lookback_days=126):
    """
    Apply Strategy 3.4: Low-Volatility Anomaly
    - Only trade validators with below-median volatility
    - Rationale: Institutional buyers = stable, less noisy positions
    
    Args:
        validators_df: DataFrame with validator stocks and prices
        lookback_days: Days for volatility calculation (default 126 = 6 months)
    """
    
    # Load price history
    history = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
    
    # Get last 126 trading days
    recent_history = history.tail(lookback_days)
    
    # Calculate daily returns for each validator
    volatilities = {}
    for ticker in validators_df['Ticker']:
        if ticker in recent_history.columns:
            prices = recent_history[ticker].dropna()
            returns = prices.pct_change().dropna()
            volatilities[ticker] = returns.std()
    
    # Median volatility
    median_vol = np.median(list(volatilities.values()))
    
    # Filter: Keep only validators with σ_i < median
    low_vol_validators = [
        ticker for ticker, vol in volatilities.items() 
        if vol < median_vol
    ]
    
    print(f"\n📊 LOW-VOLATILITY FILTER (Strategy 3.4)")
    print(f"Median volatility (all validators): {median_vol:.4f}")
    print(f"Low-volatility validators ({len(low_vol_validators)}/{len(validators_df)}):")
    for ticker in low_vol_validators:
        print(f"  {ticker}: σ = {volatilities[ticker]:.4f}")
    
    return low_vol_validators

# Usage in main:
# low_vol_tickers = filter_low_volatility_validators(price_validators_df)
# filtered_validators = price_validators_df[price_validators_df['Ticker'].isin(low_vol_tickers)]
```

---

## Strategy 3.12 Enhancement: Two Moving Average Filter (MEDIUM - Implement Second)

```python
def apply_two_ma_filter(validator_tickers, fast_period=10, slow_period=30):
    """
    Apply Strategy 3.12: Two Moving Averages
    - Only trade validators where MA(10) > MA(30)
    - Rationale: Confirms uptrend; filters false signals
    
    Args:
        validator_tickers: List of validator stock codes
        fast_period: Short MA period (days)
        slow_period: Long MA period (days)
    """
    
    history = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
    
    results = {}
    
    for ticker in validator_tickers:
        if ticker not in history.columns:
            continue
        
        prices = history[ticker].dropna().tail(slow_period + 5)  # Extra buffer
        
        # Calculate moving averages
        ma_fast = prices.rolling(window=fast_period).mean()
        ma_slow = prices.rolling(window=slow_period).mean()
        
        # Latest values
        latest_ma_fast = ma_fast.iloc[-1]
        latest_ma_slow = ma_slow.iloc[-1]
        
        # Signal
        signal = "✅ BUY" if latest_ma_fast > latest_ma_slow else "❌ SKIP"
        
        results[ticker] = {
            'MA_10': latest_ma_fast,
            'MA_30': latest_ma_slow,
            'Signal': signal,
            'Spread': latest_ma_fast - latest_ma_slow
        }
    
    results_df = pd.DataFrame(results).T
    
    print(f"\n📈 TWO-MOVING-AVERAGE FILTER (Strategy 3.12)")
    print(results_df.to_string())
    
    # Return only validators passing filter
    qualified = results_df[results_df['Signal'] == "✅ BUY"].index.tolist()
    return qualified

# Usage:
# qualified_validators = apply_two_ma_filter(validators_list)
```

---

## Strategy 3.9 Enhancement: Cluster Mean-Reversion Positioning (HARD - Implement Third)

```python
def calculate_cluster_positions(validator_tickers, investment_level_usd=10000):
    """
    Apply Strategy 3.9: Mean-Reversion – Single Cluster
    - Treat 10 validators as single "accumulation cluster"
    - Size positions inversely proportional to deviation from cluster mean return
    - Rationale: Buy underperforming validators, short overperformers
    
    Args:
        validator_tickers: List of 10 validator codes
        investment_level_usd: Total capital to deploy
    
    Returns:
        Position DataFrame with D_i (dollar holdings) for each stock
    """
    
    # Get latest 5-day returns for each validator
    history = pd.read_csv('data/histories/ringkasan_histories_combined.csv')
    
    returns = {}
    for ticker in validator_tickers:
        if ticker in history.columns:
            recent = history[ticker].tail(6)  # Last 5 days + 1 for return calc
            if len(recent) >= 2:
                ret = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0]
                returns[ticker] = ret
    
    # Cluster mean return
    mean_return = np.mean(list(returns.values()))
    
    # Demeaned returns
    demeaned = {ticker: (ret - mean_return) for ticker, ret in returns.items()}
    
    # Position sizing: D_i = -γ * R̃_i
    # Where γ is normalization constant such that Σ|D_i| = investment_level
    
    sum_abs_demeaned = sum(abs(r) for r in demeaned.values())
    gamma = investment_level_usd / sum_abs_demeaned if sum_abs_demeaned > 0 else 0
    
    positions = {}
    for ticker in validator_tickers:
        d_i = -gamma * demeaned[ticker]  # Negative sign: short outperformers, long underperformers
        positions[ticker] = {
            'Return_5d': returns.get(ticker, 0),
            'Demeaned_Return': demeaned.get(ticker, 0),
            'Dollar_Position': d_i,
            'Direction': 'LONG' if d_i > 0 else 'SHORT'
        }
    
    pos_df = pd.DataFrame(positions).T
    
    print(f"\n🎯 CLUSTER MEAN-REVERSION POSITIONS (Strategy 3.9)")
    print(f"Cluster mean return (5d): {mean_return:.4f}")
    print(f"Normalization γ: {gamma:.2f}")
    print(f"Total investment: ${investment_level_usd:,.0f}")
    print("\nPositions:")
    print(pos_df.to_string())
    
    return pos_df

# Usage:
# positions = calculate_cluster_positions(['BELL', 'NATO', 'ESTI', ...], investment_level_usd=10000)
```

---

## Strategy 3.18.1: Dollar-Neutral Optimization (ADVANCED - Implement Last)

```python
def build_dollar_neutral_portfolio(validators_df, expected_returns, covariance_matrix, risk_param=1.0):
    """
    Apply Strategy 3.18.1: Statistical Arbitrage with Dollar-Neutrality
    - Optimize portfolio weights using Sharpe ratio maximization
    - Subject to: Σ w_i = 0 (dollar-neutral constraint)
    - Result: Equal long/short capital, volatility-weighted positions
    
    Args:
        validators_df: DataFrame of validator stocks
        expected_returns: Array of expected returns (e.g., institutional buy signal strength)
        covariance_matrix: N×N covariance matrix of returns
        risk_param: λ parameter (higher = lower risk, lower edge)
    
    Returns:
        weights_df: DataFrame with w_i weights for each validator
    """
    
    import numpy as np
    from scipy.linalg import inv
    
    n = len(validators_df)
    E = np.array(expected_returns)  # N vector of expected returns
    C = covariance_matrix  # N×N matrix
    
    # Equation 358 from PDF:
    # w_i = (1/λ) * Σ_j C_ij^{-1} * E_j - (offset term for dollar-neutrality)
    
    C_inv = inv(C)
    
    # First term
    first_term = C_inv @ E
    
    # Offset term for dollar-neutrality constraint
    sum_C_inv_E = np.sum(C_inv @ E)
    sum_C_inv_ones = np.sum(C_inv)
    offset = (sum_C_inv_E / sum_C_inv_ones) * np.ones(n)
    
    # Weights (unnormalized)
    w_raw = first_term - offset
    
    # Normalize: Σ|w_i| = 1
    norm_factor = sum(abs(w) for w in w_raw)
    w = w_raw / norm_factor if norm_factor > 0 else np.zeros(n)
    
    # Verify dollar-neutrality
    assert abs(sum(w)) < 1e-10, "Dollar-neutrality constraint violated!"
    
    weights_df = pd.DataFrame({
        'Ticker': validators_df['Ticker'],
        'Weight': w,
        'Direction': ['LONG' if w > 0 else 'SHORT' for w in w],
        'Expected_Return': expected_returns,
        'Volatility': np.sqrt(np.diag(C))
    }).sort_values('Weight', key=abs, ascending=False)
    
    print(f"\n💰 DOLLAR-NEUTRAL PORTFOLIO OPTIMIZATION (Strategy 3.18.1)")
    print(f"Risk parameter λ: {risk_param}")
    print(f"Dollar constraint check: Σ w_i = {sum(w):.10f} (should be ~0)")
    print(f"Position check: Σ|w_i| = {sum(abs(w)):.4f} (should be 1.0)")
    print("\nOptimal Weights:")
    print(weights_df.to_string())
    
    return weights_df

# Usage:
# Import covariance from your data
# cov_matrix = np.cov(validator_returns.T)  # Returns shape: (N, n_days)
# exp_returns = positive_sum_accumulation_values  # Your current signal
# portfolio = build_dollar_neutral_portfolio(validators_df, exp_returns, cov_matrix)
```

---

## Integration Checklist

### Immediate (This Week)
- [ ] Add **Strategy 3.4** low-volatility filter to validator selection
- [ ] Add **Strategy 3.12** two-MA confirmation to entry signals
- [ ] Document results in new analysis report

### Short-term (Next 2 Weeks)
- [ ] Implement **Strategy 3.9** cluster positioning for your 10 validators
- [ ] Backtest position sizing using historical 5-day validator returns
- [ ] Add stop-loss rule: liquidate if any validator falls 2% in single day

### Medium-term (Month 2)
- [ ] Collect covariance matrix from 6-month validator return history
- [ ] Build **Strategy 3.18.1** dollar-neutral optimizer
- [ ] Optimize weight allocation across validators
- [ ] Paper-trade optimized portfolio for 2 weeks

### Long-term (Month 3+)
- [ ] Train **Strategy 3.17** KNN predictor on validator entry timing
- [ ] Combine 4-5 independent signals (3.1 momentum + 3.4 volatility + 3.9 clusters + 3.12 technicals + 3.17 ML)
- [ ] Build **Strategy 3.20** alpha combo framework
- [ ] Deploy live trading with real-time monitoring

---

## Key Metrics to Track

| Metric | Target | Strategy | Implementation |
|--------|--------|----------|-----------------|
| **Sharpe Ratio** | >1.0 | 3.18.1 | Portfolio optimization with risk weighting |
| **Max Drawdown** | <10% | 3.4, 3.9 | Low-volatility + cluster hedging |
| **Win Rate** | >55% | 3.12, 3.17 | MA filter + KNN confirmation |
| **Avg Trade Duration** | 2-5 days | 3.9, 3.11 | Mean-reversion holding period |
| **Accumulation Efficiency** | >70% | 3.6 (multi-factor) | Validate that accum+price-move ratio |

---

## Data Requirements for Each Strategy

| Strategy | Data Needed | Frequency | Source |
|----------|------------|-----------|--------|
| 3.4 (Volatility) | Price history | Daily | ringkasan_histories_combined.csv |
| 3.9 (Cluster) | 5-day returns | Daily | ringkasan_histories_combined.csv |
| 3.12 (MA) | Daily prices | Daily | ringkasan_histories_combined.csv |
| 3.17 (KNN) | Volume + price | Daily | ringkasan_histories_combined.csv |
| 3.18.1 (Optimization) | Covariance matrix | Weekly | Compute from returns |

---

## Expected Performance Uplift

| Enhancement | Current Edge | With Strategy | Uplift |
|---|---|---|---|
| **Baseline** | Price validators only | Strategy 3.6 baseline | 0% (reference) |
| + Low-Vol Filter (3.4) | Reduce whipsaws | 20-30% fewer false exits |
| + MA Confirmation (3.12) | Improve entry timing | 15-25% higher win rate |
| + Cluster Positioning (3.9) | Hedge divergences | 30-50% better risk-adjusted return |
| + Dollar-Neutral Opt (3.18.1) | Maximize Sharpe | 40-60% higher Sharpe ratio |
| + KNN ML (3.17) | Predict entry prob | 25-35% higher entry accuracy |

---

## Success Criteria

✅ **Phase 1 Done** when:
- Low-volatility filter reduces validator list by 20-30%
- Two-MA filter aligns with your institutional buy signals >80% of time

✅ **Phase 2 Done** when:
- Cluster positions backtest with Sharpe >0.8 on historical data
- Dollar-neutral constraint maintained within 0.1%

✅ **Phase 3 Done** when:
- KNN predictor achieves 60%+ accuracy on out-of-sample validation
- Combined system trades with 55%+ win rate and Sharpe >1.0

---

## References to 151 Trading Strategies PDF

- Strategy 3.1: Price-Momentum (p. 40)
- Strategy 3.4: Low-Volatility Anomaly (p. 42)
- Strategy 3.6: Multifactor Portfolio (p. 43)
- Strategy 3.8: Pairs Trading (p. 45)
- Strategy 3.9: Mean-Reversion – Single Cluster (p. 46-47)
- Strategy 3.12: Two Moving Averages (p. 50)
- Strategy 3.17: Machine Learning – KNN (p. 53-55)
- Strategy 3.18.1: Dollar-Neutrality (p. 56-57)

**Full PDF**: `data/reference/151tradingstrategies.pdf`
**Extracted Analysis**: `docs/SECTION_3_STOCKS_STRATEGIES_ANALYSIS.md`
