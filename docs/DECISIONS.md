# Owner decisions log

Source: PROJECT.md (17 Nov 2026), rounds 1–6. Record new decisions here with date.

## Round 1 (17 Nov 2026)
| # | Question | Decision |
|---|---|---|
| 2 | WhatsApp source | Keep WhatsApp via Baileys; add auction properties as second source. Ban risk accepted. |
| 3 | Users | Single user (owner only). Access control still required. |
| 5 | Route source | Official map is the base layer; notice dots snapped to it. SVD route guess removed. |
| 6 | Hosting | Personal server (Ubuntu LTS). |
| 7 | Target parcels | Survey numbers near the highway, only after official approval; show size and owner details. |

Interpretation to confirm: "circular land acquisition notice" read as the land-acquisition notice per parcel, shown as a dot.

## Round 2
- Auction source: bank e-auction properties.
- Server OS: Ubuntu LTS.
- Alert channel: Telegram bot.
- Official map fields: map name, survey no., village, village cross, road cross, local office circular.

## Round 3
- Highway size: from official documents (ROW per section).
- Margin: +20 ft on each side.
- Target area: both sides.
- Owner details: name, PAN (masked), Aadhaar (last 4 if available).

## Round 4
- Margin measured from road edge (ROW boundary), both sides. **Target zone rule locked.**

## Round 5
- Owner data source: no open API found. Manual entry from official portals, with source and date. Automated connector later, only if access is granted.

## Round 6
- Georeferencing tool: QGIS.
- OCR: Gemini kept only if it beats Tesseract (Tamil) on a labelled sample.
- Bank auction notices found for Erode and Bhavani area (status to verify).

## Open decisions (see OPEN_QUESTIONS.md)
- Official map files.
- Approval stage confirmation (3D).
- Owner data storage: one store or two.
