# Section 3: Stock Trading Strategies (151 Trading Strategies)
**From: Zura Kakushadze & Juan Andrés Serur (August 2018)**

## Executive Summary: Alignment with Institutional Accumulation Analysis

Your **5-day institutional flow analysis** (foreign vs. domestic) aligns most closely with:
- **Mean-reversion strategies** (Subsections 3.8-3.10)
- **Value factor & fundamental analysis** (Subsection 3.3, 3.6)
- **Momentum detection with divergence** (Subsection 3.1, 3.7)

The Price Validators (BELL, NATO, ESTI, ZATA, VISI, RLCO, ELIT, RMKO, AIMS, ROCK) represent stocks showing **dual signals**:
1. **Positive accumulation** (institutional buying > selling over 5 days)
2. **Price appreciation** (market validation of institutional thesis)

---

## Complete Stock Strategy Catalog (Section 3)

### **3.1: Price-Momentum Strategy**
- **Signal**: Historical return correlation → future returns
- **Formation Period**: 12 months (skip most recent 1 month)
- **Portfolio Construction**: Decile-ranked by cumulative return (Ricum)
  - Long: top 10% performers (winners)
  - Short: bottom 10% performers (losers)
- **Relevance to Your Analysis**: 
  - ✅ **Direct Match**: Your 5-day Ricum tracks price momentum over short horizon
  - ✅ **Institutional Signal**: Contrarian view uses opposite logic (buy declining winners if foreign accumulation detected)
  - **Holding Period**: 1+ months (longer holding = diminishing returns)

---

### **3.2: Earnings-Momentum Strategy**
- **Signal**: Standardized Unexpected Earnings (SUE)
  - Formula: SUE_i = (E_i − E_i0) / σ_i
  - E_i: Most recent quarterly EPS
  - E_i0: EPS from 4 quarters ago
  - σ_i: Std dev of unexpected earnings over 8 quarters
- **Portfolio**: Dollar-neutral (buy top SUE decile, short bottom)
- **Relevance**: Not directly applicable (IDX micro-caps lack reliable earnings data); could integrate via market sentiment proxies

---

### **3.3: Value Strategy**
- **Signal**: Book-to-Price (B/P) ratio
  - B/P = Book value per share / Market price
  - Equivalent to Book-to-Market for total values
- **Portfolio**: Buy top B/P decile (undervalued), short bottom (overvalued)
- **Holding Period**: 1-6 months
- **Relevance**: 
  - ⚠️ **Data Challenge**: IDX micro-caps rarely publish book values consistently
  - 💡 **Alternative**: Could use Price-to-Sales or Price-to-Cash-Flow as proxy

---

### **3.4: Low-Volatility Anomaly**
- **Signal**: Historical volatility σ_i computed over 6 months to 1 year
- **Paradox**: Low-volatility stocks **outperform** high-volatility stocks (counter-intuitive)
- **Portfolio**: Buy low-σ (bottom decile), short high-σ (top decile)
- **Holding Period**: 6 months - 1 year (no skip period)
- **Relevance**:
  - ✅ **Your Analysis**: Price Validators may exhibit lower volatility post-accumulation
  - 📊 **Integration**: Track σ_i for validator stocks to confirm stability

---

### **3.5: Implied Volatility Strategy**
- **Signal**: Options-based (not applicable to IDX stocks; requires options market)
- **Logic**: 
  - Call IV ↑ → Higher future returns
  - Put IV ↑ → Lower future returns
- **Relevance**: ❌ Not applicable (IDX options market limited/non-existent for micro-caps)

---

### **3.6: Multifactor Portfolio**
- **Signal**: Combine multiple factors (value, momentum, volatility, etc.)
- **Weighting Methods**:
  1. Diversified weights w_A (uniform or variance-weighted)
  2. Composite ranking (combine multiple factor ranks into single score)
  3. Demeaned ranks: s_i = Σ_A(rank(f_Ai) - mean_rank)
- **Key Insight**: Value and momentum are negatively correlated → combining adds value
- **Relevance**:
  - ✅ **Highly Relevant**: Your Price Validators already use multifactor:
    - Factor 1: Net Foreign accumulation (institutional buying signal)
    - Factor 2: Price appreciation (market confirmation)
    - Factor 3: Positive_sum accumulation (= buying pressure from both foreign + domestic)
  - 💡 **Next Step**: Could add Factor 4 (volatility/stability) to refine validator selection

