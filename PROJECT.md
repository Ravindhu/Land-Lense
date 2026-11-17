# PROJECT.md: tn-highway-land-intel

**Project:** Personal highway land-acquisition tracker for Tamil Nadu (Erode, Perundurai, Bhavani, Gobichettipalayam, Tiruchengode, Namakkal corridor)
**Owner / only user:** Single person
**Hosting:** Personal server (self-hosted)
**Document status:** Design, updated with owner decisions. No code exists yet.
**Last updated:** 17 November 2026

---

## 1. Owner decisions (17 Nov 2026)

| # | Question | Decision | Effect on design |
|---|---|---|---|
| 2 | WhatsApp source | Keep WhatsApp via Baileys. Add auction properties as a second listing source. | Baileys ban risk is accepted. Auction collector is added (Section 4.2). |
| 3 | Users | Single user (owner only) | No multi-user accounts or roles. Access control is still required because the server is internet-reachable. |
| 5 | Route source | Use the official map. Connect circular land-acquisition notice dots to it. | SVD route guess is removed. Official alignment is the base layer; notice dots are snapped onto it (Section 5). |
| 6 | Hosting | Personal server | Self-hosted deployment, scheduled jobs on the server, own backups (Section 8). |
| 7 | Target parcels | Survey numbers near the highway, only after official approval. Show parcel size and owner details. | New target filter and a parcel detail panel (Section 6). |

**Interpretation to confirm:** "circular land acquisition notice" is read as the land-acquisition notice for each parcel, shown as a dot. If a different meaning was intended, tell me and Section 5 will be updated.

---

## 2. Purpose

1. Collect highway land-acquisition notices from Central and Tamil Nadu gazettes.
2. Place each notice's survey numbers on the official highway map.
3. Flag parcels that sit near the highway after official approval.
4. Show each target parcel's size and owner details.
5. Track auction properties and WhatsApp broker listings in the same corridor.

---

## 3. Repository structure (updated)

```
tn-highway-land-intel/
├── pyproject.toml              # Single source of dependencies
├── Makefile                    # install, sync, serve, whatsapp, ui, test
├── .env.example                # GEMINI_API_KEY, GOOGLE_SHEET_NAME, GOOGLE_SERVICE_ACCOUNT_JSON, WEBHOOK_SECRET, UI_PASSWORD
├── .gitignore                  # .env, *.json credentials, venv/, storage/, auth_session/, node_modules/
├── README.md
├── config/
│   ├── settings.yaml           # Corridor, stage rules, buffers, approval stage
│   └── official_maps/          # Official alignment maps (GeoJSON or shapefile, once obtained)
├── src/tn_highway_intel/
│   ├── domain/                 # models.py, settings.py
│   ├── collectors/
│   │   ├── central_egazette.py
│   │   ├── tn_state_gazette.py
│   │   ├── tngis_cadastral.py
│   │   ├── portal_listings.py
│   │   └── auction_listings.py     # NEW: e-auction property notices
│   ├── engine/
│   │   ├── gazette_parser.py       # Gemini OCR -> survey numbers + notice dots
│   │   ├── official_map.py         # NEW: loads official alignment, replaces SVD route builder
│   │   ├── dot_snapper.py          # NEW: snaps notice dots onto official alignment
│   │   ├── target_filter.py        # NEW: approved-stage parcels within buffer of highway
│   │   ├── spatial_analyzer.py     # RoW band, intersecting and safe parcels, distances
│   │   ├── patta_lookup.py         # Survey no, patta, owner, area
│   │   ├── corridor_scorer.py      # Scoring (weights documented, configurable)
│   │   └── ai_map_agent.py
│   ├── services/
│   │   ├── daily_sync.py
│   │   └── webhook.py              # FastAPI: WhatsApp + auction intake, authenticated
│   └── ui/
│       └── map_dashboard.py        # Streamlit + Folium, password-protected
├── whatsapp_listener/
│   ├── package.json
│   └── index.js                    # Baileys listener, secondary SIM
├── tests/
│   ├── test_spatial_engine.py
│   ├── test_dot_snapper.py         # NEW
│   ├── test_target_filter.py       # NEW
│   ├── test_patta_lookup.py        # NEW
│   └── test_gazette_parser.py      # NEW (uses saved sample PDFs)
└── storage/                        # Runtime data, not committed
    ├── raw_pdfs/
    ├── notice_dots.json            # Survey numbers + notice dots (replaces confirmed_dots.json)
    ├── official_alignment.geojson  # Official highway alignment (from official map)
    ├── snapped_dots.geojson        # Notice dots snapped onto alignment
    ├── village_cadastrals.geojson
    ├── patta_registry.json
    ├── whatsapp_deals.json
    ├── auction_listings.json       # NEW
    └── audit_log.jsonl             # NEW: who/what/when for every write
```

