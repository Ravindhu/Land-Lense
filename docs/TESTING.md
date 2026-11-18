# Testing

Run with `make test` (pytest). Every phase has tests before the next starts.

## 1. Unit tests
| Test file | Covers |
|---|---|
| `test_spatial_engine.py` | RoW band, zone width, side (left/right), distances in UTM 43N |
| `test_dot_snapper.py` | Snap to nearest point; tolerance flags to review |
| `test_target_filter.py` | Stage ≥ 3D; zone rule; survey match; 3A stays pending |
| `test_patta_lookup.py` | Area in sq ft and cents; no owner data in non-owner outputs |
| `test_gazette_parser.py` | Parsing saved sample PDFs; schema validation; low confidence to review |
| `test_idempotency.py` | Re-running sync creates no duplicates (key check) |
| `test_audit.py` | Every owner view and edit writes an audit line |
| `test_privacy.py` | Alerts, sheets and exports contain no owner name, PAN, Aadhaar, or phone |

## 2. Worked-example tests
- ROW 45 m → half-width 22.5 m → zone 28.6 m each side → band about 57.2 m (`docs/RULES.md` section 2).
- Stage 3A parcel inside zone → **pending**, not target.
- Stage 3D parcel outside zone → not target.

## 3. OCR accuracy test
- Label 30–50 gazette pages (Tamil and English). Keep the labels in `tests/data/labels/` (no owner data).
- Score each engine (Gemini vs Tesseract with Tamil data) on:
  - exact survey-number match
  - sub-division match
  - village name match
- Keep the higher-scoring engine. Gemini output is still checked against the source page before use.
- Record the scores in `docs/DECISIONS.md`.

## 4. Snapping tolerance test
- Start with a tolerance chosen by the owner. Review every dot beyond it.
- Record the tolerance chosen and the reason.

## 5. Manual checks before each release
- Map: alignment only; no guessed lines.
- Each target shows source, date, ROW, margin, and "not advice".
- Owner panel is behind login; alerts have no owner data.
- Restore test passed this month.
