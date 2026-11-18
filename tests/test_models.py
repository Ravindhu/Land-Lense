from datetime import date

import pytest
from pydantic import ValidationError

from tn_highway_intel.domain.models import (
    AuctionProperty,
    NoticeDot,
    OwnerDetails,
    TargetParcel,
)


def _dot(**overrides):
    base = dict(
        dot_id="d1",
        district="Erode",
        taluk="Perundurai",
        village="Ingur",
        survey_no="123/4",
        stage="3D",
        gazette_id="G-1",
        gazette_date=date(2026, 3, 1),
        source_pdf="raw_pdfs/x.pdf",
        source_page=2,
        coords=(1000.0, 2000.0),
        confidence=0.9,
    )
    base.update(overrides)
    return base


def test_notice_dot_accepts_valid_record():
    dot = NoticeDot(**_dot())
    assert dot.key == ("Erode", "Perundurai", "Ingur", "123/4", "G-1")


def test_notice_dot_rejects_unknown_stage():
    with pytest.raises(ValidationError):
        NoticeDot(**_dot(stage="15(2)"))


def test_notice_dot_rejects_unknown_field():
    with pytest.raises(ValidationError):
        NoticeDot(**_dot(extra_field="x"))


def test_owner_accepts_masked_pan_and_last4():
    owner = OwnerDetails(
        owner_name="Test Owner",
        pan_masked="ABCDE****F",
        aadhaar_last4="1234",
        owner_source="sale deed 2025-01-01",
        verified_on=date(2026, 1, 1),
    )
    assert owner.pan_masked == "ABCDE****F"


def test_owner_rejects_full_pan():
    with pytest.raises(ValidationError):
        OwnerDetails(
            owner_name="Test Owner",
            pan_masked="ABCDE1234F",
            owner_source="sale deed",
            verified_on=date(2026, 1, 1),
        )


def test_owner_rejects_long_aadhaar():
    with pytest.raises(ValidationError):
        OwnerDetails(
            owner_name="Test Owner",
            aadhaar_last4="123456789012",
            owner_source="doc",
            verified_on=date(2026, 1, 1),
        )


def test_owner_requires_source():
    with pytest.raises(ValidationError):
        OwnerDetails(owner_name="Test Owner", owner_source="", verified_on=date(2026, 1, 1))


def test_target_side_must_be_left_or_right():
    with pytest.raises(ValidationError):
        TargetParcel(
            parcel_id="p",
            survey_no="1",
            village="v",
            taluk="t",
            district="d",
            stage="3D",
            gazette_date=date(2026, 1, 1),
            source_pdf="x.pdf",
            dist_to_alignment_m=10,
            dist_to_row_edge_m=1,
            dist_to_zone_edge_m=2,
            side="north",
            row_width_m=45,
            updated_on=date(2026, 1, 1),
        )


def test_auction_requires_https_source():
    with pytest.raises(ValidationError):
        AuctionProperty(
            auction_id="a1",
            bank_name="Bank",
            property_address="addr",
            survey_no="1",
            village="v",
            reserve_price_inr=100000,
            auction_date=date(2026, 12, 1),
            status="active",
            notice_pdf="raw_pdfs/a.pdf",
            notice_date=date(2026, 11, 1),
            source_url="http://insecure.example",
        )
