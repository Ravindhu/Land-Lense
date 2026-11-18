"""Auction intake (Phase 5, manual import first, docs/RULES.md section 6, docs/ROADMAP.md phase 5).

Input is a JSON list of auction records. Each record is validated against AuctionProperty.
Notice PDFs must already sit under raw_pdfs/ (no path traversal). Scheduled scraping of bank
e-auction sites stays off until each site's terms are cleared (docs/SOURCES.md).
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from tn_highway_intel.domain.models import AuctionProperty


class AuctionIntakeError(ValueError):
    pass


def safe_notice_path(raw_dir: Path, notice_pdf: str) -> Path:
    """Resolve a notice PDF path and refuse anything outside raw_dir."""
    candidate = (Path(raw_dir) / notice_pdf).resolve()
    root = Path(raw_dir).resolve()
    if root not in candidate.parents:
        raise AuctionIntakeError("notice_pdf must be inside raw_pdfs/")
    return candidate


def load_auctions(path: Path, raw_dir: Path) -> tuple[list[AuctionProperty], list[dict]]:
    """Return (valid, rejected). Rejected entries carry the field names that failed, never values."""
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise AuctionIntakeError("expected a JSON list of auction records")
    valid: list[AuctionProperty] = []
    rejected: list[dict] = []
    for index, row in enumerate(rows):
        try:
            record = AuctionProperty.model_validate(row)
            safe_notice_path(raw_dir, record.notice_pdf)
            valid.append(record)
        except (ValidationError, AuctionIntakeError) as err:
            fields = sorted({".".join(str(p) for p in e["loc"]) for e in err.errors()}) if isinstance(err, ValidationError) else ["notice_pdf"]
            rejected.append({"index": index, "fields": fields})
    return valid, rejected
