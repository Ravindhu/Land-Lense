Here is the complete, standalone src/ layout workspace (tn-highway-land-intel/) with zero external vendor/ dependencies—every gazette scraper, TN Govt TNGIS cadastral boundary loader, auto-highway route builder, Patta owner lookup, WhatsApp broker group listener, and Google Hybrid map UI is consolidated cleanly inside src/ and whatsapp_listener/.

1. Complete Standalone src/ Workspace Tree (tn-highway-land-intel/)

text
tn-highway-land-intel/
├── pyproject.toml                          # Standard Python src-layout build & package metadata
├── requirements.txt                        # All Python runtime dependencies
├── Makefile                                # Single-word commands: make install, make sync, make whatsapp, make ui
├── .env.example                            # GEMINI_API_KEY, GOOGLE_SHEET_NAME, GOOGLE_SERVICE_ACCOUNT_JSON
├── .gitignore                              # Ignores venv/, storage/raw_pdfs/, .env, node_modules/, auth_session/
├── README.md                               # Quickstart, Indian-IP TNGIS guide, WhatsApp QR setup & cron docs
│
├── config/
│   └── settings.yaml                       # Erode, Perundurai, Bhavani, Tiruchengode & Namakkal corridor config
│
├── src/
│   └── tn_highway_intel/                   # Importable Python package (src-layout)
│       ├── __init__.py
│       │
│       ├── domain/                         # Core Data Models & Settings Loader
│       │   ├── __init__.py
│       │   ├── models.py                   # Pydantic models: ConfirmedDot, SurveyParcel, PattaRecord, PropertyPin, MapState
│       │   └── settings.py                 # Loads config/settings.yaml & .env variables
│       │
│       ├── collectors/                     # Native Data Collectors (Zero external repo clones)
│       │   ├── __init__.py
│       │   ├── central_egazette.py         # Fetches Central Extraordinary Gazettes (NHAI / MoRTH Section 3A & 3D PDFs)
│       │   ├── tn_state_gazette.py         # Fetches Tamil Nadu Govt Gazettes & Highways G.O.s (requires Indian IP)
│       │   ├── tngis_cadastral.py          # Connects to TN Govt TNGIS (tngis.tn.gov.in) WMS & village FMB GeoJSONs
│       │   └── portal_listings.py          # Scrapes & geocodes plots/land for sale around Erode & Namakkal
│       │
│       ├── engine/                         # Geospatial, AI & Valuation Engines
│       │   ├── __init__.py
│       │   ├── gazette_parser.py           # Multilingual Gemini PDF OCR (Tamil + English) -> survey numbers & GPS dots
│       │   ├── route_builder.py            # Auto-stitches confirmed survey dots into continuous proposed highway plan
│       │   ├── spatial_analyzer.py         # Builds Highway Project Outer Boundary (RoW) + Red (Risk) vs. Green (Safe) plots
│       │   ├── patta_lookup.py             # Resolves clicked/outlined land area -> Survey No, Patta No, Owner & Area
│       │   ├── corridor_scorer.py          # Computes NH Act 3A–3H stage certainty & locality growth velocity score
│       │   └── ai_map_agent.py             # Translates natural-language user prompts into live map toggles & buffers
│       │
│       ├── services/                       # Orchestrators & API Endpoints
│       │   ├── __init__.py
│       │   ├── daily_sync.py               # Master cron job: Collect Gazettes -> Parse Dots -> Rebuild Highway -> Update Map
│       │   └── whatsapp_webhook.py         # FastAPI webhook: AI filters WhatsApp group deals -> Google Sheets + Map Pin
│       │
│       └── ui/                             # Interactive Google-Hybrid Map Frontend
│           ├── __init__.py
│           └── map_dashboard.py            # Streamlit + Folium Google Hybrid Map (Zoom-in Boundaries + Survey Nos + Contacts)
│
├── whatsapp_listener/                      # Native Node.js Baileys Socket Listener (Secondary SIM)
│   ├── package.json                        # @whiskeysockets/baileys, axios, qrcode-terminal
│   └── index.js                            # Captures Erode/TN real-estate WhatsApp group messages & pins -> FastAPI
│
├── tests/                                  # Unit tests for spatial overlaps, route stitching & Patta lookup
│   ├── __init__.py
│   └── test_spatial_engine.py
│
└── storage/                                # Local Runtime Data Store (JSON & GeoJSON)
    ├── raw_pdfs/                           # Downloaded Central & Tamil Nadu highway acquisition PDFs
    ├── confirmed_dots.json                 # Confirmed survey centroids that auto-generate the proposed highway plan
    ├── highway_route.geojson               # Auto-constructed continuous proposed highway centerline
    ├── village_cadastrals.geojson          # Official TN Govt TNGIS land boundary polygons with survey_no metadata
    ├── patta_registry.json                 # Cached Tamil Nadu Patta & Owner details mapped by Village:Survey_No
    ├── whatsapp_deals.json                 # Structured log of extracted WhatsApp broker land deals
    └── active_listings.geojson             # Combined portal + WhatsApp pins with Price, Distance & Seller Contact Info
