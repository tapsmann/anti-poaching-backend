import math
from datetime import datetime


ZIMBABWE_PARKS = {
    "hwange": {"lat": -18.56, "lng": 26.49, "risk_base": 0.7, "poaching_hotspot": True},
    "gonarezhou": {"lat": -21.73, "lng": 31.55, "risk_base": 0.65, "poaching_hotspot": True},
    "mana_pools": {"lat": -15.75, "lng": 29.38, "risk_base": 0.6, "poaching_hotspot": True},
    "matobo": {"lat": -20.55, "lng": 28.51, "risk_base": 0.45, "poaching_hotspot": False},
    "victoria_falls": {"lat": -17.93, "lng": 25.85, "risk_base": 0.35, "poaching_hotspot": False},
    "chizarira": {"lat": -17.93, "lng": 27.87, "risk_base": 0.7, "poaching_hotspot": True},
    "matusadona": {"lat": -16.92, "lng": 28.47, "risk_base": 0.6, "poaching_hotspot": True},
    "gwayi_shangani": {"lat": -18.18, "lng": 27.40, "risk_base": 0.5, "poaching_hotspot": False},
    "chivero": {"lat": -17.88, "lng": 30.55, "risk_base": 0.25, "poaching_hotspot": False},
    "kariba": {"lat": -16.52, "lng": 28.85, "risk_base": 0.4, "poaching_hotspot": False},
}

ZIMBABWE_ROADS = [
    {"lat1": -17.83, "lng1": 25.86, "lat2": -17.88, "lng2": 31.05, "importance": 1.0},
    {"lat1": -19.01, "lng1": 25.86, "lat2": -22.22, "lng2": 32.23, "importance": 0.9},
    {"lat1": -17.83, "lng1": 25.86, "lat2": -15.43, "lng2": 28.28, "importance": 0.8},
    {"lat1": -20.15, "lng1": 28.58, "lat2": -21.22, "lng2": 32.85, "importance": 0.7},
    {"lat1": -17.88, "lng1": 30.55, "lat2": -19.45, "lng2": 32.10, "importance": 0.7},
    {"lat1": -18.56, "lng1": 26.49, "lat2": -18.18, "lng2": 27.40, "importance": 0.6},
]

ZIMBABWE_RIVERS = [
    {"name": "Zambezi", "lat": -15.75, "lng": 28.50, "width_km": 1.5},
    {"name": "Limpopo", "lat": -22.15, "lng": 29.50, "width_km": 0.8},
    {"name": "Save", "lat": -21.05, "lng": 32.40, "width_km": 0.3},
    {"name": "Runde", "lat": -21.20, "lng": 31.20, "width_km": 0.15},
    {"name": "Gwayi", "lat": -18.18, "lng": 27.40, "width_km": 0.1},
]


def _haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _distance_to_nearest_road(lat, lng):
    min_dist = 9999.0
    for road in ZIMBABWE_ROADS:
        d = _point_to_segment_distance(lat, lng, road["lat1"], road["lng1"], road["lat2"], road["lng2"])
        min_dist = min(min_dist, d)
    return min_dist


def _point_to_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return _haversine_km(px, py, x1, y1)
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return _haversine_km(px, py, proj_x, proj_y)


def _distance_to_nearest_river(lat, lng):
    min_dist = 9999.0
    for river in ZIMBABWE_RIVERS:
        d = _haversine_km(lat, lng, river["lat"], river["lng"])
        min_dist = min(min_dist, d)
    return min_dist


def _nearest_park_risk(lat, lng):
    min_dist = 9999.0
    risk_base = 0.3
    for park_data in ZIMBABWE_PARKS.values():
        d = _haversine_km(lat, lng, park_data["lat"], park_data["lng"])
        if d < min_dist:
            min_dist = d
            risk_base = park_data["risk_base"]
    return min_dist, risk_base


def _moon_illumination(timestamp):
    day = timestamp.day
    return abs(math.sin(2 * math.pi * day / 29.53))


def _seasonal_factor(month):
    dry_season = {5, 6, 7, 8, 9, 10}
    if month in dry_season:
        return 1.3
    return 0.8


def _time_of_day_factor(hour):
    if 20 <= hour or hour <= 4:
        return 1.4
    elif 5 <= hour <= 6 or 17 <= hour <= 19:
        return 1.1
    else:
        return 0.7


def extract_training_features(lat, lng, timestamp):
    features = {}

    features["hour"] = timestamp.hour
    features["day_of_week"] = timestamp.weekday()
    features["month"] = timestamp.month

    features["moon_illumination"] = _moon_illumination(timestamp)

    dist_road = _distance_to_nearest_road(lat, lng)
    features["distance_to_road"] = min(dist_road, 10.0)

    dist_river = _distance_to_nearest_river(lat, lng)
    features["distance_to_river"] = min(dist_river, 15.0)

    dist_park, park_risk = _nearest_park_risk(lat, lng)
    features["distance_to_park"] = min(dist_park, 20.0)
    features["park_risk_base"] = park_risk

    features["time_risk"] = _time_of_day_factor(timestamp.hour)
    features["seasonal_risk"] = _seasonal_factor(timestamp.month)

    poaching_density = 0
    if dist_park < 10:
        poaching_density = int(max(0, 10 - dist_park))
    elif dist_park < 25:
        poaching_density = int(max(0, 5 - (dist_park - 10) / 3))
    features["poaching_density"] = poaching_density

    patrol_frequency = int(max(0, 20 - dist_park * 0.8))
    features["patrol_frequency"] = min(patrol_frequency, 20)

    return features
