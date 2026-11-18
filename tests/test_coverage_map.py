from pathlib import Path

import pytest

from tn_highway_intel.engine.coverage_map import (
    build_map,
    filter_network,
    load_coverage,
    load_notices,
    notice_table,
    road_class,
    validate_notice,
)

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = load_coverage(ROOT / "config" / "coverage.yaml")
SEED = load_notices(ROOT / "config" / "notices_seed.json")


def test_scope_is_exactly_the_eight_listed_districts():
    assert COVERAGE.districts == [
        "Erode", "Namakkal", "Salem", "Coimbatore", "Tiruppur", "Karur", "Dindigul", "Dharmapuri",
    ]


def test_every_stage_has_a_distinct_colour():
    colours = [v["colour"] for v in COVERAGE.stages.values()]
    assert len(colours) == len(set(colours))


@pytest.mark.parametrize("ref,expected", [
    ("NH 544H", "national"),
    ("NH544", "national"),
    ("NH-381A", "national"),
    ("SH 79", "state"),
    ("SH-6A", "state"),
    ("MDR 12", "other"),
    ("", "other"),
])
def test_road_class_from_ref(ref, expected):
    assert road_class(ref) == expected


def test_filter_keeps_listed_districts_and_counts_unassigned():
    net = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"ref": "NH 544", "district": "Erode"}, "geometry": None},
        {"type": "Feature", "properties": {"ref": "SH 1", "district": "Chennai"}, "geometry": None},
        {"type": "Feature", "properties": {"ref": "SH 79"}, "geometry": None},
    ]}
    kept, unassigned = filter_network(net, COVERAGE.districts)
    refs = [f["properties"]["ref"] for f in kept["features"]]
    assert "NH 544" in refs
    assert "SH 1" not in refs
    assert "SH 79" in refs
    assert unassigned == 1


def test_seed_notices_are_all_in_scope_and_have_known_stages():
    for rec in SEED:
        validate_notice(rec, COVERAGE)


def test_out_of_scope_district_is_refused():
    bad = dict(SEED[0], district="Chennai", notice_id="x")
    with pytest.raises(ValueError):
        validate_notice(bad, COVERAGE)


def test_unknown_stage_is_refused():
    bad = dict(SEED[0], stage="nh_9z", notice_id="y")
    with pytest.raises(ValueError):
        validate_notice(bad, COVERAGE)


def test_notice_table_marks_undrawn_notices():
    rows = notice_table(SEED, COVERAGE)
    assert len(rows) == 3
    assert all(r["drawn"] is False for r in rows)


def test_build_map_draws_roads_and_stage_colours(tmp_path):
    net = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"ref": "NH 544", "district": "Erode"},
         "geometry": {"type": "LineString", "coordinates": [[77.7, 11.3], [77.8, 11.4]]}},
        {"type": "Feature", "properties": {"ref": "SH 79", "district": "Namakkal"},
         "geometry": {"type": "LineString", "coordinates": [[78.1, 11.4], [78.2, 11.5]]}},
    ]}
    notices = [dict(SEED[2], geometry={"type": "LineString", "coordinates": [[76.9, 11.0], [77.0, 11.05]]})]
    out = tmp_path / "coverage.html"
    counts = build_map(net, notices, COVERAGE, out)
    assert counts["roads_drawn"]["national"] == 1
    assert counts["roads_drawn"]["state"] == 1
    assert counts["notices_drawn"] == 1
    html = out.read_text(encoding="utf-8")
    assert "TN Highways Act s.15(1) initial" in html
    assert COVERAGE.stages["tn_15_1_initial"]["colour"] in html
    assert "Not advice" in html
