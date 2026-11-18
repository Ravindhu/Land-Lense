import json

import pytest

from tn_highway_intel.domain.audit import AuditError, AuditLog
from tn_highway_intel.domain.settings import MissingSecret, load_settings, require_env, project_root


def test_project_root_finds_pyproject():
    assert (project_root() / "pyproject.toml").exists()


def test_settings_load_defaults_from_yaml():
    s = load_settings()
    assert s.approval_stage == "3D"
    assert s.target_zone.margin_ft == 20
    assert s.target_zone.margin_m == pytest.approx(6.096)
    assert s.collector("central_egazette").enabled is False


def test_unknown_collector_is_disabled():
    s = load_settings()
    assert s.collector("does_not_exist").enabled is False


def test_require_env_raises_without_printing_value(monkeypatch):
    monkeypatch.delenv("TN_TEST_SECRET", raising=False)
    with pytest.raises(MissingSecret) as err:
        require_env("TN_TEST_SECRET")
    assert "TN_TEST_SECRET" in str(err.value)


def test_audit_chain_verifies_and_detects_tamper(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append("create", "owner-service", "owner:1", {"owner_id": 1})
    log.append("view", "owner-panel", "owner:1", {"owner_id": 1})
    assert log.verify() == (True, None)

    lines = (tmp_path / "audit.jsonl").read_text().splitlines()
    record = json.loads(lines[0])
    record["detail"]["owner_id"] = 999
    lines[0] = json.dumps(record, sort_keys=True)
    (tmp_path / "audit.jsonl").write_text("\n".join(lines) + "\n")
    assert log.verify() == (False, 1)


def test_audit_refuses_personal_data_keys(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    with pytest.raises(AuditError):
        log.append("view", "owner-panel", "owner:1", {"owner_name": "Someone"})
    assert not (tmp_path / "audit.jsonl").exists()
