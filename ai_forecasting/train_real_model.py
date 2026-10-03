import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import xgboost as xgb
import os
import joblib
import json
import time
import csv

def train_real_models():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    processed_path = os.path.join(base_dir, 'data', 'processed', 'real_load_dataset.csv')
    artifacts_dir = os.path.join(base_dir, 'artifacts', 'real_data')
    models_dir = os.path.join(base_dir, 'artifacts', 'models')
    results_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    
    os.makedirs(artifacts_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    
    if not os.path.exists(processed_path):
        print(f"Error: {processed_path} not found. Run preprocessing first.")
        return
        
    print("Loading preprocessed real dataset...")
    df = pd.read_csv(processed_path, index_col=0, parse_dates=True)
    
    # 1. CHRONOLOGICAL SPLIT
    n = len(df)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]
    
    features = ['hour', 'day_of_week', 'month', 'is_weekend', 
                'load_kw', 'load_lag_1', 'load_lag_4', 'load_lag_96', 'load_roll_mean_4']
    target = 'target_load_kw'
    
    X_train, y_train = train_df[features], train_df[target]
    X_val, y_val = val_df[features], val_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    # 2. Naive Baseline
    naive_preds = test_df['load_kw']
    naive_mae = mean_absolute_error(y_test, naive_preds)
    naive_rmse = np.sqrt(mean_squared_error(y_test, naive_preds))
    naive_r2 = r2_score(y_test, naive_preds)
    
    # 3. Train Random Forest (Fast baseline)
    start_time = time.time()
    rf_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    rf_train_time = time.time() - start_time
    rf_preds = rf_model.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))
    rf_r2 = r2_score(y_test, rf_preds)
    joblib.dump(rf_model, os.path.join(models_dir, 'real_baseline_model.pkl'))
    
    # 4. Train XGBoost strictly to convergence
    print("\n--- CPU TRAINING: XGBoost to Convergence ---")
    start_time = time.time()
    
    xgb_model = xgb.XGBRegressor(
        n_estimators=200, 
        learning_rate=0.05, 
        max_depth=6, 
        random_state=42,
        early_stopping_rounds=20,
        eval_metric='rmse'
    )
    
    xgb_model.fit(
        X_train, y_train, 
        eval_set=[(X_train, y_train), (X_val, y_val)], 
        verbose=True
    )
    xgb_train_time = time.time() - start_time
    
    best_iteration = xgb_model.best_iteration
    print(f"\n[CONVERGENCE REACHED] Best iteration was {best_iteration}.")
    
    # Save history to CSV
    history_csv = os.path.join(results_dir, 'xgboost_training_history.csv')
    evals = xgb_model.evals_result()
    train_rmse_list = evals['validation_0']['rmse']
    val_rmse_list = evals['validation_1']['rmse']
    
    with open(history_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['iteration', 'train_metric', 'validation_metric', 'best_validation_metric', 'improvement', 'rounds_without_improvement'])
        
        best_val = float('inf')
        no_improvement_streak = 0
        for i, (t_rmse, v_rmse) in enumerate(zip(train_rmse_list, val_rmse_list)):
            improvement = best_val - v_rmse
            if improvement > 0.0001:
                best_val = v_rmse
                no_improvement_streak = 0
            else:
                no_improvement_streak += 1
                
            writer.writerow([i, t_rmse, v_rmse, best_val, improvement, no_improvement_streak])
            
    print(f"Training history saved to {history_csv}")
    
    # Predict using the BEST iteration automatically handled by xgboost best_ntree_limit
    xgb_preds = xgb_model.predict(X_test)
    xgb_mae = mean_absolute_error(y_test, xgb_preds)
    xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_preds))
    xgb_r2 = r2_score(y_test, xgb_preds)
    print(f"XGBoost Test MAE: {xgb_mae:.4f} kW")
    
    joblib.dump(xgb_model, os.path.join(models_dir, 'real_xgboost_model.pkl'))
    
    # 5. Save Forecasts
    forecasts_df = pd.DataFrame({
        'timestamp': test_df.index,
        'actual_load': y_test.values,
        'baseline_prediction': naive_preds.values,
        'rf_prediction': rf_preds,
        'xgboost_prediction': xgb_preds,
        'xgboost_error': y_test.values - xgb_preds
    })
    forecasts_df.to_csv(os.path.join(artifacts_dir, 'forecasts.csv'), index=False)
    
    # 6. Save Model Comparison
    comparison = {
        "Naive Persistence": {"MAE": naive_mae, "RMSE": naive_rmse, "R2": naive_r2, "Training_Time_s": 0},
        "Random Forest": {"MAE": rf_mae, "RMSE": rf_rmse, "R2": rf_r2, "Training_Time_s": rf_train_time},
        "XGBoost": {"MAE": xgb_mae, "RMSE": xgb_rmse, "R2": xgb_r2, "Training_Time_s": xgb_train_time, "Best_Iteration": best_iteration}
    }
    with open(os.path.join(artifacts_dir, 'model_comparison.json'), 'w') as f:
        json.dump(comparison, f, indent=4)
        
    print("\nPipeline complete. Models and metrics saved.")

if __name__ == "__main__":
    train_real_models()
