import os
from datetime import datetime
from typing import Optional

from ml.predict import PoachingPredictor

_predictor: Optional[PoachingPredictor] = None


def get_predictor() -> PoachingPredictor:
    global _predictor
    if _predictor is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(base_dir, "ml", "models", "poaching_risk.pkl")
        _predictor = PoachingPredictor(model_path=model_path)
    return _predictor


def predict_risk_score(lat: float, lng: float, timestamp: Optional[datetime] = None) -> float:
    predictor = get_predictor()
    return round(predictor.predict_risk(lat, lng, timestamp), 2)


def generate_hotspots(
    center_lat: float = -19.0,
    center_lng: float = 29.5,
    grid_size: int = 5,
    step: float = 0.15,
) -> list[dict]:
    predictor = get_predictor()
    hotspots = []
    half = grid_size // 2
    now = datetime.utcnow()

    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            lat = center_lat + i * step
            lng = center_lng + j * step
            risk = round(predictor.predict_risk(lat, lng, now), 2)
            hotspots.append({"lat": lat, "lng": lng, "risk": risk, "risk_score": risk})

    hotspots.sort(key=lambda h: h["risk"], reverse=True)
    return hotspots
