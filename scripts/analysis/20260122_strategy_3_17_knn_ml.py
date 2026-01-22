#!/usr/bin/env python3
"""
Strategy 3.17: Machine Learning - KNN (k-Nearest Neighbors)

Signal: Predict next-day returns using historical price-volume patterns.
- Features: Moving averages of price & volume (multiple horizons)
- Target: Next-day return (classification: up/down or regression: % return)
- KNN: Find k nearest neighbors, average their outcomes

Our Implementation:
- Features: 3d/5d/10d MA(price), 3d/5d/10d MA(volume), 5d volatility, current momentum
- Target: 1-day forward return (regression)
- Training: 60% historical data, validation: 40%
- Output: Predicted returns for MA-filtered positions

Inputs:
- data/histories/ringkasan_histories_combined.csv : for feature engineering
- results/strategy_3_12_ma_filtered_positions.csv : stocks to predict

Outputs:
- results/strategy_3_17_knn_predictions.csv : predicted returns per stock
- results/strategy_3_17_report.txt : model performance and recommendations
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

HIST_FILE = Path("data/histories/ringkasan_histories_combined.csv")
POSITIONS_FILE = Path("results/strategy_3_12_ma_filtered_positions.csv")
OUTPUT_FILE = Path("results/strategy_3_17_knn_predictions.csv")
REPORT_FILE = Path("results/strategy_3_17_report.txt")

K_NEIGHBORS = 5  # Reduced for smaller samples
TRAIN_RATIO = 0.7  # More training data
MIN_SAMPLE_SIZE = 20  # Minimum data points


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features for KNN model."""
    df = df.sort_values(["Kode Saham", "SourceDate"]).copy()
    
    # Price MAs
    df["ma_price_3d"] = df.groupby("Kode Saham")["Penutupan"].transform(
        lambda x: x.rolling(3, min_periods=3).mean()
    )
    df["ma_price_5d"] = df.groupby("Kode Saham")["Penutupan"].transform(
        lambda x: x.rolling(5, min_periods=5).mean()
    )
    df["ma_price_10d"] = df.groupby("Kode Saham")["Penutupan"].transform(
        lambda x: x.rolling(10, min_periods=10).mean()
    )
    
    # Volume MAs
    df["ma_volume_3d"] = df.groupby("Kode Saham")["Volume"].transform(
        lambda x: x.rolling(3, min_periods=3).mean()
    )
    df["ma_volume_5d"] = df.groupby("Kode Saham")["Volume"].transform(
        lambda x: x.rolling(5, min_periods=5).mean()
    )
    df["ma_volume_10d"] = df.groupby("Kode Saham")["Volume"].transform(
        lambda x: x.rolling(10, min_periods=10).mean()
    )
    
    # Returns
    df["ret_1d"] = df.groupby("Kode Saham")["Penutupan"].pct_change() * 100
    df["ret_5d"] = df.groupby("Kode Saham")["Penutupan"].pct_change(5) * 100
    
    # Volatility
    df["volatility_5d"] = df.groupby("Kode Saham")["ret_1d"].transform(
        lambda x: x.rolling(5, min_periods=5).std()
    )
    
    # Target: next-day return
    df["target_ret_1d"] = df.groupby("Kode Saham")["ret_1d"].shift(-1)
    
    # Drop nulls
    df = df.dropna()
    
    return df


def train_knn_model(data: pd.DataFrame, stock: str):
    """Train KNN model for a single stock."""
    stock_data = data[data["Kode Saham"] == stock].copy()
    
    if len(stock_data) < MIN_SAMPLE_SIZE:  # Minimum sample size
        return None, None, {}
    
    # Features
    feature_cols = ["ma_price_3d", "ma_price_5d", "ma_price_10d", 
                    "ma_volume_3d", "ma_volume_5d", "ma_volume_10d",
                    "ret_5d", "volatility_5d"]
    
    X = stock_data[feature_cols].values
    y = stock_data["target_ret_1d"].values
    
    # Train/test split (temporal)
    split_idx = int(len(X) * TRAIN_RATIO)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train KNN
    k = min(K_NEIGHBORS, len(X_train) - 1)
    knn = KNeighborsRegressor(n_neighbors=k, weights='distance')
    knn.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = knn.predict(X_test_scaled)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Directional accuracy
    direction_correct = np.sum((y_test > 0) == (y_pred > 0)) / len(y_test)
    
    metrics = {
        "mse": mse,
        "mae": mae,
        "r2": r2,
        "direction_accuracy": direction_correct,
        "n_train": len(X_train),
        "n_test": len(X_test)
    }
    
    return knn, scaler, metrics


