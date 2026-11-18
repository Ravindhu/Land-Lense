# tn-highway-land-intel: documentation index

Personal highway land-acquisition tracker for the Tamil Nadu corridor (Erode, Perundurai, Bhavani, Gobichettipalayam, Tiruchengode, Namakkal).

**Status:** Design complete, no code yet. See `docs/ROADMAP.md`.
**Users:** one (the owner). **Hosting:** self-hosted Ubuntu LTS.

## What it does
1. Collects highway land-acquisition notices from Central and Tamil Nadu gazettes.
2. Places each notice's survey numbers on the official highway map.
3. Flags parcels near the highway after official approval (stage 3D).
4. Shows each target parcel's size and owner details (owner panel only).
5. Tracks bank auction properties and WhatsApp broker listings in the same corridor.

## Not financial advice
Scores and flags are research aids. Check every record against its source and date before acting.

## Documentation
| File | Purpose |
|---|---|
| `AGENTS.md` | Rules for coding agents |
| `docs/PRD.md` | Product requirements |
| `docs/RULES.md` | Target zone, stages, review rules |
| `docs/ARCHITECTURE.md` | Modules and data flow |
| `docs/DESIGN.md` | Visual design, components, states, accessibility |
| `docs/DATABASE.md` | Storage technology, owner database schema, encryption, migrations, backups |
| `docs/DATA_MODEL.md` | Record shapes |
| `docs/API.md` | Webhook endpoints, outbound integrations, environment variables |
| `docs/SOURCES.md` | Data sources and terms status |
| `docs/SECURITY_AND_LEGAL.md` | Security, privacy, legal |
| `docs/DEPLOYMENT.md` | Ubuntu server, backups, alerts |
| `docs/TESTING.md` | Test plan and labelled samples |
| `docs/TOKEN_OPTIMIZATION.md` | Cutting LLM, OCR, and fetch costs |
| `docs/DECISIONS.md` | Owner decisions log |
| `docs/OPEN_QUESTIONS.md` | Unresolved points |
| `CHANGELOG.md` | Document history |

## Quick start (once code exists)
```bash
make install                 # venv, editable install, npm install
cp .env.example .env         # fill in keys (never commit)
make serve                   # webhook + WhatsApp listener (supervised)
make sync                    # daily pipeline (also run by systemd timer)
make ui                      # Streamlit dashboard (behind proxy)
make test                    # pytest
```
