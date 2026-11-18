"""Owner dashboard (Streamlit + Folium). Phase 4, read-only.

Run: make ui  (served on 127.0.0.1 behind the HTTPS proxy, docs/DEPLOYMENT.md).

- Locked until UI_PASSWORD_SHA256 is set and the correct password is entered.
- Owner panel needs the password again in this session before any owner detail is decrypted.
- Targets, pending items and review items come from JSON files written by daily_sync.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
from shapely.geometry import LineString

from tn_highway_intel.domain.audit import AuditLog
from tn_highway_intel.domain.models import TargetParcel
from tn_highway_intel.domain.owner_store import OwnerStore, OwnerStoreError
from tn_highway_intel.domain.settings import get_env, migrations_dir, storage_dir
from tn_highway_intel.ui.auth import check_password
from tn_highway_intel.ui.view_model import NOT_ADVICE, review_rows, target_rows

st.set_page_config(page_title="Highway land tracker", layout="wide")
st.caption(NOT_ADVICE)

storage = storage_dir()


def _read(name: str, default):
    path = storage / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


if not st.session_state.get("unlocked"):
    expected = get_env("UI_PASSWORD_SHA256")
    if not expected:
        st.error("Dashboard locked: UI_PASSWORD_SHA256 is not set.")
        st.stop()
    password = st.text_input("Password", type="password")
    if st.button("Unlock"):
        if check_password(password, expected):
            st.session_state["unlocked"] = True
            st.rerun()
        st.error("Wrong password.")
    st.stop()

targets = [TargetParcel.model_validate(t) for t in _read("targets.json", [])]
pending = _read("pending.json", [])
review = _read("review_queue.json", [])
status = _read("sync_status.json", {})

st.title("Land parcels near the official highway")
if status:
    st.write(f"Last sync: {status.get('finished_at', 'never')} · status: {status.get('status', 'unknown')}")

tab_targets, tab_pending, tab_review, tab_owner = st.tabs(["Targets", "Pending", "Review", "Owner panel"])

with tab_targets:
    rows = target_rows(targets)
    st.write(f"{len(rows)} target parcel(s).")
    st.dataframe(rows, use_container_width=True)

with tab_pending:
    st.write(f"{len(pending)} pending item(s). Pending notices are not targets.")
    st.dataframe(pending, use_container_width=True)

with tab_review:
    st.write(f"{len(review)} item(s) need review.")
    st.dataframe(review_rows(review), use_container_width=True)

with tab_owner:
    st.write("Owner details are shown only after password re-entry in this session.")
    if not st.session_state.get("owner_unlocked"):
        again = st.text_input("Re-enter password", type="password", key="owner_pw")
        if st.button("Open owner panel"):
            if check_password(again, get_env("UI_PASSWORD_SHA256")):
                st.session_state["owner_unlocked"] = True
                st.rerun()
            st.error("Wrong password.")
    else:
        key = get_env("OWNER_DB_KEY")
        if not key:
            st.error("Owner panel disabled: OWNER_DB_KEY is not set.")
        else:
            try:
                store = OwnerStore(storage / "owners.db", key, migrations_dir(), AuditLog(storage / "audit_log.jsonl"))
                ids = store.owner_ids()
                if not ids:
                    st.info("No owner records yet. Add them through the owner form (manual entry, with a source).")
                choice = st.selectbox("Owner ID", ids) if ids else None
                if choice is not None:
                    owner = store.get_owner(choice, session_ref=st.session_state.get("session_id"))
                    st.write(f"Name: {owner.owner_name}")
                    st.write(f"PAN (masked): {owner.pan_masked or '—'}")
                    st.write(f"Aadhaar (last 4): {owner.aadhaar_last4 or '—'}")
                    st.write(f"Source: {owner.owner_source} · verified {owner.verified_on}")
                    st.write("Parcels: " + ", ".join(f"{p.village} {p.survey_no}" for p in store.parcels_for(choice)))
                store.close()
            except OwnerStoreError as err:
                st.error(str(err))
