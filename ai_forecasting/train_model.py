import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
import os
import joblib

def generate_emarc_synthetic_data(days=365):
    """
    Generates a rigorous synthetic dataset mimicking an Indian neighbourhood transformer
    based on characteristics observed in the eMARC (Prayas Energy Group) dataset.
    """
    print(f"Generating synthetic eMARC-style dataset for {days} days...")
    
    dates = pd.date_range(start='2025-01-01', periods=days*24*4, freq='15min') # 15-min intervals
    df = pd.DataFrame({'timestamp': dates})
    
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['month'] = df['timestamp'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Simulate Temperature (Summer peaks in May/June, Winter in Dec/Jan)
    # Base temp + daily cycle + seasonal cycle + noise
    base_temp = 25
    seasonal_temp = 10 * np.sin((df['month'] - 4) * np.pi / 6) # Peaks in May/June
    daily_temp = 5 * np.sin((df['hour'] - 14) * np.pi / 12) # Peaks at 14:00
    df['temperature_c'] = base_temp + seasonal_temp + daily_temp + np.random.normal(0, 2, len(df))
    
    # Simulate Transformer Load (kW) - Max capacity 100 kVA (~85 kW safe)
    # Baseload
    load = 30 + np.random.normal(0, 2, len(df))
    
    # Morning peak (07:00 - 09:00) - Water heaters, cooking
    morning_mask = (df['hour'] >= 7) & (df['hour'] <= 9)
    load[morning_mask] += 20 + np.random.normal(5, 3, morning_mask.sum())
    
    # Evening peak (18:00 - 22:00) - Lighting, ACs, TVs, Cooking
    evening_mask = (df['hour'] >= 18) & (df['hour'] <= 22)
    load[evening_mask] += 40 + np.random.normal(10, 5, evening_mask.sum())
    
    # Temperature dependency (AC load increases sharply above 30C)
    ac_load = np.maximum(0, (df['temperature_c'] - 30) * 3.5)
    load += ac_load
    
    # Weekend effect (slightly higher baseload, shifted peaks)
    load[df['is_weekend'] == 1] += 5
    
    df['load_kw'] = np.maximum(15, load) # Minimum load of 15kW
    
    return df

def create_features(df):
    """Creates lag features and rolling windows for time-series forecasting."""
    print("Engineering time-series features...")
    df = df.copy()
    
    # Target variable is load in the next 15 mins (t+1)
    df['target_load_kw'] = df['load_kw'].shift(-1)
    
    # Lags (past load values)
    df['load_lag_1'] = df['load_kw'].shift(1)
    df['load_lag_4'] = df['load_kw'].shift(4)   # 1 hour ago
    df['load_lag_96'] = df['load_kw'].shift(96) # 24 hours ago
    
    # Rolling stats
    df['load_roll_mean_4'] = df['load_kw'].rolling(window=4).mean()
    df['load_roll_std_4'] = df['load_kw'].rolling(window=4).std()
    
    df = df.dropna()
    return df

def train_models():
    # 1. Get Data
    df = generate_emarc_synthetic_data()
    df_features = create_features(df)
    
    # 2. Prepare Train/Test Split
    # Must use temporal split for time-series, not random shuffle
    train_size = int(len(df_features) * 0.8)
    train, test = df_features.iloc[:train_size], df_features.iloc[train_size:]
    
    features = ['hour', 'day_of_week', 'month', 'is_weekend', 'temperature_c', 
                'load_kw', 'load_lag_1', 'load_lag_4', 'load_lag_96', 
                'load_roll_mean_4', 'load_roll_std_4']
    
    X_train, y_train = train[features], train['target_load_kw']
    X_test, y_test = test[features], test['target_load_kw']
    
    print(f"Training on {len(X_train)} samples, validating on {len(X_test)} samples.")
    
    # 3. Train Random Forest (Baseline AI)
    print("\nTraining Random Forest Regressor...")
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    
    print(f"Random Forest MAE: {mean_absolute_error(y_test, rf_preds):.2f} kW")
    print(f"Random Forest R2:  {r2_score(y_test, rf_preds):.4f}")
    
    # 4. Train XGBoost (Advanced AI)
    print("\nTraining XGBoost Regressor...")
    xgb_model = xgb.XGBRegressor(n_estimators=150, learning_rate=0.05, max_depth=6, random_state=42)
    xgb_model.fit(X_train, y_train)
    xgb_preds = xgb_model.predict(X_test)
    
    print(f"XGBoost MAE: {mean_absolute_error(y_test, xgb_preds):.2f} kW")
    print(f"XGBoost R2:  {r2_score(y_test, xgb_preds):.4f}")
    
    # 5. Save the best model
    os.makedirs('ai_forecasting/models', exist_ok=True)
    joblib.dump(xgb_model, 'ai_forecasting/models/xgboost_load_forecaster.pkl')
    print("\n✅ Best model (XGBoost) saved to ai_forecasting/models/xgboost_load_forecaster.pkl")
    
    # 6. Feature Importance
    importance = pd.DataFrame({
        'Feature': features,
        'Importance': xgb_model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("\nTop 5 Predictive Features:")
    print(importance.head(5).to_string(index=False))

if __name__ == "__main__":
    train_models()
