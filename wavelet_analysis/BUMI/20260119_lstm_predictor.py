"""
LSTM Neural Network for BUMI Stock Price Prediction
Predicts 1-5 day forward returns using historical price patterns
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import warnings
warnings.filterwarnings('ignore')

tf.get_logger().setLevel('ERROR')


class LSTMPricePredictor:
    """LSTM model for stock price prediction"""
    
    def __init__(self, ticker='BUMI', csv_file='data/histories/ringkasan_histories_combined.csv', lookback_days=5):
        self.ticker = ticker
        self.csv_file = csv_file
        self.lookback_days = lookback_days  # How many days to look back for pattern
        self.prices = None
        self.dates = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model = None
        self.history = None
        
    def load_data(self):
        """Load stock data"""
        df = pd.read_csv(self.csv_file)
        ticker_data = df[df['Kode Saham'] == self.ticker].copy()
        
        if len(ticker_data) == 0:
            raise ValueError(f"No data found for {self.ticker}")
        
        ticker_data['SourceDate'] = pd.to_datetime(ticker_data['SourceDate'])
        ticker_data = ticker_data.sort_values('SourceDate').reset_index(drop=True)
        
        self.prices = ticker_data['Penutupan'].values.astype(float)
        self.dates = ticker_data['SourceDate'].values
        
        print(f"✓ Loaded {len(self.prices)} trading days for {self.ticker}")
        return self.prices, self.dates
    
    def prepare_data(self):
        """
        Prepare data for LSTM training
        Converts sequential prices into (lookback, 1) shaped sequences
        """
        # Normalize prices to 0-1 range
        scaled_prices = self.scaler.fit_transform(self.prices.reshape(-1, 1))
        
        X, y = [], []
        for i in range(len(scaled_prices) - self.lookback_days):
            X.append(scaled_prices[i:i + self.lookback_days])
            y.append(scaled_prices[i + self.lookback_days])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split: use 70% for training, 30% for testing
        split_idx = int(len(X) * 0.7)
        
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        print(f"✓ Data prepared: {len(X_train)} training samples, {len(X_test)} test samples")
        print(f"  Lookback window: {self.lookback_days} days")
        print(f"  Sequence shape: {X_train.shape}")
        
        return X_train, X_test, y_train, y_test
    
    def build_model(self, lstm_units=32, dropout_rate=0.2):
        """
        Build LSTM neural network
        
        Architecture:
        - LSTM layer 1: 32 units (learns temporal patterns)
        - Dropout: 0.2 (prevents overfitting)
        - LSTM layer 2: 16 units (refines patterns)
        - Dense: 8 units (combines features)
        - Output: 1 unit (price prediction)
        """
        self.model = Sequential([
            LSTM(lstm_units, return_sequences=True, input_shape=(self.lookback_days, 1)),
            Dropout(dropout_rate),
            LSTM(lstm_units // 2, return_sequences=False),
            Dropout(dropout_rate),
            Dense(8, activation='relu'),
            Dense(1, activation='sigmoid')  # sigmoid: output between 0-1 (matches normalized data)
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        print(f"✓ LSTM model built:")
        self.model.summary()
        
        return self.model
    
    def train_model(self, X_train, X_test, y_train, y_test, epochs=50, batch_size=2):
        """
        Train LSTM model
        
        Early stopping: Stop if validation loss doesn't improve
        """
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=0
        )
        
        print(f"✓ Model trained for {len(self.history.history['loss'])} epochs")
        return self.history
    
    def evaluate_model(self, X_test, y_test):
        """
        Evaluate model performance on test set
        """
        y_pred = self.model.predict(X_test, verbose=0)
        
        # Inverse scale predictions and actuals back to original price range
        y_test_original = self.scaler.inverse_transform(y_test.reshape(-1, 1))
        y_pred_original = self.scaler.inverse_transform(y_pred)
        
        mse = mean_squared_error(y_test_original, y_pred_original)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test_original, y_pred_original)
        mape = mean_absolute_percentage_error(y_test_original, y_pred_original)
        
        metrics = {
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape,
            'MSE': mse
        }
        
        print(f"\n✓ Model Performance on Test Set:")
        print(f"  RMSE: {rmse:.4f} IDR")
        print(f"  MAE:  {mae:.4f} IDR")
        print(f"  MAPE: {mape:.4f} ({mape*100:.2f}%)")
        
        return metrics, y_pred_original, y_test_original
    
    def predict_next_prices(self, steps=5):
        """
        Predict next N days of prices
        
        Uses the last lookback_days prices as context
        """
        last_sequence = self.scaler.transform(self.prices[-self.lookback_days:].reshape(-1, 1))
        last_sequence = last_sequence.reshape(1, self.lookback_days, 1)
        
        predictions = []
        
        for _ in range(steps):
            # Predict next price
            next_pred = self.model.predict(last_sequence, verbose=0)[0, 0]
            predictions.append(next_pred)
            
            # Update sequence: remove first element, add new prediction
            last_sequence = np.append(last_sequence[:, 1:, :], 
                                     [[[next_pred]]], axis=1)
        
        # Inverse scale predictions
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = self.scaler.inverse_transform(predictions)
        
        print(f"\n✓ Generated {steps}-day price forecast")
        return predictions
    
    def get_forecast_report(self):
        """Generate forecast report with statistics"""
        current_price = self.prices[-1]
        predictions = self.predict_next_prices(steps=5)
        
        changes = ((predictions - current_price) / current_price * 100).flatten()
        
        report = {
            'current_price': current_price,
            'predictions': predictions.flatten(),
            'price_changes_pct': changes,
            'average_prediction': np.mean(predictions),
            'trend': 'UP' if predictions[-1] > current_price else 'DOWN',
            'confidence': 'HIGH' if np.std(changes) < 5 else 'MEDIUM' if np.std(changes) < 10 else 'LOW'
        }
        
        return report
    
    def print_forecast_report(self):
        """Print forecast report"""
        report = self.get_forecast_report()
        
        print("\n" + "="*60)
        print(f"LSTM PRICE FORECAST: {self.ticker}")
        print("="*60)
        print(f"Current Price: {report['current_price']:.0f} IDR")
        print(f"Forecast Direction: {report['trend']}")
        print(f"Prediction Confidence: {report['confidence']}")
        
        print(f"\n5-Day Price Forecast:")
        for i, (pred, change) in enumerate(zip(report['predictions'], report['price_changes_pct']), 1):
            print(f"  Day +{i}: {pred:.0f} IDR ({change:+.2f}%)")
        
        print(f"\nForecast Statistics:")
        print(f"  Average Predicted Price: {report['average_prediction']:.0f} IDR")
        print(f"  Price Change Volatility: {np.std(report['price_changes_pct']):.2f}%")
        print("="*60)


def main():
    # Initialize predictor
    predictor = LSTMPricePredictor('BUMI', lookback_days=5)
    
    # Load data
    prices, dates = predictor.load_data()
    
    # Prepare training/test data
    X_train, X_test, y_train, y_test = predictor.prepare_data()
    
    # Build model
    predictor.build_model(lstm_units=32, dropout_rate=0.2)
    
    # Train model
    predictor.train_model(X_train, X_test, y_train, y_test, epochs=50, batch_size=2)
    
    # Evaluate model
    metrics, y_pred, y_test_original = predictor.evaluate_model(X_test, y_test)
    
    # Generate forecast
    predictor.print_forecast_report()
    
    # Visualization
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Training History - Loss
    axes[0, 0].plot(predictor.history.history['loss'], label='Training Loss', linewidth=2)
    axes[0, 0].plot(predictor.history.history['val_loss'], label='Validation Loss', linewidth=2)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss (MSE)')
    axes[0, 0].set_title('LSTM Model Training History')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Training History - MAE
    axes[0, 1].plot(predictor.history.history['mae'], label='Training MAE', linewidth=2)
    axes[0, 1].plot(predictor.history.history['val_mae'], label='Validation MAE', linewidth=2)
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('MAE (IDR)')
    axes[0, 1].set_title('Mean Absolute Error During Training')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Test Set Predictions vs Actual
    axes[1, 0].plot(y_test_original, 'o-', label='Actual Price', linewidth=2, markersize=6)
    axes[1, 0].plot(y_pred, 's-', label='LSTM Prediction', linewidth=2, markersize=5, alpha=0.7)
    axes[1, 0].set_xlabel('Test Sample')
    axes[1, 0].set_ylabel('Price (IDR)')
    axes[1, 0].set_title('Test Set: Actual vs Predicted Prices')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: 5-Day Forecast
    current_price = predictor.prices[-1]
    forecast = predictor.predict_next_prices(steps=5).flatten()
    
    # Simple chart: show last 8 historical + 5 forecasted
    last_n = min(8, len(predictor.prices))
    x = np.arange(last_n + 5)
    all_data = np.concatenate([predictor.prices[-last_n:], forecast])
    
    axes[1, 1].plot(x[:last_n], predictor.prices[-last_n:], 'o-', label='Historical Price', linewidth=2, markersize=6, color='blue')
    axes[1, 1].plot(x[last_n-1:], all_data[last_n-1:], 's--', label='LSTM Forecast', linewidth=2, markersize=6, color='orange')
    axes[1, 1].axvline(last_n-0.5, color='red', linestyle=':', alpha=0.5, linewidth=1.5)
    axes[1, 1].set_xlabel('Days')
    axes[1, 1].set_ylabel('Price (IDR)')
    axes[1, 1].set_title('5-Day Price Forecast')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('wavelet_analysis/BUMI/lstm_prediction.png', dpi=300, bbox_inches='tight')
    print("\n✓ Visualization saved: wavelet_analysis/BUMI/lstm_prediction.png")
    
    return predictor


if __name__ == '__main__':
    predictor = main()
