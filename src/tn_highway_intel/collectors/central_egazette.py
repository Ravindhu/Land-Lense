"""Central gazette collector (Phase 1, FR-1).

Safety gates, in order:
1. The collector runs only when settings say enabled AND terms_cleared (docs/SOURCES.md).
2. Requests are rate limited (min_interval_s between calls) and time out.
3. Only content that starts with %PDF is stored. Files are named by SHA-256, so a re-download
   of the same document is detected and not stored twice.
4. A manifest records hash, URL, gazette ID, date, and fetch time for every stored PDF.

Tests inject a fake session, so no test makes a network call.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from tn_highway_intel.domain.settings import CollectorSettings

REQUEST_TIMEOUT_S = 30
PDF_MAGIC = b"%PDF"


class CollectorDisabled(RuntimeError):
    """Raised when the collector is not enabled or its terms are not cleared."""


class BadDocument(ValueError):
    pass


@dataclass(frozen=True)
class ManifestEntry:
    sha256: str
    url: str
    gazette_id: str
    gazette_date: str
    path: str
    fetched_on: str


class CentralEgazetteCollector:
    name = "central_egazette"

    def __init__(
        self,
        settings: CollectorSettings,
        raw_dir: Path,
        session: Any,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self.raw_dir = Path(raw_dir)
        self.session = session
        self._clock = clock
        self._sleep = sleep
        self._last_call: Optional[float] = None

    def _require_enabled(self) -> None:
        if not (self.settings.enabled and self.settings.terms_cleared):
            raise CollectorDisabled(
                "central_egazette is disabled: enable it and set terms_cleared after reading the site terms"
            )

    def _throttle(self) -> None:
        if self._last_call is not None:
            wait = self.settings.min_interval_s - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    @property
    def manifest_path(self) -> Path:
        return self.raw_dir / "manifest.json"

    def load_manifest(self) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, entries: list[dict]) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.manifest_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.manifest_path)

    def fetch(self, url: str, gazette_id: str, gazette_date: date) -> Optional[ManifestEntry]:
        """Download one gazette PDF. Returns None when identical content is already stored."""
        self._require_enabled()
        if not url.startswith("https://"):
            raise BadDocument("only https URLs are fetched")
        self._throttle()
        response = self.session.get(url, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()
        content: bytes = response.content
        if not content.startswith(PDF_MAGIC):
            raise BadDocument("response is not a PDF")

        digest = hashlib.sha256(content).hexdigest()
        entries = self.load_manifest()
        if any(entry["sha256"] == digest for entry in entries):
            return None

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        rel_path = f"{digest}.pdf"
        (self.raw_dir / rel_path).write_bytes(content)
        entry = ManifestEntry(
            sha256=digest,
            url=url,
            gazette_id=gazette_id,
            gazette_date=gazette_date.isoformat(),
            path=rel_path,
            fetched_on=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        entries.append(asdict(entry))
        self._write_manifest(entries)
        return entry
