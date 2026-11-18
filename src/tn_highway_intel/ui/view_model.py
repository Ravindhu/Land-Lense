"""View models for the dashboard. Pure functions, so the privacy rules are testable.

Rule (docs/DESIGN.md section 6, docs/RULES.md section 7): nothing in these outputs carries owner
names, PAN, Aadhaar, or phone numbers. The owner panel is the only place owner details appear.
"""

from __future__ import annotations

from typing import Any

from shapely.geometry import LineString, Point, mapping

from tn_highway_intel.domain.models import NoticeDot, TargetParcel

TARGET_ROW_FIELDS = (
    "survey_no", "village", "taluk", "district", "stage", "gazette_date", "side",
    "area_sqft", "area_cents", "dist_to_alignment_m", "dist_to_row_edge_m", "dist_to_zone_edge_m",
    "row_width_m", "margin_m", "source_pdf", "updated_on",
)
PENDING_ROW_FIELDS = ("survey_no", "village", "taluk", "district", "stage", "gazette_date", "source_pdf")
FORBIDDEN_KEYS = frozenset({"owner_name", "pan", "pan_masked", "aadhaar", "aadhaar_last4", "phone", "contact_phone", "borrower_name"})

NOT_ADVICE = "Research aid, not advice. Check each record against its source and date."


def target_rows(targets: list[TargetParcel]) -> list[dict[str, Any]]:
    rows = []
    for t in targets:
        data = t.model_dump(mode="json")
        rows.append({k: data[k] for k in TARGET_ROW_FIELDS})
    return rows


def pending_rows(dots: list[NoticeDot]) -> list[dict[str, Any]]:
    rows = []
    for d in dots:
        data = d.model_dump(mode="json")
        rows.append({k: data[k] for k in PENDING_ROW_FIELDS})
    return rows


def review_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"reason": i["reason"], "source_pdf": i.get("source_pdf"), "page": i.get("page")} for i in items]


def map_features(alignment: LineString, targets: list[TargetParcel], points: dict[str, tuple[float, float]]) -> dict[str, Any]:
    """GeoJSON for the map. Targets are drawn as points at their survey centroid."""
    features: list[dict[str, Any]] = [
        {"type": "Feature", "geometry": mapping(alignment), "properties": {"layer": "alignment", "label": "Official alignment"}}
    ]
    for t in targets:
        coords = points.get(t.survey_no)
        if coords is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": mapping(Point(coords)),
            "properties": {"layer": "target", "survey_no": t.survey_no, "village": t.village, "stage": t.stage, "side": t.side},
        })
    return {"type": "FeatureCollection", "features": features}


def assert_no_personal_data(payload: Any) -> None:
    """Raise if a payload carries an owner or contact key anywhere in its structure."""
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            bad = FORBIDDEN_KEYS.intersection(item.keys())
            if bad:
                raise ValueError(f"personal data key in dashboard payload: {sorted(bad)}")
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
