# Open questions

| # | Question | Why it matters | Blocks |
|---|---|---|---|
| 1 | Can the owner share official highway map PDFs or images for each section? Georeferencing needs at least 3 known points per map. | No alignment, no map. | Phase 1 |
| 2 | Is final declaration (3D) the stage meant by "official approval"? | Sets the target rule. | Phase 3 |
| 3 | Is "circular land acquisition notice" the per-parcel acquisition notice? | Defines notice dots. | Phase 2 |
| 4 | Should the target margin run from the ROW boundary (current) or the paved carriageway edge? | Changes zone width. | Phase 3 |
| 5 | What is the stage "15(2)"? Is it an NH Act stage, or from another law? | Appears in earlier drafts; not confirmed. | Phase 3 UI |
| 6 | Owner data: one encrypted store (`owners.db`) or also in `patta_registry.json`? | Avoids duplicate sensitive data. | Phase 4 |
| 7 | Lawyer review of PAN and Aadhaar storage. | Legal limits. | Phase 4 |
| 8 | Which DPDP provisions are in force, and does the personal-use exemption cover this tool? | Legal risk. | Phase 4 |
| 9 | Snapping tolerance (metres). | Needs real data. | Phase 2 |
| 10 | Which stage certainty weights to use, if any? Earlier weights are unsourced. | Scores are assumptions. | Phase 3 |
| 11 | Terms of use for TNGIS, CLIP, TNREGINET, eservices, and each bank auction site. | Collector legality. | Phases 1, 5 |
| 12 | Alert chat setup for Telegram (chat ID, bot). | Alerts. | Phase 7 |
| 13 | Is Gemini still the chosen OCR, and at which model? | Model names change. | Phase 2 |
| 14 | Map tiles: Google Maps Platform or OpenStreetMap / satellite? | Terms and cost. | Phase 4 |
| 15 | Which document gives the ROW width for each section? | ROW is required for zone. | Phase 3 |

## Resolved (from PROJECT.md)
- Official map is the route source (round 1).
- Margin is 20 ft from road edge, both sides (round 4).
- Owner data is manual entry from official portals (round 5).
- Auction source is bank e-auctions (round 2).
