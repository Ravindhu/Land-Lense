# Roadmap

Each phase must work and be tested before the next starts. Status: all **Planned**.

## Phase 0: Foundations
- Repo skeleton, `pyproject.toml`, `.gitignore`, `.env.example`
- Domain models and settings, with tests
- Audit log writer

**Done when:** `make test` passes; audit writer tested.

## Phase 1: Official map and sources
- Obtain the official highway map for each section (open question 1 in OPEN_QUESTIONS.md).
- Georeference in QGIS; save `official_alignment.geojson`; record control points.
- Record terms for TNGIS, gazette sites, portals, and auction sites in `docs/SOURCES.md`.
- Central gazette collector with manifest (hash, date, URL).

**Done when:** alignment saved with control points; collector writes manifest; terms recorded.

## Phase 2: Extraction and snapping
- Gemini (or chosen OCR) extraction with validated output and confidence.
- Label 30–50 Tamil and English pages; measure accuracy.
- `dot_snapper` with tolerance and review queue.

**Done when:** accuracy measured and recorded; dots snap or go to review.

## Phase 3: Target logic
- TNGIS polygons (or manual GeoJSON fallback where permission is pending).
- `target_filter` with approval stage and zone from settings.
- RoW band and distances.

**Done when:** worked-example tests pass; targets match the rules.

## Phase 4: Map UI (read-only)
- Alignment, dots, targets, size, and owner panel (authenticated).
- Source date and "not advice" on every layer.

**Done when:** privacy tests pass; owner panel behind login.

## Phase 5: Auction and listings
- Manual entry from notices first.
- Automated collector only after terms are confirmed.

**Done when:** matched auctions pin on the map; expired notices are marked.

## Phase 6: WhatsApp
- Baileys listener to webhook with `WEBHOOK_SECRET`.
- Filter, Sheets output (no owner data), contact pins.
- Export backup of deals.

**Done when:** listener restarts cleanly; export tested.

## Phase 7: Server and automation
- Caddy HTTPS, firewall, supervisor, timer.
- Nightly backup and monthly restore test.
- Telegram failure alerts.

**Done when:** one restore test passed; alerts tested.

## Blocked until the owner decides
- Official map files (phase 1).
- Owner data process and lawyer review (phases 4 and 6).
- Stage "15(2)" (phase 3 UI text).
