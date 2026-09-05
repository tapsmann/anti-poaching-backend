import os
import pickle
import warnings
from datetime import datetime
from typing import Optional

import numpy as np

try:
    from features import extract_training_features
except ImportError:
    from ml.features import extract_training_features


def _transform(scaler, X):
    if scaler is None:
        return X
    if hasattr(scaler, "feature_names_in_"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return scaler.transform(X)
    return scaler.transform(X)


class PoachingPredictor:
    def __init__(self, model_path=None, scaler_path=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if model_path is None:
            model_path = os.path.join(base_dir, "models", "poaching_risk.pkl")
        if scaler_path is None:
            scaler_path = os.path.join(base_dir, "models", "scaler.pkl")

        self.loaded = False
        self.model = None
        self.scaler = None
        self.load_error = None

        try:
            with open(model_path, "rb") as f:
                self.model = pickle.load(f)
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)
            self.loaded = True
        except Exception as exc:
            self.load_error = str(exc)
            print(f"ML model unavailable; using deterministic fallback: {exc}")

    def predict_risk(self, lat, lng, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()

        features = extract_training_features(lat, lng, timestamp)
        feature_values = list(features.values())

        if not self.loaded:
            score = (
                features.get("park_risk_base", 0.3) * 30
                + features.get("poaching_density", 0) * 3
                + features.get("time_risk", 1.0) * 15
                + features.get("seasonal_risk", 1.0) * 10
                + max(0, (10 - features.get("distance_to_road", 10))) * 1.5
                + max(0, (15 - features.get("distance_to_river", 15))) * 0.8
                + features.get("moon_illumination", 0) * 8
                - features.get("patrol_frequency", 0) * 1.2
            )
            return max(0.0, min(100.0, float(score)))

        X = np.array([feature_values])
        X = _transform(self.scaler, X)
        risk_prob = self.model.predict_proba(X)[0][1]
        return risk_prob * 100

    def predict_risk_many(self, points, timestamp=None):
        """Predict risk for many (lat, lng) points in a single vectorized call.

        ``points`` is an iterable of (lat, lng) tuples. Returns a list of
        scores aligned with the input order.
        """
        if timestamp is None:
            timestamp = datetime.now()

        features_list = [list(extract_training_features(lat, lng, timestamp).values()) for lat, lng in points]

        if not self.loaded:
            return [self.predict_risk(lat, lng, timestamp) for lat, lng in points]

        X = np.array(features_list)
        X = _transform(self.scaler, X)
        risk_probs = self.model.predict_proba(X)[:, 1]
        return [float(p * 100) for p in risk_probs]