---

## 4. Module inventory

Status: all **Planned**. Risk: how much the module depends on outside data or rules.

### 4.1 Domain

| File | Purpose | Risk |
|---|---|---|
| `models.py` | Pydantic: `NoticeDot`, `SurveyParcel`, `PattaRecord`, `OwnerDetails`, `TargetParcel`, `AuctionProperty`, `PropertyPin`, `MapState` | Low |
| `settings.py` | Loads YAML and `.env` from the project root | Low |

### 4.2 Collectors

| File | Purpose | Risk |
|---|---|---|
| `central_egazette.py` | Central extraordinary gazettes (MoRTH / NHAI, Sections 3A, 3D) | Medium |
| `tn_state_gazette.py` | TN gazettes and Highways G.O.s (Indian IP needed) | High |
| `tngis_cadastral.py` | Village FMB survey boundaries from TNGIS | High (terms to confirm) |
| `portal_listings.py` | Land-for-sale listings | High (portal terms) |
| `auction_listings.py` | **NEW.** Property e-auction notices (bank and government auction portals) in the corridor: survey no., reserve price, auction date, EMD, contact | High (terms per portal; verify each) |

### 4.3 Engine

| File | Purpose | Risk |
|---|---|---|
| `gazette_parser.py` | Gemini OCR of Tamil and English PDFs. Outputs survey numbers and notice dots with confidence scores. | Medium |
| `official_map.py` | **NEW.** Loads the official alignment from the gazette map. Source of truth for the highway line. | Medium (map format and availability) |
| `dot_snapper.py` | **NEW.** Places each notice dot on the nearest point of the official alignment. Flags dots farther than a set tolerance. | Low |
| `target_filter.py` | **NEW.** Selects parcels that (a) are within the configured buffer of the official alignment and (b) have reached the approved stage. | Low (rule is owner-defined) |
| `spatial_analyzer.py` | RoW band (UTM 43N), intersecting and safe parcels, distances | Low |
| `patta_lookup.py` | Survey no., patta no., owner details, area (sq ft and cents) | High (data access; Section 7) |
| `corridor_scorer.py` | Scoring with documented, configurable weights | Medium |
| `ai_map_agent.py` | Natural-language map control | Low |

**Removed:** `route_builder.py` (SVD straight-line route). It is replaced by `official_map.py` and `dot_snapper.py`, because the owner chose the official map as the source.

### 4.4 Services

| File | Purpose | Risk |
|---|---|---|
| `daily_sync.py` | Daily job: collect, parse, snap, filter, refresh listings, write audit log | Low |
| `webhook.py` | FastAPI intake for WhatsApp and auction data. Requires `WEBHOOK_SECRET`. Bound to localhost; exposed only via reverse proxy with HTTPS. | Medium |

### 4.5 WhatsApp listener

| File | Purpose | Risk |
|---|---|---|
| `index.js` | Baileys listener on secondary SIM, forwards group messages to webhook | High (Section 7.2; risk accepted) |

### 4.6 UI

| File | Purpose | Risk |
|---|---|---|
| `map_dashboard.py` | Map with official alignment, notice dots, target parcels, owner panel, auction and WhatsApp pins. Password-protected. | Medium |

---

## 5. Official map and notice dot flow

```
Official highway map (gazette schedule map)
        │  georeferenced once, saved as official_alignment.geojson
        ▼
Gazette notices (Central + TN) ──► gazette_parser (Gemini)
        │  survey no. + notice dot + confidence + source PDF
        ▼
Survey no. ──► TNGIS cadastral polygon (parcel) ──► centroid
        │
        ▼
dot_snapper: project each dot onto official_alignment
        │  distance from alignment recorded; > tolerance flagged for review
        ▼
snapped_dots.geojson  ──► RoW band (official alignment + row width)
        │
        ▼
target_filter: parcels within buffer AND approved stage
        ▼
map_dashboard
```

