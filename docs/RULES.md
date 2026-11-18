# Business rules

## 1. Target parcel
A parcel is a **target** only when all are true:
1. **Approval reached.** Notice stage ≥ `approval_stage` in `config/settings.yaml` (default **3D**, final declaration). Earlier notices (3A) show as **pending**, never as targets.
2. **Inside target zone, either side.** Parcel touches or lies within the zone on the left or right of the official alignment.
3. **Survey number matched.** Survey number maps to a TNGIS polygon (or the approved manual GeoJSON fallback).

## 2. Target zone
- `row_width_m`: highway right-of-way width, read from the gazette or official map for each section. Never guessed.
- Margin: **20 ft = 6.096 m**, added outward from the road edge on each side.
- Zone on each side of the centreline = `row_width_m / 2 + 6.096 m`.

Worked example: ROW 45 m → half-width 22.5 m → zone 28.6 m each side → total band about 57.2 m.

Confirmed in owner rounds 3 and 4. The road edge is the ROW boundary read from documents. If the owner later means the paved carriageway edge, the zone narrows; this needs a new decision.

```yaml
target_zone:
  row_width_m: <per section, from document>
  margin_ft: 20
  margin_m: 6.096          # derived: margin_ft x 0.3048
  sides: both
  approval_stage: 3D
```

## 3. Stages
- Stages recorded: 3A, 3C, 3D, 3E, 3G, 3H (National Highways Act, 1956; see `docs/SOURCES.md`).
- **15(2)** appears in earlier drafts but is not confirmed as an NH Act stage. Do not show it in UI text until verified (see `docs/OPEN_QUESTIONS.md`).
- Stage labels must match the governing law before they appear in the UI.

## 4. Notice dot rules
- A notice dot is the survey number's centroid from the cadastral polygon, snapped to the alignment.
- Snap distance is recorded. Distance beyond tolerance goes to the **review queue**, not the map.
- A dot that cannot be matched to a parcel goes to the review queue.
- Every dot keeps its source PDF, page, and gazette date.

## 5. Official map and circulars
- Each `OfficialMapEntry` keeps map name, survey number, village, village cross, road cross, chainage (if printed), circular number and date, issuing office, and control points.
- A survey number on the map links to its circular. Missing circular shows **"circular pending"**.
- Georeferencing is a manual, one-time step per sheet. Record control points used.

## 6. Auction rule
- An auction becomes a map pin only when its survey number matches a parcel in the target zone.
- Auction status: active, expired, or sold. Check the sale date. Old notices are not active.
- Borrower names are stored only for properties that match a target.

## 7. Owner data rule
- Owner details require a source (document name and date) and a verified date. No source, no owner record.
- Owner details are entered manually from documents the owner holds. No automated lookup (see `docs/OPEN_QUESTIONS.md`).
- Owner details never leave the owner panel.

## 8. Review queue
Items go to review when: OCR confidence is low; a dot is beyond snap tolerance; a dot has no parcel match; a circular is pending; a record has no source.

## 9. Scoring
- Scores are research aids, not advice. Show "not advice" on every score.
- Stage certainty weights (for example 3A = 65%, 3D = 92%, 3G = 98%) are **assumptions** from an earlier draft. Keep them in config, label them as assumptions in the UI, and do not present them as statutory facts.
