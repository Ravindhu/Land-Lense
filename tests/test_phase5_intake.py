import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from shapely.geometry import box, mapping

from tn_highway_intel.collectors.auction_listings import load_auctions, safe_notice_path
from tn_highway_intel.domain.models import AuctionProperty, TargetParcel
from tn_highway_intel.engine.auction_match import auction_pins, expire_if_past, match_auctions
from tn_highway_intel.engine.listing_parser import mask_phone, parse_listing
from tn_highway_intel.services.webhook import create_app
from tn_highway_intel.services.webhook_guard import RateLimiter, secret_matches

SECRET = "test-secret-not-real"
TODAY = date(2026, 11, 18)


@pytest.fixture
def client(tmp_path):
    (tmp_path / "raw_pdfs").mkdir()
    (tmp_path / "raw_pdfs" / "a.pdf").write_bytes(b"%PDF-1 notice")
    app = create_app(secret=SECRET, storage=tmp_path)
    return TestClient(app)


def _auction(**over):
    base = dict(
        auction_id="A-1", bank_name="Sample Bank", property_address="Plot near Ingur",
        survey_no="12", village="Ingur", reserve_price_inr=500000, auction_date="2026-12-10",
        status="active", notice_pdf="a.pdf", notice_date="2026-11-01",
        source_url="https://bank.example/notice/1",
    )
    base.update(over)
    return base


HEADERS = {"x-webhook-secret": SECRET, "content-type": "application/json"}


