#!/usr/bin/env bash
# Restore test (docs/DEPLOYMENT.md section 4). Verifies the newest backup and checks owner decryption.
# Requires OWNER_DB_KEY in the environment (or .env). Never prints owner data.
set -euo pipefail
ROOT="${TN_INTEL_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BACKUPS="${TN_INTEL_BACKUPS:-$ROOT/backups}"
STORAGE="${TN_INTEL_STORAGE:-$ROOT/storage}"
PY="${PYTHON:-$ROOT/.venv/bin/python}"
LATEST="$(ls -1d "$BACKUPS"/*/ 2>/dev/null | sort | tail -n 1 || true)"
if [ -z "$LATEST" ]; then
  echo "restore_test: no backup found in $BACKUPS" >&2
  exit 1
fi
"$PY" - "$LATEST" "$STORAGE/owners.db" <<'PY'
import os, sys
from pathlib import Path
from tn_highway_intel.domain.settings import load_env
from tn_highway_intel.services.backup import verify_backup, restore_test
load_env()
backup, live = Path(sys.argv[1]), Path(sys.argv[2])
ok, bad = verify_backup(backup)
if not ok:
    print("restore_test: hash mismatch in", len(bad), "file(s)")
    sys.exit(1)
key = os.environ.get("OWNER_DB_KEY", "")
if not key:
    print("restore_test: OWNER_DB_KEY not set; cannot check decryption")
    sys.exit(1)
result = restore_test(backup, live, key)
print({k: v for k, v in result.items() if k in ("ok", "owners_backup", "owners_live", "decrypt_ok")})
sys.exit(0 if result.get("ok") else 1)
PY
