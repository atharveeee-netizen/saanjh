"""One-step-ahead load forecast used by the evening peak case.

The XGBoost model was trained on the UCI household dataset (one French household,
15-minute resolution). It predicts the next 15-minute block from the current one. The
feeder total is divided by the number of homes to match the model's single-household
domain, then multiplied back. This is a methodology demonstration, not an Indian-trained
forecaster; Prompt 6 replaces it with a day-ahead probabilistic deficit forecast.
"""
import joblib
import numpy as np
import pandas as pd


class OneStepLoadForecaster:
    FEATURES = ["hour", "day_of_week", "month", "is_weekend", "load_kw",
                "load_lag_1", "load_lag_4", "load_lag_96", "load_roll_mean_4"]

    def __init__(self, model_path, num_homes):
        self.model = joblib.load(model_path)
        self.num_homes = num_homes
        self.history = []   # per-home average kW for each completed step

    def observe(self, total_kw):
        self.history.append(total_kw / self.num_homes)

    def predict(self, hour_of_last_obs, day_of_week=2, month=10):
        """Forecast the next step's feeder total from observations so far."""
        h = self.history
        if not h:
            return None
        def lag(k):
            return h[-1 - k] if len(h) > k else h[0]
        row = pd.DataFrame([{
            "hour": int(hour_of_last_obs) % 24,
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": int(day_of_week >= 5),
            "load_kw": h[-1],
            "load_lag_1": lag(1),
            "load_lag_4": lag(4),
            "load_lag_96": lag(96),
            "load_roll_mean_4": float(np.mean(h[-4:])),
        }], columns=self.FEATURES)
        return float(self.model.predict(row)[0]) * self.num_homes
