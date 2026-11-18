"""Encrypted owner store (Phase 4, docs/DATABASE.md, docs/RULES.md section 7).

- Names and last-4 Aadhaar are encrypted with Fernet (key from OWNER_DB_KEY, never stored here).
- Masked PAN and dates are plain text. A full PAN is rejected by the model before it reaches this layer.
- Every create, view and update writes an audit line that carries IDs only, never names.
- Reads that reveal owner details are logged to owner_access_log as well.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from tn_highway_intel.domain.audit import AuditLog
from tn_highway_intel.domain.models import OwnerDetails


class OwnerStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParcelRef:
    district: str
    taluk: str
    village: str
    survey_no: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fernet(key: str) -> Fernet:
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, TypeError) as err:
        # Do not include the key in the message.
        raise OwnerStoreError("OWNER_DB_KEY is not a valid Fernet key") from err


def _migrate(conn: sqlite3.Connection, migrations: Path) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    files = sorted(migrations.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    for path in files:
        version = int(path.name[:4])
        if version <= current:
            continue
        for statement in path.read_text(encoding="utf-8").split(";\n"):
            if statement.strip():
                conn.execute(statement)
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()
        current = version


class OwnerStore:
    def __init__(self, db_path: Path, key: str, migrations: Path, audit: AuditLog) -> None:
        self.db_path = Path(db_path)
        self._fernet = _fernet(key)
        self._audit = audit
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        _migrate(self._conn, Path(migrations))

    def close(self) -> None:
        self._conn.close()

    def schema_version(self) -> int:
        return self._conn.execute("PRAGMA user_version").fetchone()[0]

    def _enc(self, value: str) -> bytes:
        return self._fernet.encrypt(value.encode("utf-8"))

    def _dec(self, value: bytes) -> str:
        try:
            return self._fernet.decrypt(value).decode("utf-8")
        except InvalidToken as err:
            raise OwnerStoreError("owner record could not be decrypted; check OWNER_DB_KEY") from err

    def add_owner(self, owner: OwnerDetails, parcels: list[ParcelRef], actor: str = "owner-form") -> int:
        now = _now()
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO owner (owner_name_enc, pan_masked, aadhaar_last4_enc, owner_source, verified_on, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    self._enc(owner.owner_name),
                    owner.pan_masked,
                    self._enc(owner.aadhaar_last4) if owner.aadhaar_last4 else None,
                    owner.owner_source,
                    owner.verified_on.isoformat(),
                    now,
                    now,
                ),
            )
            owner_id = int(cur.lastrowid)
            for p in parcels:
                self._conn.execute(
                    "INSERT INTO owner_parcel (owner_id, district, taluk, village, survey_no, parcel_ref, linked_on)"
                    " VALUES (?, ?, ?, ?, ?, NULL, ?)",
                    (owner_id, p.district, p.taluk, p.village, p.survey_no, now[:10]),
                )
        self._audit.append("owner_create", actor, f"owner:{owner_id}", {"owner_id": owner_id, "parcel_count": len(parcels)})
        return owner_id

    def get_owner(self, owner_id: int, actor: str = "owner-panel", session_ref: Optional[str] = None) -> OwnerDetails:
        """Decrypt one owner. Always audited. Use only from the authenticated owner panel."""
        row = self._conn.execute("SELECT * FROM owner WHERE id = ?", (owner_id,)).fetchone()
        if row is None:
            raise OwnerStoreError("owner not found")
        with self._conn:
            self._conn.execute(
                "INSERT INTO owner_access_log (owner_id, action, at, session_ref) VALUES (?, 'view', ?, ?)",
                (owner_id, _now(), _hash_session(session_ref)),
            )
        self._audit.append("owner_view", actor, f"owner:{owner_id}", {"owner_id": owner_id})
        return OwnerDetails(
            owner_id=owner_id,
            owner_name=self._dec(row["owner_name_enc"]),
            pan_masked=row["pan_masked"],
            aadhaar_last4=self._dec(row["aadhaar_last4_enc"]) if row["aadhaar_last4_enc"] else None,
            owner_source=row["owner_source"],
            verified_on=row["verified_on"],
        )

    def owner_for_parcel(self, ref: ParcelRef) -> Optional[int]:
        """Return an owner ID only. Names are never returned by this lookup."""
        row = self._conn.execute(
            "SELECT owner_id FROM owner_parcel WHERE district = ? AND taluk = ? AND village = ? AND survey_no = ?",
            (ref.district, ref.taluk, ref.village, ref.survey_no),
        ).fetchone()
        return int(row["owner_id"]) if row else None

    def owner_ids(self) -> list[int]:
        return [int(r["id"]) for r in self._conn.execute("SELECT id FROM owner ORDER BY id")]

    def parcels_for(self, owner_id: int) -> list[ParcelRef]:
        rows = self._conn.execute(
            "SELECT district, taluk, village, survey_no FROM owner_parcel WHERE owner_id = ? ORDER BY id",
            (owner_id,),
        ).fetchall()
        return [ParcelRef(r["district"], r["taluk"], r["village"], r["survey_no"]) for r in rows]


def _hash_session(session_ref: Optional[str]) -> Optional[str]:
    """Store a hash of the session reference, never the raw token."""
    if not session_ref:
        return None
    return hashlib.sha256(session_ref.encode("utf-8")).hexdigest()


def new_fernet_key() -> str:
    """Generate a key for OWNER_DB_KEY. Store it in a password manager, separate from backups."""
    return Fernet.generate_key().decode("ascii")

