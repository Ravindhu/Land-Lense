import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from tn_highway_intel.domain.audit import AuditLog
from tn_highway_intel.domain.settings import load_settings
from tn_highway_intel.services import alerts
from tn_highway_intel.services.backup import create_backup, restore_test, verify_backup
from tn_highway_intel.services.daily_sync import run_sync

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 18)


class FakeResponse:
    def __init__(self, status):
        self.status_code = status


class FakeSession:
    def __init__(self, status=200, raise_exc=False):
        self.status = status
        self.raise_exc = raise_exc
        self.calls = []

    def post(self, url, data=None, timeout=None):
        self.calls.append({"url": url, "data": data})
        if self.raise_exc:
            raise ConnectionError("network down")
        return FakeResponse(self.status)


# ---- alerts -------------------------------------------------------------

def test_redact_removes_pan_aadhaar_and_masks_phone():
    text = "PAN ABCDE1234F, aadhaar 2345 6789 0123, call 9876543210"
    out = alerts.redact(text)
    assert "ABCDE1234F" not in out
    assert "2345 6789 0123" not in out
    assert "9876543210" not in out
    assert out.endswith("3210")


def test_alert_refused_when_protected_term_present(tmp_path):
    session = FakeSession()
    with pytest.raises(alerts.AlertRefused):
        alerts.send_alert(
            "Owner Ravi Kumar has a new notice",
            token="t", chat_id="1", protected_terms=["Ravi Kumar"], session=session,
        )
    assert session.calls == []


def test_alert_sent_and_text_is_redacted():
    session = FakeSession(status=200)
    ok = alerts.send_alert("Targets 3, phone 9876543210", token="t", chat_id="1", session=session)
    assert ok is True
    sent = session.calls[0]["data"]["text"]
    assert "9876543210" not in sent


def test_failed_send_is_queued_and_flushed(tmp_path):
    pending = tmp_path / "alerts_pending.jsonl"
    ok = alerts.send_alert("sync partial", token="t", chat_id="1", pending_path=pending, session=FakeSession(raise_exc=True))
    assert ok is False
    assert pending.exists()
    sent = alerts.flush_pending(pending, token="t", chat_id="1", session=FakeSession(status=200))
    assert sent == 1
    assert not pending.exists()


def test_missing_token_queues_without_network(tmp_path):
    pending = tmp_path / "alerts_pending.jsonl"
    session = FakeSession()
    assert alerts.send_alert("hello", token=None, chat_id=None, pending_path=pending, session=session) is False
    assert session.calls == []
    assert pending.exists()


def test_token_never_in_queue_file(tmp_path):
    pending = tmp_path / "alerts_pending.jsonl"
    alerts.send_alert("x", token="SECRET-TOKEN-XYZ", chat_id="1", pending_path=pending, session=FakeSession(status=500))
    assert "SECRET-TOKEN-XYZ" not in pending.read_text()


# ---- backup and restore -------------------------------------------------

@pytest.fixture
def storage(tmp_path):
    s = tmp_path / "storage"
    s.mkdir()
    key = Fernet.generate_key().decode()
    db = s / "owners.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE owner (id INTEGER PRIMARY KEY, owner_name_enc TEXT)")
        f = Fernet(key.encode())
        conn.execute("INSERT INTO owner (owner_name_enc) VALUES (?)", (f.encrypt(b"Test Owner").decode(),))
        conn.execute("INSERT INTO owner (owner_name_enc) VALUES (?)", (f.encrypt(b"Second Owner").decode(),))
    (s / "targets.json").write_text("[]")
    (s / "auth_session").mkdir()
    (s / "auth_session" / "creds.json").write_text("{}")
    (s / "x.tmp").write_text("partial")
    return s, key


def test_backup_skips_session_and_tmp_and_verifies(storage, tmp_path):
    s, _ = storage
    dest = create_backup(s, tmp_path / "backups", stamp="20261118T000000Z")
    assert (dest / "owners.db").exists()
    assert (dest / "targets.json").exists()
    assert not (dest / "auth_session").exists()
    assert not (dest / "x.tmp").exists()
    ok, bad = verify_backup(dest)
    assert ok and bad == []


