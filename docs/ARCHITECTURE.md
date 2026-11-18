# Architecture

## 1. Layout
```
tn-highway-land-intel/
├── pyproject.toml
├── Makefile
├── .env.example
├── .gitignore
├── README.md
├── AGENTS.md
├── config/
│   ├── settings.yaml
│   └── official_maps/
├── src/tn_highway_intel/
│   ├── domain/        models.py, settings.py
│   ├── collectors/    central_egazette.py, tn_state_gazette.py, tngis_cadastral.py,
│   │                  portal_listings.py, auction_listings.py
│   ├── engine/        gazette_parser.py, official_map.py, dot_snapper.py,
│   │                  target_filter.py, spatial_analyzer.py, patta_lookup.py,
│   │                  corridor_scorer.py, ai_map_agent.py
│   ├── services/      daily_sync.py, webhook.py
│   └── ui/            map_dashboard.py
├── whatsapp_listener/ package.json, index.js
├── tests/
└── storage/           (runtime, not committed)
```

## 2. Data flow
```
Official highway map (gazette schedule map)
   │ georeference once (QGIS) → official_alignment.geojson
   ▼
Gazette notices (Central + TN) → gazette_parser (OCR)
   │ survey no. + notice dot + confidence + source PDF
   ▼
Survey no. → TNGIS cadastral polygon → centroid
   ▼
dot_snapper → snapped_dots.geojson  (distance to alignment recorded)
   ▼
spatial_analyzer → RoW band, zone, side (left/right), distances
   ▼
target_filter (stage ≥ 3D AND inside zone AND survey matched)
   ▼
map_dashboard (owner panel is authenticated)
```

Auction and WhatsApp records join at the target filter: a match on survey number creates a pin.

## 3. Modules
| Module | Responsibility | Depends on outside data | Risk |
|---|---|---|---|
| `domain/models.py` | Pydantic models | No | Low |
| `domain/settings.py` | Load YAML and `.env` from project root | No | Low |
| `collectors/central_egazette.py` | Central gazettes (MoRTH/NHAI) | Yes | Medium |
| `collectors/tn_state_gazette.py` | TN gazettes, Highways G.O.s | Yes (Indian IP) | High |
| `collectors/tngis_cadastral.py` | FMB survey boundaries | Yes (terms) | High |
| `collectors/portal_listings.py` | Land-for-sale listings | Yes (portal terms) | High |
| `collectors/auction_listings.py` | Bank e-auction notices | Yes (terms per site) | High |
| `engine/gazette_parser.py` | OCR, validated output | Yes (OCR engine) | Medium |
| `engine/official_map.py` | Load official alignment | Yes (map files) | Medium |
| `engine/dot_snapper.py` | Snap dots to alignment | No | Low |
| `engine/target_filter.py` | Target rule | No | Low |
| `engine/spatial_analyzer.py` | RoW band, zone, distances (UTM 43N, EPSG:32643) | No | Low |
| `engine/patta_lookup.py` | Survey no., patta, owner, area | Yes (data access) | High |
| `engine/corridor_scorer.py` | Configurable scoring | No | Medium |
| `engine/ai_map_agent.py` | Natural-language map control | No | Low |
| `services/daily_sync.py` | Daily pipeline | No | Low |
| `services/webhook.py` | FastAPI intake (WhatsApp, auctions), authenticated | No | Medium |
| `ui/map_dashboard.py` | Streamlit + Folium, password-protected | No | Medium |

**Removed from earlier draft:** `route_builder.py` (SVD straight-line route) and Google satellite tiles. The owner chose the official map. Map tiles must follow `docs/SOURCES.md` terms (Maps Platform key, or OpenStreetMap / satellite with attribution).

## 4. Processes (production)
1. `uvicorn` webhook on `127.0.0.1:8001`
2. `node whatsapp_listener/index.js`
3. Streamlit UI on `127.0.0.1:8501` (behind proxy)
4. systemd timer → `make sync` daily

## 5. Storage
| File | Content |
|---|---|
| `raw_pdfs/` (with manifest) | Gazette and circular PDFs |
| `notice_dots.json` | Survey numbers and notice dots |
| `official_alignment.geojson` | Official highway line |
| `snapped_dots.geojson` | Dots on alignment |
| `village_cadastrals.geojson` | Parcel polygons |
| `patta_registry.json` | Patta and owner records (non-sensitive fields) |
| `owners.db` | Encrypted owner records (SQLite, key from `OWNER_DB_KEY`) |
| `whatsapp_deals.json` | WhatsApp listings |
| `auction_listings.json` | Auction records |
| `audit_log.jsonl` | Who, what, when, for every write |

Note: the design also keeps owner data in `owners.db`. Use one owner store; do not duplicate owner fields into `patta_registry.json`. Resolve this in `docs/OPEN_QUESTIONS.md`.
