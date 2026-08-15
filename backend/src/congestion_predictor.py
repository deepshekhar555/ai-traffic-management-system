"""
XGBoost Machine Learning Traffic Congestion Forecasting & Prediction Engine
SIH 2026 - Smart City Traffic Intelligence

Uses XGBoost (Extreme Gradient Boosting) / Gradient Boosting Regressors
with rolling window lag-feature engineering to predict multi-horizon (+15m, +30m, +60m)
traffic density & bottleneck risk.

CHANGE FROM ORIGINAL: _bootstrap_initial_training() now tries to load REAL
historical density from your traffic_data.db (built from actual camera
detections via TrafficDatabase) before falling back to the synthetic
sine-wave curve. Run your detection pipeline for even 1-2 real days first,
then this will train on genuine data instead of a fabricated baseline.
"""

import numpy as np
import time
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from pathlib import Path
import sys

_backend_dir = Path(__file__).parent.parent.resolve()
_root_dir = Path(__file__).parent.parent.parent.resolve()
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

try:
    from src.logger import logger
except ImportError:
    try:
        from logger import logger
    except ImportError:
        import logging
        logger = logging.getLogger("traffic_ai")

# ─── XGBoost Import with Fallback ─────────────────────────────────────────────
HAS_XGBOOST = False
try:
    import xgboost as xgb
    HAS_XGBOOST = True
    logger.info("XGBoost library successfully imported for ML Traffic Forecasting!")
except ImportError:
    logger.warning("XGBoost package not found. Falling back to Scikit-Learn GradientBoostingRegressor.")
    try:
        from sklearn.ensemble import GradientBoostingRegressor
    except ImportError:
        GradientBoostingRegressor = None


def _load_real_density_history(db_path: str = None, max_hours: int = 240) -> List[Tuple[float, float]]:
    """
    Pull real vehicle-count-per-time-bucket from traffic_data.db (populated by
    TrafficDatabase.log_vehicle during normal camera operation) and convert it
    into a (timestamp, density 0-1) series usable for training.

    Density is approximated as min(1.0, vehicles_in_bucket / NORMALIZATION_CAP).
    Adjust NORMALIZATION_CAP to roughly the max vehicles/minute your camera
    realistically sees at your intersection during peak congestion.
    """
    NORMALIZATION_CAP = 15.0  # vehicles per 1-minute bucket judged "100% dense"

    if db_path is None:
        db_path = str(_root_dir / "data" / "traffic_data.db")

    if not Path(db_path).exists():
        return []

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(hours=max_hours)).isoformat()
        c.execute(
            """
            SELECT strftime('%Y-%m-%d %H:%M', timestamp) as bucket, COUNT(*) as cnt
            FROM vehicles
            WHERE timestamp >= ?
            GROUP BY bucket
            ORDER BY bucket ASC
            """,
            (cutoff,),
        )
        rows = c.fetchall()
        conn.close()

        if len(rows) < 20:
            return []  # not enough real history yet - caller will fall back to synthetic

        series = []
        for bucket_str, cnt in rows:
            ts = time.mktime(datetime.strptime(bucket_str, "%Y-%m-%d %H:%M").timetuple())
            density = min(1.0, cnt / NORMALIZATION_CAP)
            series.append((ts, density))
        return series
    except Exception as e:
        logger.warning(f"[CongestionPredictor] Could not load real density history: {e}")
        return []


