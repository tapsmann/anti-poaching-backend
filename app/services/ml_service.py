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


PARK_CENTERS = {
    "Hwange": {"lat": -18.56, "lng": 26.49, "spread": 0.4},
    "Gonarezhou": {"lat": -21.73, "lng": 31.55, "spread": 0.35},
    "Mana Pools": {"lat": -15.75, "lng": 29.38, "spread": 0.3},
    "Matobo": {"lat": -20.55, "lng": 28.51, "spread": 0.2},
    "Victoria Falls": {"lat": -17.93, "lng": 25.85, "spread": 0.15},
    "Chizarira": {"lat": -17.93, "lng": 27.87, "spread": 0.3},
    "Matusadona": {"lat": -16.92, "lng": 28.47, "spread": 0.3},
}


def _normalize_park_name(park_name: Optional[str]) -> Optional[str]:
    if not park_name:
        return None
    normalized = park_name.strip().replace(" National Park", "").replace(" Park", "").replace(" Conservancy", "")
    for key in PARK_CENTERS:
        if key.lower() == normalized.lower():
            return key
    return normalized


def generate_hotspots(
    center_lat: float = -19.0,
    center_lng: float = 29.5,
    grid_size: int = 7,
    step: float = 0.12,
    park_name: Optional[str] = None,
) -> list[dict]:
    predictor = get_predictor()
    now = datetime.utcnow()

    park_key = _normalize_park_name(park_name)
    if park_key and park_key in PARK_CENTERS:
        park = PARK_CENTERS[park_key]
        center_lat = park["lat"]
        center_lng = park["lng"]
        spread = park["spread"]
        half = grid_size // 2
        step = (spread * 2) / max(grid_size, 1)
    else:
        half = grid_size // 2

    grid_points = []
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            grid_points.append((center_lat + i * step, center_lng + j * step))

    scores = predictor.predict_risk_many(grid_points, now)

    hotspots = []
    for (lat, lng), risk in zip(grid_points, scores):
        risk = round(risk, 2)
        hotspots.append({
            "lat": round(lat, 4),
            "lng": round(lng, 4),
            "risk": risk,
            "risk_score": risk,
        })

    hotspots.sort(key=lambda h: h["risk"], reverse=True)
    return hotspots


def generate_park_hotspots() -> list[dict]:
    all_hotspots = []
    for park_name, park in PARK_CENTERS.items():
        hotspots = generate_hotspots(
            center_lat=park["lat"],
            center_lng=park["lng"],
            grid_size=5,
            step=0.08,
            park_name=park_name,
        )
        for h in hotspots[:3]:
            h["park"] = park_name
            all_hotspots.append(h)
    all_hotspots.sort(key=lambda h: h["risk"], reverse=True)
    return all_hotspots
