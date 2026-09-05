from typing import Any, Optional

from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from shapely.geometry import LineString, Point


def point_from_latlng(lat: float, lng: float) -> WKTElement:
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


def linestring_from_coords(coords: list[dict[str, float]]) -> WKTElement:
    if len(coords) < 2:
        raise ValueError("Route requires at least 2 coordinate points")
    points = [(c["lng"], c["lat"]) for c in coords]
    return WKTElement(LineString(points).wkt, srid=4326)


def latlng_from_geometry(geometry: Any) -> tuple[Optional[float], Optional[float]]:
    if geometry is None:
        return None, None
    try:
        shape = to_shape(geometry)
        if isinstance(shape, Point):
            return shape.y, shape.x
    except Exception:
        pass
    return None, None


def coords_from_linestring(geometry: Any) -> list[dict[str, float]]:
    if geometry is None:
        return []
    try:
        shape = to_shape(geometry)
        if isinstance(shape, LineString):
            return [{"lat": lat, "lng": lng} for lng, lat in shape.coords]
    except Exception:
        pass
    return []
