"""Auction matching and pins (Phase 5, docs/RULES.md section 6).

- An auction pins to the map only when its survey number and village match a target parcel.
- Borrower names are kept only for matched auctions; unmatched records have borrower_name cleared.
- Expired and sold auctions never become active pins.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from tn_highway_intel.domain.models import AuctionProperty, PropertyPin, TargetParcel


def expire_if_past(auction: AuctionProperty, today: date) -> AuctionProperty:
    if auction.status == "active" and auction.auction_date < today:
        return auction.model_copy(update={"status": "expired"})
    return auction


def match_auctions(
    auctions: list[AuctionProperty],
    targets: list[TargetParcel],
) -> list[AuctionProperty]:
    index = {(t.village, t.survey_no): t.parcel_id for t in targets}
    out: list[AuctionProperty] = []
    for auction in auctions:
        parcel_id = index.get((auction.village, auction.survey_no))
        if parcel_id:
            out.append(auction.model_copy(update={"matched_parcel_id": parcel_id}))
        else:
            out.append(auction.model_copy(update={"matched_parcel_id": None, "borrower_name": None}))
    return out


def auction_pins(matched: list[AuctionProperty], today: date) -> list[PropertyPin]:
    pins: list[PropertyPin] = []
    for a in matched:
        if a.matched_parcel_id is None or a.status != "active" or a.auction_date < today:
            continue
        pins.append(
            PropertyPin(
                title=f"{a.bank_name} auction: {a.property_address}",
                price_inr=a.reserve_price_inr,
                village=a.village,
                survey_ref=a.survey_no,
                source=f"{a.bank_name} e-auction notice {a.notice_date.isoformat()}",
                url=a.source_url,
                received_on=today,
            )
        )
    return pins


def summarize(matched: list[AuctionProperty]) -> dict[str, Any]:
    return {
        "total": len(matched),
        "matched": sum(1 for a in matched if a.matched_parcel_id),
        "active": sum(1 for a in matched if a.status == "active"),
    }
