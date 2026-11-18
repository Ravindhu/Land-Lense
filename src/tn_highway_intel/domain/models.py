"""Pydantic models. Shapes follow docs/DATA_MODEL.md. All models forbid unknown fields."""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Stage = Literal["3A", "3C", "3D", "3E", "3G", "3H"]
STAGE_ORDER: dict[str, int] = {"3A": 1, "3C": 2, "3D": 3, "3E": 4, "3G": 5, "3H": 6}

# Masked PAN only: five letters, four stars, one letter. A full PAN never matches.
MASKED_PAN_RE = re.compile(r"^[A-Z]{5}\*{4}[A-Z]$")
LAST4_RE = re.compile(r"^\d{4}$")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NoticeDot(_Strict):
    dot_id: str
    district: str
    taluk: str
    village: str
    survey_no: str
    stage: Stage
    gazette_id: str
    gazette_date: date
    source_pdf: str
    source_page: int = Field(ge=1)
    coords: tuple[float, float]
    snap_distance_m: Optional[float] = Field(default=None, ge=0)
    confidence: float = Field(ge=0, le=1)
    status: Literal["mapped", "review"] = "mapped"

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        """Idempotency key from AGENTS.md rule 7."""
        return (self.district, self.taluk, self.village, self.survey_no, self.gazette_id)


class SurveyParcel(_Strict):
    parcel_id: str
    district: str
    taluk: str
    village: str
    survey_no: str
    polygon: dict  # GeoJSON geometry, coordinates in the project CRS (metres)
    area_sqft: Optional[float] = Field(default=None, ge=0)
    area_cents: Optional[float] = Field(default=None, ge=0)
    source: Literal["tngis", "manual"]
    retrieved_on: date


class PattaRecord(_Strict):
    district: str
    taluk: str
    village: str
    survey_no: str
    patta_no: str
    land_type: str
    source: str
    verified_on: date


class OwnerDetails(_Strict):
    """Owner record. Shown only in the authenticated owner panel (docs/RULES.md section 7)."""

    owner_id: Optional[int] = None
    owner_name: str = Field(min_length=1)
    pan_masked: Optional[str] = None
    aadhaar_last4: Optional[str] = None
    owner_source: str = Field(min_length=1)
    verified_on: date

    @field_validator("pan_masked")
    @classmethod
    def _masked_only(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not MASKED_PAN_RE.match(value):
            raise ValueError("pan must be masked, e.g. ABCDE****F; full PAN is not stored")
        return value

    @field_validator("aadhaar_last4")
    @classmethod
    def _last4_only(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not LAST4_RE.match(value):
            raise ValueError("aadhaar_last4 must be exactly 4 digits")
        return value


class TargetParcel(_Strict):
    parcel_id: str
    survey_no: str
    village: str
    taluk: str
    district: str
    stage: Stage
    gazette_date: date
    source_pdf: str
    area_sqft: Optional[float] = None
    area_cents: Optional[float] = None
    dist_to_alignment_m: float = Field(ge=0)
    dist_to_row_edge_m: float
    dist_to_zone_edge_m: float
    side: Literal["left", "right"]
    row_width_m: float = Field(gt=0)
    margin_m: float = Field(default=6.096, gt=0)
    owner_ref: Optional[str] = None  # an owner id, never a name
    updated_on: date


class OfficialMapEntry(_Strict):
    map_id: str
    map_name: str
    map_file: str
    district: str
    taluk: str
    village: str
    survey_no: str
    village_cross: Optional[tuple[float, float]] = None
    road_cross: Optional[dict] = None
    chainage_km: Optional[float] = None
    circular_no: Optional[str] = None
    circular_date: Optional[date] = None
    circular_office: Optional[str] = None
    circular_pdf: Optional[str] = None
    georef_points: list[tuple[tuple[float, float], tuple[float, float]]] = Field(default_factory=list)


class AuctionProperty(_Strict):
    auction_id: str
    bank_name: str
    property_address: str
    survey_no: str
    village: str
    reserve_price_inr: int = Field(ge=0)
    emd_inr: Optional[int] = Field(default=None, ge=0)
    auction_date: date
    status: Literal["active", "expired", "sold"]
    notice_pdf: str
    notice_date: date
    source_url: str
    matched_parcel_id: Optional[str] = None
    borrower_name: Optional[str] = None  # stored only when matched (RULES section 6)

    @field_validator("source_url")
    @classmethod
    def _https_only(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("source_url must be https")
        return value


class PropertyPin(_Strict):
    title: str
    price_inr: Optional[int] = None
    plot_size: Optional[str] = None
    village: Optional[str] = None
    survey_ref: Optional[str] = None
    contact_phone: Optional[str] = None  # masked in every alert and export
    source: str
    url: Optional[str] = None
    distance_to_highway_m: Optional[float] = None
    received_on: date


class MapState(_Strict):
    show_alignment: bool = True
    show_dots: bool = True
    show_targets: bool = True
    show_pending: bool = False
    show_auctions: bool = False
    show_contacts: bool = False
    show_scores: bool = False
