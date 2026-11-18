"""Small JSON record store with idempotent upserts (docs/ARCHITECTURE.md section 5).

Records are kept in a list in one JSON file, written atomically. An idempotency index maps a
natural key to the stored record's ID so that a resend returns "duplicate" and writes nothing.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Optional


class JsonStore:
    _lock = threading.Lock()

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, items: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def upsert(self, key_field: str, record: dict[str, Any]) -> tuple[str, Optional[str]]:
        """Insert a record unless its key already exists. Returns ("created"|"duplicate", key)."""
        key = str(record[key_field])
        with self._lock:
            items = self.read()
            if any(str(item.get(key_field)) == key for item in items):
                return "duplicate", key
            items.append(record)
            self._write(items)
        return "created", key

    def replace_all(self, items: list[dict[str, Any]]) -> None:
        with self._lock:
            self._write(items)
