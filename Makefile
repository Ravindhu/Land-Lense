PY ?= .venv/bin/python

install:
	python3 -m venv .venv
	$(PY) -m pip install -e ".[dev]"
	cd whatsapp_listener && npm install

test:
	$(PY) -m pytest -q
	cd whatsapp_listener && node --test

sync:
	$(PY) -m tn_highway_intel.services.daily_sync

serve:
	$(PY) -m uvicorn tn_highway_intel.services.webhook:app --host 127.0.0.1 --port 8001

whatsapp:
	cd whatsapp_listener && node index.js

ui:
	$(PY) -m streamlit run src/tn_highway_intel/ui/map_dashboard.py --server.address 127.0.0.1 --server.port 8501