def test_health_needs_no_secret(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_wrong_secret_is_401_with_generic_body(client):
    r = client.post("/v1/auctions", json=_auction(), headers={"x-webhook-secret": "wrong", "content-type": "application/json"})
    assert r.status_code == 401
    assert r.json() == {"error": "unauthorized"}


def test_missing_secret_is_401(client):
    r = client.post("/v1/auctions", json=_auction(), headers={"content-type": "application/json"})
    assert r.status_code == 401


def test_wrong_content_type_is_415(client):
    r = client.post("/v1/auctions", content=b"x", headers={"x-webhook-secret": SECRET, "content-type": "text/plain"})
    assert r.status_code == 415


def test_oversized_body_is_413(client):
    big = {"text": "x" * 70000}
    r = client.post("/v1/listings/whatsapp", content=json.dumps(big), headers=HEADERS)
    assert r.status_code == 413


def test_unknown_field_is_400_and_error_lists_field_names_only(client):
    body = _auction()
    body["surprise"] = "SECRET-VALUE-123"
    r = client.post("/v1/auctions", json=body, headers=HEADERS)
    assert r.status_code == 400
    assert "surprise" in r.json()["fields"] or "surprise" in str(r.json())
    assert "SECRET-VALUE-123" not in r.text


def test_auction_created_then_duplicate(client):
    first = client.post("/v1/auctions", json=_auction(), headers=HEADERS)
    second = client.post("/v1/auctions", json=_auction(), headers=HEADERS)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"


def test_auction_rejects_http_source(client):
    r = client.post("/v1/auctions", json=_auction(source_url="http://x.example"), headers=HEADERS)
    assert r.status_code == 400


def test_whatsapp_listing_created_then_duplicate_and_phone_masked(client, tmp_path):
    body = {
        "message_id": "m-1", "group_ref": "g-erode", "received_at": "2026-11-18T10:00:00+05:30",
        "text": "Village: Ingur\nSurvey No: 12/3\nPrice: 25 lakh\n2 cents\nCall 9876543210",
    }
    first = client.post("/v1/listings/whatsapp", json=body, headers=HEADERS)
    second = client.post("/v1/listings/whatsapp", json=body, headers=HEADERS)
    assert first.status_code == 201
    assert second.json()["status"] == "duplicate"
    stored = json.loads((tmp_path / "whatsapp_deals.json").read_text())
    assert len(stored) == 1
    assert "9876543210" not in json.dumps(stored)
    assert stored[0]["contact_phone"].endswith("3210")
    assert stored[0]["price_inr"] == 2500000


def test_rate_limit_returns_429_with_retry_after(tmp_path):
    t = {"now": 0.0}
    app = create_app(secret=SECRET, storage=tmp_path, clock=lambda: t["now"], rate_per_minute=2)
    c = TestClient(app)
    assert c.post("/v1/auctions", json=_auction(auction_id="A-2"), headers=HEADERS).status_code == 201
    assert c.post("/v1/auctions", json=_auction(auction_id="A-3"), headers=HEADERS).status_code == 201
    r = c.post("/v1/auctions", json=_auction(auction_id="A-4"), headers=HEADERS)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


def test_no_secret_configured_refuses_writes(tmp_path):
    c = TestClient(create_app(secret=None, storage=tmp_path))
    r = c.post("/v1/auctions", json=_auction(), headers=HEADERS)
    assert r.status_code == 503


def test_secret_check_is_constant_time_helper():
    assert secret_matches("abc", "abc")
    assert not secret_matches("abd", "abc")
    assert not secret_matches(None, "abc")


def test_rate_limiter_refills_over_time():
    t = {"now": 0.0}
    rl = RateLimiter(60, clock=lambda: t["now"])
    for _ in range(60):
        assert rl.allow()[0]
    assert rl.allow()[0] is False
    t["now"] += 1.0
    assert rl.allow()[0] is True


def test_listing_parser_fields_and_masking():
    fields = parse_listing("Village: Ingur\nSurvey No 12/3\nRate: 1.5 cr\n5 cents\nWhatsapp +91 9123456789")
    assert fields["village"] == "Ingur"
    assert fields["survey_ref"] == "12/3"
    assert fields["price_inr"] == 15000000
    assert fields["plot_size"] == "5 cents"
    assert fields["contact_phone"] == mask_phone("9123456789")
    assert "9123456789" not in str(fields)


def test_auction_expires_past_date_and_matches_only_targets():
    t = TargetParcel(
        parcel_id="p-12", survey_no="12", village="Ingur", taluk="P", district="Erode", stage="3D",
        gazette_date=date(2026, 3, 1), source_pdf="a.pdf", dist_to_alignment_m=5,
        dist_to_row_edge_m=5, dist_to_zone_edge_m=10, side="left", row_width_m=45,
        updated_on=TODAY,
    )
    active = AuctionProperty.model_validate({**_auction(), "borrower_name": "Borrower Name"})
    other = AuctionProperty.model_validate({**_auction(auction_id="A-9", survey_no="99"), "borrower_name": "Other Borrower"})
    matched = match_auctions([active, other], [t])
    by_id = {a.auction_id: a for a in matched}
    assert by_id["A-1"].matched_parcel_id == "p-12"
    assert by_id["A-1"].borrower_name == "Borrower Name"
    assert by_id["A-9"].matched_parcel_id is None
    assert by_id["A-9"].borrower_name is None  # borrower kept only when matched

    old = AuctionProperty.model_validate(_auction(auction_id="A-old", auction_date="2026-01-01"))
    assert expire_if_past(old, TODAY).status == "expired"
    pins = auction_pins(matched, TODAY)
    assert len(pins) == 1
    assert "Borrower" not in pins[0].model_dump_json()


def test_notice_path_cannot_escape_raw_dir(tmp_path):
    raw = tmp_path / "raw_pdfs"
    raw.mkdir()
    with pytest.raises(Exception):
        safe_notice_path(raw, "../secret.pdf")


def test_auction_file_import_rejects_bad_rows(tmp_path):
    raw = tmp_path / "raw_pdfs"
    raw.mkdir()
    rows = [_auction(), _auction(auction_id="bad", source_url="http://no")]
    path = tmp_path / "auctions.json"
    path.write_text(json.dumps(rows))
    valid, rejected = load_auctions(path, raw)
    assert len(valid) == 1
    assert rejected[0]["index"] == 1
    assert "source_url" in rejected[0]["fields"]
