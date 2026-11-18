# Data model

All models are Pydantic. Validate every write.

## NoticeDot
| Field | Type | Notes |
|---|---|---|
| `dot_id` | str | Generated |
| `district`, `taluk`, `village` | str | |
| `survey_no` | str | Include sub-division where printed |
| `stage` | str | `3A`, `3C`, `3D`, `3E`, `3G`, `3H` |
| `gazette_id` | str | From egazette or TN gazette |
| `gazette_date` | date | |
| `source_pdf`, `source_page` | str, int | |
| `coords` | [lon, lat] | Centroid, then snapped |
| `snap_distance_m` | float | Distance to alignment |
| `confidence` | float 0–1 | From OCR |
| `status` | enum | `mapped`, `review` |

## SurveyParcel
`parcel_id`, `district`, `taluk`, `village`, `survey_no`, `polygon` (GeoJSON), `area_sqft`, `area_cents`, `source` (TNGIS or manual), `retrieved_on`.

## PattaRecord (non-sensitive)
`district`, `taluk`, `village`, `survey_no`, `patta_no`, `land_type`, `source`, `verified_on`.

## OwnerDetails (encrypted store, owner panel only)
| Field | Stored as | Notes |
|---|---|---|
| `owner_name` | full name | Required |
| `pan_masked` | e.g. `ABCDE****F` | Full PAN never stored or shown |
| `aadhaar_last4` | 4 digits | Only if the owner's document shows them |
| `owner_source` | document name and date | Mandatory |
| `verified_on` | date | Owner details go stale |

Subject to legal review (`docs/SECURITY_AND_LEGAL.md`).

## TargetParcel
`parcel_id`, `survey_no`, `village`, `taluk`, `district`, `stage`, `gazette_date`, `source_pdf`, `area_sqft`, `area_cents`, `dist_to_alignment_m`, `dist_to_row_edge_m`, `dist_to_zone_edge_m`, `side` (`left`/`right`), `row_width_m`, `margin_m` (6.096), `owner_ref` (not the owner name), `updated_on`.

## OfficialMapEntry
As in PROJECT.md section 13.1: `map_id`, `map_name`, `map_file`, `district`, `taluk`, `village`, `survey_no`, `village_cross` (point), `road_cross` (point, road name), `chainage_km`, `circular_no`, `circular_date`, `circular_office`, `circular_pdf`, `georef_points`.

## AuctionProperty
`auction_id`, `bank_name`, `property_address`, `survey_no`, `village`, `reserve_price_inr`, `emd_inr`, `auction_date`, `status` (`active`/`expired`/`sold`), `notice_pdf`, `notice_date`, `source_url`, `matched_parcel_id` (nullable), `borrower_name` (only if matched).

## PropertyPin (WhatsApp and portal listings)
`title`, `price_inr`, `plot_size`, `village`, `survey_ref`, `contact_phone` (masked in alerts), `source`, `url`, `distance_to_highway_m`, `received_on`.

## MapState (UI)
Layer toggles: `show_alignment`, `show_dots`, `show_targets`, `show_pending`, `show_auctions`, `show_contacts`, `show_scores`. Buffers from settings.

## Keys
- Notice dot: `(district, taluk, village, survey_no, gazette_id)`.
- Idempotent upsert on these keys.
