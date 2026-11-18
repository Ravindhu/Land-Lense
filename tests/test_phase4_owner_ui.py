import json
from datetime import date

import pytest
from shapely.geometry import LineString, box, mapping

from tn_highway_intel.domain.audit import AuditLog
from tn_highway_intel.domain.models import OwnerDetails, SurveyParcel, TargetParcel
from tn_highway_intel.domain.owner_store import OwnerStore, OwnerStoreError, ParcelRef, new_fernet_key
from tn_highway_intel.domain.settings import migrations_dir
from tn_highway_intel.engine.patta_lookup import lookup
from tn_highway_intel.ui.auth import check_password, hash_password
from tn_highway_intel.ui.view_model import assert_no_personal_data, map_features, target_rows

OWNER_NAME = "Test Owner Name"


@pytest.fixture
def store(tmp_path):
    audit = AuditLog(tmp_path / "audit_log.jsonl")
    s = OwnerStore(tmp_path / "owners.db", new_fernet_key(), migrations_dir(), audit)
    yield s
    s.close()


def _owner():
    return OwnerDetails(
        owner_name=OWNER_NAME,
        pan_masked="ABCDE****F",
        aadhaar_last4="4321",
        owner_source="sale deed 2025-01-01 (test fixture)",
        verified_on=date(2026, 1, 1),
    )


def test_migration_sets_schema_version(store):
    assert store.schema_version() == 1


def test_owner_name_is_encrypted_at_rest(store, tmp_path):
    store.add_owner(_owner(), [ParcelRef("Erode", "Perundurai", "Ingur", "12")])
    raw = (tmp_path / "owners.db").read_bytes()
    assert OWNER_NAME.encode() not in raw
    assert b"4321" not in raw  # last-4 Aadhaar encrypted too


def test_get_owner_decrypts_and_is_audited(store, tmp_path):
    owner_id = store.add_owner(_owner(), [ParcelRef("Erode", "Perundurai", "Ingur", "12")])
    got = store.get_owner(owner_id, session_ref="session-token-xyz")
    assert got.owner_name == OWNER_NAME
    audit_text = (tmp_path / "audit_log.jsonl").read_text()
    assert OWNER_NAME not in audit_text  # audit holds IDs, never names
    assert "owner_view" in audit_text
    assert "session-token-xyz" not in (tmp_path / "owners.db").read_bytes().decode("latin-1")


def test_owner_for_parcel_returns_id_not_name(store):
    owner_id = store.add_owner(_owner(), [ParcelRef("Erode", "Perundurai", "Ingur", "12")])
    assert store.owner_for_parcel(ParcelRef("Erode", "Perundurai", "Ingur", "12")) == owner_id
    assert store.owner_for_parcel(ParcelRef("Erode", "Perundurai", "Ingur", "99")) is None


def test_wrong_key_cannot_read_owner(tmp_path):
    audit = AuditLog(tmp_path / "audit_log.jsonl")
    s1 = OwnerStore(tmp_path / "owners.db", new_fernet_key(), migrations_dir(), audit)
    oid = s1.add_owner(_owner(), [])
    s1.close()
    s2 = OwnerStore(tmp_path / "owners.db", new_fernet_key(), migrations_dir(), audit)
    with pytest.raises(OwnerStoreError):
        s2.get_owner(oid)
    s2.close()


def test_invalid_key_error_does_not_echo_key(tmp_path):
    with pytest.raises(OwnerStoreError) as err:
        OwnerStore(tmp_path / "owners.db", "not-a-real-key-SECRET123", migrations_dir(), AuditLog(tmp_path / "a.jsonl"))
    assert "SECRET123" not in str(err.value)


def test_migration_is_idempotent(tmp_path):
    key = new_fernet_key()
    audit = AuditLog(tmp_path / "a.jsonl")
    OwnerStore(tmp_path / "owners.db", key, migrations_dir(), audit).close()
    s = OwnerStore(tmp_path / "owners.db", key, migrations_dir(), audit)
    assert s.schema_version() == 1
    s.close()


def test_db_rejects_full_pan_at_model_level():
    with pytest.raises(ValueError):
        OwnerDetails(owner_name="x", pan_masked="ABCDE1234F", owner_source="s", verified_on=date(2026, 1, 1))


def test_password_check_is_hashed_and_locks_when_unset():
    digest = hash_password("correct horse")
    assert check_password("correct horse", digest)
    assert not check_password("wrong", digest)
    assert not check_password("anything", None)


def test_target_rows_contain_no_personal_data():
    t = TargetParcel(
        parcel_id="p1", survey_no="12", village="Ingur", taluk="P", district="Erode", stage="3D",
        gazette_date=date(2026, 3, 1), source_pdf="raw/a.pdf", dist_to_alignment_m=10,
        dist_to_row_edge_m=12.5, dist_to_zone_edge_m=18.6, side="left", row_width_m=45,
        owner_ref="owner:1", updated_on=date(2026, 11, 18),
    )
    rows = target_rows([t])
    assert_no_personal_data(rows)
    assert "owner_ref" not in rows[0]


def test_map_features_have_no_personal_data():
    t = TargetParcel(
        parcel_id="p1", survey_no="12", village="Ingur", taluk="P", district="Erode", stage="3D",
        gazette_date=date(2026, 3, 1), source_pdf="raw/a.pdf", dist_to_alignment_m=10,
        dist_to_row_edge_m=12.5, dist_to_zone_edge_m=18.6, side="left", row_width_m=45,
        updated_on=date(2026, 11, 18),
    )
    fc = map_features(LineString([(0, 0), (100, 0)]), [t], {"12": (50, 10)})
    assert_no_personal_data(fc)
    assert len(fc["features"]) == 2


def test_personal_data_guard_catches_nested_key():
    with pytest.raises(ValueError):
        assert_no_personal_data({"rows": [{"owner_name": "x"}]})


def test_patta_lookup_returns_area_and_no_owner_fields():
    parcel = SurveyParcel(
        parcel_id="p1", district="Erode", taluk="P", village="Ingur", survey_no="12",
        polygon=mapping(box(0, 0, 40, 30)), source="manual", retrieved_on=date(2026, 11, 1),
    )
    registry = [{
        "district": "Erode", "taluk": "P", "village": "Ingur", "survey_no": "12", "patta_no": "77",
        "land_type": "dry", "source": "official record", "verified_on": "2026-10-01", "owner_name": "SHOULD NOT APPEAR",
    }]
    out = lookup(parcel, registry)
    assert out["area_sqft"] == pytest.approx(40 * 30 * 10.7639104, rel=1e-4)
    assert out["area_cents"] == pytest.approx(40 * 30 * 10.7639104 / 435.6, rel=1e-4)
    assert "owner_name" not in json.dumps(out)
