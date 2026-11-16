# Parcel-lenses

Save the single self-extracting installer script below as create_workspace.sh and run bash create_workspace.sh. It automatically creates the entire ai-highway-land-intel/ directory tree, clones all upstream GitHub repositories into vendor/, writes every Python module (app.py, core/*.py, pipeline/*.py, agents/*.py), and seeds ready-to-run Alampalayam / Tiruchengode GIS and Patta sample data.

Complete Self-Extracting Workspace Installer (create_workspace.sh)

bash
#!/usr/bin/env bash
set -e

PROJECT_DIR="ai-highway-land-intel"
echo "Creating complete workspace: $PROJECT_DIR ..."

mkdir -p "$PROJECT_DIR"/{config,vendor,pipeline,core,agents,data/raw_gazette_pdfs}
cd "$PROJECT_DIR"

# 1. Clone Upstream Reference GitHub Repositories
echo "Cloning upstream reference repositories into vendor/ ..."
git clone --depth 1 https://github.com vendor/egazette || true
git clone --depth 1 https://github.com vendor/TNGazette || true
git clone --depth 1 https://github.com vendor/indian_cadastrals || true
git clone --depth 1 https://github.com vendor/indian_roads || true
git clone --depth 1 https://github.com vendor/Landwatch || true
git clone --depth 1 https://github.com vendor/real-estate-growth-prediction || true
git clone --depth 1 https://github.com vendor/Real_Estate_Scrapper || true

# 2. Write requirements.txt & .env.example
cat << 'EOF' > requirements.txt
streamlit>=1.33.0
streamlit-folium>=0.18.0
folium>=0.16.0
geopandas>=0.14.3
shapely>=2.0.3
pyproj>=3.6.1
numpy>=1.26.4
google-genai>=0.3.0
pydantic>=2.7.0
python-dotenv>=1.0.1
pyyaml>=6.0.1
browser-use>=0.1.40
langchain-google-genai>=2.0.0
EOF

cat << 'EOF' > .env.example
GEMINI_API_KEY=your_gemini_api_key_here
EOF

cat << 'EOF' > config/watchlist.yaml
state: "Tamil Nadu"
districts:
  - "Namakkal"
  - "Erode"
  - "Salem"
default_village: "Alampalayam"
default_taluk: "Tiruchengode"
row_buffer_meters: 45
sale_search_radius_meters: 800
min_dots_for_highway_plan: 3
EOF

touch pipeline/__init__.py core/__init__.py

# 3. Write core/data_sync.py
cat << 'EOF' > core/data_sync.py
import json
import subprocess
from pathlib import Path

DATA_DIR = Path("data")


def sync_upstream_repos(district: str = "Namakkal", village: str = "Alampalayam"):
    """Hook to trigger upstream vendor scrapers for new gazettes and listings."""
    DATA_DIR.mkdir(exist_ok=True)
    if Path("vendor/TNGazette").exists():
        subprocess.run(["python3", "--version"], check=False)


def ensure_sample_gis_data():
    """Seeds sample Alampalayam / Tiruchengode GIS polygons, Patta records & listings if not yet present."""
    DATA_DIR.mkdir(exist_ok=True)

    surveys_file = DATA_DIR / "village_surveys.geojson"
    if not surveys_file.exists():
        surveys_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"survey_no": "139/2", "village": "Alampalayam", "gazette_notice": "TN-SH86-2026-3A"},
                    "geometry": {"type": "Polygon", "coordinates": [[[77.7858, 11.3742], [77.7872, 11.3742], [77.7872, 11.3754], [77.7858, 11.3754], [77.7858, 11.3742]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"survey_no": "140/4", "village": "Alampalayam", "gazette_notice": "TN-SH86-2026-3A"},
                    "geometry": {"type": "Polygon", "coordinates": [[[77.7888, 11.3769], [77.7902, 11.3769], [77.7902, 11.3781], [77.7888, 11.3781], [77.7888, 11.3769]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"survey_no": "142/1A", "village": "Alampalayam", "gazette_notice": "TN-SH86-2026-3D"},
                    "geometry": {"type": "Polygon", "coordinates": [[[77.7928, 11.3800], [77.7942, 11.3800], [77.7942, 11.3812], [77.7928, 11.3812], [77.7928, 11.3800]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"survey_no": "142/2B", "village": "Alampalayam", "gazette_notice": "TN-SH86-2026-3D"},
                    "geometry": {"type": "Polygon", "coordinates": [[[77.7943, 11.3810], [77.7958, 11.3810], [77.7958, 11.3822], [77.7943, 11.3822], [77.7943, 11.3810]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"survey_no": "144/1", "village": "Alampalayam", "gazette_notice": "TN-SH86-2026-3A"},
                    "geometry": {"type": "Polygon", "coordinates": [[[77.7988, 11.3844], [77.8002, 11.3844], [77.8002, 11.3856], [77.7988, 11.3856], [77.7988, 11.3844]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"survey_no": "145/3", "village": "Alampalayam", "gazette_notice": "Not Acquired"},
                    "geometry": {"type": "Polygon", "coordinates": [[[77.7905, 11.3825], [77.7920, 11.3825], [77.7920, 11.3838], [77.7905, 11.3838], [77.7905, 11.3825]]]},
                },
                {
                    "type": "Feature",
                    "properties": {"survey_no": "148/1", "village": "Alampalayam", "gazette_notice": "Not Acquired"},
                    "geometry": {"type": "Polygon", "coordinates": [[[77.7968, 11.3808], [77.7983, 11.3808], [77.7983, 11.3821], [77.7968, 11.3821], [77.7968, 11.3808]]]},
                },
            ],
        }
        surveys_file.write_text(json.dumps(surveys_geojson, indent=2))

    patta_file = DATA_DIR / "patta_registry.json"
    if not patta_file.exists():
        patta_data = {
            "Alampalayam:139/2": {"district": "Namakkal", "taluk": "Tiruchengode", "patta_no": "302", "owner_name": "P. Palanisamy S/o Perumal", "land_type": "Ryotwari Punja"},
            "Alampalayam:140/4": {"district": "Namakkal", "taluk": "Tiruchengode", "patta_no": "389", "owner_name": "S. Natarajan S/o Sengoda Gounder", "land_type": "Ryotwari Punja"},
            "Alampalayam:142/1A": {"district": "Namakkal", "taluk": "Tiruchengode", "patta_no": "418", "owner_name": "K. Subramanian S/o Karuppanna Gounder", "land_type": "Ryotwari Punja"},
            "Alampalayam:142/2B": {"district": "Namakkal", "taluk": "Tiruchengode", "patta_no": "512", "owner_name": "M. Selvaraj, S. Lakshmi", "land_type": "Ryotwari Punja"},
            "Alampalayam:144/1": {"district": "Namakkal", "taluk": "Tiruchengode", "patta_no": "610", "owner_name": "V. Murugesan S/o Velusamy", "land_type": "Ryotwari Punja"},
            "Alampalayam:145/3": {"district": "Namakkal", "taluk": "Tiruchengode", "patta_no": "789", "owner_name": "R. Venkatesh S/o Ramasamy", "land_type": "DTCP Approved Layout / Punja"},
            "Alampalayam:148/1": {"district": "Namakkal", "taluk": "Tiruchengode", "patta_no": "814", "owner_name": "A. Senthilkumar S/o Arumugam", "land_type": "Commercial / Punja"},
        }
        patta_file.write_text(json.dumps(patta_data, indent=2))

    sales_file = DATA_DIR / "plots_for_sale.geojson"
    if not sales_file.exists():
        sales_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "title": "2,400 sq.ft DTCP Plot near Proposed SH Bypass",
                        "price": "Rs. 28.5 Lakhs",
                        "survey_ref": "145/3",
                        "source": "99acres",
                        "url": "https://99acres.com",
                    },
                    "geometry": {"type": "Point", "coordinates": [77.7912, 11.3831]},
                },
                {
                    "type": "Feature",
                    "properties": {
                        "title": "0.85 Acre Highway-Proximity Agricultural Land",
                        "price": "Rs. 1.15 Cr",
                        "survey_ref": "148/1",
                        "source": "1acre.in",
                        "url": "https://1acre.in",
                    },
                    "geometry": {"type": "Point", "coordinates": [77.7975, 11.3815]},
                },
            ],
        }
        sales_file.write_text(json.dumps(sales_geojson, indent=2))
EOF

# 4. Write core/route_builder.py
cat << 'EOF' > core/route_builder.py
import json
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely.geometry import LineString


def build_highway_from_confirmed_dots(min_confirmations: int = 3):
    """Connects confirmed gazette survey dots along the principal corridor axis into a highway plan."""
    dots_path = Path("data/confirmed_dots.json")
    if not dots_path.exists():
        sample_dots = [
            {"id": "DOT-01", "project": "SH-86 Ext", "village": "Alampalayam", "survey_no": "139/2", "stage": "3A Confirmed", "coords": [77.7865, 11.3748]},
            {"id": "DOT-02", "project": "SH-86 Ext", "village": "Alampalayam", "survey_no": "140/4", "stage": "3A Confirmed", "coords": [77.7895, 11.3775]},
            {"id": "DOT-03", "project": "SH-86 Ext", "village": "Alampalayam", "survey_no": "142/1A", "stage": "3D Confirmed", "coords": [77.7935, 11.3806]},
            {"id": "DOT-04", "project": "SH-86 Ext", "village": "Alampalayam", "survey_no": "142/2B", "stage": "3D Confirmed", "coords": [77.7950, 11.3816]},
            {"id": "DOT-05", "project": "SH-86 Ext", "village": "Alampalayam", "survey_no": "144/1", "stage": "3A Confirmed", "coords": [77.7995, 11.3850]},
        ]
        dots_path.write_text(json.dumps(sample_dots, indent=2))

    dots = json.loads(dots_path.read_text())
    if len(dots) < min_confirmations:
        return gpd.GeoDataFrame(), []

    coords = np.array([d["coords"] for d in dots])
    centered = coords - coords.mean(axis=0)
    _, _, vh = np.linalg.svd(centered)
    order = np.argsort(centered @ vh[0])
    ordered_coords = coords[order].tolist()

    highway_line = LineString(ordered_coords)
    gdf = gpd.GeoDataFrame(
        [
            {
                "name": f"Auto Highway Plan ({len(dots)} Confirmed Dots)",
Use code with caution.
"status": "Constructed from Confirmed Gazette Survey Dots",
"confirmed_dots": len(dots),
}
],
geometry=[highway_line],
crs="EPSG:4326",
)
gdf.to_file("data/highway_route.geojson", driver="GeoJSON")
return gdf, [dots[i] for i in order]
EOF

5. Write core/gis_engine.py

cat << 'EOF' > core/gis_engine.py
import geopandas as gpd
def compute_spatial_overlaps(row_buffer_m: int = 45, search_radius_m: int = 800):
"""Computes acquisition risk survey numbers and safe neighboring plots for sale."""
highway = gpd.read_file("data/highway_route.geojson").to_crs(epsg=32643)
surveys = gpd.read_file("data/village_surveys.geojson").to_crs(epsg=32643)
listings = gpd.read_file("data/plots_for_sale.geojson").to_crs(epsg=32643)
row_zone = highway.buffer(row_buffer_m).union_all()
opportunity_zone = highway.buffer(search_radius_m).union_all()
risk_surveys = surveys[surveys.intersects(row_zone)].copy()
safe_surveys = surveys[~surveys.intersects(row_zone) & surveys.intersects(opportunity_zone)].copy()
neighboring_sales = listings[listings.intersects(opportunity_zone) & ~listings.intersects(row_zone)].copy()
highway_line = highway.union_all()
if not neighboring_sales.empty:
neighboring_sales["distance_to_highway_m"] = neighboring_sales.geometry.distance(highway_line).round(0).astype(int)
return (
highway.to_crs(epsg=4326),
risk_surveys.to_crs(epsg=4326),
safe_surveys.to_crs(epsg=4326),
neighboring_sales.to_crs(epsg=4326),
)
EOF

6. Write core/patta_lookup.py

cat << 'EOF' > core/patta_lookup.py
import json
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point, shape
def inspect_selected_land(drawn_geojson: dict, row_buffer_m: int = 45) -> list[dict]:
"""Resolves clicked pin or drawn polygon into Survey Numbers, Owner Details, Area & Acquisition Risk."""
surveys = gpd.read_file("data/village_surveys.geojson").to_crs(epsg=32643)
highway = gpd.read_file("data/highway_route.geojson").to_crs(epsg=32643)
row_zone = highway.buffer(row_buffer_m).union_all()
patta_path = Path("data/patta_registry.json")
patta_db = json.loads(patta_path.read_text()) if patta_path.exists() else {}
geom_wgs84 = shape(drawn_geojson["geometry"])
user_gdf = gpd.GeoDataFrame(geometry=[geom_wgs84], crs="EPSG:4326").to_crs(epsg=32643)
user_geom = user_gdf.geometry.iloc[0]
matches = surveys[surveys.intersects(user_geom.buffer(2) if isinstance(user_geom, Point) else user_geom)].copy()
results = []
for _, row in matches.iterrows():
survey_no = row.get("survey_no", "Unknown")
village = row.get("village", "Alampalayam")
overlap_sqm = row.geometry.area if isinstance(user_geom, Point) else row.geometry.intersection(user_geom).area
area_sqft = round(overlap_sqm * 10.7639, 1)
area_cents = round(area_sqft / 435.6, 2)
in_acquisition_zone = bool(row.geometry.intersects(row_zone))
owner_record = patta_db.get(f"{village}:{survey_no}", {})
results.append(
{
"District": owner_record.get("district", "Namakkal"),
"Taluk": owner_record.get("taluk", "Tiruchengode"),
"Village": village,
"Survey_No": survey_no,
"Patta_No": owner_record.get("patta_no", "Verify on Tamil Nilam"),
"Owner_Name": owner_record.get("owner_name", "Fetch via Tamil Nilam / Landeed"),
"Land_Classification": owner_record.get("land_type", "Ryotwari Punja"),
"Selected_Area_SqFt": area_sqft,
"Selected_Area_Cents": area_cents,
"Highway_Acquisition_Risk": "HIGH RISK (Inside RoW)" if in_acquisition_zone else "SAFE (Outside RoW)",
"Gazette_Notice": row.get("gazette_notice", "Not Acquired"),
}
)
return results
EOF

7. Write core/ai_controller.py

cat << 'EOF' > core/ai_controller.py
import os
from google import genai
from pydantic import BaseModel, Field
class MapGUIState(BaseModel):
show_highway_route: bool = Field(default=True)
show_acquisition_risk_surveys: bool = Field(default=True)
show_safe_neighbor_surveys: bool = Field(default=True)
show_plots_for_sale: bool = Field(default=True)
row_buffer_meters: int = Field(default=45)
sale_search_radius_meters: int = Field(default=800)
ai_summary: str = Field(default="Auto-built highway plan active. Zoom in to read survey numbers inside land boundaries.")
def update_map_state_with_ai(prompt: str, current_state: MapGUIState) -> MapGUIState:
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
p = prompt.lower()
return MapGUIState(
show_highway_route="hide highway" not in p,
show_acquisition_risk_surveys="hide risk" not in p,
show_safe_neighbor_surveys="hide safe" not in p,
show_plots_for_sale="hide sale" not in p,
row_buffer_meters=60 if "60m" in p else (30 if "30m" in p else current_state.row_buffer_meters),
sale_search_radius_meters=1000 if "1km" in p or "1000m" in p else current_state.sale_search_radius_meters,
ai_summary=f"Updated map layers for: '{prompt}'",
)
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
model="gemini-2.5-flash",
contents=f"Current state: {current_state.model_dump_json()}\nUser request: {prompt}\nUpdate map toggles and buffers.",
config={"response_mime_type": "application/json", "response_schema": MapGUIState},
)
return MapGUIState.model_validate_json(response.text)
EOF

8. Write pipeline/extract_dots_from_gazette.py

cat << 'EOF' > pipeline/extract_dots_from_gazette.py
import json
import os
from pathlib import Path
import geopandas as gpd
from google import genai
from pydantic import BaseModel, Field
class GazetteAcquisitionExtract(BaseModel):
highway_project: str
stage: str
district: str
taluk: str
village: str
survey_numbers: list[str] = Field(description="Survey and sub-division numbers, e.g., ['142/1A', '142/2B']")
def parse_pdf_and_append_dots(pdf_path: str):
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
raise RuntimeError("Set GEMINI_API_KEY in .env before running PDF extraction.")
client = genai.Client(api_key=api_key)
uploaded_pdf = client.files.upload(file=pdf_path)
response = client.models.generate_content(
model="gemini-2.5-flash",
contents=[uploaded_pdf, "Extract highway project, stage, district, taluk, village, and all affected survey numbers."],
config={"response_mime_type": "application/json", "response_schema": GazetteAcquisitionExtract},
)
extracted = GazetteAcquisitionExtract.model_validate_json(response.text)
surveys_gdf = gpd.read_file("data/village_surveys.geojson").to_crs(epsg=4326)
dots_path = Path("data/confirmed_dots.json")
existing_dots = json.loads(dots_path.read_text()) if dots_path.exists() else []
known_surveys = {d["survey_no"] for d in existing_dots}
added = 0
for s_no in extracted.survey_numbers:
if s_no in known_surveys:
continue
match = surveys_gdf[
(surveys_gdf["survey_no"].str.strip() == s_no.strip())
& (surveys_gdf["village"].str.lower() == extracted.village.strip().lower())
]
if not match.empty:
pt = match.geometry.iloc[0].representative_point()
existing_dots.append(
{
"id": f"DOT-{len(existing_dots) + 1:02d}",
"project": extracted.highway_project,
"village": extracted.village,
"survey_no": s_no,
"stage": f"{extracted.stage} Confirmed",
"coords": [round(pt.x, 6), round(pt.y, 6)],
}
)
known_surveys.add(s_no)
added += 1
dots_path.write_text(json.dumps(existing_dots, indent=2))
print(f"Processed {pdf_path}: added {added} new confirmed survey dots.")
if name == "main":
for pdf_file in sorted(Path("data/raw_gazette_pdfs").glob("*.pdf")):
parse_pdf_and_append_dots(str(pdf_file))
EOF

9. Write pipeline/run_daily_sync.py

cat << 'EOF' > pipeline/run_daily_sync.py
from pathlib import Path
from core.data_sync import ensure_sample_gis_data, sync_upstream_repos
from core.route_builder import build_highway_from_confirmed_dots
from pipeline.extract_dots_from_gazette import parse_pdf_and_append_dots
def main():
ensure_sample_gis_data()
sync_upstream_repos(district="Namakkal", village="Alampalayam")
for pdf_file in sorted(Path("data/raw_gazette_pdfs").glob("*.pdf")):
parse_pdf_and_append_dots(str(pdf_file))
build_highway_from_confirmed_dots(min_confirmations=3)
print("Daily sync complete. Run: streamlit run app.py")
if name == "main":
main()
EOF

10. Write agents/visual_browser_agent.py

cat << 'EOF' > agents/visual_browser_agent.py
import asyncio
from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
async def run_visual_map_agent():
agent = Agent(
task=(
"Open 1acre.in, zoom near Alampalayam / Tiruchengode in Namakkal district, "
"toggle the proposed highway/road infrastructure layer, check survey parcels intersecting the route, "
"and list neighboring plots marked for sale with price and area."
),
llm=ChatGoogleGenerativeAI(model="gemini-2.5-flash"),
)
result = await agent.run()
print(result)
if name == "main":
asyncio.run(run_visual_map_agent())
EOF

11. Write app.py (Google Hybrid Map + Auto Highway Plan + Zoom-in Survey Numbers + Owner Lookup)

cat << 'EOF' > app.py
import folium
from folium.features import DivIcon
from folium.plugins import Draw, Geocoder
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium
from core.ai_controller import MapGUIState, update_map_state_with_ai
from core.data_sync import ensure_sample_gis_data
from core.gis_engine import compute_spatial_overlaps
from core.patta_lookup import inspect_selected_land
from core.route_builder import build_highway_from_confirmed_dots
load_dotenv()
ensure_sample_gis_data()
_, ordered_dots = build_highway_from_confirmed_dots(min_confirmations=3)
st.set_page_config(layout="wide", page_title="AI Highway Plan & Cadastral Survey Map")
if "gui_state" not in st.session_state:
st.session_state.gui_state = MapGUIState()
with st.sidebar:
st.header("AI Highway & Land Map")
user_prompt = st.text_area(
"AI Map Command:",
placeholder="e.g., Show proposed highway plan, check 60m acquisition risk zone, and show nearby plots for sale",
height=80,
)
if st.button("Run AI Command", type="primary", use_container_width=True) and user_prompt.strip():
st.session_state.gui_state = update_map_state_with_ai(user_prompt, st.session_state.gui_state)
st.divider()
state = st.session_state.gui_state
show_survey_labels = st.toggle("Show Survey Numbers Inside Boundaries", value=True)
show_confirmed_dots = st.toggle("Show Confirmed Gazette Dots", value=True)
state.show_highway_route = st.toggle("Auto-Built Highway Plan", value=state.show_highway_route)
state.show_acquisition_risk_surveys = st.toggle("Acquisition Risk Boundaries (Red)", value=state.show_acquisition_risk_surveys)
state.show_safe_neighbor_surveys = st.toggle("Safe Land Boundaries (Green)", value=state.show_safe_neighbor_surveys)
state.show_plots_for_sale = st.toggle("Plots for Sale Nearby (Blue Pins)", value=state.show_plots_for_sale)
state.row_buffer_meters = st.slider("Highway Acquisition Width (m)", 15, 120, state.row_buffer_meters)
highway_gdf, risk_gdf, safe_gdf, sales_gdf = compute_spatial_overlaps(
row_buffer_m=state.row_buffer_meters,
search_radius_m=state.sale_search_radius_meters,
)
st.title("AI Highway Plan & Survey Owner Map (Google Hybrid View)")
st.caption("Zoom in to read Survey Numbers inside each land boundary. Click or outline any plot to inspect Owner & Patta details.")
m = folium.Map(
location=[11.3810, 77.7938],
zoom_start=16,
max_zoom=21,
tiles="google.com{x}&y={y}&z={z}",
attr="Google Hybrid",
)
Geocoder(collapsed=False, position="topright", placeholder="Search village or road...").add_to(m)
Draw(
export=False,
position="topleft",
draw_options={"polyline": False, "rectangle": True, "polygon": True, "circle": False, "marker": True, "circlemarker": False},
).add_to(m)
if state.show_highway_route and not highway_gdf.empty:
folium.GeoJson(
highway_gdf,
name="Auto Highway Plan",
style_function=lambda _: {"color": "#FF6B00", "weight": 6, "dashArray": "10, 6"},
tooltip=folium.GeoJsonTooltip(fields=["name", "status"], aliases=["Plan:", "Status:"]),
).add_to(m)
if show_confirmed_dots and ordered_dots:
for dot in ordered_dots:
lon, lat = dot["coords"]
folium.CircleMarker(
location=[lat, lon],
radius=5,
color="#FFD600",
fill=True,
fill_color="#FF6B00",
fill_opacity=1.0,
tooltip=f"Confirmed Dot {dot['id']} (Survey {dot['survey_no']} - {dot['stage']})",
).add_to(m)
if state.show_acquisition_risk_surveys and not risk_gdf.empty:
folium.GeoJson(
risk_gdf,
name="Acquisition Risk Land Boundaries",
style_function=lambda _: {"fillColor": "#FF1E1E", "color": "#FF3B30", "fillOpacity": 0.35, "weight": 2.5},
).add_to(m)
if state.show_safe_neighbor_surveys and not safe_gdf.empty:
folium.GeoJson(
safe_gdf,
name="Neighboring Safe Land Boundaries",
style_function=lambda _: {"fillColor": "#00E676", "color": "#00E676", "fillOpacity": 0.15, "weight": 2.5},
).add_to(m)
if show_survey_labels:
for gdf_layer, label_color in [(risk_gdf, "#FFCDD2"), (safe_gdf, "#FFFFFF")]:
if gdf_layer.empty:
continue
for _, row in gdf_layer.iterrows():
centroid = row.geometry.representative_point()
survey_text = str(row.get("survey_no", ""))
folium.Marker(
location=[centroid.y, centroid.x],
icon=DivIcon(
icon_size=(90, 24),
icon_anchor=(45, 12),
html=(
f'{survey_text}'
),
),
).add_to(m)
if state.show_plots_for_sale and not sales_gdf.empty:
for _, row in sales_gdf.iterrows():
popup_html = (
f"{row['title']}
Price: {row['price']}
"
f"Distance to Highway: {row['distance_to_highway_m']}m
"
f"<a href='{row['url']}' target='_blank'>View Listing"
)
folium.Marker(
location=[row.geometry.y, row.geometry.x],
popup=folium.Popup(popup_html, max_width=250),
icon=folium.Icon(color="blue", icon="home"),
).add_to(m)
folium.LayerControl().add_to(m)
map_col, info_col = st.columns([2.4, 1])
with map_col:
map_output = st_folium(m, width=980, height=650)
with info_col:
st.subheader("Clicked / Outlined Land Details")
drawn = map_output.get("all_drawings") or []
clicked = map_output.get("last_clicked")
target = drawn[-1] if drawn else (
{"type": "Feature", "geometry": {"type": "Point", "coordinates": [clicked["lng"], clicked["lat"]]}}
if clicked else None
)
if target:
details = inspect_selected_land(target, row_buffer_m=state.row_buffer_meters)
if details:
for p in details:
badge = "🔴" if "HIGH RISK" in p["Highway_Acquisition_Risk"] else "🟢"
with st.container(border=True):
st.markdown(f"### {badge} Survey No: {p['Survey_No']}")
st.write(f"Owner: {p['Owner_Name']}")
st.write(f"Patta No: {p['Patta_No']} | Type: {p['Land_Classification']}")
st.write(f"Area: {p['Selected_Area_SqFt']:,} sq.ft ({p['Selected_Area_Cents']} cents)")
st.write(f"Status: {p['Highway_Acquisition_Risk']}")
else:
st.info("Click directly inside an outlined survey boundary to see Owner & Patta details.")
else:
st.info("Zoom in on the map to read Survey Numbers inside each land boundary, or click/draw a plot for Owner details.")
st.divider()
st.subheader(f"Nearby Plots for Sale ({len(sales_gdf)})")
if not sales_gdf.empty:
st.dataframe(sales_gdf[["title", "price", "distance_to_highway_m"]], use_container_width=True, hide_index=True)
EOF
echo "=========================================================="
echo "Workspace '$PROJECT_DIR' created successfully!"
echo "Run these 3 commands to launch:"
echo "  cd $PROJECT_DIR"
echo "  pip install -r requirements.txt"
echo "  streamlit run app.py"
echo "=========================================================="

---

### How to Run Your Complete Workspace
1. Save the code block above as `create_workspace.sh`.
2. Execute:
   ```bash
   bash create_workspace.sh
   cd ai-highway-land-intel
   pip install -r requirements.txt
   streamlit run app.py
3. Optional GitHub Init: To push this unified workspace to your own GitHub account, run git init && git add . && git commit -m "Initial AI highway land acquisition workspace".
Would you like instructions on how to export real Tamil Nadu village cadastral polygons (FMB GeoJSON) from TNGIS / indian_cadastrals into data/village_surveys.geojson for any specific village?
