import json
from datetime import date

import pytest
from shapely.geometry import LineString, box, mapping

from tn_highway_intel.collectors.manual_parcels import ParcelFileError, load_manual_parcels
from tn_highway_intel.collectors.tngis_cadastral import TngisCadastralCollector, TngisDisabled
from tn_highway_intel.domain.models import NoticeDot, SurveyParcel
from tn_highway_intel.domain.settings import CollectorSettings
from tn_highway_intel.engine.spatial_analyzer import build_zone, side_of_alignment
from tn_highway_intel.engine.target_filter import select_targets
from shapely.geometry import Point

ALIGN = LineString([(0, 0), (1000, 0)])  # runs east; left of travel is +y
MARGIN = 6.096
TODAY = date(2026, 11, 18)


def _parcel(survey, x0, y0, x1, y1, village="Ingur"):
    return SurveyParcel(
        parcel_id=f"p-{survey}",
        district="Erode",
        taluk="Perundurai",
        village=village,
        survey_no=survey,
        polygon=mapping(box(x0, y0, x1, y1)),
        source="manual",
        retrieved_on=date(2026, 11, 1),
    )


def _dot(survey, stage, village="Ingur"):
    return NoticeDot(
        dot_id=f"d-{survey}", district="Erode", taluk="Perundurai", village=village,
        survey_no=survey, stage=stage, gazette_id="G1", gazette_date=date(2026, 3, 1),
        source_pdf="raw/a.pdf", source_page=2, coords=(500, 10), confidence=0.95,
    )


def test_worked_example_zone_half_width():
    # ROW 45 m -> half 22.5 m -> zone half 22.5 + 6.096 = 28.596 m
    zone = build_zone(ALIGN, 45, MARGIN)
    assert zone.row_half_m == pytest.approx(22.5)
    assert zone.zone_half_m == pytest.approx(28.596)
    minx, miny, maxx, maxy = zone.zone.bounds
    assert maxy == pytest.approx(28.596)
    assert miny == pytest.approx(-28.596)


def test_side_left_and_right_of_travel_direction():
    assert side_of_alignment(ALIGN, Point(500, 10)) == "left"
    assert side_of_alignment(ALIGN, Point(500, -10)) == "right"


def test_3d_parcel_inside_zone_is_target_with_metrics():
    parcels = [_parcel("12", 480, 10, 520, 40)]  # sits left of the line, inside 28.596 m
    result = select_targets([_dot("12", "3D")], parcels, ALIGN, 45, MARGIN, "3D", TODAY)
    assert len(result.targets) == 1
    t = result.targets[0]
    assert t.side == "left"
    assert t.row_width_m == 45
    assert t.margin_m == pytest.approx(6.096)
    assert t.dist_to_alignment_m == pytest.approx(10.0)
    assert t.dist_to_zone_edge_m == pytest.approx(28.596 - 10.0, abs=0.01)
    assert t.area_sqft == pytest.approx(40 * 30 * 10.7639104, rel=1e-4)


def test_3a_parcel_inside_zone_is_pending_not_target():
    parcels = [_parcel("13", 480, 10, 520, 40)]
    result = select_targets([_dot("13", "3A")], parcels, ALIGN, 45, MARGIN, "3D", TODAY)
    assert result.targets == []
    assert len(result.pending) == 1


def test_3d_parcel_outside_zone_is_not_target_and_not_pending():
    parcels = [_parcel("14", 480, 200, 520, 230)]  # far outside
    result = select_targets([_dot("14", "3D")], parcels, ALIGN, 45, MARGIN, "3D", TODAY)
    assert result.targets == []
    assert result.pending == []
    assert result.review == []


def test_unmatched_survey_goes_to_review():
    result = select_targets([_dot("99", "3D")], [], ALIGN, 45, MARGIN, "3D", TODAY)
    assert result.targets == []
    assert result.review[0]["reason"] == "no_parcel_match"


def test_missing_row_width_blocks_targets_and_reports():
    parcels = [_parcel("12", 480, 10, 520, 40)]
    result = select_targets([_dot("12", "3D")], parcels, ALIGN, None, MARGIN, "3D", TODAY)
    assert result.targets == []
    assert result.review[0]["reason"] == "missing_row_width"


def test_stage_at_or_past_approval_is_target():
    parcels = [_parcel("15", 480, 10, 520, 40)]
    result = select_targets([_dot("15", "3H")], parcels, ALIGN, 45, MARGIN, "3D", TODAY)
    assert len(result.targets) == 1


def test_manual_parcel_loader_and_validation(tmp_path):
    good = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": mapping(box(0, 0, 10, 10)),
            "properties": {"district": "Erode", "taluk": "P", "village": "Ingur", "survey_no": "1",
                           "parcel_id": "p1", "retrieved_on": "2026-11-01"},
        }],
    }
    path = tmp_path / "parcels.geojson"
    path.write_text(json.dumps(good))
    parcels = load_manual_parcels(path)
    assert parcels[0].source == "manual"

    bad = json.loads(json.dumps(good))
    del bad["features"][0]["properties"]["parcel_id"]
    path.write_text(json.dumps(bad))
    with pytest.raises(ParcelFileError):
        load_manual_parcels(path)


def test_tngis_collector_stays_disabled_until_terms_cleared():
    collector = TngisCadastralCollector(CollectorSettings(enabled=True, terms_cleared=False))
    with pytest.raises(TngisDisabled):
        collector.require_enabled()