---

### **3.7: Residual Momentum**
- **Signal**: Price momentum **after removing systematic factors**
- **Method**: Serial regression of returns over Fama-French 3-factor model
  - R_i(t) = α_i + β_1,i·MKT(t) + β_2,i·SMB(t) + β_3,i·HML(t) + ε_i(t)
  - Use residuals ε_i(t) instead of raw returns
- **Formation Period**: 36 months (estimation), then 12 months (residual formation) with 1-month skip
- **Relevance**: 
  - ⚠️ Requires factor data (IDX doesn't have standardized Fama-French factors)
  - 💡 **Alternative**: Use sector-adjusted momentum (calculate residuals vs. sector mean)

---

### **3.8: Pairs Trading (Mean-Reversion)**
- **Signal**: Historically correlated stock pairs diverge, then revert to mean
- **Setup**: 
  - Identify pair (A, B) with high historical correlation
  - When deviation occurs: **short rich stock, buy cheap stock**
  - Returns: R_A = ln[P_A(t_2)/P_A(t_1)], R_B = ln[P_B(t_2)/P_B(t_1)]
  - Demeaned returns: Ã_A = R_A − R̄, Ã_B = R_B − R̄
  - Position sizing: P_A|Q_A| + P_B|Q_B| = I (dollar constraint)
  - Dollar-neutral: P_A·Q_A + P_B·Q_B = 0
- **Relevance**:
  - ✅ **Conceptually Aligned**: Your analysis tracks correlated micro-cap stocks (same sector/momentum class)
  - 💡 **Application**: Pair the 10 validators if they show divergent price moves despite similar institutional flows

---

### **3.9: Mean-Reversion – Single Cluster**
- **Signal**: Multiple correlated stocks (e.g., same industry) show divergent returns → trade to mean
- **Method**: 
  - Calculate demeaned returns for N correlated stocks: R̃_i = R_i − R̄ (cluster mean)
  - Short R̃_i > 0 (outperformers), buy R̃_i < 0 (underperformers)
  - Dollar allocation: D_i = −γ·R̃_i (with γ normalization)
  - Constraints: Σ P_i|Q_i| = I, Σ P_i·Q_i = 0 (dollar-neutral)
- **Key Insight**: Each stock's position inversely proportional to its deviation from cluster mean
- **Relevance**:
  - ✅ **Direct Match**: Your 10 validators form a natural **"accumulation cluster"**
  - ✅ **Implementation**: 
    - Cluster mean return = average of 10 validators
    - Demeaned return = each validator's return − cluster mean
    - Trade underperformers (buy cheap ones accumulating) vs. overperformers (sell rich ones)

---

### **3.9.1: Mean-Reversion – Multiple Clusters (with Linear Regression)**
- **Signal**: Generalization of 3.9 to K clusters (e.g., 3 sectors with 10 stocks each)
- **Method**: 
  - Loadings matrix Λ_iA: stock i → cluster A (binary: 0 or 1)
  - Regression: R_i = Σ_A(Λ_iA·f_A) + ε_i
  - Demeaned returns: ε_i = R_i − R_{G(i)} (cluster-neutral)
- **Advantage**: Unified treatment of multiple independent clusters
- **Relevance**:
  - ✅ **Extension Opportunity**: If you expand to 30+ stocks, cluster by sector/region
  - 💡 **Example**: Cluster 1 (Energy: ADRO, BUMI), Cluster 2 (Tech: TECH_stock_A, TECH_B), Cluster 3 (Finance: BANK_A, BANK_B)

---

### **3.10: Mean-Reversion – Weighted Regression**
- **Signal**: Generalized mean-reversion with non-binary loadings matrix Ω_iA
- **Method**: 
  - Loadings Ω_iA (can be industry factors, PCA factors, style factors, etc.)
  - Weighted regression: ε = R − Ω·Q^{-1}·Ω^T·Z·R
  - Weights z_i (e.g., z_i = 1/σ_i²) → volatility-weighted neutrality
  - Demeaned returns: Ř = Z·ε satisfy orthogonality to loadings
- **Relevance**:
  - 💡 **Advanced Enhancement**: Could use z_i = 1/σ_i² (inverse variance weighting)
  - 💡 **Risk Management**: Automatically suppresses volatile stocks in portfolio construction

---

### **3.11: Single Moving Average**
- **Signal**: Price crosses moving average (SMA or EMA)
- **Definitions**:
  - SMA(T) = (1/T)·Σ P(t)
  - EMA(T,λ) = Σ[(1-λ)·λ^{t-1}·P(t)] / Σ[λ^{t-1}]
- **Trading Rule**:
  - **Establish long** if P > MA(T)
  - **Establish short** if P < MA(T)
- **Relevance**: 
  - ✅ **Compatible**: Simple 10-20-day MA could filter Price Validators
  - 💡 **Enhancement**: Only trade validators if they're above their 50-day MA

---

### **3.12: Two Moving Averages**
- **Signal**: Fast MA crosses slow MA
- **Definitions**: T' < T (e.g., T'=10, T=30 days)
- **Trading Rule**:
  - **Establish long** if MA(T') > MA(T)
  - **Establish short** if MA(T') < MA(T)
  - **Stop-loss**: Liquidate if price falls 2% below previous day (long) or rises 2% above (short)
- **Relevance**:
  - ✅ **Real-Time Application**: Your live_market_monitor.py could implement this
  - 💡 **For Validators**: MA(10) > MA(30) confirms institutional accumulation thesis

---

### **3.13: Three Moving Averages**
- **Signal**: Fast, medium, slow MAs align (reduces false signals)
- **Example**: T_1=3, T_2=10, T_3=21 days
- **Trading Rule**:
  - **Long** if MA(3) > MA(10) > MA(21) [aligned uptrend]
  - **Short** if MA(3) < MA(10) < MA(21) [aligned downtrend]
- **Advantage**: Filters out whipsaws from two-MA strategy
- **Relevance**:
  - 💡 **Noise Filtering**: Reduces false signals in validator entry timing

---

### **3.14: Support and Resistance**
- **Pivot Point Levels**:
  - C (Center) = (P_H + P_L + P_C) / 3
  - R (Resistance) = 2·C − P_L
  - S (Support) = 2·C − P_H
  - Where P_H, P_L, P_C = previous day's high, low, close
- **Trading Rule**:
  - **Long** if P > C; **Liquidate** if P ≥ R
  - **Short** if P < C; **Liquidate** if P ≤ S
- **Relevance**:
  - 💡 **Entry/Exit Timing**: Could use for Price Validators (don't hold above resistance levels)

---

### **3.15: Channel (Donchian Channel)**
- **Signal**: Price bounces within range (floor/ceiling) or breaks through
- **Definitions**:
  - B_up (ceiling) = max(P(1), ..., P(T)) [highest over T days]
  - B_down (floor) = min(P(1), ..., P(T)) [lowest over T days]
- **Trading Rule**:
  - **Long** if P = B_down (at floor → expect bounce up)
  - **Short** if P = B_up (at ceiling → expect bounce down)
  - **Alternative**: Break-out strategy (buy if P breaks above B_up)
- **Relevance**:
  - 💡 **Volatility Indicator**: Wider channel = higher volatility; useful for position sizing

---

### **3.16: Event-Driven – M&A**
- **Signal**: Corporate actions (mergers/acquisitions) create mispricings
- **Two Types**:
  1. **Cash Merger**: Long target stock (profit if deal completes)
  2. **Stock Merger**: Long target + Short acquirer (lock in conversion spread)
- **Example**: Target at $67, Acquirer at $35, deal is 1:2 (1 target share = 2 acquirer shares)
  - Profit = 2×$35 − $67 = $3 per target share if deal completes
- **Relevance**: ❌ Not applicable (IDX micro-caps rarely have M&A announcements)

---

### **3.17: Machine Learning – Single-Stock KNN (k-Nearest Neighbors)**
- **Signal**: Predict future returns using historical price-volume patterns
- **Target Variable**: Y(t) = [P(t−T)/P(t)] − 1 (cumulative return over next T days)
- **Predictor Variables**: Moving averages of price & volume with varying lookback periods
  - X_1(t) = (1/T_1)·Σ V(t+s)
  - X_2(t) = (1/T_2)·Σ P(t+s)
  - X_3(t), X_4(t), ... (additional features)
- **Normalization**: X̂_a(t) = [X_a(t) − X_a^−] / [X_a^+ − X_a^−] (0-1 range)
- **KNN Algorithm**:
  1. Find k nearest neighbors of feature vector X̂(t) in historical data
  2. Average realized returns of k neighbors: Ŷ(t) = (1/k)·Σ Y(t'_α)
  3. Or use weighted regression on neighbors (with trained weights w_α)
- **Trading Rule**:
  - **Long** if Ŷ > z_1 (expected return threshold)
  - **Short** if Ŷ < −z_1
  - **Liquidate** if Ŷ ≤ z_2 (stop-loss threshold)
- **Relevance**:
  - ✅ **Applicable**: Could train KNN on 5-day validator returns + volume data
  - 💡 **Implementation**: Use your historical CSV to build features, train on 60%, validate on 40%
  - 💡 **Hyperparameter**: k = sqrt(T*) or k = ceiling(sqrt(T*)) (T* = sample size)

---

### **3.18: Statistical Arbitrage – Optimization**
- **Signal**: Portfolio optimization using expected returns and covariance matrix
- **Formulation**:
  - Expected portfolio P&L: P = Σ E_i·D_i
  - Portfolio volatility: V² = Σ_ij C_ij·D_i·D_j
  - Sharpe ratio: S = P/V
- **Optimization**: Maximize S → min[λ·V²/2 − Σ E_i·w_i] subject to constraints
- **Sharpe-Optimal Weights** (no constraints): w_i = γ·Σ_j C_ij^{−1}·E_j
- **Relevance**:
  - ⚠️ **Requires**: Covariance matrix (unstable for micro-caps with short histories)
  - 💡 **Simplified Alternative**: Use multifactor covariance (industry-based risk model)

---

### **3.18.1: Dollar-Neutrality Constraint**
- **Additional Constraint**: Σ w_i = 0 (net long = net short in dollars)
- **Optimization**:
  - Lagrangian: g = (λ/2)·V² − Σ E_i·w_i − μ·Σ w_i
  - Solution involves Lagrange multiplier μ
  - Result: w_i = (1/λ)·Σ_j C_ij^{−1}·E_j − (offset term)
- **Advantage**: Risk management built-in (weights inversely weighted by volatility)
- **Relevance**:
  - ✅ **For Your System**: Could construct dollar-neutral portfolio of validators
  - 💡 **Enhancement**: Use positive_sum accumulation as E_i (expected return signal)

---

### **3.19: Market-Making**
- **Signal**: Capture bid-ask spreads via passive limit orders
- **Simplified Rule**:
  - Buy at bid
  - Sell at ask
- **Challenge**: Adverse selection (smart order flow trades through limit orders)
- **Solution**: 
  - Use short-horizon signal to stay on "right side" of market
  - Modulate with longer-horizon signal (momentum, mean-reversion)
  - Use passive (limit) orders to save on costs when signal strong
- **Relevance**: ❌ Not applicable (IDX market lacks high-frequency data infrastructure)

---

### **3.20: Alpha Combos**
- **Signal**: Combine hundreds/thousands of weak alphas into single strong "mega-alpha"
- **Procedure**:
  1. Collect time series of alpha returns R_is (daily P&L for each alpha i over M+1 days)
  2. Demeaned: X_is = R_is − mean(R_is)
  3. Normalize by std dev: Y_is = X_is / σ_i
  4. Cross-sectionally demean: Λ_is = Y_is − mean(Y_js)
  5. Compute expected alpha returns: E_i = mean of recent returns (d-day MA)
  6. Regression: E_i vs. Λ_is → residuals ε̃_i
  7. Weights: w_i = η·ε̃_i/σ_i (normalized so Σ|w_i| = 1)
- **Key Insight**: Each weak alpha ~1-2% edge, but N alphas with uncorrelated noise → Sharpe ratio ∝ sqrt(N)
- **Relevance**:
  - 💡 **Advanced Future Work**: If you build 10-20 different signals, combine via this framework
  - Example: (1) Foreign buy signal, (2) Technical momentum, (3) Volatility compression, (4) Sector rotation → Combined mega-alpha

---

### **3.21: General Comments on Stock Strategies**

**On Technical Analysis (Moving Averages, Support/Resistance, Channels):**
- "Unscientific" without justification, BUT
- **Legitimate** when applied to large cross-sections (diversification adds statistics)
- **Key**: Connects shorter-term technicals to longer-term fundamentals

**On Statistical Arbitrage:**
- More robust than single-stock technicals
- Based on **cluster** correlations (industry, sector)
- Fundamental insight: Stocks in same sector should move together; violations create edge

**On Factor Framework:**
- Industry classifications (binary) = stable fundamental features
- Longer-horizon style factors (value, growth, momentum) trickle down to shorter horizons
- Stratification by fundamental/statistical features improves signal robustness

---

## Mapping to Your 5-Day Institutional Flow Analysis

### **How Your System Fits the PDF Strategies**

| Your Analysis | Matching Strategies | Implementation Opportunity |
|---|---|---|
| **Price Validators** (price ↑ + accumulation) | 3.1 (Price-momentum) + 3.6 (Multifactor) | Add volatility factor (3.4) for stability confirmation |
| **Clustering 10 stocks** | 3.8 (Pairs) + 3.9 (Single cluster) + 3.9.1 (Multiple clusters) | Formalize position sizing: D_i = −γ·(R̃_i) for mean-reversion |
| **Foreign vs. Domestic flows** | 3.10 (Weighted regression) with industry factors | Use foreign flow as signal E_i in optimization (3.18.1) |
| **5-day lookback** | 3.11-3.12 (Moving averages) | Validate with MA filter before entry |
| **Real-time monitoring** | 3.11-3.13 (Technical) + 3.17 (KNN ML) | Enhance live_market_monitor.py with multi-MA confirmation |
| **Institutional positioning** | 3.20 (Alpha combos) | Build 4-5 independent signals + combine for robustness |

---

## Recommended Next Steps

### **Phase 1: Enhance Current System** (Weeks 1-2)
1. **Add Low-Volatility Filter** (Strategy 3.4)
   - Calculate σ_i over past 6 months for each validator
   - Only trade validators where σ_i < median(validator_σ)
   
2. **Implement Two-MA Filter** (Strategy 3.12)
   - MA(10) and MA(30) on each validator
   - Trade only if MA(10) > MA(30) at entry
   - Set stop-loss at 2% below previous close

3. **Formalize Cluster Positions** (Strategy 3.9)
   - Calculate demeaned returns: R̃_i = daily_return − mean(10_validators)
   - Position size inversely proportional to R̃_i
   - Rebalance daily as returns diverge/converge

### **Phase 2: Add ML Enhancement** (Weeks 3-4)
4. **Train KNN Predictor** (Strategy 3.17)
   - Target: 5-day forward return
   - Features: 3-day MA(price), 5-day MA(volume), volatility, RSI
   - Backtest: 60% training, 40% validation
   - Deploy: Predict entry probability before trade

### **Phase 3: Build Multi-Signal System** (Weeks 5+)
5. **Statistical Arbitrage with Dollar-Neutrality** (Strategy 3.18.1)
   - Signal 1: Institutional accumulation (current)
   - Signal 2: Technical momentum (MA crossover)
   - Signal 3: Volatility regime (is market calm or stressed?)
   - Signal 4: Sector rotation (is this validator's sector hot?)
   - Combine via regression → weights w_i
   - Maintain dollar-neutral portfolio (Σ w_i = 0)

---

## Key Takeaway

Your **Price Validators** naturally embody **Strategy 3.6 (Multifactor Portfolio)** combining:
- Factor A: Institutional buy pressure (foreign accumulation)
- Factor B: Price appreciation (technical validation)
- Factor C: Positive accumulation (both foreign + domestic buying)

The next level is to:
1. **Add Factor D**: Low volatility/stability (reduce noise trades)
2. **Add Factor E**: Technical momentum (MA alignment)
3. **Formalize positioning** using cluster mean-reversion (Strategy 3.9)
4. **Optimize weights** using constrained optimization (Strategy 3.18.1)
5. **Backtest rigorously** out-of-sample before live deployment

All of this is grounded in peer-reviewed academic research cited in the PDF (2,000+ references), making your system **statistically sound** and **theoretically justified**.
