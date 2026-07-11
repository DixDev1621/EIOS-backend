"""
Environmental forecasting + explainable AI.

For each district, this module:
  1. Pulls real historical hourly PM2.5/weather data (Open-Meteo archive)
  2. Builds lag/rolling/time-of-day features
  3. Trains a small XGBoost regressor to predict PM2.5 24h ahead
  4. Produces a forecast + SHAP-based feature attributions ("reasons")
  5. Derives a confidence score from the model's cross-validated error,
     not a hardcoded number

Models are cached in-process per district for CACHE_TTL (see core.cache)
so we don't retrain on every request, but they are always trained on
real fetched data -- there is no pre-baked/fake model shipped with the
repo. On first request per district there will be a short (~1-3s)
training delay; subsequent requests are served from cache.
"""

import logging

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error

from app.core.cache import cached
from app.core.config import get_settings
from app.services.open_meteo_service import fetch_historical_air_quality, fetch_historical_weather
from app.services.aqi_calculator import compute_aqi

logger = logging.getLogger(__name__)

FORECAST_HORIZON_HOURS = 24
LAGS = [1, 3, 6, 12, 24, 48]
ROLLING_WINDOWS = [6, 24]


def _build_feature_frame(aq_hourly: dict, wx_hourly: dict) -> pd.DataFrame:
    df = pd.DataFrame({
        "time": pd.to_datetime(aq_hourly["time"]),
        "pm25": aq_hourly.get("pm2_5"),
        "pm10": aq_hourly.get("pm10"),
        "no2": aq_hourly.get("nitrogen_dioxide"),
        "so2": aq_hourly.get("sulphur_dioxide"),
        "co": aq_hourly.get("carbon_monoxide"),
        "o3": aq_hourly.get("ozone"),
    })
    wx_df = pd.DataFrame({
        "time": pd.to_datetime(wx_hourly["time"]),
        "temp": wx_hourly.get("temperature_2m"),
        "humidity": wx_hourly.get("relative_humidity_2m"),
        "wind_speed": wx_hourly.get("wind_speed_10m"),
        "precipitation": wx_hourly.get("precipitation"),
    })
    df = df.merge(wx_df, on="time", how="left")
    df = df.sort_values("time").reset_index(drop=True)
    df["hour"] = df["time"].dt.hour
    df["day_of_week"] = df["time"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    for lag in LAGS:
        df[f"pm25_lag_{lag}h"] = df["pm25"].shift(lag)
    for window in ROLLING_WINDOWS:
        df[f"pm25_roll_mean_{window}h"] = df["pm25"].rolling(window).mean()

    df["target_pm25"] = df["pm25"].shift(-FORECAST_HORIZON_HOURS)
    return df


FEATURE_COLUMNS = (
    ["pm10", "no2", "so2", "co", "o3", "temp", "humidity", "wind_speed", "precipitation",
     "hour", "day_of_week", "is_weekend"]
    + [f"pm25_lag_{l}h" for l in LAGS]
    + [f"pm25_roll_mean_{w}h" for w in ROLLING_WINDOWS]
)


async def _train_district_model(lat: float, lon: float) -> dict:
    aq_hist = await fetch_historical_air_quality(lat, lon, days_back=60)
    wx_hist = await fetch_historical_weather(lat, lon, days_back=60)

    df = _build_feature_frame(aq_hist["hourly"], wx_hist["hourly"])
    model_df = df.dropna(subset=FEATURE_COLUMNS + ["target_pm25"])

    if len(model_df) < 100:
        return {"status": "insufficient_data", "rows_available": len(model_df)}

    X = model_df[FEATURE_COLUMNS]
    y = model_df["target_pm25"]

    # Time-series cross-validation to get an honest out-of-sample error,
    # which becomes the basis of the confidence score below.
    tscv = TimeSeriesSplit(n_splits=4)
    fold_errors = []
    for train_idx, test_idx in tscv.split(X):
        fold_model = xgb.XGBRegressor(
            n_estimators=150, max_depth=4, learning_rate=0.08,
            subsample=0.85, colsample_bytree=0.85, random_state=42,
        )
        fold_model.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = fold_model.predict(X.iloc[test_idx])
        fold_errors.append(mean_absolute_error(y.iloc[test_idx], preds))

    mean_mae = float(np.mean(fold_errors))

    # Final model trained on all available data
    final_model = xgb.XGBRegressor(
        n_estimators=150, max_depth=4, learning_rate=0.08,
        subsample=0.85, colsample_bytree=0.85, random_state=42,
    )
    final_model.fit(X, y)

    explainer = shap.TreeExplainer(final_model)

    latest_row = df.dropna(subset=FEATURE_COLUMNS).iloc[[-1]][FEATURE_COLUMNS]
    prediction = float(final_model.predict(latest_row)[0])
    shap_values = explainer.shap_values(latest_row)[0]

    # Confidence: derived from cross-validated MAE relative to the
    # observed PM2.5 range at this location -- tighter relative error
    # means higher confidence. Clamped to [0.35, 0.97] so the model
    # never claims near-certainty or near-zero usefulness.
    pm25_range = max(float(y.max() - y.min()), 1.0)
    relative_error = mean_mae / pm25_range
    confidence = float(np.clip(1 - relative_error, 0.35, 0.97))

    attributions = sorted(
        zip(FEATURE_COLUMNS, shap_values.tolist()),
        key=lambda pair: abs(pair[1]),
        reverse=True,
    )[:5]

    return {
        "status": "ok",
        "prediction_pm25": round(prediction, 1),
        "horizon_hours": FORECAST_HORIZON_HOURS,
        "cross_validated_mae": round(mean_mae, 2),
        "confidence": round(confidence, 2),
        "training_rows": len(model_df),
        "top_factors": [
            {"feature": _humanize_feature(name), "impact": round(value, 2)}
            for name, value in attributions
        ],
        "latest_observed_pm25": round(float(df["pm25"].iloc[-1]), 1) if pd.notna(df["pm25"].iloc[-1]) else None,
    }


def _humanize_feature(name: str) -> str:
    mapping = {
        "wind_speed": "Wind speed",
        "humidity": "Relative humidity",
        "temp": "Temperature",
        "precipitation": "Recent precipitation",
        "hour": "Time of day",
        "day_of_week": "Day of week",
        "is_weekend": "Weekend effect",
        "pm10": "PM10 level",
        "no2": "NO2 level",
        "so2": "SO2 level",
        "co": "CO level",
        "o3": "Ozone level",
    }
    if name in mapping:
        return mapping[name]
    if name.startswith("pm25_lag_"):
        return f"PM2.5 {name.split('_')[-1]} ago"
    if name.startswith("pm25_roll_mean_"):
        return f"PM2.5 {name.split('_')[-1]} average"
    return name


async def get_district_forecast(lat: float, lon: float) -> dict:
    settings = get_settings()
    key = f"forecast:{lat:.3f}:{lon:.3f}"
    result = await cached(key, settings.CACHE_TTL_SECONDS, lambda: _train_district_model(lat, lon))

    if result.get("status") != "ok":
        return result

    aqi_result = compute_aqi(pm25=result["prediction_pm25"])
    result["predicted_aqi"] = aqi_result.aqi if aqi_result else None
    result["predicted_category"] = aqi_result.category if aqi_result else None
    return result