**Rules:**
- The official alignment is the only highway line used on the map. Nothing is drawn from a guessed route.
- Every dot keeps its source PDF, page, and gazette date.
- A dot that cannot be matched to a parcel, or sits too far from the alignment, goes to a review queue instead of the map.
- Georeferencing the official map is a manual, one-time step. Record the control points used.

---

## 6. Target parcel rule (owner requirements 3 and 7)

A parcel becomes a **target** when all of the following are true:

1. **Official approval reached.** The notice has reached the approval stage in `settings.yaml` (default: final declaration, 3D). Earlier notices (3A) show as "pending", not targets.
2. **Inside the target zone on either side.** The parcel touches or lies within the target zone, which runs on **both sides** of the official alignment (see the zone calculation below).
3. **Survey number matched.** The survey number maps to a TNGIS polygon.

### 6.1 Target zone calculation

- **Highway width (ROW)** is read from the gazette or official map document for each section and stored as `row_width_m`. It is not guessed.
- **Extra margin:** 20 feet (6.096 m), added outward on each side of the right of way.
- **Zone on each side** = (row_width_m / 2) + 6.096 m, measured from the alignment centreline.

Worked example: a 45 m ROW gives a half-width of 22.5 m. Each side's zone is 22.5 + 6.096 = 28.6 m from the centreline, so the total target band is about 57.2 m wide.

Settings (in `config/settings.yaml`):

```yaml
target_zone:
  row_width_m: <read from document per section>
  margin_ft: 20
  margin_m: 6.096          # derived: margin_ft x 0.3048
  sides: both
  approval_stage: 3D
```

Document the zone rule in the UI so the owner can see which ROW value and margin were used for each section.

**Confirmed (round 4):** 20 feet is added from the road edge on each side, and target land is included on both sides. The road edge is the ROW boundary read from the documents. If you meant the paved carriageway edge instead of the ROW boundary, the zone would be narrower. Tell me if so.

Each target shows:
- Survey number, village, taluk, district
- Parcel size in sq ft and cents
- Owner details (Section 14)
- Stage, gazette date, and source PDF link
- Distance to the official alignment, the ROW edge, and the outer edge of the target zone
- Which side of the alignment the parcel lies on (left or right)

Targets are refreshed by `daily_sync`. Any change in stage or owner creates an audit log entry.

---

## 7. Review findings (updated)

### 7.1 Structure
1. Dependencies live in `pyproject.toml` only. `requirements.txt` is removed or generated.
2. `pytest` is added as a dev extra. Tests now cover snapping, target filtering, patta lookup, and gazette parsing (Section 3).
3. Config is resolved from the project root.
4. Makefile recipes use tab characters.
5. `make serve` starts the webhook and the WhatsApp listener under one supervisor on the server, so the two processes do not need separate terminals.

### 7.2 WhatsApp (Baileys), risk accepted
- Owner has accepted that Baileys is unofficial and the account may be banned.
- Mitigations: use a secondary SIM, limit the listener to the chosen groups, keep message volume low, store only needed fields, and keep an export of `whatsapp_deals.json` so data survives a ban.
- Never use the number for mass messaging. The listener only reads.

### 7.3 Owner details (requirement 7)
- Owner names and patta details are personal data. Even for a single user, store only what is needed, and keep `storage/` off any public path.
- **Open point:** the design does not yet have a confirmed source for owner details. Only use a source that permits this use. If owner details come from a government lookup, record the lookup date and reference for each record.
- Owner details are shown only in the authenticated owner panel and never exported to shared files.

### 7.4 Technical
1. **Official map georeferencing** is the largest technical task. Accuracy depends on the control points chosen. Measure the offset between the official line and known survey boundaries.
2. **Dot snapping tolerance** must be set from real data. Start with a tolerance and review every dot beyond it.
3. **OCR accuracy** for Tamil gazettes must be measured on a labelled sample before use. Low-confidence results go to review.
4. **Scoring weights** (stage certainty percentages) are unsourced. Keep them configurable and labelled as assumptions in the UI.
5. **Stage labels** (3A, 3D, 3G, 3H, 15(2)) must be confirmed against the governing law before they appear in UI text.
6. **Idempotency.** Key: `(district, taluk, village, survey_no, gazette_id)`. Re-running `daily_sync` must not create duplicates.
7. **Gemini output** is validated against a Pydantic schema before it is stored.

