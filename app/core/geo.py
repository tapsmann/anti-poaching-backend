from typing import Any, Optional
import re

from geoalchemy2 import WKTElement
from geoalchemy2.shape import to_shape
from shapely.geometry import LineString, Point


def point_from_latlng(lat: float, lng: float) -> str:
    # Stored as TEXT ("lat,lng") — see _migrate_columns which converts all
    # geometry columns to TEXT. latlng_from_geometry() parses this format.
    return f"{lat},{lng}"


def linestring_from_coords(coords: list[dict[str, float]]) -> str:
    if len(coords) < 2:
        raise ValueError("Route requires at least 2 coordinate points")
    points = [(c["lng"], c["lat"]) for c in coords]
    # Store plain WKT string — coords_from_linestring() parses this format.
    return LineString(points).wkt


def _parse_latlng(text: str):
    if not text or not isinstance(text, str):
        return None
    try:
        parts = text.strip().split(",")
        if len(parts) == 2:
            lat = float(parts[0])
            lng = float(parts[1])
            return lat, lng
    except (ValueError, IndexError):
        pass
    return None


def latlng_from_geometry(geometry: Any) -> tuple[Optional[float], Optional[float]]:
    if geometry is None:
        return None, None
    if isinstance(geometry, str):
        result = _parse_latlng(geometry)
        if result:
            return result
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
    if isinstance(geometry, str):
        try:
            wkt = geometry
            if wkt.upper().startswith("LINESTRING"):
                inner = wkt[wkt.find("(") + 1: wkt.rfind(")")]
                coords = []
                for part in inner.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    nums = part.split()
                    if len(nums) >= 2:
                        lng = float(nums[0])
                        lat = float(nums[1])
                        coords.append({"lat": lat, "lng": lng})
                return coords
            if " " in geometry and "," in geometry:
                coords = []
                for pair in geometry.strip().split():
                    if "," in pair:
                        parts = pair.split(",")
                        if len(parts) == 2:
                            try:
                                lat = float(parts[0])
                                lng = float(parts[1])
                                coords.append({"lat": lat, "lng": lng})
                            except ValueError:
                                continue
                if coords:
                    return coords
            result = _parse_latlng(geometry)
            if result:
                return [{"lat": result[0], "lng": result[1]}]
        except Exception:
            pass
        return []
    try:
        shape = to_shape(geometry)
        if isinstance(shape, LineString):
            return [{"lat": lat, "lng": lng} for lng, lat in shape.coords]
    except Exception:
        pass
    return []
