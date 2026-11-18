"""TNGIS cadastral collector (Phase 3). Gated: stays disabled until TNGIS terms are read and cleared.

The fetch itself is not implemented. Until permission is confirmed, parcels come from
collectors/manual_parcels.py. docs/SOURCES.md lists TNGIS as "Open. Read before any automated access."
"""

from __future__ import annotations

from tn_highway_intel.domain.settings import CollectorSettings


class TngisDisabled(RuntimeError):
    pass


class TngisCadastralCollector:
    name = "tngis_cadastral"

    def __init__(self, settings: CollectorSettings) -> None:
        self.settings = settings

    def require_enabled(self) -> None:
        if not (self.settings.enabled and self.settings.terms_cleared):
            raise TngisDisabled("tngis_cadastral is disabled until TNGIS terms are cleared (docs/SOURCES.md)")

    def fetch_village(self, district: str, taluk: str, village: str):  # pragma: no cover - gated
        self.require_enabled()
        raise NotImplementedError("TNGIS fetch is not implemented; use manual_parcels until permission is confirmed")
