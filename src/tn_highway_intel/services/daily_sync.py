"""Daily pipeline (Phase 7, FR-11, docs/ARCHITECTURE.md section 2).

Steps, each recorded in sync_status.json:
  1. collectors   central gazette fetch, only when enabled and terms cleared (otherwise skipped)
  2. ocr          parse new gazette PDFs from the manifest (cache by hash; skipped without a client)
  3. centroids    parcel centroids from manual parcels (TNGIS stays gated)
  4. dots         place each OCR record on its parcel centroid; no match goes to review
  5. alignment    snap dots to the official alignment; far dots go to review
  6. targets      apply the target rule (approval stage, zone, survey match)
  7. auctions     expire past auctions; match to targets; borrower kept only for matches
  8. write        JSON outputs for the dashboard, audit line, and an alert if not fully ok

Status never includes owner data. Alerts pass through redaction in services/alerts.py.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from shapely.geometry import shape

from tn_highway_intel.collectors.auction_listings import AuctionIntakeError  # noqa: F401 (documented failure type)
from tn_highway_intel.collectors.manual_parcels import load_manual_parcels
from tn_highway_intel.domain.audit import AuditLog
from tn_highway_intel.domain.models import AuctionProperty, NoticeDot, SurveyParcel, TargetParcel
from tn_highway_intel.domain.settings import Settings, get_env, load_env, load_settings, project_root, storage_dir
from tn_highway_intel.engine.auction_match import auction_pins, expire_if_past, match_auctions
from tn_highway_intel.engine.dot_snapper import snap_dots
from tn_highway_intel.engine.gazette_parser import OcrClient, ReviewItem, parse_gazette, to_notice_dots
from tn_highway_intel.engine.official_map import load_alignment
from tn_highway_intel.engine.ocr_cache import OcrCache
from tn_highway_intel.engine.target_filter import select_targets
from tn_highway_intel.services.alerts import send_alert
from tn_highway_intel.services.review_queue import ReviewQueue

log = logging.getLogger("tn_intel.sync")


@dataclass
class SyncContext:
    storage: Path
    settings: Settings
    today: date
    review: list[ReviewItem] = field(default_factory=list)
    steps: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    ocr_stats: dict[str, Any] = field(default_factory=lambda: {"pdfs_seen": 0, "pdfs_parsed": 0, "cache_hits": 0, "model_calls": 0, "usage": {}})


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _ocr_step(ctx: SyncContext, client: Optional[OcrClient]) -> tuple[list[tuple[dict, Any]], set[str]]:
    """Return ([(source, OcrRecord)...], newly_processed_hashes)."""
    manifest = _read_json(ctx.storage / "raw_pdfs" / "manifest.json", [])
    processed = set(_read_json(ctx.storage / "processed_pdfs.json", []))
    ctx.ocr_stats["pdfs_seen"] = len(manifest)
    if client is None:
        ctx.steps["ocr"] = "skipped: no OCR client configured (set GEMINI_API_KEY)"
        return [], set()
    cache = OcrCache(ctx.storage / "ocr_cache")
    collected: list[tuple[dict, Any]] = []
    newly: set[str] = set()
    failures = 0
    for entry in manifest:
        if entry["sha256"] in processed:
            continue
        pdf_path = ctx.storage / "raw_pdfs" / entry["path"]
        try:
            result = parse_gazette(
                pdf_path.read_bytes(),
                source_pdf=entry["path"],
                client=client,
                cache=cache,
                prompt_version=ctx.settings.ocr.prompt_version,
            )
        except Exception as err:  # one bad PDF must not stop the run
            failures += 1
            ctx.errors.append(f"ocr failed for {entry['path']}: {type(err).__name__}")
            continue
        ctx.ocr_stats["pdfs_parsed"] += 1
        if result.cache_hit:
            ctx.ocr_stats["cache_hits"] += 1
        else:
            ctx.ocr_stats["model_calls"] += 1
            for k, v in (result.usage or {}).items():
                if isinstance(v, (int, float)):
                    ctx.ocr_stats["usage"][k] = ctx.ocr_stats["usage"].get(k, 0) + v
        ctx.review.extend(result.review)
        source = {"source_pdf": entry["path"], "gazette_id": entry["gazette_id"], "gazette_date": entry["gazette_date"]}
        for rec in result.records:
            collected.append((source, rec))
        newly.add(entry["sha256"])
    ctx.steps["ocr"] = "ok" if failures == 0 else f"partial: {failures} PDF(s) failed"
    return collected, newly


def _parcels(ctx: SyncContext) -> list[SurveyParcel]:
    path = ctx.storage / "manual_parcels.geojson"
    if not path.exists():
        ctx.steps["parcels"] = "skipped: no manual_parcels.geojson (TNGIS gated)"
        return []
    ctx.steps["parcels"] = "ok"
    return load_manual_parcels(path)


def run_sync(
    storage: Path,
    settings: Settings,
    ocr_client: Optional[OcrClient] = None,
    alert: Optional[Any] = None,
    today: Optional[date] = None,
) -> dict[str, Any]:
    storage = Path(storage)
    today = today or datetime.now(timezone.utc).date()
    started = datetime.now(timezone.utc)
    ctx = SyncContext(storage=storage, settings=settings, today=today)
    audit = AuditLog(storage / "audit_log.jsonl")

    chain_ok, first_bad = audit.verify()
    ctx.steps["audit_chain"] = "ok" if chain_ok else f"tampered: first bad line {first_bad}"
    ctx.steps["collectors"] = "ok: no collector run by daily_sync (enable via CLI when terms are cleared)"
    collected, newly_processed = _ocr_step(ctx, ocr_client)

    parcels = _parcels(ctx)
    centroids: dict[tuple[str, str], tuple[float, float]] = {}
    for p in parcels:
        c = shape(p.polygon).centroid
        centroids[(p.village, p.survey_no)] = (c.x, c.y)

    dots: list[NoticeDot] = []
    by_source: dict[str, tuple[dict, list[Any]]] = {}
    for source, rec in collected:
        by_source.setdefault(source["source_pdf"], (source, []))[1].append(rec)
    for source, records in by_source.values():
        placed, review = to_notice_dots(records, {**source, "gazette_date": source["gazette_date"]}, centroids)
        dots.extend(placed)
        ctx.review.extend(ReviewItem(r.reason, r.source_pdf, r.page, r.detail) for r in review)

    alignment_path = storage / "official_alignment.geojson"
    targets: list[TargetParcel] = []
    pending: list[NoticeDot] = []
    mapped: list[NoticeDot] = []
    if not alignment_path.exists():
        ctx.steps["alignment"] = "missing: no official_alignment.geojson; no dots mapped, no targets computed"
    else:
        alignment = load_alignment(alignment_path)
        mapped, far = snap_dots(dots, alignment, settings.snap_tolerance_m)
        for d in far:
            ctx.review.append(ReviewItem("far_from_alignment", d.source_pdf, d.source_page, {"survey_no": d.survey_no, "village": d.village}))
        ctx.steps["alignment"] = "ok"
        row = settings.target_zone.default_row_width_m
        result = select_targets(
            mapped, parcels, alignment, row, settings.target_zone.margin_m,
            settings.approval_stage, today,
        )
        targets, pending = result.targets, result.pending
        for item in result.review:
            ctx.review.append(ReviewItem(item["reason"], "", None, {k: v for k, v in item.items() if k != "reason"}))
        ctx.steps["targets"] = "ok" if row is not None else "partial: no default row width set; no targets"

    # Auctions: expire, match, and keep borrower names only for matched records.
    auction_path = storage / "auction_listings.json"
    raw_auctions = _read_json(auction_path, [])
    auctions: list[AuctionProperty] = []
    for raw in raw_auctions:
        raw = {k: v for k, v in raw.items() if k != "key"}
        try:
            auctions.append(AuctionProperty.model_validate(raw))
        except Exception:
            ctx.errors.append("auction record skipped: failed validation")
    auctions = [expire_if_past(a, today) for a in auctions]
    matched = match_auctions(auctions, targets)
    _write_json(storage / "auction_matches.json", [a.model_dump(mode="json") for a in matched])
    _write_json(storage / "auction_pins.json", [p.model_dump(mode="json") for p in auction_pins(matched, today)])
    ctx.steps["auctions"] = f"ok: {len(matched)} record(s)"

    # Outputs for the dashboard.
    _write_json(storage / "targets.json", [t.model_dump(mode="json") for t in targets])
    _write_json(storage / "pending.json", [d.model_dump(mode="json") for d in pending])
    _write_json(storage / "notice_dots.json", [d.model_dump(mode="json") for d in mapped])
    ReviewQueue(storage / "review_queue.json").path.unlink(missing_ok=True)
    review_queue = ReviewQueue(storage / "review_queue.json")
    for item in ctx.review:
        review_queue.add(item)
    _write_json(storage / "processed_pdfs.json", sorted(set(_read_json(storage / "processed_pdfs.json", [])) | newly_processed))

    status_name = "ok"
    if ctx.errors or any(v.startswith(("partial", "missing")) for v in ctx.steps.values()):
        status_name = "partial"
    finished = datetime.now(timezone.utc)
    status = {
        "status": status_name,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "steps": ctx.steps,
        "errors": ctx.errors,
        "counts": {
            "dots_placed": len(dots),
            "dots_mapped": len(mapped),
            "targets": len(targets),
            "pending": len(pending),
            "review": len(ctx.review),
            "auctions": len(matched),
        },
        "ocr": ctx.ocr_stats,
    }
    _write_json(storage / "sync_status.json", status)
    audit.append(
        "sync_run",
        "daily_sync",
        "sync",
        {"status": status_name, "targets": len(targets), "dots_mapped": len(mapped), "review": len(ctx.review)},
    )
    if status_name != "ok" and alert is not None:
        alert(f"Daily sync {status_name} at {finished.date().isoformat()}: {', '.join(k for k, v in ctx.steps.items() if v.startswith(('partial', 'missing')))}")
    return status


def main(argv: Optional[list[str]] = None) -> int:
    root = project_root()
    load_env(root)
    settings = load_settings()
    storage = storage_dir(root)
    client = None
    api_key = get_env("GEMINI_API_KEY")
    if settings.ocr.engine == "gemini" and api_key:
        import requests

        from tn_highway_intel.engine.gazette_parser import GeminiOcrClient

        client = GeminiOcrClient(api_key, settings.ocr.model, requests.Session(), settings.ocr.timeout_s)

    token, chat = get_env("TELEGRAM_BOT_TOKEN"), get_env("TELEGRAM_CHAT_ID")

    def alert(text: str) -> None:
        send_alert(text, token=token, chat_id=chat, pending_path=storage / "alerts_pending.jsonl")

    status = run_sync(storage, settings, ocr_client=client, alert=alert)
    print(json.dumps({"status": status["status"], "counts": status["counts"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
