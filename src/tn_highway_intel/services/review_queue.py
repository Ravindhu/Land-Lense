"""Review queue store (docs/RULES.md section 8). Items hold reasons and sources, never owner data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tn_highway_intel.engine.gazette_parser import ReviewItem

ALLOWED_REASONS = frozenset(
    {
        "ocr_output_invalid",
        "low_confidence",
        "no_parcel_match",
        "far_from_alignment",
        "circular_pending",
        "missing_source",
    }
)


class ReviewQueue:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def add(self, item: ReviewItem) -> None:
        if item.reason not in ALLOWED_REASONS:
            raise ValueError(f"unknown review reason: {item.reason}")
        items = self._load()
        items.append({"reason": item.reason, "source_pdf": item.source_pdf, "page": item.page, "detail": item.detail})
        self._write(items)

    def add_raw(self, reason: str, source_pdf: str, page: int | None, detail: dict[str, Any]) -> None:
        self.add(ReviewItem(reason, source_pdf, page, detail))

    def all(self) -> list[dict[str, Any]]:
        return self._load()

    def _write(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
