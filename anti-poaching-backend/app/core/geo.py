from typing import Any, Optional
from geoalchemy2 import WKTElement

def point_from_latlng(lat: float, lng: float) -> WKTElement:
    """Create a PostGIS POINT from latitude and longitude."""
    return WKTElement(f"POINT({lng} {lat})", srid=4326)

def linestring_from_coords(coords: list[dict[str, float]]) -> WKTElement:
    """Create a PostGIS LINESTRING from a list of coordinates."""
    if len(coords) < 2:
        raise ValueError("Route requires at least 2 coordinate points")
    points_str = ", ".join([f"{c['lng']} {c['lat']}" for c in coords])
    return WKTElement(f"LINESTRING({points_str})", srid=4326)

def latlng_from_geometry(geometry: Any) -> tuple[Optional[float], Optional[float]]:
    """Extract latitude and longitude from a PostGIS POINT."""
    if geometry is None:
        return None, None
    try:
        # Parse WKT format: "POINT(lng lat)"
        import re
        match = re.search(r"POINT\(([^ ]+) ([^)]+)\)", str(geometry))
        if match:
            lng = float(match.group(1))
            lat = float(match.group(2))
            return lat, lng
    except Exception:
        pass
    return None, None

def coords_from_linestring(geometry: Any) -> list[dict[str, float]]:
    """Extract coordinates from a PostGIS LINESTRING."""
    if geometry is None:
        return []
    try:
        import re
        # Parse WKT format: "LINESTRING(lng1 lat1, lng2 lat2, ...)"
        match = re.search(r"LINESTRING\(([^)]+)\)", str(geometry))
        if match:
            points_str = match.group(1)
            coords = []
            for point in points_str.split(","):
                point = point.strip()
                parts = point.split()
                if len(parts) == 2:
                    lng, lat = float(parts[0]), float(parts[1])
                    coords.append({"lat": lat, "lng": lng})
            return coords
    except Exception:
        pass
    return []
