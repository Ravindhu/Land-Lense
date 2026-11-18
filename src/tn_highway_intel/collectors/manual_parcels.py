"""Manual parcel loader: the fallback when TNGIS permission is pending (docs/OPEN_QUESTIONS.md item 11).

Input is a GeoJSON FeatureCollection in the project CRS. Each feature needs:
district, taluk, village, survey_no, parcel_id, retrieved_on (ISO date). Source is set to "manual".
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from tn_highway_intel.domain.models import SurveyParcel

REQUIRED = ("district", "taluk", "village", "survey_no", "parcel_id", "retrieved_on")


class ParcelFileError(ValueError):
    pass


def load_manual_parcels(path: Path) -> list[SurveyParcel]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection":
        raise ParcelFileError("expected a GeoJSON FeatureCollection")
    parcels: list[SurveyParcel] = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        missing = [key for key in REQUIRED if key not in props]
        if missing:
            raise ParcelFileError(f"parcel is missing fields: {missing}")
        parcels.append(
            SurveyParcel(
                parcel_id=str(props["parcel_id"]),
                district=props["district"],
                taluk=props["taluk"],
                village=props["village"],
                survey_no=str(props["survey_no"]),
                polygon=feature["geometry"],
                source="manual",
                retrieved_on=date.fromisoformat(props["retrieved_on"]),
            )
        )
    return parcels
