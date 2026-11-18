# Product requirements (PRD)

**Version:** 0.1 (from PROJECT.md, 17 Nov 2026)

## 1. Problem
Highway land acquisition notices in Tamil Nadu are published as gazette PDFs with survey numbers. Linking them to the real highway line, to parcels, and to owners is manual and slow. The owner wants to find good land investments earlier and with sources for every fact.

## 2. Goals
1. Collect acquisition notices from Central and Tamil Nadu gazettes.
2. Place notice dots on the official alignment.
3. Identify target parcels that are inside the zone after approval.
4. Show parcel size and owner details for targets.
5. Track bank auction properties and WhatsApp broker listings in the same corridor.

## 3. Non-goals
- Multi-user accounts, roles, or sharing.
- Investment advice or automated buying.
- Mass messaging of any kind.
- Public website.
- Guessing highway routes where no official map exists.

## 4. Users
One person: the owner. Access control is still required because the server is internet-reachable.

## 5. Functional requirements

| ID | Requirement | Owner decision |
|---|---|---|
| FR-1 | Collect Central (MoRTH/NHAI) and TN gazette notices, store PDFs with manifest | Phase 1 |
| FR-2 | Extract survey numbers and notice dots from Tamil and English PDFs, with confidence | Round 1 |
| FR-3 | Use the official alignment as the only highway line | Decision 5 |
| FR-4 | Snap each notice dot to the alignment; flag dots beyond tolerance | Decision 5 |
| FR-5 | Map survey numbers to TNGIS parcel polygons | Decision 7 |
| FR-6 | Mark a parcel as target when stage ≥ approval stage and inside target zone | Round 3, 4 |
| FR-7 | Show parcel size (sq ft and cents), owner details, stage, date, source, distances | Decision 7 |
| FR-8 | Show which ROW value and margin were used for each section | Section 6.1 |
| FR-9 | Track bank auction properties; pin when survey number matches a target | Round 2 |
| FR-10 | Ingest WhatsApp broker listings via read-only listener and webhook | Decision 2 |
| FR-11 | Daily sync: collect, parse, snap, filter, refresh, audit | Section 4.4 |
| FR-12 | Telegram alerts (no owner data; link to dashboard) | Round 2 |
| FR-13 | Password-protected dashboard | Section 7.5 |
| FR-14 | Nightly backups and monthly restore test | Section 8 |

## 6. Non-functional requirements
- **Privacy:** owner data encrypted at rest, shown only in owner panel, audited on view and edit.
- **Traceability:** every record has source file, page, and date.
- **Reliability:** daily sync is idempotent; failures alert the owner.
- **Security:** webhook on localhost behind HTTPS proxy; firewall open only on 22 (known IPs), 80, 443.
- **Maintainability:** config in YAML; dependencies in one place; tests per engine module.

## 7. Success measures (proposed; owner to confirm)
- OCR survey-number accuracy measured on 30–50 labelled pages before use.
- Zero dots on the map that are not on the official alignment.
- Zero owner data in alerts or exports.
- One successful restore test per month.

## 8. Key risks
See `docs/SECURITY_AND_LEGAL.md` and `docs/OPEN_QUESTIONS.md`.
- Official map availability and georeferencing accuracy.
- WhatsApp account ban (risk accepted by owner).
- Source terms for portals and auction sites.
- Legal limits on PAN and Aadhaar storage.
