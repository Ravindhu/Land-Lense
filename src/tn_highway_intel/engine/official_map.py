"""Official map georeferencing and alignment storage (Phase 1, docs/RULES.md section 5).

Control points pair a map pixel (px, py) with a projected coordinate (x, y) in metres (EPSG:32643).
An affine transform is fitted by least squares. The RMS residual is the accuracy measure that the
plan asks to record. At least 3 non-collinear points are required.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from shapely.geometry import LineString, shape

MIN_CONTROL_POINTS = 3

Pair = tuple[tuple[float, float], tuple[float, float]]


class GeoreferenceError(ValueError):
    pass


@dataclass(frozen=True)
class AffineFit:
    matrix: np.ndarray  # shape (2, 3): [[a, b, c], [d, e, f]]
    rms_m: float        # RMS residual of the control points, metres
    n_points: int

    def apply(self, px: float, py: float) -> tuple[float, float]:
        x = self.matrix[0, 0] * px + self.matrix[0, 1] * py + self.matrix[0, 2]
        y = self.matrix[1, 0] * px + self.matrix[1, 1] * py + self.matrix[1, 2]
        return float(x), float(y)


def fit_affine(points: Sequence[Pair]) -> AffineFit:
    """Fit pixel -> projected coordinates. Refuses fewer than 3 points or collinear points."""
    if len(points) < MIN_CONTROL_POINTS:
        raise GeoreferenceError(f"need at least {MIN_CONTROL_POINTS} control points, got {len(points)}")
    src = np.array([[p[0][0], p[0][1], 1.0] for p in points])
    dst = np.array([[p[1][0], p[1][1]] for p in points])
    if np.linalg.matrix_rank(src) < 3:
        raise GeoreferenceError("control points are collinear; choose points spread across the sheet")
    solution, *_ = np.linalg.lstsq(src, dst, rcond=None)  # (3, 2)
    matrix = solution.T  # (2, 3)
    predicted = src @ solution
    residuals = np.linalg.norm(predicted - dst, axis=1)
    rms = float(np.sqrt(np.mean(residuals**2)))
    return AffineFit(matrix=matrix, rms_m=rms, n_points=len(points))


def check_accuracy(fit: AffineFit, max_rms_m: float) -> None:
    if fit.rms_m > max_rms_m:
        raise GeoreferenceError(f"georeference RMS {fit.rms_m:.2f} m exceeds limit {max_rms_m:.2f} m")


def load_alignment(path: Path) -> LineString:
    """Load the official alignment from GeoJSON (a Feature or a bare LineString geometry)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    geometry = data["geometry"] if data.get("type") == "Feature" else data
    line = shape(geometry)
    if line.geom_type != "LineString":
        raise GeoreferenceError(f"alignment must be a LineString, got {line.geom_type}")
    return line


def save_alignment(line: LineString, path: Path, source: dict) -> None:
    """Write the alignment as GeoJSON with the source recorded (every record keeps its source)."""
    payload = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": [list(c) for c in line.coords]},
        "properties": source,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def transform_polyline(fit: AffineFit, pixel_points: Sequence[tuple[float, float]]) -> LineString:
    coords = [fit.apply(px, py) for px, py in pixel_points]
    if len(coords) < 2:
        raise GeoreferenceError("a polyline needs at least 2 points")
    return LineString(coords)
