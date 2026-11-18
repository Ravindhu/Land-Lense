# Implementation plan

Built from the template's planning prompt. Read first: `docs/PRD.md`, `docs/DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/API.md`, `AGENTS.md`. Decisions: `docs/DECISIONS.md`. Open points: `docs/OPEN_QUESTIONS.md`.

**No application code is written by this plan.** Each phase lists the files it will touch, so the coding agent can scope its work.

**Status:** all phases Planned. No code exists yet.

---

## Phase 0: Foundations

**Goal:** a runnable, tested skeleton with domain models, settings, and the audit log.

**Tasks**
1. Create `pyproject.toml` (single dependency source), `Makefile` (tab-indented recipes), `.env.example`, `.gitignore`.
2. Create the package layout from `docs/ARCHITECTURE.md` section 1 (empty modules with docstrings).
3. Write `domain/models.py`: `NoticeDot`, `SurveyParcel`, `PattaRecord`, `OwnerDetails`, `TargetParcel`, `OfficialMapEntry`, `AuctionProperty`, `PropertyPin`, `MapState` (see `docs/DATA_MODEL.md`).
4. Write `domain/settings.py`: load `config/settings.yaml` and `.env` from the project root.
5. Create `config/settings.yaml` with `target_zone` (see `docs/RULES.md` section 2), `approval_stage: 3D`, snap tolerance placeholder, `llm_budget` placeholder.
6. Write the audit log writer: append-only JSONL with `prev_hash` chain (`docs/DATABASE.md` section 7).

**Files:** `pyproject.toml`, `Makefile`, `.env.example`, `.gitignore`, `config/settings.yaml`, `src/tn_highway_intel/domain/*.py`, `src/tn_highway_intel/engine/audit.py` (or `domain/audit.py`), `tests/test_models.py`, `tests/test_settings.py`, `tests/test_audit.py`.

**DB / API changes:** none.

**Tests**
- Models reject unknown fields and invalid stages.
- Settings load from the project root regardless of working directory.
- Audit chain detects a changed line.

**Depends on:** nothing.

**Completion criteria**
- `make install` and `make test` succeed on a clean checkout.
- Audit chain test passes, including the tamper case.
- No secret values in the repo.

---

## Phase 1: Official map and sources

**Goal:** an official highway alignment saved with control points, and the first gazette collector with a manifest.

**Tasks**
1. Owner supplies official map files (open question 1). Store under `config/official_maps/`.
2. Georeference each sheet in QGIS. Record control points in `OfficialMapEntry.georef_points`.
3. Export `storage/official_alignment.geojson`.
4. Write the central gazette collector: fetch Gazette of India Part II Section 3(ii) notices (`docs/SOURCES.md`), store PDFs under `storage/raw_pdfs/`, write a manifest (hash, date, URL, gazette ID).
5. Record terms of use for each source in `docs/SOURCES.md` before any collector is enabled.

**Files:** `config/official_maps/`, `storage/official_alignment.geojson` (runtime), `src/tn_highway_intel/engine/official_map.py`, `src/tn_highway_intel/collectors/central_egazette.py`, `tests/test_official_map.py`, `tests/test_central_egazette.py`.

**DB / API changes:** none. Manifest is a JSON file.

**Tests**
- Alignment loads and round-trips through GeoJSON.
- Control points stored for every sheet.
- Collector writes the manifest; re-running does not duplicate a PDF (hash check).
- Collector respects the rate limit and timeout (use recorded responses; no live calls in tests).

**Depends on:** Phase 0; owner's official map files; terms recorded.

**Completion criteria**
- One official sheet georeferenced with at least 3 control points, with an error measurement recorded.
- Manifest covers every downloaded PDF.
- Collector is disabled by default until the owner clears its terms.

---

## Phase 2: Extraction and snapping

**Goal:** survey numbers and notice dots extracted from gazette PDFs with confidence, and each dot snapped to the alignment.