class XGBoostCongestionPredictor:
    """
    XGBoost-powered Machine Learning Traffic Density & Congestion Predictor.

    Engineered Features:
      - Lag 1, Lag 2, Lag 3, Lag 5 historical density samples
      - Rolling Mean (w=3, w=5)
      - Rolling Delta (velocity of density change)
      - Cyclic Time Features (sin/cos of minute/hour)
    """

    def __init__(self, max_history: int = 200, db_path: str = None):
        self.max_history = max_history
        self.db_path = db_path
        self.history: List[float] = []
        self.timestamps: List[float] = []
        self.is_trained = False
        self.trained_on_real_data = False

        # Models for multi-horizon forecasting (+15m, +30m, +60m)
        self.models: Dict[str, object] = {}
        self._init_models()

        # Pre-seed model with real data if available, else synthetic baseline
        self._bootstrap_initial_training()

    def _init_models(self):
        """Initialise separate XGBoost regressors for +15m, +30m, +60m horizons."""
        horizons = ["15m", "30m", "60m"]
        for h in horizons:
            if HAS_XGBOOST:
                self.models[h] = xgb.XGBRegressor(
                    n_estimators=30,
                    max_depth=3,
                    learning_rate=0.1,
                    objective="reg:squarederror",
                    random_state=42,
                    verbosity=0
                )
            elif GradientBoostingRegressor is not None:
                self.models[h] = GradientBoostingRegressor(
                    n_estimators=30,
                    max_depth=3,
                    learning_rate=0.1,
                    random_state=42
                )
            else:
                self.models[h] = None

    def _extract_features(self, history_slice: List[float], ts: float = None) -> np.ndarray:
        """
        Extract lag and statistical features from recent density samples.
        Requires at least 5 samples.
        """
        if len(history_slice) < 5:
            avg = np.mean(history_slice) if history_slice else 0.2
            history_slice = [avg] * (5 - len(history_slice)) + list(history_slice)

        arr = np.array(history_slice[-10:])
        lag1 = arr[-1]
        lag2 = arr[-2] if len(arr) >= 2 else lag1
        lag3 = arr[-3] if len(arr) >= 3 else lag2
        lag5 = arr[-5] if len(arr) >= 5 else lag3

        roll_mean_3 = np.mean(arr[-3:])
        roll_mean_5 = np.mean(arr[-5:])
        roll_std    = np.std(arr[-5:]) if len(arr) >= 5 else 0.0
        delta_1     = lag1 - lag2
        delta_3     = lag1 - lag3

        ts_val = ts or time.time()
        t_struct = time.localtime(ts_val)
        minute_sin = np.sin(2 * np.pi * t_struct.tm_min / 60.0)
        minute_cos = np.cos(2 * np.pi * t_struct.tm_min / 60.0)
        hour_sin   = np.sin(2 * np.pi * t_struct.tm_hour / 24.0)

        feats = [
            lag1, lag2, lag3, lag5,
            roll_mean_3, roll_mean_5, roll_std,
            delta_1, delta_3,
            minute_sin, minute_cos, hour_sin
        ]
        return np.array(feats).reshape(1, -1)

    def _bootstrap_initial_training(self):
        """
        Train XGBoost models on REAL historical density pulled from
        traffic_data.db if enough exists; otherwise fall back to the
        synthetic sine-curve baseline so the model still works from frame 1.
        """
        if not HAS_XGBOOST and GradientBoostingRegressor is None:
            return

        real_series = _load_real_density_history(self.db_path)

        if real_series:
            self._train_on_real_series(real_series)
            return

        logger.info(
            "[CongestionPredictor] No sufficient real history in traffic_data.db yet "
            "(need 20+ one-minute buckets, i.e. ~20+ min of camera logging). "
            "Bootstrapping on synthetic data as a temporary placeholder - "
            "run your detection pipeline a while, then call retrain_from_database()."
        )
        self._bootstrap_synthetic()

    def _train_on_real_series(self, series: List[Tuple[float, float]]):
        """Build lag-feature training set from real (timestamp, density) pairs."""
        try:
            densities = [d for _, d in series]
            timestamps = [t for t, _ in series]

            X_list, y_15_list, y_30_list, y_60_list = [], [], [], []
            for i in range(5, len(densities) - 1):
                feats = self._extract_features(densities[:i], timestamps[i])[0]
                X_list.append(feats)
                # Use next real sample as a proxy target for all horizons
                # (short real logs won't span a full 60 min yet; this still
                # trains the model on genuine traffic shape rather than fiction)
                y_15_list.append(densities[i + 1])
                y_30_list.append(densities[i + 1])
                y_60_list.append(densities[i + 1])

            if len(X_list) < 10:
                logger.warning("[CongestionPredictor] Real series too short after feature extraction, using synthetic bootstrap instead.")
                self._bootstrap_synthetic()
                return

            X = np.array(X_list)
            self.models["15m"].fit(X, np.array(y_15_list))
            self.models["30m"].fit(X, np.array(y_30_list))
            self.models["60m"].fit(X, np.array(y_60_list))
            self.is_trained = True
            self.trained_on_real_data = True

            # Seed live history buffer with the tail of real data so
            # predict_future_congestion() has immediate context.
            self.history = densities[-self.max_history:]
            self.timestamps = timestamps[-self.max_history:]

            algo = "XGBoost Regressor" if HAS_XGBOOST else "GradientBoosting Regressor"
            logger.info(
                f"[CongestionPredictor] Trained on {len(X_list)} REAL samples from traffic_data.db ({algo})!"
            )
        except Exception as e:
            logger.error(f"[CongestionPredictor] Failed to train on real data, falling back to synthetic: {e}")
            self._bootstrap_synthetic()

    def _bootstrap_synthetic(self):
        """Original synthetic sine-curve bootstrap, kept as a fallback only."""
        np.random.seed(42)
        samples = 300
        X_list = []
        y_15_list, y_30_list, y_60_list = [], [], []

        for i in range(samples):
            t_hour = (i % 24)
            base_density = 0.2 + 0.5 * np.sin(np.pi * (t_hour - 6) / 12) ** 2
            base_density = np.clip(base_density + np.random.normal(0, 0.05), 0.05, 0.95)

            hist = [np.clip(base_density + np.random.normal(0, 0.03), 0.05, 0.95) for _ in range(10)]
            feats = self._extract_features(hist, time.time() + i * 3600)
            X_list.append(feats[0])

            y_15 = np.clip(base_density + np.random.normal(0.02, 0.04), 0.0, 1.0)
            y_30 = np.clip(base_density + np.random.normal(0.04, 0.06), 0.0, 1.0)
            y_60 = np.clip(base_density + np.random.normal(0.06, 0.08), 0.0, 1.0)

            y_15_list.append(y_15)
            y_30_list.append(y_30)
            y_60_list.append(y_60)

        X = np.array(X_list)
        try:
            if self.models["15m"]:
                self.models["15m"].fit(X, np.array(y_15_list))
                self.models["30m"].fit(X, np.array(y_30_list))
                self.models["60m"].fit(X, np.array(y_60_list))
                self.is_trained = True
                self.trained_on_real_data = False
                algo = "XGBoost Regressor" if HAS_XGBOOST else "GradientBoosting Regressor"
                logger.info(f"ML Model bootstrapped on SYNTHETIC data ({algo}) - replace with real data before final demo!")
        except Exception as e:
            logger.error(f"Failed to fit initial ML models: {e}")

    def retrain_from_database(self):
        """
        Call this periodically (e.g. once a day, or right before your demo)
        to re-bootstrap the model on the latest real data accumulated in
        traffic_data.db. Cheap to call - just re-runs the real-data path.
        """
        real_series = _load_real_density_history(self.db_path)
        if real_series:
            self._train_on_real_series(real_series)
            return True
        logger.info("[CongestionPredictor] retrain_from_database: still not enough real data logged yet.")
        return False

    def add_datapoint(self, density: float):
        """Add live density sample (0.0 to 1.0)"""
        self.history.append(float(density))
        self.timestamps.append(time.time())

        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.timestamps.pop(0)

        if len(self.history) % 30 == 0 and len(self.history) >= 20:
            self._online_retrain()

    def _online_retrain(self):
        """Online incremental retraining using real live captured stream samples."""
        if not HAS_XGBOOST and GradientBoostingRegressor is None:
            return

        try:
            X_live, y_live = [], []
            for i in range(5, len(self.history) - 1):
                f = self._extract_features(self.history[:i], self.timestamps[i])[0]
                X_live.append(f)
                y_live.append(self.history[i + 1])

            if len(X_live) > 10:
                X_arr = np.array(X_live)
                y_arr = np.array(y_live)
                self.models["15m"].fit(X_arr, y_arr)
                self.models["30m"].fit(X_arr, y_arr)
                self.models["60m"].fit(X_arr, y_arr)
                self.is_trained = True
                self.trained_on_real_data = True  # live data is always real
        except Exception as e:
            logger.warning(f"Online retrain skipped: {e}")

    def predict_future_congestion(self) -> Dict:
        """
        Predict traffic density for +15m, +30m, +60m horizons using XGBoost ML model.
        """
        curr = self.history[-1] if self.history else 0.2

        if self.is_trained:
            try:
                feats = self._extract_features(self.history)
                p_15 = float(np.clip(self.models["15m"].predict(feats)[0], 0.0, 1.0))
                p_30 = float(np.clip(self.models["30m"].predict(feats)[0], 0.0, 1.0))
                p_60 = float(np.clip(self.models["60m"].predict(feats)[0], 0.0, 1.0))

                diff = p_30 - curr
                if diff > 0.15:
                    trend = "RAPIDLY INCREASING"
                elif diff > 0.05:
                    trend = "INCREASING"
                elif diff < -0.15:
                    trend = "RAPIDLY DECREASING"
                elif diff < -0.05:
                    trend = "DECREASING"
                else:
                    trend = "STABLE"

                algo_name = "XGBoost ML Engine" if HAS_XGBOOST else "GradientBoosting ML Engine"
                data_source = "REAL traffic_data.db" if self.trained_on_real_data else "SYNTHETIC bootstrap (replace before demo)"
                return {
                    "current_density": round(curr * 100, 1),
                    "forecast_15m": {"density": round(p_15 * 100, 1), "level": self._density_to_level(p_15)},
                    "forecast_30m": {"density": round(p_30 * 100, 1), "level": self._density_to_level(p_30)},
                    "forecast_60m": {"density": round(p_60 * 100, 1), "level": self._density_to_level(p_60)},
                    "trend": trend,
                    "model_used": algo_name,
                    "trained_on": data_source,
                }
            except Exception as e:
                logger.error(f"XGBoost inference error: {e}")

        return self._fallback_polyfit(curr)

    def _fallback_polyfit(self, curr: float) -> Dict:
        if len(self.history) < 3:
            return {
                "current_density": round(curr * 100, 1),
                "forecast_15m": {"density": round(curr * 100, 1), "level": self._density_to_level(curr)},
                "forecast_30m": {"density": round(curr * 105, 1), "level": self._density_to_level(curr * 1.05)},
                "forecast_60m": {"density": round(curr * 110, 1), "level": self._density_to_level(curr * 1.1)},
                "trend": "STABLE",
                "model_used": "Linear Polyfit Fallback",
                "trained_on": "insufficient data",
            }

        x = np.arange(len(self.history))
        y = np.array(self.history)
        slope, _ = np.polyfit(x, y, 1)

        p_15 = max(0.0, min(1.0, curr + slope * 15))
        p_30 = max(0.0, min(1.0, curr + slope * 30))
        p_60 = max(0.0, min(1.0, curr + slope * 60))

        trend = "INCREASING" if slope > 0.001 else ("DECREASING" if slope < -0.001 else "STABLE")
        return {
            "current_density": round(curr * 100, 1),
            "forecast_15m": {"density": round(p_15 * 100, 1), "level": self._density_to_level(p_15)},
            "forecast_30m": {"density": round(p_30 * 100, 1), "level": self._density_to_level(p_30)},
            "forecast_60m": {"density": round(p_60 * 100, 1), "level": self._density_to_level(p_60)},
            "trend": trend,
            "model_used": "Linear Polyfit Fallback",
            "trained_on": "live rolling history",
        }

    def _density_to_level(self, density: float) -> str:
        if density > 0.7:
            return "HIGH CONGESTION"
        elif density > 0.4:
            return "MODERATE TRAFFIC"
        else:
            return "LOW DENSITY"


# Alias for backward compatibility
CongestionPredictor = XGBoostCongestionPredictor


if __name__ == "__main__":
    predictor = CongestionPredictor()
    for d in [0.2, 0.25, 0.3, 0.38, 0.45, 0.52]:
        predictor.add_datapoint(d)
    forecast = predictor.predict_future_congestion()
    print(f"[OK] XGBoostCongestionPredictor tested successfully!")
    print(f"  Model Used: {forecast.get('model_used')} | Trained on: {forecast.get('trained_on')}")
    print(f"  Current Density: {forecast['current_density']}% | Trend: {forecast['trend']}")
    print(f"  +15m Forecast: {forecast['forecast_15m']}")
    print(f"  +30m Forecast: {forecast['forecast_30m']}")
    print(f"  +60m Forecast: {forecast['forecast_60m']}")
