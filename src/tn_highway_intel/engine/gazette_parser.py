"""Gazette parser (Phase 2, FR-2).

Flow: PDF bytes -> cache check -> OCR client -> JSON -> schema validation -> records.
Anything low-confidence, malformed, or unmatched goes to the review queue, never to the map.

The OCR client is an interface. GeminiOcrClient is the production client; tests use a fake.
Model output is untrusted: it is parsed and validated before use (AGENTS.md rule 8).
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tn_highway_intel.domain.models import NoticeDot, Stage
from tn_highway_intel.engine.ocr_cache import OcrCache, cache_key

PROMPT_V1 = (
    "You read a Tamil or English Indian highway land-acquisition gazette page. "
    "Return only JSON: {\"records\": [{\"district\": str, \"taluk\": str, \"village\": str, "
    "\"survey_no\": str, \"stage\": one of 3A,3C,3D,3E,3G,3H, \"page\": int, \"confidence\": 0..1}]}. "
    "Copy survey numbers exactly. Do not guess. Use confidence below 0.8 when unsure."
)

LOW_CONFIDENCE = 0.8


class OcrRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    district: str = Field(min_length=1)
    taluk: str = Field(min_length=1)
    village: str = Field(min_length=1)
    survey_no: str = Field(min_length=1)
    stage: Stage
    page: int = Field(ge=1)
    confidence: float = Field(ge=0, le=1)


class OcrOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[OcrRecord]


class OcrClient(Protocol):
    engine: str
    model: str

    def extract(self, pdf_bytes: bytes, prompt: str) -> tuple[str, dict[str, Any]]:
        """Return (raw_text, usage). raw_text must be JSON."""


@dataclass
class ReviewItem:
    reason: str
    source_pdf: str
    page: Optional[int]
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    records: list[OcrRecord]
    review: list[ReviewItem]
    cache_hit: bool
    usage: dict[str, Any]


def parse_gazette(
    pdf_bytes: bytes,
    source_pdf: str,
    client: OcrClient,
    cache: OcrCache,
    prompt_version: str = "v1",
    prompt: str = PROMPT_V1,
) -> ParseResult:
    key = cache_key(pdf_bytes, client.engine, client.model, prompt_version)
    cached = cache.get(key)
    if cached is not None:
        raw, usage, hit = cached["raw"], {}, True
    else:
        raw, usage = client.extract(pdf_bytes, prompt)
        cache.put(key, {"raw": raw, "usage": usage})
        hit = False

    review: list[ReviewItem] = []
    try:
        output = OcrOutput.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as err:
        review.append(ReviewItem("ocr_output_invalid", source_pdf, None, {"error": type(err).__name__}))
        return ParseResult([], review, hit, usage)

    records: list[OcrRecord] = []
    for rec in output.records:
        if rec.confidence < LOW_CONFIDENCE:
            review.append(ReviewItem("low_confidence", source_pdf, rec.page, {"survey_no": rec.survey_no, "confidence": rec.confidence}))
        else:
            records.append(rec)
    return ParseResult(records, review, hit, usage)


def to_notice_dots(
    records: list[OcrRecord],
    source: dict[str, Any],
    centroids: dict[tuple[str, str], tuple[float, float]],
) -> tuple[list[NoticeDot], list[ReviewItem]]:
    """Place each record on its parcel centroid. Records with no parcel match go to review.

    centroids maps (village, survey_no) -> (x, y) in the project CRS, from the cadastral layer.
    """
    dots: list[NoticeDot] = []
    review: list[ReviewItem] = []
    for rec in records:
        coords = centroids.get((rec.village, rec.survey_no))
        if coords is None:
            review.append(ReviewItem("no_parcel_match", source["source_pdf"], rec.page, {"survey_no": rec.survey_no, "village": rec.village}))
            continue
        dots.append(
            NoticeDot(
                dot_id=f"{source['gazette_id']}:{rec.village}:{rec.survey_no}",
                district=rec.district,
                taluk=rec.taluk,
                village=rec.village,
                survey_no=rec.survey_no,
                stage=rec.stage,
                gazette_id=source["gazette_id"],
                gazette_date=source["gazette_date"] if isinstance(source["gazette_date"], date) else date.fromisoformat(source["gazette_date"]),
                source_pdf=source["source_pdf"],
                source_page=rec.page,
                coords=coords,
                confidence=rec.confidence,
            )
        )
    return dots, review


class GeminiOcrClient:
    """Gemini generateContent client over HTTPS. Not exercised live in tests (no key in CI)."""

    engine = "gemini"
    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str, session: Any, timeout_s: float = 120) -> None:
        self._api_key = api_key
        self.model = model
        self._session = session
        self._timeout = timeout_s

    def extract(self, pdf_bytes: bytes, prompt: str) -> tuple[str, dict[str, Any]]:
        body = {
            "contents": [
                {
                    "parts": [
                        {"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("ascii")}},
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
        }
        response = self._session.post(
            self.ENDPOINT.format(model=self.model),
            headers={"x-goog-api-key": self._api_key, "content-type": "application/json"},
            data=json.dumps(body),
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        usage = payload.get("usageMetadata", {})
        return text, usage
