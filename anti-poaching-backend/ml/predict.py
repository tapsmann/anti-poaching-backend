import os
import pickle
from datetime import datetime
from typing import Optional

import numpy as np

try:
    from features import extract_training_features
except ImportError:
    from ml.features import extract_training_features


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
            # A serialized sklearn model can be incompatible after a Python or
            # dependency upgrade. Keep the API available while it is retrained.
            self.load_error = str(exc)
            print(f"ML model unavailable; using deterministic fallback risk score: {exc}")

    def predict_risk(self, lat, lng, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()

        if not self.loaded:
            # Explainable fallback for development/demo operation. It uses the
            # same geographic/time features as the trained model and always
            # returns a stable 0-100 score for the same input.
            features = extract_training_features(lat, lng, timestamp)
            score = (
                features["poaching_density"] * 6
                + (20 - features["patrol_frequency"]) * 2
                + (10 - min(features["distance_to_road"], 10)) * 1.5
                + (15 - min(features["distance_to_river"], 15))
                + features["moon_illumination"] * 10
            )
            return max(0.0, min(100.0, float(score)))

        features = extract_training_features(lat, lng, timestamp)
        X = np.array([list(features.values())])
        if self.scaler is not None:
            X = self.scaler.transform(X)
        risk_prob = self.model.predict_proba(X)[0][1]
        return risk_prob * 100
