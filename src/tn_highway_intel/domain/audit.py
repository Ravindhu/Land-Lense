"""Append-only audit log with a hash chain (docs/DATABASE.md section 7).

Each line stores the SHA-256 of the previous line. Changing or removing a line breaks the chain.
Owner names, PAN, Aadhaar, phone numbers and borrower names are refused as detail keys:
the log records IDs and actions, never personal data.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

FORBIDDEN_DETAIL_KEYS = frozenset(
    {
        "owner_name",
        "owner_name_enc",
        "pan",
        "pan_masked",
        "aadhaar",
        "aadhaar_last4",
        "contact_phone",
        "phone",
        "borrower_name",
    }
)
GENESIS = "0" * 64


class AuditError(ValueError):
    pass


def _digest(prev_hash: str, record: dict[str, Any]) -> str:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(f"{prev_hash}|{body}".encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _last_hash(self) -> str:
        if not self.path.exists():
            return GENESIS
        last = GENESIS
        with self.path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = json.loads(line)["hash"]
        return last

    def append(self, action: str, actor: str, entity: str, detail: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        detail = detail or {}
        bad = FORBIDDEN_DETAIL_KEYS.intersection(detail)
        if bad:
            raise AuditError(f"audit detail may not contain personal data keys: {sorted(bad)}")
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "action": action,
            "actor": actor,
            "entity": entity,
            "detail": detail,
            "prev_hash": self._last_hash(),
        }
        record["hash"] = _digest(record["prev_hash"], {k: v for k, v in record.items() if k != "hash"})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        return record

    def verify(self) -> tuple[bool, Optional[int]]:
        """Return (ok, line_number_of_first_break). Line numbers start at 1."""
        if not self.path.exists():
            return True, None
        prev = GENESIS
        with self.path.open("r", encoding="utf-8") as fh:
            for number, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("prev_hash") != prev:
                    return False, number
                expected = _digest(prev, {k: v for k, v in record.items() if k != "hash"})
                if record.get("hash") != expected:
                    return False, number
                prev = record["hash"]
        return True, None
