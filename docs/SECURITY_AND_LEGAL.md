# Security, privacy and legal

**Not legal advice.** Confirm the points marked *lawyer review* with a lawyer before storing identifiers.

## 1. Data classes
| Class | Examples | Where stored | Shown where |
|---|---|---|---|
| Public-record land data | Survey no., village, stage, gazette | JSON / GeoJSON | Map |
| Owner data (sensitive) | Owner name, masked PAN, Aadhaar last 4 | Encrypted `owners.db` | Owner panel only |
| Borrower data | Auction borrower name | Only if matched to a target | Owner panel only |
| Contact data | Broker phone numbers | Masked in alerts | Owner panel |
| Logs | Audit trail | `audit_log.jsonl` | Owner only |

## 2. Hard rules
1. No owner names, PAN, Aadhaar, or phone numbers in Telegram alerts, Google Sheets, exports, or commits.
2. Full PAN and full Aadhaar are never stored. Masked PAN and last 4 Aadhaar only.
3. PAN and Aadhaar come only from documents the owner holds (for example a sale deed). No database or portal lookup.
4. Every view and edit of owner data is audited.
5. `.env`, `OWNER_DB_KEY`, and credential JSON are mode 600 and never committed.

## 3. Identifier law (lawyer review)
- **Aadhaar Act:** restricts storing and displaying the full 12-digit number. The design stores last 4 digits only. *Lawyer review.*
- **PAN:** confidential tax information. Store only from documents the owner gives. *Lawyer review.*
- **DPDP Act 2023:** applies to digital personal data in India. Its exemption for personal or domestic processing may cover private use, but may not cover shared or commercial use. Re-review if the tool is shared or used commercially. *Lawyer review.*
- Record purpose and source for each identifier. Keep only what the target feature needs. Delete when no longer needed.

## 4. Server security
- Webhook binds to `127.0.0.1:8001`. Public access through Caddy with HTTPS and a `WEBHOOK_SECRET` header check.
- Streamlit UI behind the same proxy with a password, or over a VPN (for example Tailscale). Not public.
- UFW: allow 22 from known IPs, 80, 443 only.
- Unattended security upgrades on Ubuntu LTS.
- Rotate `WEBHOOK_SECRET` and `UI_PASSWORD` on a schedule and after any suspected leak.

## 5. WhatsApp risk (accepted by owner)
- Baileys is unofficial. The account may be banned.
- Mitigations: secondary SIM; listener limited to chosen groups; low message volume; store only needed fields; keep an export of `whatsapp_deals.json`.
- Never send messages with the number. The listener only reads.
- Review this risk if the owner's use changes.

## 6. Source terms
Before any collector scrapes a site, record its terms in `docs/SOURCES.md`. Prefer official feeds or manual entry where terms are unclear. Do not use third-party aggregators as an owner source.

## 7. Investment use
Scores and flags are not advice. Show "not advice" on every layer. Show source and date on every record.

## 8. Incident steps
1. Stop the listener and the webhook (`systemctl stop tn-intel-webhook tn-intel-whatsapp`).
2. Rotate `WEBHOOK_SECRET`, `UI_PASSWORD`, `OWNER_DB_KEY`, and bot token.
3. Review `audit_log.jsonl` for the period.
4. Tell the owner and record the incident in `docs/DECISIONS.md`.