def test_backup_tamper_is_detected(storage, tmp_path):
    s, _ = storage
    dest = create_backup(s, tmp_path / "backups", stamp="t1")
    (dest / "targets.json").write_text("[{\"tampered\": true}]")
    ok, bad = verify_backup(dest)
    assert not ok
    assert "targets.json" in bad


def test_restore_test_counts_rows_and_decrypts_without_audit(storage, tmp_path):
    s, key = storage
    dest = create_backup(s, tmp_path / "backups", stamp="t2")
    result = restore_test(dest, s / "owners.db", key)
    assert result["ok"] is True
    assert result["owners_backup"] == 2
    assert result["owners_live"] == 2
    assert result["decrypt_ok"] is True
    assert "Test Owner" not in json.dumps(result)


def test_restore_test_fails_with_wrong_key(storage, tmp_path):
    s, _ = storage
    dest = create_backup(s, tmp_path / "backups", stamp="t3")
    result = restore_test(dest, s / "owners.db", Fernet.generate_key().decode())
    assert result["decrypt_ok"] is False
    assert result["ok"] is False


def test_restore_test_temp_copy_removed(storage, tmp_path, monkeypatch):
    s, key = storage
    dest = create_backup(s, tmp_path / "backups", stamp="t4")
    seen = {}
    import tn_highway_intel.services.backup as backup_mod

    real = backup_mod._copy_db

    def spy(src, dst):
        seen["dst"] = Path(dst)
        real(src, dst)

    monkeypatch.setattr(backup_mod, "_copy_db", spy)
    restore_test(dest, s / "owners.db", key)
    assert not seen["dst"].exists()


# ---- audit chain --------------------------------------------------------

def test_audit_tamper_detected(tmp_path):
    path = tmp_path / "audit_log.jsonl"
    log = AuditLog(path)
    log.append("sync_run", "daily_sync", "sync", {"status": "ok"})
    log.append("sync_run", "daily_sync", "sync", {"status": "ok"})
    assert log.verify()[0] is True
    lines = path.read_text().splitlines()
    lines[0] = lines[0].replace('"ok"', '"partial"')
    path.write_text("\n".join(lines) + "\n")
    ok, line = log.verify()
    assert ok is False
    assert line == 1


# ---- daily sync end to end (no alignment, no OCR client) ------------------

def test_sync_without_inputs_writes_status_and_outputs(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    settings = load_settings(ROOT / "config" / "settings.yaml")
    status = run_sync(storage, settings, ocr_client=None, today=TODAY)
    assert status["status"] == "partial"  # alignment missing is reported, not hidden
    assert "missing" in status["steps"]["alignment"]
    assert json.loads((storage / "targets.json").read_text()) == []
    assert json.loads((storage / "sync_status.json").read_text())["status"] == "partial"
    lines = (storage / "audit_log.jsonl").read_text().splitlines()
    assert json.loads(lines[-1])["action"] == "sync_run"
    assert "audit_chain" in status["steps"]


def test_sync_status_has_no_owner_data(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    settings = load_settings(ROOT / "config" / "settings.yaml")
    run_sync(storage, settings, ocr_client=None, today=TODAY)
    text = (storage / "sync_status.json").read_text() + (storage / "audit_log.jsonl").read_text()
    for forbidden in ("owner_name", "aadhaar", "pan_masked", "contact_phone", "borrower_name"):
        assert forbidden not in text


def test_sync_alert_sent_only_on_partial(tmp_path):
    storage = tmp_path / "storage"
    storage.mkdir()
    settings = load_settings(ROOT / "config" / "settings.yaml")
    messages = []
    run_sync(storage, settings, ocr_client=None, alert=messages.append, today=TODAY)
    assert len(messages) == 1
    assert "partial" in messages[0]
