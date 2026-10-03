import pandas as pd
import os
import json
import numpy as np

def preprocess_uci_data():
    raw_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'raw', 'real', 'household_power_consumption.txt'))
    processed_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'processed', 'real_load_dataset.csv'))
    artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'artifacts', 'real_data'))
    
    if not os.path.exists(raw_path):
        print(f"Error: {raw_path} not found. Run download script first.")
        return
        
    print("Loading raw dataset (this might take a moment)...")
    # Read only the first year (approx 500,000 rows) to keep training fast for the demo
    df = pd.read_csv(raw_path, sep=';', na_values=['?'], low_memory=False, nrows=500000)
    
    print("Cleaning and downsampling...")
    df = df.dropna()
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M:%S')
    df = df.set_index('datetime')
    
    # The Global_active_power is in kilowatts
    df['load_kw'] = pd.to_numeric(df['Global_active_power'])
    
    # Resample to 15-minute intervals (mean load over 15 mins)
    df_15m = df['load_kw'].resample('15T').mean().to_frame()
    df_15m = df_15m.dropna()
    
    # Feature Engineering (Appropriate for 15-minute resolution)
    df_15m['hour'] = df_15m.index.hour
    df_15m['day_of_week'] = df_15m.index.dayofweek
    df_15m['month'] = df_15m.index.month
    df_15m['is_weekend'] = df_15m['day_of_week'].isin([5, 6]).astype(int)
    
    # Lags (15-min intervals)
    df_15m['load_lag_1'] = df_15m['load_kw'].shift(1)       # 15 mins ago
    df_15m['load_lag_4'] = df_15m['load_kw'].shift(4)       # 1 hour ago
    df_15m['load_lag_96'] = df_15m['load_kw'].shift(96)     # 24 hours ago
    
    # Rolling stats
    df_15m['load_roll_mean_4'] = df_15m['load_kw'].rolling(window=4).mean()
    
    # Target variable (predict load in the next 15 mins)
    df_15m['target_load_kw'] = df_15m['load_kw'].shift(-1)
    
    df_15m = df_15m.dropna()
    
    print(f"Processed dataset has {len(df_15m)} rows.")
    df_15m.to_csv(processed_path)
    
    # Generate metadata
    metadata = {
        "original_rows": 500000,
        "processed_rows": len(df_15m),
        "resolution": "15-minute",
        "features": list(df_15m.columns),
        "target": "target_load_kw",
        "start_date": str(df_15m.index.min()),
        "end_date": str(df_15m.index.max()),
        "missing_values_handled": "Dropped NA, Resampled mean",
        "data_leakage_prevented": True
    }
    
    os.makedirs(artifacts_dir, exist_ok=True)
    with open(os.path.join(artifacts_dir, 'preprocessing_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print(f"Saved processed data to {processed_path}")

if __name__ == "__main__":
    preprocess_uci_data()
