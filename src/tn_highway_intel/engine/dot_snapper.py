"""Snap notice dots onto the official alignment (Phase 2, FR-4, docs/RULES.md section 4).

Coordinates are in the project CRS (EPSG:32643, metres). A dot farther than the tolerance from the
alignment is not moved onto the line; it goes to review.
"""

from __future__ import annotations

from shapely.geometry import LineString, Point

from tn_highway_intel.domain.models import NoticeDot


def snap_dots(
    dots: list[NoticeDot],
    alignment: LineString,
    tolerance_m: float,
) -> tuple[list[NoticeDot], list[NoticeDot]]:
    """Return (mapped, review). Mapped dots sit on the line and keep snap_distance_m."""
    mapped: list[NoticeDot] = []
    review: list[NoticeDot] = []
    for dot in dots:
        point = Point(dot.coords)
        distance = alignment.distance(point)
        if distance > tolerance_m:
            review.append(dot.model_copy(update={"snap_distance_m": round(distance, 3), "status": "review"}))
            continue
        nearest = alignment.interpolate(alignment.project(point))
        mapped.append(
            dot.model_copy(
                update={
                    "coords": (round(nearest.x, 3), round(nearest.y, 3)),
                    "snap_distance_m": round(distance, 3),
                    "status": "mapped",
                }
            )
        )
    return mapped, review