### 7.5 Self-hosted server security
1. Webhook binds to `127.0.0.1`. Public access is through a reverse proxy (for example Caddy or Nginx) with HTTPS and a `WEBHOOK_SECRET` header check.
2. Streamlit UI sits behind the same proxy with a password, or a VPN (for example Tailscale) so it is not public.
3. Firewall: open only ports 80 and 443 (and SSH from known IPs).
4. Keep `.env` and credential JSON files at mode 600 and out of Git.
5. Automatic security updates on the OS.

### 7.6 Legal and terms (single-user, personal use)
These still apply even for personal use:

| Area | Concern | Action |
|---|---|---|
| WhatsApp (Baileys) | Unofficial client, ban risk. Accepted by owner. | Keep the risk log (Section 7.2). |
| Property portals and auction sites | Scraping may breach terms. | Check each site's terms before its collector is built. Prefer official feeds or manual entry. |
| TNGIS | WMS and exports may be restricted. | Read the terms first. Use only what is allowed. |
| Google map tiles | Must use Google Maps Platform with a key, or an open tile provider. | Use the Maps Platform, or OpenStreetMap / Satellite tiles with proper attribution. |
| Owner / patta data | Access may be restricted. | Section 7.3. |
| Investment use | Scores could be read as advice. | Keep a "not advice" note in the UI. Show source and date on every record. |

If the owner later shares this tool or uses it commercially, these items must be reviewed again.

---

## 8. Personal server deployment

**Stack:** Python 3.10+ venv, Node.js LTS (for Baileys), SQLite or JSON storage (as now), Caddy for HTTPS.

**Processes (run under systemd or a supervisor):**
1. `uvicorn` webhook on `127.0.0.1:8001`
2. `node whatsapp_listener/index.js`
3. Streamlit UI on `127.0.0.1:8501` (proxied)
4. Cron (or systemd timer) for `make sync`, once a day

**Backups:**
- Nightly copy of `storage/` (JSON, GeoJSON, audit log) to a second location (external disk or cloud storage).
- Keep `raw_pdfs/` with its manifest so each notice can be re-checked.
- Test one restore per month.

**Monitoring:** `daily_sync` writes a status file. A failed run sends an alert to the owner (channel to be chosen).

---

## 9. Setup (updated)

```bash
cd tn-highway-land-intel
make install                 # venv, editable install, npm install
cp .env.example .env         # fill in keys, WEBHOOK_SECRET, UI_PASSWORD (never commit)
make serve                   # webhook + WhatsApp listener (supervised)
make sync                    # daily pipeline (also run by cron)
make ui                      # Streamlit dashboard (behind proxy)
make test                    # pytest
```

**Environment variables:**

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | OCR and extraction |
| `GOOGLE_SHEET_NAME` | Sheet for WhatsApp and auction records |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Path to credentials (mode 600) |
| `WEBHOOK_SECRET` | Shared secret for the webhook |
| `UI_PASSWORD` | Dashboard password |

---

## 10. Build roadmap (updated)

Each phase must work and be tested before the next starts.

**Phase 0: Foundations**
- Repo skeleton, `pyproject.toml`, `.gitignore`, `.env.example`
- Domain models and settings, with tests
- Audit log writer

**Phase 1: Official map and sources**
- Obtain the official highway map for each corridor section. Georeference it and save `official_alignment.geojson`.
- Record the terms of use for TNGIS, gazette sites, portals, and auction sites.
- Central gazette collector with a manifest (hash, date, URL).

**Phase 2: Extraction and snapping**
- Gemini extraction with validated output and confidence scores
- Labelled Tamil and English sample set; measure accuracy
- `dot_snapper` with tolerance and review queue

**Phase 3: Target logic**
- TNGIS polygons (or manual GeoJSON fallback where permission is pending)
- `target_filter` with approval stage and buffer from `settings.yaml`
- RoW band and distances
- Tests for all of the above

**Phase 4: Map UI (read-only)**
- Official alignment, dots, target parcels, size and owner panel (authenticated)
- Source date and "not advice" note on every layer

