"""Coverage map for the listed districts: NH and SH network plus land-acquisition stages in different colours.

Inputs (all supplied as files, because the sandbox cannot reach OSM or the gazette site):
- a road network GeoJSON (LineString features) with properties: ref (e.g. "NH 544H", "SH 79"), and optional district
- notice records (config/notices_seed.json format), each with a stage key from config/coverage.yaml

Notices with no coordinates are listed in the table but are not drawn. They are drawn only when a
point or line geometry is supplied in the notice record as "geometry" (GeoJSON).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

NH_RE = "NH"
SH_RE = "SH"


@dataclass
class Coverage:
    districts: list[str]
    stages: dict[str, dict[str, str]]
    roads: dict[str, dict[str, Any]]


def load_coverage(path: Path) -> Coverage:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return Coverage(districts=list(data["districts"]), stages=data["stages"], roads=data["roads"])


def road_class(ref: str) -> str:
    """Classify a road by its ref prefix. Anything else is 'other'."""
    text = (ref or "").strip().upper().replace("-", " ")
    if text.startswith(NH_RE + " ") or text.startswith(NH_RE) and text[2:3].isdigit():
        return "national"
    if text.startswith(SH_RE + " ") or text.startswith(SH_RE) and text[2:3].isdigit():
        return "state"
    return "other"


def filter_network(network: dict[str, Any], districts: list[str]) -> tuple[dict[str, Any], int]:
    """Keep roads in the listed districts. Roads with no district property are kept and counted as unassigned."""
    keep, unassigned = [], 0
    wanted = {d.lower() for d in districts}
    for feat in network.get("features", []):
        props = feat.get("properties") or {}
        district = (props.get("district") or "").strip()
        if not district:
            unassigned += 1
            keep.append(feat)
        elif district.lower() in wanted:
            keep.append(feat)
    return {"type": "FeatureCollection", "features": keep}, unassigned


def validate_notice(rec: dict[str, Any], coverage: Coverage) -> None:
    if rec.get("stage") not in coverage.stages:
        raise ValueError(f"unknown stage for notice {rec.get('notice_id')}: {rec.get('stage')}")
    if rec.get("district") not in coverage.districts:
        raise ValueError(f"notice {rec.get('notice_id')} is outside the listed districts")


def notice_table(notices: list[dict[str, Any]], coverage: Coverage) -> list[dict[str, Any]]:
    rows = []
    for rec in notices:
        validate_notice(rec, coverage)
        rows.append({
            "notice_id": rec["notice_id"],
            "district": rec["district"],
            "project": rec["project"],
            "stage": coverage.stages[rec["stage"]]["label"],
            "gazette": f'{rec["gazette"]} ({rec["gazette_date"]})',
            "drawn": bool(rec.get("geometry")),
        })
    return rows


def build_map(
    network: dict[str, Any],
    notices: list[dict[str, Any]],
    coverage: Coverage,
    out_html: Path,
) -> dict[str, Any]:
    """Write a folium map. Returns counts for the report."""
    import folium

    filtered, unassigned = filter_network(network, coverage.districts)
    m = folium.Map(location=[11.0, 78.0], zoom_start=8, tiles="OpenStreetMap")

    road_groups = {k: folium.FeatureGroup(name=v["label"], show=True) for k, v in coverage.roads.items()}
    counts = {k: 0 for k in coverage.roads}
    for feat in filtered["features"]:
        cls = road_class((feat.get("properties") or {}).get("ref", ""))
        style = coverage.roads[cls]
        folium.GeoJson(
            feat,
            style_function=lambda _f, s=style: {"color": s["colour"], "weight": s["weight"], "opacity": 0.9},
            tooltip=(feat.get("properties") or {}).get("ref", ""),
        ).add_to(road_groups[cls])
        counts[cls] += 1
    for group in road_groups.values():
        group.add_to(m)

    stage_groups = {k: folium.FeatureGroup(name=v["label"], show=True) for k, v in coverage.stages.items()}
    drawn = 0
    for rec in notices:
        validate_notice(rec, coverage)
        geom = rec.get("geometry")
        if not geom:
            continue
        style = coverage.stages[rec["stage"]]
        folium.GeoJson(
            {"type": "Feature", "geometry": geom, "properties": {}},
            style_function=lambda _f, s=style: {"color": s["colour"], "weight": 5, "opacity": 1},
            tooltip=f'{rec["notice_id"]}: {style["label"]}',
        ).add_to(stage_groups[rec["stage"]])
        drawn += 1
    for group in stage_groups.values():
        group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.get_root().html.add_child(folium.Element(_legend_html(coverage)))
    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_html))
    return {"roads_drawn": counts, "unassigned_roads": unassigned, "notices_drawn": drawn, "notices_listed": len(notices)}


def _legend_html(coverage: Coverage) -> str:
    rows = []
    for v in coverage.roads.values():
        rows.append(f'<div><span style="display:inline-block;width:18px;height:4px;background:{v["colour"]};margin-right:6px"></span>{v["label"]}</div>')
    rows.append("<hr>")
    for v in coverage.stages.values():
        rows.append(f'<div><span style="display:inline-block;width:18px;height:10px;background:{v["colour"]};margin-right:6px"></span>{v["label"]}</div>')
    return (
        '<div style="position:fixed;bottom:24px;left:24px;z-index:9999;background:white;padding:10px 12px;'
        'border:1px solid #999;font:12px sans-serif;max-width:320px">'
        "<b>Legend</b>" + "".join(rows) + "<hr><small>Not advice. Source and date on every notice.</small></div>"
    )


def load_notices(path: Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