**Tasks**
1. Build the labelled sample: 30–50 Tamil and English pages (`docs/TESTING.md` section 3). Labels hold no owner data.
2. Implement `gazette_parser.py` with the Gemini client, the Pydantic output schema, and the PDF-hash cache (`docs/TOKEN_OPTIMIZATION.md`).
3. Implement the Tesseract (Tamil) path on the same sample. Score both engines on survey-number, sub-division, and village match. Record the result in `docs/DECISIONS.md`.
4. Implement `dot_snapper.py`: project each dot onto the alignment; record `snap_distance_m`; send beyond-tolerance dots to review.
5. Implement the review queue store (`storage/review_queue.json`).

**Files:** `src/tn_highway_intel/engine/gazette_parser.py`, `src/tn_highway_intel/engine/dot_snapper.py`, `src/tn_highway_intel/engine/ocr_cache.py`, `tests/data/labels/`, `tests/test_gazette_parser.py`, `tests/test_dot_snapper.py`.

**DB / API changes:** none. Results go to `notice_dots.json` and `snapped_dots.geojson`.

**Tests**
- Schema rejects a malformed model response; the dot goes to review.
- Cache hit skips the model call (mock the client and assert zero calls).
- Snapping: a dot on the line snaps with distance 0; a dot beyond tolerance is flagged.
- Accuracy test runs on the labelled sample and writes the score.

**Depends on:** Phase 0, Phase 1; labelled sample from the owner.

**Completion criteria**
- Engine choice recorded in `docs/DECISIONS.md` with scores.
- Snap tolerance set from real data and recorded.
- Every stored dot has source PDF, page, and date (checked by test).

---

## Phase 3: Target logic

**Goal:** parcels matched to survey numbers, the RoW band and zone computed, and targets selected by the rule.

**Tasks**
1. Obtain TNGIS parcel polygons, or create the manual GeoJSON fallback where permission is pending (`docs/OPEN_QUESTIONS.md` items 11 and 15).
2. Implement `tngis_cadastral.py` (read-only, only after terms are cleared) or the manual loader.
3. Implement `spatial_analyzer.py` in EPSG:32643: RoW band, zone edges, left/right side, distances.
4. Read `row_width_m` per section from the documents; store it in settings with the source.
5. Implement `target_filter.py` with the three rules in `docs/RULES.md` section 1.
6. Implement `stage` labels from config; leave "15(2)" out of the UI until verified.

**Files:** `src/tn_highway_intel/collectors/tngis_cadastral.py` (or `manual_parcels.py`), `src/tn_highway_intel/engine/spatial_analyzer.py`, `src/tn_highway_intel/engine/target_filter.py`, `config/settings.yaml`, `tests/test_spatial_engine.py`, `tests/test_target_filter.py`.

**DB / API changes:** none. Targets written to a JSON file.

**Tests**
- Worked example: ROW 45 m → zone 28.6 m each side → band about 57.2 m.
- Stage 3A inside the zone is pending, not a target.
- Stage 3D outside the zone is not a target.
- Parcel with no survey match is not a target and goes to review.
- Left and right side assigned correctly.

**Depends on:** Phases 1 and 2; TNGIS terms or manual fallback; `row_width_m` per section.

**Completion criteria**
- All worked-example tests pass.
- Each target carries ROW, margin, side, and source (checked by test).
- Scoring not wired to targets yet (Phase 4 shows scores with the advice note).

---

## Phase 4: Map UI (read-only)

**Goal:** the owner can see the alignment, dots, targets, and owner panel in a password-protected dashboard.

**Tasks**
1. Build `ui/map_dashboard.py` (Streamlit + Folium) per `docs/DESIGN.md`: map, right panel, top bar, tabs (Targets, Pending, Review, Auctions, Contacts).
2. Implement `FilterBar` with state in the URL.
3. Implement `SourceLine`, `StatusBadge`, `TargetCard`, `ZoneNote`, `NotAdviceNote`, `ReviewQueueRow`.
4. Implement the owner panel behind login, with re-authentication on open and an audit entry per view.
5. Implement `patta_lookup.py`: area in sq ft and cents; owner lookup from the encrypted store only.
6. Add the loading, empty, and error states from `docs/DESIGN.md` section 8.
7. Add the accessibility pass: keyboard, text summary, contrast check.

