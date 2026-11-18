"""Target selection (Phase 3, docs/RULES.md section 1).

A parcel is a TARGET only when:
  1. its notice stage is at or past the approval stage (default 3D), AND
  2. the parcel touches or lies inside the zone on either side, AND
  3. its survey number matched a parcel polygon.
Earlier notices inside the zone are PENDING, never targets. Anything missing goes to review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from shapely.geometry import LineString, shape

from tn_highway_intel.domain.models import STAGE_ORDER, NoticeDot, SurveyParcel, TargetParcel
from tn_highway_intel.engine.spatial_analyzer import area_units, build_zone, in_zone, parcel_metrics


@dataclass
class FilterResult:
    targets: list[TargetParcel] = field(default_factory=list)
    pending: list[NoticeDot] = field(default_factory=list)
    review: list[dict[str, Any]] = field(default_factory=list)


def _index_parcels(parcels: list[SurveyParcel]) -> dict[tuple[str, str], SurveyParcel]:
    return {(p.village, p.survey_no): p for p in parcels}


def select_targets(
    dots: list[NoticeDot],
    parcels: list[SurveyParcel],
    alignment: LineString,
    row_width_m: float | None,
    margin_m: float,
    approval_stage: str,
    updated_on: date,
) -> FilterResult:
    result = FilterResult()
    if row_width_m is None:
        for dot in dots:
            result.review.append({"reason": "missing_row_width", "survey_no": dot.survey_no, "village": dot.village})
        return result

    zone = build_zone(alignment, row_width_m, margin_m)
    index = _index_parcels(parcels)
    approved_rank = STAGE_ORDER[approval_stage]

    for dot in dots:
        parcel = index.get((dot.village, dot.survey_no))
        if parcel is None:
            result.review.append({"reason": "no_parcel_match", "survey_no": dot.survey_no, "village": dot.village})
            continue
        geom = shape(parcel.polygon)
        if not in_zone(zone, geom):
            continue  # outside the zone: not a target and not pending
        if STAGE_ORDER[dot.stage] < approved_rank:
            result.pending.append(dot)
            continue
        metrics = parcel_metrics(alignment, zone, geom)
        sqft, cents = area_units(geom)
        result.targets.append(
            TargetParcel(
                parcel_id=parcel.parcel_id,
                survey_no=dot.survey_no,
                village=dot.village,
                taluk=dot.taluk,
                district=dot.district,
                stage=dot.stage,
                gazette_date=dot.gazette_date,
                source_pdf=dot.source_pdf,
                area_sqft=sqft,
                area_cents=cents,
                row_width_m=row_width_m,
                margin_m=margin_m,
                updated_on=updated_on,
                **metrics,
            )
        )
    return result
