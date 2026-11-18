"""Inbound webhook (Phase 5, docs/API.md section 1). Bound to 127.0.0.1 behind the HTTPS proxy.

Order of checks on every write: content type (415) -> secret (401) -> size (413) -> rate limit (429)
-> schema (400) -> idempotency (200 duplicate / 201 created). Error bodies never echo request data.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tn_highway_intel.domain.audit import AuditLog
from tn_highway_intel.domain.models import AuctionProperty
from tn_highway_intel.domain.settings import get_env, storage_dir
from tn_highway_intel.engine.listing_parser import parse_listing
from tn_highway_intel.services.store import JsonStore
from tn_highway_intel.services.webhook_guard import RateLimiter, secret_matches

log = logging.getLogger("tn_intel.webhook")

MAX_BODY_BYTES = 64 * 1024
RATE_PER_MINUTE = 60


class WhatsAppListingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1, max_length=200)
    group_ref: str = Field(min_length=1, max_length=200)
    received_at: datetime
    text: str = Field(min_length=1, max_length=2000)


class AuctionIn(AuctionProperty):
    """Same fields as AuctionProperty. Matching and borrower handling happen in the engine, not at intake."""

    matched_parcel_id: Optional[str] = None
    borrower_name: Optional[str] = None


def _error(status: int, code: str, fields: Optional[list[str]] = None, headers: Optional[dict[str, str]] = None) -> JSONResponse:
    body: dict = {"error": code}
    if fields is not None:
        body["fields"] = fields
    return JSONResponse(body, status_code=status, headers=headers)


def create_app(
    secret: Optional[str],
    storage: Path,
    clock: Callable[[], float] = time.monotonic,
    rate_per_minute: int = RATE_PER_MINUTE,
) -> FastAPI:
    app = FastAPI(title="tn-highway-intel webhook", docs_url=None, redoc_url=None, openapi_url=None)
    limiter = RateLimiter(rate_per_minute, clock)
    listings = JsonStore(storage / "whatsapp_deals.json")
    auctions = JsonStore(storage / "auction_listings.json")
    audit = AuditLog(storage / "audit_log.jsonl")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    async def _guard(request: Request) -> Optional[JSONResponse]:
        if "application/json" not in request.headers.get("content-type", ""):
            return _error(415, "unsupported_media_type")
        if secret is None:
            return _error(503, "not_configured")
        if not secret_matches(request.headers.get("x-webhook-secret"), secret):
            log.info("rejected request: bad secret path=%s", request.url.path)
            return _error(401, "unauthorized")
        declared = request.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            return _error(413, "too_large")
        ok, retry = limiter.allow()
        if not ok:
            return _error(429, "rate_limited", headers={"Retry-After": str(retry)})
        return None

    async def _json(request: Request) -> tuple[Optional[dict], Optional[JSONResponse]]:
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            return None, _error(413, "too_large")
        try:
            return json.loads(body), None
        except json.JSONDecodeError:
            return None, _error(400, "validation", ["body"])

    @app.post("/v1/listings/whatsapp")
    async def whatsapp(request: Request):
        refused = await _guard(request)
        if refused:
            return refused
        data, err = await _json(request)
        if err:
            return err
        try:
            item = WhatsAppListingIn.model_validate(data)
        except ValidationError as exc:
            return _error(400, "validation", sorted({".".join(map(str, e["loc"])) for e in exc.errors()}))
        fields = parse_listing(item.text)
        record = {
            "message_id": item.message_id,
            "group_ref": item.group_ref,
            "received_on": item.received_at.date().isoformat(),
            "title": "Broker listing",
            "village": fields["village"],
            "survey_ref": fields["survey_ref"],
            "price_inr": fields["price_inr"],
            "plot_size": fields["plot_size"],
            "contact_phone": fields["contact_phone"],
            "source": f"whatsapp group {item.group_ref}",
        }
        outcome, key = listings.upsert("message_id", record)
        if outcome == "created":
            audit.append("listing_create", "webhook", f"listing:{key}", {"message_id": key})
            return JSONResponse({"id": key, "status": "created"}, status_code=201)
        return JSONResponse({"id": key, "status": "duplicate"}, status_code=200)

    @app.post("/v1/auctions")
    async def auction(request: Request):
        refused = await _guard(request)
        if refused:
            return refused
        data, err = await _json(request)
        if err:
            return err
        try:
            item = AuctionIn.model_validate(data)
        except ValidationError as exc:
            return _error(400, "validation", sorted({".".join(map(str, e["loc"])) for e in exc.errors()}))
        record = item.model_dump(mode="json")
        record["key"] = f"{item.auction_id}:{item.notice_date.isoformat()}"
        outcome, key = auctions.upsert("key", record)
        if outcome == "created":
            audit.append("auction_create", "webhook", f"auction:{item.auction_id}", {"auction_id": item.auction_id})
            return JSONResponse({"id": item.auction_id, "status": "created"}, status_code=201)
        return JSONResponse({"id": item.auction_id, "status": "duplicate"}, status_code=200)

    return app


def _default_app() -> FastAPI:
    return create_app(secret=get_env("WEBHOOK_SECRET"), storage=storage_dir())


app = _default_app()