**Phase 5: Auction and listings**
- Auction collector for each permitted portal
- Portal listings from permitted sources or manual entry

**Phase 6: WhatsApp**
- Baileys listener to webhook with `WEBHOOK_SECRET`
- AI filter, Sheets output, contact pins
- Export backup of deals

**Phase 7: Server and automation**
- Caddy HTTPS, firewall, supervisor, cron
- Nightly backup and monthly restore test
- Failure alerts

---

## 11. Open questions (remaining)

Answered in round 2 (Section 13): auction type, server OS, alert channel, official map fields. Answered in round 3 (Section 14): buffer distance, owner detail fields. Answered in round 4 (Section 15): margin measured from road edge, both sides.

Still open:
1. **Official map files:** Can you share the official highway map PDFs or images for each section? Georeferencing needs at least three known points per map.
2. **Approval stage:** Is final declaration (3D) the stage you mean by "official approval"?
4. **Owner data source:** Answered in round 5 (Section 16). No open API found. Manual entry from official portals is the current route.

## 13. Round 2 owner decisions (17 Nov 2026)

| Topic | Decision |
|---|---|
| Auction source | Bank auction properties (bank e-auction notices for secured assets) |
| Server OS | Ubuntu (LTS) |
| Alert channel | Telegram bot |
| Official map data | Map name, survey number, village, village cross, road cross, and the local office circular for highway land acquisition |

### 13.1 Official map record (new data model)

Each row in the official map layer is one `OfficialMapEntry`:

| Field | Meaning | Source |
|---|---|---|
| `map_id` | Unique ID for the map sheet | Generated |
| `map_name` | Name of the official map (as printed) | Map title block |
| `map_file` | Path to the scanned map or GeoJSON in `config/official_maps/` | Owner upload |
| `district`, `taluk`, `village` | Location | Map and circular |
| `survey_no` | Survey number shown on the map | Map and gazette |
| `village_cross` | Point where the alignment crosses a village boundary or village road, with coordinates | Map (georeferenced) |
| `road_cross` | Point where the alignment crosses an existing road, with road name and coordinates | Map (georeferenced) |
| `chainage_km` | Distance along the alignment, if printed | Map |
| `circular_no`, `circular_date` | Circular number and date | Local office circular |
| `circular_office` | Issuing office (for example the district land acquisition office or Highways Department unit) | Local office circular |
| `circular_pdf` | Stored copy of the circular | Owner upload, saved under `storage/raw_pdfs/circulars/` |
| `georef_points` | Control points used to georeference the map sheet | Manual step, recorded |

**Rules:**
- A survey number on the map is linked to the matching circular. If the circular is missing, the entry shows "circular pending."
- Village crossings and road crossings are shown as separate map markers, so you can see where the alignment enters and leaves each village or road.
- Every entry keeps its source file, page, and date.

### 13.2 Bank auction properties (replaces generic auction source)

- Source: bank e-auction notices for secured properties in the corridor.
- Fields collected: auction ID, bank name, property address, survey number, village, reserve price, EMD, auction date and time, status, and the notice PDF.
- Check each bank portal's terms before building its collector. Prefer the official notice feed or manual entry where the portal does not allow automated reading.
- Auction properties that match a target parcel are flagged on the map.

### 13.3 Ubuntu server

- Ubuntu LTS with `unattended-upgrades` for security patches.
- Services managed by `systemd`:
  - `tn-intel-webhook.service` (uvicorn on 127.0.0.1:8001)
  - `tn-intel-whatsapp.service` (Baileys listener)
  - `tn-intel-ui.service` (Streamlit on 127.0.0.1:8501)
- `systemd` timer `tn-intel-sync.timer` runs `make sync` daily.
- Caddy as reverse proxy with automatic HTTPS.
- UFW firewall: allow 22 (from known IPs), 80, 443 only.

### 13.4 Telegram alerts

- A Telegram bot sends alerts to one private chat (the owner).
- Alert types:
  - `daily_sync` failed or partially failed
  - new target parcel found
  - stage change on a target parcel
  - new auction property matching a target parcel
  - WhatsApp listener disconnected
  - backup failed
- Bot token and chat ID stored in `.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`), never in Git.
- Alerts contain no owner names or phone numbers. They link to the dashboard instead.

### 13.5 Updated environment variables

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram alert bot |
| `TELEGRAM_CHAT_ID` | Owner's private chat |

