# AGENTS.md: rules for coding agents (tn-highway-land-intel)

Read this before changing any file. Source of truth for design: `docs/PRD.md` and `docs/RULES.md`. Owner decisions: `docs/DECISIONS.md`.

## What this project is
A single-user, self-hosted tracker for Tamil Nadu highway land acquisition. It places gazette notice dots on the official highway alignment, flags parcels inside the target zone after approval, and shows size and owner details to the owner only.

## Non-negotiable rules
1. **Official alignment only.** Never draw a guessed route. The only highway line on the map is `official_alignment.geojson`, built from the official map.
2. **Every record has a source.** Each dot, parcel, owner detail and auction keeps source file, page, and date. No source, no record.
3. **Owner data stays private.** Owner details (name, masked PAN, Aadhaar last 4) appear only in the authenticated owner panel. Never in Telegram alerts, Google Sheets, exports, logs, or commits.
4. **No full PAN or Aadhaar.** Store masked PAN and last 4 Aadhaar digits only. Do not look up any identifier from a database or portal. Do not add new identifier fields without a lawyer review (see `docs/SECURITY_AND_LEGAL.md`).
5. **Stage labels are config, not code.** Approval stage (default 3D) and stage certainty weights live in `config/settings.yaml`. Do not hardcode them.
6. **Corridor and margins are config.** ROW width is read from documents per section and stored as `row_width_m`. Never guess it.
7. **Idempotency.** Key: `(district, taluk, village, survey_no, gazette_id)`. Re-running `daily_sync` must not create duplicates.
8. **Validate all model output.** Gemini (or any OCR engine) output is validated against a Pydantic schema before storage. Low confidence goes to review.
9. **Audit every write** that touches owner, target, stage or auction data. Append to `storage/audit_log.jsonl`.
10. **Do not scrape a site until its terms are recorded** in `docs/SOURCES.md`.
11. **Bind services to 127.0.0.1.** Public access only through the reverse proxy with HTTPS.

## How to work
- Build in phase order (`docs/ROADMAP.md`). Each phase must run and have tests before the next starts.
- Keep dependencies in `pyproject.toml` only.
- Run `make test` before every commit.
- Do not commit `.env`, credential JSON, `storage/`, `auth_session/`, or `node_modules/`.
- Mark anything unverified as `TODO(verify)` in code comments and in `docs/OPEN_QUESTIONS.md`.

## Where to look
| Need | File |
|---|---|
| What to build and why | `docs/PRD.md` |
| Target zone, stages, review rules | `docs/RULES.md` |
| Module list and data flow | `docs/ARCHITECTURE.md` |
| Record shapes | `docs/DATA_MODEL.md` |
| Source list and terms status | `docs/SOURCES.md` |
| Tests | `docs/TESTING.md` |
| Server and backups | `docs/DEPLOYMENT.md` |
| Token and cost rules | `docs/TOKEN_OPTIMIZATION.md` |
| Open questions | `docs/OPEN_QUESTIONS.md` |
