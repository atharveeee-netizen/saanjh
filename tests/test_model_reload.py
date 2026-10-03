import joblib
import pandas as pd
import numpy as np
import os

def test_model_reload():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    model_path = os.path.join(base_dir, 'artifacts', 'models', 'real_xgboost_model.pkl')
    
    print(f"Testing reload of {model_path}...")
    
    # 1. Reload Model
    model = joblib.load(model_path)
    
    # 2. Create a dummy single-row dataframe matching the feature schema
    dummy_input = pd.DataFrame({
        'hour': [18],
        'day_of_week': [3],
        'month': [10],
        'is_weekend': [0],
        'load_kw': [1.5],
        'load_lag_1': [1.4],
        'load_lag_4': [1.1],
        'load_lag_96': [1.3],
        'load_roll_mean_4': [1.35]
    })
    
    # 3. Predict
    prediction = model.predict(dummy_input)
    print(f"Successful Prediction: {prediction[0]:.4f} kW")
    
    assert not np.isnan(prediction[0]), "Prediction is NaN!"
    
    print("[SUCCESS] Model reload and inference test passed!")

if __name__ == "__main__":
    test_model_reload()