(Other variables unchanged from Section 9.)

---

## 14. Round 3 owner decisions (17 Nov 2026)

| Topic | Decision |
|---|---|
| Highway size | Read from the official documents (ROW width per section) |
| Margin | +20 ft on each side of the highway |
| Target area | Parcels on both sides of the highway |
| Owner details | Land owner name, PAN card, Aadhaar (if available) |

### 14.1 Owner detail record

| Field | Stored as | Source | Notes |
|---|---|---|---|
| `owner_name` | Full name as on the record | Patta, sale deed, or documents you hold | Required for all targets |
| `pan` | Encrypted; shown masked (for example `ABCDE****F`) | Only from documents the owner gives you | Full PAN is never shown on the map or in alerts |
| `aadhaar_last4` | Last 4 digits only | Only from documents the owner gives you | Full Aadhaar is never stored (see 14.2) |
| `owner_source` | Document name and date | Record | Mandatory: no owner detail without a source |
| `verified_on` | Date you last checked | Record | Owner details go stale |

### 14.2 Important limits on PAN and Aadhaar

These limits come from law and should be confirmed with a lawyer before you store any identifier:

- **Aadhaar:** The Aadhaar Act restricts storing and displaying the full 12-digit number. The design stores only the last 4 digits and only when the document you hold shows them. It does not fetch Aadhaar from any government service.
- **PAN:** PAN details are confidential tax information. The design does not look up anyone's PAN from any database or portal. It only records PAN from a document the owner gives you, for example a sale deed or a form they signed.
- **Consent and purpose:** Record the purpose and source for each identifier. Only keep what the target-parcel feature needs.
- **DPDP Act 2023:** This applies even for personal use. Store the data encrypted, limit access to you, and delete a record when it is no longer needed.

If you later need full PAN or Aadhaar for any reason, stop and review with a lawyer first.

### 14.3 Storage and display rules

- Owner records are stored in an encrypted SQLite database (`storage/owners.db`) with a key from `.env` (`OWNER_DB_KEY`), not in plain JSON.
- Owner panel shows name, masked PAN, last 4 Aadhaar digits, source, and verified date.
- Owner details never appear in Telegram alerts, the Google Sheet, or any export. Telegram alerts link to the dashboard only.
- Every view or edit of an owner record is written to `audit_log.jsonl`.

### 14.4 Updated environment variables

| Variable | Purpose |
|---|---|
| `OWNER_DB_KEY` | Encryption key for owner records |

---

## 15. Round 4 owner decisions (17 Nov 2026)

| Topic | Decision |
|---|---|
| Road size edge | ROW width from documents; the edge is the ROW boundary |
| Margin | +20 ft from the road edge, on each side |
| Target land | Both sides of the highway |

The target zone rule in Section 6.1 is now confirmed. No further change to the calculation or the settings.

---

---

## 16. Round 5: owner data source check (17 Nov 2026)

**Question:** Does the Tamil Nadu Registration Department (or related departments) offer an open source or API for owner details?

**Finding:** No public open API or open dataset for owner details was found. The following official channels exist, all web-based:

| Channel | Operator | What it offers | Automation status |
|---|---|---|---|
| TNREGINET (tnreginet.gov.in) | Registration Department | Encumbrance Certificate view, guideline value, Patta Chitta view, registration details. Requires user registration. | Web portal only. No public API found. |
| CLIP (clip.tn.gov.in) | Land records (Revenue / Survey and Settlement) | Patta and Chitta, TSLR, FMB diagrams, EC from Registration Department, patta transfer status | Web portal only. No public API found. |
| eservices.tn.gov.in | Survey and Settlement | Anytime Anywhere eServices for land records | Web portal only. |
| TamilNILAM | NIC for the state | Land records software behind the portals. An NIC report lists a "TAMIL NILAM API" among integrations, but no public API documentation was found. | Likely government-to-government access. Not public. |
| Third-party apps (for example verified.realestate, LandLens) | Private companies | Aggregated land data, WhatsApp alerts for patta and registration changes | Not official. Source and legal basis unclear. Do not use as the owner source. |