**Files:** `src/tn_highway_intel/ui/map_dashboard.py`, `src/tn_highway_intel/ui/components/*.py`, `src/tn_highway_intel/engine/patta_lookup.py`, `src/tn_highway_intel/domain/owner_store.py`, `tests/test_patta_lookup.py`, `tests/test_privacy.py`.

**DB / API changes:** `owners.db` created with the schema in `docs/DATABASE.md` section 2 (migration `0001_init.sql`).

**Tests**
- Privacy: owner fields absent from every non-owner-panel view and from alerts.
- Owner panel refuses access without login; each view writes an audit line.
- Full PAN and full Aadhaar input rejected by validation.
- Migration test on a copy of the database.
- UI smoke test: main page loads with fixture data; empty and error states render.

**Depends on:** Phase 3; lawyer review for owner identifiers (`docs/OPEN_QUESTIONS.md` item 7); `OWNER_DB_KEY` set.

**Completion criteria**
- Owner panel behind login and audited.
- Colour is not the only status cue (checked in review).
- Contrast and keyboard checks pass.
- "Research aid, not advice" on the main page and on each score.

---

## Phase 5: Auction and listings

**Goal:** bank auction properties recorded and pinned when they match a target.

**Tasks**
1. Manual entry form or import for auction notices, with the notice PDF and status (active, expired, sold).
2. Implement `auction_listings.py` (manual import first; a scheduled check only after each site's terms are cleared).
3. Implement the match: auction survey number inside a target parcel creates a pin.
4. Mark expired auctions and remove them from active pins.
5. Implement `portal_listings.py` only after its terms are cleared, or keep manual entry.
6. Add the `POST /v1/auctions` endpoint with `X-Webhook-Secret` (`docs/API.md` section 1).

**Files:** `src/tn_highway_intel/collectors/auction_listings.py`, `src/tn_highway_intel/services/webhook.py`, `src/tn_highway_intel/engine/auction_match.py`, `tests/test_auction_match.py`, `tests/test_webhook_auctions.py`.

**DB / API changes:** endpoint `POST /v1/auctions`. Records in `auction_listings.json`.

**Tests**
- Matching auction pins to the correct target; a non-matching auction does not.
- Expired auction not shown as active.
- Webhook rejects a missing or wrong secret (`401`), an oversized body (`413`), and an unknown field (`400`).
- Duplicate `auction_id` returns `200 duplicate`.
- Borrower name stored only when matched.

**Depends on:** Phase 4; auction sites' terms cleared before automation.

**Completion criteria**
- At least one real auction matched or confirmed unmatched by hand.
- Webhook tests pass, including the rate limit.

---

## Phase 6: WhatsApp

**Goal:** broker listings received read-only from a secondary SIM and shown as contact pins.

**Tasks**
1. Build `whatsapp_listener/index.js` (Baileys) with a listen-only allowlist of groups.
2. Store the session under `auth_session/` (never committed).
3. Forward each group message to `POST /v1/listings/whatsapp` with retry and backoff; queue to disk when the webhook is down.
4. Implement the AI filter and field extraction (`whatsapp_webhook.py`), storing only the fields in `PropertyPin`.
5. Mask phone numbers in alerts and Sheets output.
6. Optional Google Sheets log without owner data; check for duplicates before append.
7. Export backup of `whatsapp_deals.json` on a schedule.

**Files:** `whatsapp_listener/index.js`, `whatsapp_listener/package.json`, `src/tn_highway_intel/services/webhook.py`, `src/tn_highway_intel/engine/listing_parser.py`, `src/tn_highway_intel/collectors/whatsapp_sheets.py`, `tests/test_listing_parser.py`, `tests/test_webhook_listings.py`.

**DB / API changes:** endpoint `POST /v1/listings/whatsapp`; Sheets log optional.

**Tests**
- Listener sends only allowlisted groups (mock messages).
- Duplicate `message_id` returns `200 duplicate`.
- Phone numbers masked in alerts and Sheets rows (privacy test).
- Webhook down: messages queued, then delivered once up.
- Rate limit returns `429` with `Retry-After`.

**Depends on:** Phase 5 (webhook), Phase 7 partially (alerts) for disconnect notices.

**Completion criteria**
- Listener runs under systemd with a secondary SIM.
- No outbound message sent by the listener (checked by test and code review).
- Export backup restores to a copy.

**Risk:** Baileys is unofficial and may get the account banned (owner accepted; `docs/SECURITY_AND_LEGAL.md` section 5).

---

## Phase 7: Server and automation

**Goal:** the system runs unattended on the Ubuntu server with backups, alerts, and HTTPS.

**Tasks**
1. Provision Ubuntu LTS: `unattended-upgrades`, UFW (22 from known IPs, 80, 443), non-root service user.
2. Install Caddy with automatic HTTPS and proxy rules for the webhook and the UI (password or VPN).
3. Create systemd units: webhook, WhatsApp listener, UI, and the sync timer (`docs/DEPLOYMENT.md` section 2).
4. Implement the Telegram alerter with no owner data (`docs/API.md` section 2).
5. Implement the nightly backup of `storage/` including `owners.db` and `audit_log.jsonl`, with the key kept separately.
6. Implement the monthly restore test and record its result.
7. Implement the audit chain check as a daily job.
8. Set the monthly LLM budget and the 80% alert (`docs/TOKEN_OPTIMIZATION.md` section 5).

**Files:** `deploy/systemd/*.service`, `deploy/systemd/tn-intel-sync.timer`, `deploy/Caddyfile`, `src/tn_highway_intel/services/alerts.py`, `src/tn_highway_intel/services/backup.py`, `scripts/restore_test.sh`, `tests/test_alerts.py`, `tests/test_backup.py`.

**DB / API changes:** none.

**Tests**
- Alerter output contains no owner name, PAN, Aadhaar, or full phone (privacy test).
- Backup restores to a temp path and row counts match.
- Audit chain check detects a changed line.
- systemd units pass `systemd-analyze verify`.

**Depends on:** Phases 0–6 running; Telegram bot token and chat ID (`docs/OPEN_QUESTIONS.md` item 12).

**Completion criteria**
- One successful restore test recorded in `docs/DECISIONS.md`.
- Alert received for a deliberate sync failure.
- Services restart after a reboot.
- Firewall rules verified from outside the network.

---

## Dependencies between phases

```
0 Foundations
 └─ 1 Official map and sources
     └─ 2 Extraction and snapping
         └─ 3 Target logic
             └─ 4 Map UI (read-only)
                 └─ 5 Auctions  ──┐
                 └─ 6 WhatsApp  ──┼─ 7 Server, alerts, backups
                                  ┘
```

Phase 7 starts partly in parallel: the Telegram alerter and backup script can be built after Phase 0.

---

## Decisions needed before each phase

| Before phase | Decision | Where |
|---|---|---|
| 0 | Keep land records in JSON for the MVP (or SQLite) | `docs/DECISIONS.md` |
| 1 | Owner supplies official map files | `docs/OPEN_QUESTIONS.md` item 1 |
| 2 | OCR engine chosen by labelled-sample score; snap tolerance | `docs/DECISIONS.md` |
| 3 | Approval stage 3D confirmed; ROW source per section; margin edge | `docs/OPEN_QUESTIONS.md` items 2, 4, 15 |
| 3 | "15(2)" status | `docs/OPEN_QUESTIONS.md` item 5 |
| 4 | Lawyer review of PAN and Aadhaar; owner store layout | `docs/OPEN_QUESTIONS.md` items 6, 7 |
| 5 | Source terms for each auction site | `docs/OPEN_QUESTIONS.md` item 11 |
| 6 | Accept listener risk again if use changes | `docs/SECURITY_AND_LEGAL.md` section 5 |
| 7 | Telegram chat ID; backup location | `docs/OPEN_QUESTIONS.md` item 12 |

---

## Recommended first task

**Phase 0, task 1: create `pyproject.toml`, `Makefile`, `.env.example`, and `.gitignore`, then run `make install` and `make test` on a clean checkout.**

Why first: every later phase needs a working install and a test runner. It needs no owner input, no external service, and no owner data. It can be verified in one session.

Do not start Phase 1 before the owner supplies the official map files or confirms they will come later.