Use code with caution.

2. Package Configuration (pyproject.toml & Makefile)

Using a standard pyproject.toml with src/tn_highway_intel makes every module cleanly importable (from tn_highway_intel.engine.route_builder import ...) without sys.path hacks.

pyproject.toml

toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "tn-highway-intel"
version = "1.0.0"
description = "AI Highway Land Acquisition Tracker, TNGIS Survey Boundary Inspector & Real-Estate Deal Map"
requires-python = ">=3.10"
dependencies = [
    "streamlit>=1.33.0",
    "streamlit-folium>=0.18.0",
    "folium>=0.16.0",
    "geopandas>=0.14.3",
    "shapely>=2.0.3",
    "pyproj>=3.6.1",
    "numpy>=1.26.4",
    "google-genai>=0.3.0",
    "pydantic>=2.7.0",
    "python-dotenv>=1.0.1",
    "pyyaml>=6.0.1",
    "requests>=2.31.0",
    "beautifulsoup4>=4.12.3",
    "fastapi>=0.111.0",
    "uvicorn>=0.30.0",
    "geopy>=2.4.1",
    "gspread>=6.1.0",
    "google-auth>=2.29.0",
]

[tool.setuptools.packages.find]
where = ["src"]
Use code with caution.

Makefile

makefile
install:
	python3 -m venv venv && . venv/bin/activate && pip install -e .
	cd whatsapp_listener && npm install

sync:
	python -m tn_highway_intel.services.daily_sync

whatsapp:
	uvicorn tn_highway_intel.services.whatsapp_webhook:app --port 8001

ui:
	streamlit run src/tn_highway_intel/ui/map_dashboard.py

test:
	pytest tests/
Use code with caution.

3. Detailed Breakdown of Every Package Inside src/tn_highway_intel/


A. src/tn_highway_intel/domain/ (Schemas & Configuration)

• models.py: Defines strict Pydantic schemas:
	• ConfirmedDot: id, project, district, taluk, village, survey_no, stage (3A / 3D / 15(2)), coords ([lon, lat]).
	• PattaRecord: district, taluk, village, survey_no, patta_no, owner_name, land_type.
	• PropertyPin: title, price, survey_ref, contact_name, contact_phone, highway_note, source, url, distance_to_highway_m.
	• MapState: Controls UI layer toggles (show_project_boundary, show_tngis_wms, show_survey_labels, show_risk_parcels, show_safe_parcels, show_contact_pins) and buffer sliders (row_width_meters, sale_search_radius_meters).
• settings.py: Loads config/settings.yaml (defaulting to Erode, Perundurai, Bhavani, Gobichettipalayam, and Tiruchengode corridors) and API keys from .env.

B. src/tn_highway_intel/collectors/ (Self-Contained Data Ingestion)

