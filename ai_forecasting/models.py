"""Day-ahead probabilistic forecasters of DT net demand (96 x 15-minute blocks).

Every model exposes ``forecast(df, day) -> array (3, 96)`` of P10, P50, P90 for day
``day`` using only data before that day's midnight.

* SeasonalNaive: yesterday's profile (P50), with P10/P90 from the spread of the last
  seven days at the same block (a standard climatology band).
* WeeklyNaive: the same weekday last week.
* XGBoostQuantile: gradient-boosted quantile regression on calendar, weather and lag
  features, trained on the first part of the year (Indian-calibrated simulated data).
* Chronos: zero-shot time-series foundation model (see ChronosForecaster).
"""
import numpy as np
import pandas as pd

QUANTILES = (0.1, 0.5, 0.9)
STEPS = 96


class SeasonalNaive:
    name = "seasonal_naive"

    def forecast(self, df, day):
        m = df["net_kw"].to_numpy().reshape(-1, STEPS)
        hist = m[max(0, day - 7):day]
        p50 = m[day - 1]
        lo = np.quantile(hist, 0.1, axis=0)
        hi = np.quantile(hist, 0.9, axis=0)
        # Centre the band on yesterday's profile.
        med = np.median(hist, axis=0)
        return np.vstack([p50 + (lo - med), p50, p50 + (hi - med)])


class WeeklyNaive:
    name = "weekly_naive"

    def forecast(self, df, day):
        m = df["net_kw"].to_numpy().reshape(-1, STEPS)
        p50 = m[day - 7]
        return np.vstack([p50, p50, p50])


def _features(df):
    f = pd.DataFrame({
        "block": df["timestamp"].dt.hour * 4 + df["timestamp"].dt.minute // 15,
        "dow": df["timestamp"].dt.dayofweek,
        "doy": df["timestamp"].dt.dayofyear,
        "temp_c": df["temp_c"],
        "solar": df["solar"],
        "cloudiness": df["cloudiness"],
        "lag_96": df["net_kw"].shift(96),
        "lag_192": df["net_kw"].shift(192),
        "lag_672": df["net_kw"].shift(672),
        "day_mean_lag_96": df["net_kw"].shift(96).rolling(96).mean(),
        "temp_max_day": df.groupby(df["timestamp"].dt.date)["temp_c"].transform("max"),
    })
    return f


class XGBoostQuantile:
    name = "xgboost_quantile"

    def __init__(self, train_days=180):
        self.train_days = train_days
        self.models = None

    def fit(self, df):
        import xgboost as xgb
        X = _features(df)
        y = df["net_kw"]
        n = self.train_days * STEPS
        mask = X.notna().all(axis=1).to_numpy()
        mask[n:] = False
        self.models = {}
        for q in QUANTILES:
            m = xgb.XGBRegressor(objective="reg:quantileerror", quantile_alpha=q, n_estimators=300,
                                 max_depth=5, learning_rate=0.05, subsample=0.8, random_state=0)
            m.fit(X[mask], y[mask])
            self.models[q] = m
        self._X = X
        return self

    def forecast(self, df, day):
        X = self._X.iloc[day * STEPS:(day + 1) * STEPS]
        out = np.vstack([self.models[q].predict(X) for q in QUANTILES])
        return np.sort(out, axis=0)


class ChronosForecaster:
    """Zero-shot Chronos. Prefers Chronos-2 (supports covariates); falls back to
    Chronos-Bolt if Chronos-2 is not available in the installed package."""

    def __init__(self, context_days=28, model_id=None, device="cpu"):
        import torch
        from chronos import BaseChronosPipeline
        self.context = context_days * STEPS
        self.torch = torch
        self.variant = None
        self.pipeline = None
        tried = [model_id] if model_id else ["amazon/chronos-2", "amazon/chronos-bolt-small"]
        errors = []
        for mid in tried:
            try:
                self.pipeline = BaseChronosPipeline.from_pretrained(mid, device_map=device,
                                                                     torch_dtype=torch.float32)
                self.variant = mid
                break
            except Exception as exc:  # model not available for this package version
                errors.append(f"{mid}: {exc}")
        if self.pipeline is None:
            raise RuntimeError("No Chronos model could be loaded: " + " | ".join(errors))
        self.name = "chronos2" if "chronos-2" in self.variant else "chronos_bolt"
        self.uses_covariates = False

    def forecast_batch(self, df, days):
        """Forecast several days in one batch. Returns {day: (3, 96)}."""
        y = df["net_kw"].to_numpy(dtype=np.float32)
        out = {}
        if self.name == "chronos2":
            inputs = []
            for d in days:
                s = max(0, d * STEPS - self.context)
                e = d * STEPS
                inputs.append({
                    "target": y[s:e],
                    "past_covariates": {"temp_c": df["temp_c"].to_numpy(np.float32)[s:e],
                                        "solar": df["solar"].to_numpy(np.float32)[s:e]},
                    "future_covariates": {"temp_c": df["temp_c"].to_numpy(np.float32)[e:e + STEPS],
                                          "solar": df["solar"].to_numpy(np.float32)[e:e + STEPS]},
                })
            try:
                preds = self.pipeline.predict_quantiles(inputs, prediction_length=STEPS,
                                                        quantile_levels=list(QUANTILES))
                self.uses_covariates = True
            except Exception:
                ctx = [self.torch.tensor(i["target"]) for i in inputs]
                preds = self.pipeline.predict_quantiles(ctx, prediction_length=STEPS,
                                                        quantile_levels=list(QUANTILES))
            q = preds[0]
            for k, d in enumerate(days):
                arr = q[k]
                arr = arr.numpy() if hasattr(arr, "numpy") else np.asarray(arr)
                arr = np.squeeze(arr)              # (96, 3)
                out[d] = np.sort(arr.T, axis=0)
        else:
            ctx = [self.torch.tensor(y[max(0, d * STEPS - self.context):d * STEPS]) for d in days]
            q, _ = self.pipeline.predict_quantiles(ctx, prediction_length=STEPS,
                                                   quantile_levels=list(QUANTILES))
            for k, d in enumerate(days):
                out[d] = np.sort(q[k].numpy().T, axis=0)
        return out
