"""Backups and restore test (Phase 7, docs/DATABASE.md section 8, docs/DEPLOYMENT.md section 4).

- create_backup: copies storage/ to a dated folder. owners.db is copied with SQLite's online backup,
  so the copy is consistent even while the service runs. A manifest records SHA-256 of every file.
- verify_backup: re-hashes every file and compares with the manifest.
- restore_test: opens the backed-up owners.db in a temp folder, counts rows, and decrypts one name
  with OWNER_DB_KEY. It does not write an audit line, because it is a check, not a view of an owner.
  The temp copy is deleted afterwards.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

SKIP_NAMES = {"auth_session", "whatsapp_outbox.jsonl"}
SKIP_SUFFIXES = (".tmp",)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy_db(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(src) as source, sqlite3.connect(dst) as target:
        source.backup(target)


def create_backup(storage: Path, dest_root: Path, stamp: str | None = None) -> Path:
    storage = Path(storage)
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = Path(dest_root) / stamp
    dest.mkdir(parents=True, exist_ok=False)
    files: dict[str, str] = {}
    for src in sorted(storage.rglob("*")):
        rel = src.relative_to(storage)
        if any(part in SKIP_NAMES for part in rel.parts) or src.name.endswith(SKIP_SUFFIXES):
            continue
        if not src.is_file():
            continue
        target = dest / rel
        if src.name == "owners.db":
            _copy_db(src, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
        files[str(rel)] = _sha256(target)
    (dest / "backup_manifest.json").write_text(
        json.dumps({"created_at": stamp, "files": files}, indent=2), encoding="utf-8"
    )
    return dest


def verify_backup(backup_dir: Path) -> tuple[bool, list[str]]:
    manifest = json.loads((Path(backup_dir) / "backup_manifest.json").read_text(encoding="utf-8"))
    bad = []
    for rel, digest in manifest["files"].items():
        path = Path(backup_dir) / rel
        if not path.exists() or _sha256(path) != digest:
            bad.append(rel)
    return (not bad), bad


def restore_test(backup_dir: Path, live_db: Path, key: str) -> dict[str, Any]:
    """Check the backed-up owner database opens, has the same row count, and decrypts with the key."""
    backup_db = Path(backup_dir) / "owners.db"
    result: dict[str, Any] = {"backup_present": backup_db.exists()}
    if not backup_db.exists():
        result.update(ok=False, reason="owners.db missing from backup")
        return result
    with tempfile.TemporaryDirectory(prefix="tn-restore-") as tmp:
        copy = Path(tmp) / "owners.db"
        _copy_db(backup_db, copy)
        with sqlite3.connect(copy) as conn:
            backup_count = conn.execute("SELECT COUNT(*) FROM owner").fetchone()[0]
            first = conn.execute("SELECT owner_name_enc FROM owner ORDER BY id LIMIT 1").fetchone()
        decrypt_ok = True
        if first is not None:
            try:
                Fernet(key.encode("ascii")).decrypt(first[0])
            except (InvalidToken, ValueError):
                decrypt_ok = False
    live_count = None
    if Path(live_db).exists():
        with sqlite3.connect(live_db) as conn:
            live_count = conn.execute("SELECT COUNT(*) FROM owner").fetchone()[0]
    result.update(
        owners_backup=backup_count,
        owners_live=live_count,
        decrypt_ok=decrypt_ok,
        ok=decrypt_ok and (live_count is None or live_count == backup_count),
    )
    return result