• central_egazette.py: Queries egazette.gov.in Extraordinary Gazette feeds for Ministry of Road Transport and Highways (MoRTH / NHAI) acquisition notices and saves PDFs into storage/raw_pdfs/.
• tn_state_gazette.py: Scrapes stationeryprinting.tn.gov.in (Tamil Nadu Government Gazette & Highways Department G.O.s) from your Indian IP in Erode/Tamil Nadu.
• tngis_cadastral.py: Connects directly to TN Govt TNGIS (tngis.tn.gov.in/geoserver/wms and tngis.tnega.org) to stream official FMB survey boundaries on zoom-in (zoom >= 15) and normalizes exported village GeoJSON polygons into storage/village_cadastrals.geojson.
• portal_listings.py: Fetches active land/plot listings near Erode, Perundurai, and Tiruchengode, geocodes landmarks, and outputs structured GeoJSON pins into storage/active_listings.geojson.

C. src/tn_highway_intel/engine/ (AI & Spatial Core)

• gazette_parser.py: Uploads newly downloaded Tamil or English highway PDFs to Gemini (gemini-2.5-flash), extracts affected survey/sub-division numbers, looks up their cadastral polygon centroids, and appends new dots to storage/confirmed_dots.json.
• route_builder.py: Orders confirmed survey dots along the principal corridor axis using Singular Value Decomposition (SVD) and automatically constructs/extends the proposed highway alignment (storage/highway_route.geojson).
• spatial_analyzer.py: Projects layers into UTM Zone 43N (EPSG:32643) for accurate meter-level measurements in Tamil Nadu:
	• Draws the Yellow/Orange Highway Project Outer Boundary (e.g., 45m or 60m Right-of-Way band).
	• Flags intersecting land boundaries in Red (High Acquisition Risk).
	• Outlines neighboring safe land boundaries in Green (Investment Opportunity).
	• Measures exact distance in meters from each nearby plot for sale to the outer edge of the highway boundary.
• patta_lookup.py: Whenever you click a point or draw a custom polygon on the map, computes exact overlapping area in Sq.Ft and Cents and returns Survey No, Patta No, Owner Name, Land Classification, and Acquisition Status.
• corridor_scorer.py: Scores opportunity parcels (0–100) by combining statutory stage certainty (3A = 65%, 15(2) = 70%, 3D = 92%, 3G = 98%) with proximity to the new highway boundary.
• ai_map_agent.py: Converts natural-language user prompts (e.g., "Show 60m highway boundary, zoom to Perundurai, and show WhatsApp land contacts within 1km") into updated MapState toggles and buffer parameters.

D. src/tn_highway_intel/services/ & whatsapp_listener/

• daily_sync.py: Runs the complete daily pipeline (Central + TN Gazettes -> AI PDF Dot Extraction -> Auto Highway Route Rebuild -> Portal Listings & Valuation Update).
• whatsapp_webhook.py + whatsapp_listener/index.js: Connects a dedicated secondary WhatsApp number via QR code (@whiskeysockets/baileys), filters out group chatter with AI, extracts Price, Plot Size, Village, Survey Ref, and Seller/Broker Phone, logs to Google Sheets (gspread), and drops clickable Contact Pins (tel: + wa.me button) onto the map.

E. src/tn_highway_intel/ui/map_dashboard.py

• Renders Google Hybrid Satellite Tiles (://google.com) with:
	• Yellow/Orange Dashed Highway Project Boundary + confirmed gazette survey dots.
	• Live TN Govt TNGIS Land Boundaries + permanent centered Survey Number labels inside every parcel when zoomed in.
	• Interactive Draw / Click Tool to inspect Owner Name, Patta No & Sq.Ft/Cents on the right panel.
	• Clickable Seller/Broker Contact Pins showing asking price, distance to the highway boundary, phone number, and a one-click Message on WhatsApp button.

4. Quickstart Execution Commands

bash
# 1. Install the standalone package in editable src-layout mode + Node WhatsApp listener
cd tn-highway-land-intel
make install

# 2. Configure API keys
cp .env.example .env

# 3. Start live WhatsApp broker group listener (in two terminals, using a secondary SIM)
make whatsapp
cd whatsapp_listener && node index.js

# 4. Sync gazettes, extract survey dots & auto-build highway plan
make sync

# 5. Launch the Google Hybrid Map GUI
make ui
Use code with caution.
Would you like me to generate the single-file bash script (create_tn_highway_intel.sh) that creates this complete src/tn_highway_intel/ workspace with every Python, YAML, TOML, and Node.js file populated and ready to run?
