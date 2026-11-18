"""Right-of-way band, target zone, side and distances (Phase 3, docs/RULES.md section 2).

All geometry is in the project CRS (EPSG:32643, metres). The zone on each side of the centreline is
row_width_m / 2 + margin_m (margin = 20 ft = 6.096 m, measured from the road edge).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry

SQFT_PER_M2 = 10.7639104
SQFT_PER_CENT = 435.6  # 1 cent = 435.6 sq ft (40.47 m2), the Tamil Nadu convention


@dataclass(frozen=True)
class ZoneGeometry:
    row_half_m: float
    zone_half_m: float
    row_band: Polygon
    zone: Polygon


def build_zone(alignment: LineString, row_width_m: float, margin_m: float) -> ZoneGeometry:
    if row_width_m <= 0:
        raise ValueError("row_width_m must be positive")
    row_half = row_width_m / 2
    zone_half = row_half + margin_m
    row_band = alignment.buffer(row_half, cap_style="flat")
    zone = alignment.buffer(zone_half, cap_style="flat")
    return ZoneGeometry(row_half_m=row_half, zone_half_m=zone_half, row_band=row_band, zone=zone)


def side_of_alignment(alignment: LineString, point: Point) -> Literal["left", "right"]:
    """Left or right of the direction of travel along the alignment. Left is positive cross product."""
    s = alignment.project(point)
    step = min(1.0, alignment.length / 100) or 1.0
    a = alignment.interpolate(max(s - step, 0))
    b = alignment.interpolate(min(s + step, alignment.length))
    tx, ty = b.x - a.x, b.y - a.y
    nearest = alignment.interpolate(s)
    cross = tx * (point.y - nearest.y) - ty * (point.x - nearest.x)
    return "left" if cross >= 0 else "right"


def parcel_metrics(alignment: LineString, zone: ZoneGeometry, parcel_geom: BaseGeometry) -> dict:
    """Distances (metres) and side for a parcel. Positive dist_to_zone_edge_m means inside the zone."""
    centroid = parcel_geom.centroid
    distance = alignment.distance(parcel_geom)
    return {
        "dist_to_alignment_m": round(distance, 3),
        "dist_to_row_edge_m": round(abs(distance - zone.row_half_m), 3),
        "dist_to_zone_edge_m": round(zone.zone_half_m - distance, 3),
        "side": side_of_alignment(alignment, centroid),
    }


def in_zone(zone: ZoneGeometry, parcel_geom: BaseGeometry) -> bool:
    """A parcel counts as inside when it touches or overlaps the zone."""
    return parcel_geom.intersects(zone.zone)


def area_units(parcel_geom: BaseGeometry) -> tuple[float, float]:
    """(sq ft, cents) for a polygon in square metres."""
    sqft = parcel_geom.area * SQFT_PER_M2
    return round(sqft, 2), round(sqft / SQFT_PER_CENT, 4)