def predict_next_day(positions: pd.DataFrame, data: pd.DataFrame) -> pd.DataFrame:
    """Predict next-day returns for MA-filtered positions."""
    predictions = []
    
    for idx, row in positions.iterrows():
        stock = row["Kode Saham"]
        print(f"Training KNN for {stock}...")
        
        # Train model
        knn, scaler, metrics = train_knn_model(data, stock)
        
        if knn is None:
            print(f"  ⚠️  Insufficient data for {stock}")
            continue
        
        # Get latest features for prediction
        stock_data = data[data["Kode Saham"] == stock].sort_values("SourceDate")
        latest = stock_data.tail(1)
        
        feature_cols = ["ma_price_3d", "ma_price_5d", "ma_price_10d", 
                        "ma_volume_3d", "ma_volume_5d", "ma_volume_10d",
                        "ret_5d", "volatility_5d"]
        
        X_latest = latest[feature_cols].values
        X_latest_scaled = scaler.transform(X_latest)
        
        # Predict
        pred_ret = knn.predict(X_latest_scaled)[0]
        
        predictions.append({
            "Kode Saham": stock,
            "current_price": row["close"],
            "predicted_return_1d": pred_ret,
            "predicted_price": row["close"] * (1 + pred_ret / 100),
            "knn_mae": metrics["mae"],
            "knn_r2": metrics["r2"],
            "knn_direction_acc": metrics["direction_accuracy"],
            "mr_rank": row["mr_rank"],
            "capital_allocation": row["capital_allocation"],
            "stop_loss": row["stop_loss"]
        })
        
        print(f"  ✓ Predicted return: {pred_ret:+.2f}% | Direction acc: {metrics['direction_accuracy']:.1%}")
    
    return pd.DataFrame(predictions)


