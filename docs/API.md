# API (API.md)

Defines every HTTP endpoint, every outbound integration, and the rules that apply to both. The project has one small HTTP service (the webhook). The dashboard is Streamlit and does not expose a JSON API. Owner data has no endpoint.

Read `docs/ARCHITECTURE.md` for process layout and `docs/SECURITY_AND_LEGAL.md` for the privacy rules.

## 1. Inbound HTTP service (`webhook.py`, FastAPI)

**Bind:** `127.0.0.1:8001` only. Public access only through the Caddy reverse proxy with HTTPS.

### 1.1 Endpoints
| Method | Path | Purpose | Auth |
|---|---|---|---|
| GET | `/health` | Liveness check. Returns `{"status": "ok", "time": "<ISO>"}`. No data. | None (localhost only; proxy blocks it publicly) |
| POST | `/v1/listings/whatsapp` | Receive a WhatsApp broker listing from the listener | `X-Webhook-Secret` header |
| POST | `/v1/auctions` | Receive an auction record (manual or from a permitted feed) | `X-Webhook-Secret` header |

No GET endpoint returns listings, parcels, targets or owner data.

### 1.2 Authentication
- Every write endpoint requires the header `X-Webhook-Secret` equal to `WEBHOOK_SECRET`.
- Compare with `hmac.compare_digest`. Never with `==`.
- Missing or wrong secret: `401` with body `{"error": "unauthorized"}`. No detail about why.
- Rotate `WEBHOOK_SECRET` on a schedule and after any suspected leak (`docs/SECURITY_AND_LEGAL.md` section 8).

### 1.3 Request format
- `Content-Type: application/json`. Other types: `415`.
- Body size limit: 64 KB. Larger: `413`.
- All bodies validated against a Pydantic model. Unknown fields rejected (`extra = forbid`).

**WhatsApp listing body**
```json
{
  "message_id": "string, required, unique per group message",
  "group_ref": "string, required",
  "received_at": "ISO datetime, required",
  "village": "string",
  "survey_ref": "string",
  "plot_size": "string",
  "price_inr": "integer, optional",
  "contact_phone": "string, optional",
  "text": "string, max 2000 chars, required"
}
```
The listener sends the raw message text. The server extracts fields with the parser, and stores only the fields in `PropertyPin`. `contact_phone` is stored, but masked in every alert and export.

**Auction body**
```json
{
  "auction_id": "string, required",
  "bank_name": "string, required",
  "survey_no": "string, required",
  "village": "string, required",
  "reserve_price_inr": "integer, required",
  "emd_inr": "integer, optional",
  "auction_date": "YYYY-MM-DD, required",
  "status": "active | expired | sold, required",
  "notice_pdf": "relative path under storage/raw_pdfs/, required",
  "notice_date": "YYYY-MM-DD, required",
  "source_url": "https URL, required"
}
```
`notice_pdf` must resolve under `storage/raw_pdfs/`. Any other path is rejected to block path traversal.

### 1.4 Responses
| Status | Meaning | Body |
|---|---|---|
| 201 | Created | `{"id": "<id>", "status": "created"}` |
| 200 | Duplicate (same key already stored) | `{"id": "<id>", "status": "duplicate"}` |
| 400 | Validation failed | `{"error": "validation", "fields": ["field names only"]}` |
| 401 | Missing or wrong secret | `{"error": "unauthorized"}` |
| 413 | Body too large | `{"error": "too_large"}` |
| 415 | Wrong content type | `{"error": "unsupported_media_type"}` |
| 429 | Rate limit exceeded | `{"error": "rate_limited"}` with `Retry-After` |
| 500 | Server error | `{"error": "internal"}`. Stack trace logged locally, never returned. |

Error bodies never echo the request content, to avoid reflecting sensitive data.

### 1.5 Idempotency
- WhatsApp: key is `message_id`. Duplicate returns `200 duplicate`.
- Auction: key is `auction_id` plus `notice_date`. Duplicate returns `200 duplicate`.
- The listener may resend on network failure, so every write must be idempotent.

### 1.6 Rate limiting
- 60 requests per minute per source, enforced by the webhook process. Behind the proxy, the source is the webhook secret holder, so the limit is global.
- Limit returns `429`. The listener backs off exponentially, up to 5 minutes.

### 1.7 Logging
- Log: method, path, status, latency, request ID. No body, no headers except the request ID.
- Never log `X-Webhook-Secret`, phone numbers, owner names or listing text.

