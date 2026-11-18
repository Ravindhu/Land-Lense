# Deployment (Ubuntu LTS, self-hosted)

## 1. Stack
- Python 3.10+ in a venv
- Node.js LTS (Baileys listener)
- SQLite (owner records, encrypted) and JSON / GeoJSON files
- Caddy (reverse proxy, automatic HTTPS)
- systemd for services and timer
- UFW firewall

## 2. Services
| Unit | Command | Bind |
|---|---|---|
| `tn-intel-webhook.service` | uvicorn `tn_highway_intel.services.webhook:app` | 127.0.0.1:8001 |
| `tn-intel-whatsapp.service` | `node whatsapp_listener/index.js` | none (outbound only) |
| `tn-intel-ui.service` | Streamlit `ui/map_dashboard.py` | 127.0.0.1:8501 |
| `tn-intel-sync.timer` | `make sync` daily | none |

Each service runs as a non-root user. Mode 600 on `.env`.

## 3. First-time setup
```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades python3-venv nodejs npm ufw caddy
sudo ufw allow from <known-ip> to any port 22
sudo ufw allow 80,443/tcp && sudo ufw enable
make install
cp .env.example .env && chmod 600 .env
```

## 4. Backups
- Nightly copy of `storage/` (JSON, GeoJSON, audit log, encrypted `owners.db`) to a second location (external disk or cloud).
- Keep `raw_pdfs/` with its manifest so each notice can be re-checked.
- **Test one restore per month.** Record the date in `docs/DECISIONS.md` or a log.
- Owner records are encrypted in the backup too. Keep `OWNER_DB_KEY` separate from the backup.

## 5. Monitoring and alerts
- `daily_sync` writes a status file.
- Telegram bot alerts for: sync failed or partial; new target; stage change; auction matching a target; WhatsApp disconnected; backup failed.
- Alerts contain no owner data. They link to the dashboard.

## 6. Updates
- Unattended security updates on the OS.
- Update Python and npm dependencies manually, then run `make test`.
- Update Baileys often (protocol changes); test the listener after each update.

## 7. Failure response
See `docs/SECURITY_AND_LEGAL.md` section 8.
