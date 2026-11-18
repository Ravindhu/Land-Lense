"""Patta and area lookup (Phase 4, docs/ARCHITECTURE.md). Owner names are NOT returned here.

Area comes from the parcel polygon. Patta comes from patta_registry.json, which holds only
non-sensitive fields. Owner details are read separately, through the owner store, from the owner panel.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from shapely.geometry import shape

from tn_highway_intel.domain.models import SurveyParcel
from tn_highway_intel.engine.spatial_analyzer import area_units

NON_SENSITIVE_PATTA_FIELDS = ("district", "taluk", "village", "survey_no", "patta_no", "land_type", "source", "verified_on")


def load_patta_registry(path: Path) -> list[dict[str, Any]]:
    if not Path(path).exists():
        return []
    return json.loads(Path(path).read_text(encoding="utf-8"))


def lookup(parcel: SurveyParcel, registry: list[dict[str, Any]]) -> dict[str, Any]:
    sqft, cents = area_units(shape(parcel.polygon))
    patta: Optional[dict[str, Any]] = next(
        (r for r in registry if (r["village"], r["survey_no"]) == (parcel.village, parcel.survey_no)),
        None,
    )
    result: dict[str, Any] = {
        "parcel_id": parcel.parcel_id,
        "district": parcel.district,
        "taluk": parcel.taluk,
        "village": parcel.village,
        "survey_no": parcel.survey_no,
        "area_sqft": sqft,
        "area_cents": cents,
        "patta": None,
    }
    if patta is not None:
        result["patta"] = {k: patta[k] for k in NON_SENSITIVE_PATTA_FIELDS if k in patta}
    return result
