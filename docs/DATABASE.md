# Database (DATABASE.md)

Read `docs/DATA_MODEL.md` for record shapes and `docs/ARCHITECTURE.md` section 5 for file storage. This file defines the storage technology, the owner database schema, keys, indexes, encryption, migrations, and backups.

## 1. Technology
| Store | Technology | What it holds | Why |
|---|---|---|---|
| Owner database | SQLite file `storage/owners.db`, field-level encryption | Owner records and parcel links | Single file, no server, easy to back up |
| Land records | JSON and GeoJSON files in `storage/` | Notice dots, parcels, alignment, targets, auctions, WhatsApp listings | Matches the design in PROJECT.md section 3; simple to inspect |
| Audit trail | Append-only `storage/audit_log.jsonl` | Every write to owner, target, stage and auction data | Simple, tamper-evident with a hash chain (see section 7) |

**Decision to confirm:** keep land records in JSON for the MVP. Move them to SQLite when the record count or query needs justify it. Record the decision in `docs/DECISIONS.md`.

No network database. No hosted database service.

## 2. Owner database schema (`owners.db`)

### 2.1 Tables

**owner**
| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | Primary key |
| `owner_name_enc` | BLOB | no | Encrypted full name |
| `pan_masked` | TEXT | yes | Masked, e.g. `ABCDE****F`. Full PAN never stored. |
| `aadhaar_last4_enc` | BLOB | yes | Encrypted last 4 digits only |
| `owner_source` | TEXT | no | Document name and date. Not encrypted. |
| `verified_on` | TEXT (ISO date) | no | Not encrypted |
| `created_at` | TEXT (ISO datetime) | no | |
| `updated_at` | TEXT (ISO datetime) | no | |

**owner_parcel**
| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | Primary key |
| `owner_id` | INTEGER | no | FK → `owner.id`, ON DELETE RESTRICT |
| `district` | TEXT | no | |
| `taluk` | TEXT | no | |
| `village` | TEXT | no | |
| `survey_no` | TEXT | no | |
| `parcel_ref` | TEXT | yes | ID of the parcel in `village_cadastrals.geojson` |
| `linked_on` | TEXT (ISO date) | no | |

**owner_access_log** (optional mirror; the JSONL audit log is the primary record)
| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | no | Primary key |
| `owner_id` | INTEGER | no | FK → `owner.id` |
| `action` | TEXT | no | `view`, `create`, `update`, `delete` |
| `at` | TEXT (ISO datetime) | no | |
| `session_ref` | TEXT | yes | Hashed session ID, never the raw token |

### 2.2 Relationships (ER)
```
owner 1 ──< owner_parcel          (one owner, many parcels)
owner 1 ──< owner_access_log      (one owner, many access events)
```
Parcels are keyed by `district, taluk, village, survey_no`. They are not stored in this database; the land-record files hold them.

### 2.3 Constraints
- `owner.owner_source` must be non-empty. Enforced by `CHECK (length(owner_source) > 0)`.
- `owner.pan_masked` must match the masked pattern. Checked as length 10 with `****` at positions 6 to 9 (`CHECK (pan_masked IS NULL OR (length(pan_masked) = 10 AND substr(pan_masked, 6, 4) = '****'))`); the letter pattern is checked in Python (`MASKED_PAN_RE`). GLOB is not used because `*` is a wildcard there, not a literal asterisk.
- `owner_parcel` unique on `(owner_id, district, taluk, village, survey_no)`.
- Foreign keys enabled on every connection: `PRAGMA foreign_keys = ON`.

### 2.4 Indexes (based on real queries)
| Index | Query it serves |
|---|---|
| `owner_parcel(district, taluk, village, survey_no)` | Find the owner of a target parcel |
| `owner_parcel(owner_id)` | List parcels for one owner in the owner panel |
| `owner_access_log(owner_id, at)` | Show "viewed at" history in the owner panel |

No other indexes for the MVP. Add more only after a measured slow query.

## 3. Encryption
- Application-level field encryption with **Fernet** (AES-128-CBC with HMAC-SHA256) from the `cryptography` package.
- Key from `.env` as `OWNER_DB_KEY`. Stored with mode 600. Never in Git, backups, logs or alerts.
- Encrypted fields: `owner_name_enc`, `aadhaar_last4_enc`.
- Not encrypted, by design: masked PAN, source text, dates. They contain no full identifier.
- **Alternative:** SQLCipher (whole-file encryption). Not chosen for the MVP because it adds a build dependency. Revisit if more sensitive fields are added. Record the choice in `docs/DECISIONS.md`.
- **Key loss = data loss.** Keep a copy of `OWNER_DB_KEY` in the owner's password manager, separate from the backup.

## 4. Access rules
- Only the owner's service process opens `owners.db`. File permission 600, owned by the service user.
- No API endpoint returns owner data (see `docs/API.md`). Owner data is read by the authenticated dashboard only.
- Writes happen only through `patta_lookup.py` or the owner form, and each write creates an audit entry.

## 5. Migrations
- Use a numbered migration folder: `migrations/ (repo root)0001_init.sql`, `0002_...sql`.
- Track the applied version in `PRAGMA user_version`.
- Each migration runs in a transaction. Failure rolls back and stops the sync with an alert.
- Migrations are forward-only in production. A down-migration needs a backup and an owner decision.
- Test every migration on a copy of the current `owners.db` before applying.

## 6. Seed and test data
- No real owner data in tests or seeds.
- Test fixtures use invented names and masked identifiers stored in `tests/data/owners_fixture.json`.
- Dev database is a separate file: `storage/owners_dev.db`, never the production file.

## 7. Audit log integrity
- `audit_log.jsonl` lines carry a SHA-256 hash of the previous line (`prev_hash`). A broken chain shows tampering or a bad write.
- A daily job checks the chain and alerts on a break (see `docs/DEPLOYMENT.md`).

## 8. Backup and recovery
- Nightly copy of `owners.db` to a second location, plus `audit_log.jsonl`.
- Backups stay encrypted at rest (the database is already field-encrypted; the backup location must also be private).
- Restore test once a month: restore to a temp path, open with `OWNER_DB_KEY`, count rows, compare with live counts, delete the temp copy.
- Recovery target: restore within one working day. Record each restore test in `docs/DECISIONS.md`.

## 9. Sensitive-data handling summary
| Data | Stored | Encrypted | Shown | Logged |
|---|---|---|---|---|
| Owner name | Yes | Yes | Owner panel | Name never logged; ID logged |
| Masked PAN | Yes | No (masked) | Owner panel | Never logged in full |
| Aadhaar last 4 | Yes, if document shows it | Yes | Owner panel | Never logged |
| Owner source | Yes | No | Owner panel | Yes |
| Full PAN / full Aadhaar | Never | n/a | Never | Never |

Legal review still required before any identifier is stored (`docs/SECURITY_AND_LEGAL.md`).
