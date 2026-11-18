"""Content-hash OCR cache (docs/TOKEN_OPTIMIZATION.md section 2).

Key = SHA-256 of (PDF bytes, engine, model, prompt version). A cache hit means no model call.
Changing the model or the prompt version changes the key, so stale results are never reused.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


def cache_key(pdf_bytes: bytes, engine: str, model: str, prompt_version: str) -> str:
    h = hashlib.sha256()
    h.update(hashlib.sha256(pdf_bytes).digest())
    h.update(f"|{engine}|{model}|{prompt_version}".encode("utf-8"))
    return h.hexdigest()


class OcrCache:
    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> Optional[dict[str, Any]]:
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def put(self, key: str, value: dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        tmp = self._path(key).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._path(key))
