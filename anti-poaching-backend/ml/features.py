import math
from datetime import datetime


def _geo_hash(lat: float, lng: float, salt: str = "") -> float:
    """Deterministic pseudo-random value in [0, 1) from coordinates."""
    raw = math.sin(lat * 12.9898 + lng * 78.233 + len(salt) * 0.17) * 43758.5453
    return raw - math.floor(raw)


def extract_training_features(lat, lng, timestamp):
    """Extract deterministic features for ML training and inference."""
    features = {}

    features["hour"] = timestamp.hour
    features["day_of_week"] = timestamp.weekday()
    features["month"] = timestamp.month

    day = timestamp.day
    features["moon_illumination"] = abs(math.sin(2 * math.pi * day / 29.53))

    features["distance_to_road"] = _geo_hash(lat, lng, "road") * 10
    features["distance_to_river"] = _geo_hash(lat, lng, "river") * 15
    features["poaching_density"] = int(_geo_hash(lat, lng, "density") * 10)
    features["patrol_frequency"] = int(_geo_hash(lat, lng, "patrol") * 20)

    return features