**Conclusion:**
1. No official open API or open data for owner details was found.
2. The only confirmed route is manual lookup on the official portals, with the source and date recorded (Section 14.1).
3. Automated scraping of CLIP or TNREGINET is not recommended until the portal terms are read. The terms were not verified in this check.
4. For reliable automated access, a formal request to the Department of Survey and Settlement or NIC Tamil Nadu for API or data access is the proper route. This should be done in writing, stating the personal, non-commercial purpose.
5. Third-party aggregators are not used as a data source.

**Design change:** Owner detail import becomes a manual entry step with a source record. The owner panel shows "manual, verified on <date>". An automated connector is a later phase, only if access is granted.

---

## 17. Round 6: tools and bank auction check (17 Nov 2026)

### 17.1 Tools

| Task | Tool | Decision rule |
|---|---|---|
| Georeferencing official map sheets | QGIS | Use. Record control points per sheet. |
| OCR of Tamil and English gazette PDFs | Gemini (primary) | Keep only if it beats the alternative on a labelled sample. |
| OCR alternative | Tesseract with Tamil language data | Run on the same sample. Compare survey-number accuracy. |

**Test plan:** Label 30 to 50 gazette pages (Tamil and English). Score each engine on exact survey-number match, sub-division match, and village name. Pick the engine with the higher score. Gemini results are checked against the source page before use.

### 17.2 Bank auction notices found (official sources, Erode and Bhavani area)

These were found by search. The list is not a complete or live feed, and many notices are old. Each entry must be checked for current status before any action.

| Bank or lender | Location in notice | Notice date | Status to verify |
|---|---|---|---|
| Cholamandalam (SARFAESI notices) | Erode, Bhavani, Gobichettipalayam, Kavindapadi, Periyasemur, Surampatti | 2024 to 2026 | Most likely expired. Check sale date. |
| Equitas Small Finance Bank | Gobichettipalayam, Erode, Chithode | 2025 | Check sale date. |
| SBI (Stressed Assets, Coimbatore) | SIPCOT Industrial Growth Centre, Perundurai (plot E-6 and G-10, Ingur village) | 2019 | Likely closed. |
| SIDBI, Erode | Sathyamangalam, Erode | 2016 | Old. |
| TIIC (Erode) e-auction | Erode | Date not shown | Check. |
| Karur Vysya Bank (Asset Recovery) | Madurai property shown; Erode area not confirmed | 2025 | Not in area. |

**Notes:**
1. Notices show a bank name, borrower name, property description (survey number, village, taluk), and an auction date. They do not show the highway alignment. Each property must be placed on the official map before it counts as a target.
2. The Cholamandalam notices in Periyasemur and Surampatti appear in the Erode and Bhavani area. Check their survey numbers against the official alignment once maps are georeferenced.
3. Equitas notices name the e-auction site (bankeauctions.com). Check the other banks' e-auction links from their notices.
4. Notices name borrowers. Store borrower names only for properties that match a target, and follow Section 14 rules.

### 17.3 Changes to the design

- Auction collector (`auction_listings.py`) starts with manual entry from notices, then moves to a scheduled check of the official e-auction sites once each site's terms are confirmed.
- Each auction record keeps the notice PDF, notice date, sale date, and status (active, expired, sold).
- An auction becomes a map pin only when its survey number matches a parcel inside the target zone (Section 6).

---

## 18. Change log

| Date | Change |
|---|---|
| 17 Nov 2026 | Initial design from design text. Structure and risks reviewed. |
| 17 Nov 2026 | Owner decisions added: Baileys kept, auction source added, single user, personal server, official map with notice dots, target parcel rule with owner details. |
| 17 Nov 2026 | Round 2: bank auctions, Ubuntu server, Telegram alerts, official map record fields (village cross, road cross, circular), updated open questions. |
| 17 Nov 2026 | Round 3: target zone = ROW width (from documents) + 20 ft each side; owner fields (name, PAN masked, Aadhaar last 4 only, source, encrypted storage). |
| 17 Nov 2026 | Round 4: 20 ft margin from road edge confirmed on both sides; target zone rule locked. |
| 17 Nov 2026 | Round 5: checked Tamil Nadu Registration and land record portals for open API. None found. Owner data is manual entry from official portals. |
| 17 Nov 2026 | Round 6: QGIS for georeferencing; Gemini OCR kept only if it beats Tesseract on a labelled sample; bank auction notices found for Erode and Bhavani area (status to be verified). |