## 2. Outbound integrations

Every outbound call has: a timeout (default 10 s, OCR 120 s), retries only where the operation is idempotent, a circuit breaker after 5 consecutive failures, and a failure path that alerts the owner without sensitive data.

| Integration | Purpose | Auth | Data sent | Retries | Notes |
|---|---|---|---|---|---|
| Gemini API (Google) | OCR and extraction from gazette pages | `GEMINI_API_KEY` header | One page image or text per request, no owner data | Up to 2, exponential backoff, only for 429 and 5xx | Results cached by PDF hash (`docs/TOKEN_OPTIMIZATION.md`). Output validated against schema. |
| Telegram Bot API | Owner alerts | `TELEGRAM_BOT_TOKEN` in URL path | Alert text only. No owner names, PAN, Aadhaar, or full phone numbers. Dashboard link. | Up to 3, for 5xx and timeouts | Single private chat (`TELEGRAM_CHAT_ID`). |
| Google Sheets API (gspread) | Optional log of WhatsApp listings | Service account JSON (`GOOGLE_SERVICE_ACCOUNT_JSON`, mode 600) | Listing fields without owner data and with masked phone | No automatic retry for writes; append-only with `message_id` check first | Read the sheet before append to avoid duplicates. |
| TNGIS (tngis.tn.gov.in) | Parcel boundaries | None or public | Survey and village codes only | Up to 2 for 5xx | Read-only. Only after terms are cleared (`docs/SOURCES.md`). |
| Gazette sites (egazette.gov.in) | Notice PDFs | None | None | Up to 2 for 5xx | Read-only. Manifest stores hash and date. Only after terms are cleared. |
| Map tiles | Map background | Per provider | Tile requests | Browser handles | Google Maps Platform key or OpenStreetMap with attribution. |

No integration receives owner data. This is a hard rule and is tested (`docs/TESTING.md` section 1, `test_privacy.py`).

## 3. Internal service interfaces (Python, not HTTP)
| Function | Module | Input | Output | Notes |
|---|---|---|---|---|
| `run_daily_sync()` | `services/daily_sync.py` | none | status object | Writes status file and audit lines |
| `parse_gazette(pdf_path)` | `engine/gazette_parser.py` | PDF path | list of `NoticeDot` | Validated; low confidence to review |
| `snap_dots(dots, alignment)` | `engine/dot_snapper.py` | dots, alignment | dots with `snap_distance_m` | Tolerance from settings |
| `filter_targets(parcels, dots, settings)` | `engine/target_filter.py` | parcels, dots, settings | `TargetParcel` list | Rules in `docs/RULES.md` |
| `get_owner(owner_id)` | `engine/patta_lookup.py` | owner ID | `OwnerDetails` | Only callable from the authenticated UI; writes audit line |

## 4. Environment variables
| Variable | Used by | Secret |
|---|---|---|
| `GEMINI_API_KEY` | Gemini calls | Yes |
| `GOOGLE_SHEET_NAME` | Sheets log | No |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Sheets log (path to file) | Yes (file) |
| `WEBHOOK_SECRET` | Webhook auth | Yes |
| `UI_PASSWORD` | Dashboard login | Yes |
| `OWNER_DB_KEY` | Owner field encryption | Yes |
| `TELEGRAM_BOT_TOKEN` | Alerts | Yes |
| `TELEGRAM_CHAT_ID` | Alerts | No |

Load from `.env` in the project root. Never print these values. Never place them in a URL, except the Telegram token, which the Telegram API requires in the path; never log that URL.

## 5. Pagination and filtering
Not needed for the webhook (write-only). Dashboard tables use in-memory paging of 50 rows and filters in the URL (`docs/DESIGN.md` section 6).

## 6. Versioning
- Paths are prefixed `/v1/`. A breaking change creates `/v2/`; `/v1/` keeps working until the listener is updated.

## 7. Failure handling summary
| Failure | Behaviour |
|---|---|
| Webhook down | Listener queues messages to disk (`whatsapp_deals.json` backlog) and retries |
| Gemini down | Page stays in queue; sync reports "OCR pending" and continues with cached results |
| Telegram down | Alert written to `storage/alerts_pending.jsonl`; retried next run |
| TNGIS down | Parcels not refreshed; last good copy used and marked stale |
| Owner DB locked | Request fails with `500`; owner sees "try again"; no partial write |