def write_report(predictions: pd.DataFrame):
    """Write KNN prediction report."""
    lines = []
    lines.append("Strategy 3.17: KNN Machine Learning Predictions")
    lines.append("=" * 80)
    lines.append("")
    
    lines.append("MODEL OVERVIEW:")
    lines.append(f"  Algorithm: k-Nearest Neighbors Regression (k={K_NEIGHBORS})")
    lines.append("  Features: 3d/5d/10d MA(price), 3d/5d/10d MA(volume), 5d returns, 5d volatility")
    lines.append("  Target: Next-day return (%)")
    lines.append(f"  Train/Test Split: {int(TRAIN_RATIO*100)}% / {int((1-TRAIN_RATIO)*100)}%")
    lines.append("")
    
    if len(predictions) == 0:
        lines.append("No predictions available (insufficient data).")
        REPORT_FILE.write_text("\n".join(lines))
        return
    
    # Average model performance
    lines.append("AVERAGE MODEL PERFORMANCE:")
    lines.append(f"  Mean Absolute Error: {predictions['knn_mae'].mean():.2f}%")
    lines.append(f"  R² Score: {predictions['knn_r2'].mean():.3f}")
    lines.append(f"  Direction Accuracy: {predictions['knn_direction_acc'].mean():.1%}")
    lines.append("")
    
    # Predictions ranked by predicted return
    predictions_sorted = predictions.sort_values("predicted_return_1d", ascending=False)
    
    lines.append("NEXT-DAY RETURN PREDICTIONS (Ranked by Predicted Return):")
    lines.append("-" * 80)
    lines.append(f"{'Rank':<6}{'Ticker':<8}{'Price':<10}{'Pred Ret%':<12}{'Pred Price':<12}"
                 f"{'Dir Acc%':<12}{'Capital(M)':<12}")
    lines.append("-" * 80)
    
    for idx, row in predictions_sorted.iterrows():
        rank = predictions_sorted.index.get_loc(idx) + 1
        signal = "🟢" if row["predicted_return_1d"] > 0 else "🔴"
        lines.append(f"{rank:<6d}{row['Kode Saham']:<8}{int(row['current_price']):<10,}"
                     f"{row['predicted_return_1d']:<12.2f}{int(row['predicted_price']):<12,}"
                     f"{row['knn_direction_acc']*100:<12.1f}{row['capital_allocation']/1e6:<12.1f}")
    
    lines.append("-" * 80)
    lines.append("")
    
    # Recommendation
    bullish = predictions_sorted[predictions_sorted["predicted_return_1d"] > 0]
    bearish = predictions_sorted[predictions_sorted["predicted_return_1d"] <= 0]
    
    lines.append("RECOMMENDED ACTIONS:")
    if len(bullish) > 0:
        lines.append(f"\n✅ BUY ({len(bullish)} stocks with positive predicted return):")
        for idx, row in bullish.head(5).iterrows():
            rank = bullish.index.get_loc(idx) + 1
            lines.append(f"  {rank}. {row['Kode Saham']:6s} | Pred: {row['predicted_return_1d']:+.2f}% | "
                        f"Allocate: Rp {row['capital_allocation']/1e6:.1f}M | "
                        f"Stop: {int(row['stop_loss']):,}")
    
    if len(bearish) > 0:
        lines.append(f"\n⏸️  WAIT ({len(bearish)} stocks with negative/zero predicted return):")
        for idx, row in bearish.iterrows():
            lines.append(f"  {row['Kode Saham']:6s} | Pred: {row['predicted_return_1d']:+.2f}% → SKIP")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("INTERPRETATION:")
    lines.append("  • Positive predicted return → ML model expects price increase tomorrow")
    lines.append("  • Direction accuracy shows historical success rate of up/down calls")
    lines.append("  • Higher direction accuracy (>55%) = more reliable predictions")
    lines.append("  • Use predictions as confirmation for mean-reversion + MA signals")
    
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines))
    print(f"Report written to {REPORT_FILE}")


def main():
    # Load data
    hist = pd.read_csv(HIST_FILE)
    hist["SourceDate"] = pd.to_datetime(hist["SourceDate"])
    positions = pd.read_csv(POSITIONS_FILE)
    
    print(f"Loaded {len(positions)} MA-filtered positions...")
    print("Engineering features...")
    
    # Engineer features
    data = engineer_features(hist)
    print(f"Feature engineering complete. Training KNN models...")
    
    # Train and predict
    predictions = predict_next_day(positions, data)
    
    if len(predictions) > 0:
        # Save outputs
        predictions.to_csv(OUTPUT_FILE, index=False)
        print(f"\nPredictions saved to {OUTPUT_FILE}")
        
        # Write report
        write_report(predictions)
        
        # Console summary
        print(f"\n{'='*60}")
        print(f"KNN PREDICTIONS SUMMARY")
        print(f"{'='*60}")
        bullish = predictions[predictions["predicted_return_1d"] > 0]
        print(f"Bullish predictions: {len(bullish)}/{len(predictions)}")
        
        if len(bullish) > 0:
            print(f"\nTop 3 ML-Recommended Buys:")
            sorted_pred = predictions.sort_values("predicted_return_1d", ascending=False)
            for idx, row in sorted_pred.head(3).iterrows():
                rank = sorted_pred.index.get_loc(idx) + 1
                print(f"  {rank}. {row['Kode Saham']:6s} | Pred: {row['predicted_return_1d']:+.2f}% | "
                      f"Dir Acc: {row['knn_direction_acc']:.1%}")
    else:
        print("\n⚠️  No predictions generated (insufficient data)")
        write_report(predictions)


if __name__ == "__main__":
    main()
