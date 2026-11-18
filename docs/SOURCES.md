# Sources

Last updated: 18 Nov 2026.

Status key:
- **Verified** = the page was opened and its content checked.
- **Search only** = seen in a search result or a third-party summary, not opened. Do not rely on it.
- **Check** = not yet confirmed. Confirm before use.
- **Terms: open** = read the site's terms before building any automated collector.

Reference repo: `Ravindhu/Land-Lense` (PROJECT.md, design only, no code). Its source list is in section 3 of this file, and its decisions are in PROJECT.md sections 1, 13 to 17.

---

## 1. Highway land-acquisition data (the core source)

This is the official pipeline behind the 3A, 3D and award notices.

| Source | Operator | What it provides | Verified | Access and terms |
|---|---|---|---|---|
| **Bhoomi Rashi** (bhoomirashi.gov.in) | MoRTH; designed by NIC. Used by NHAI, NHIDCL and State PWDs. Live since 1 Apr 2018. | Digital land acquisition workflow for National Highways. Public pages: Highway Land Register [Rule 4(1)], Gazette Notification Report, Project search, LA Target Monitoring document, "What's New" (includes 3A notifications for NH projects not yet sanctioned). Headline stats: 3,803 online projects, 153,424 Ha with 3D done. | **Verified** (home page opened). Per-district notice lists and per-project 3A/3D status not confirmed. | Public pages open. Login form exists but the site banner says it is under maintenance and login is not advised. No CSV or API export; only PDFs. Terms: **Check**. Contact: supportla-morth@gov.in, +011-23711824. |
| Bhoomi Rashi Gazette Notification Report and Project search | MoRTH / NIC | Likely the per-notice list the project needs | **Check** (linked from home page, not opened) | Terms: Check |
| MoRTH land-acquisition page (morth.gov.in/land-acquisition) | MoRTH | Policy and portal links | **Check** (fetch returned metadata only, no body) | Open in a browser |
| Central Gazette (egazette.gov.in, Gazette of India Part II Sec 3(ii)) | Government of India | Official 3A, 3D and corrigendum notices as PDFs with Gazette IDs | **Verified** (search showed MoRTH notices as PDFs) | Terms: Open. Read before automated collection. |
| TN Government Gazette, Extraordinary Ex VI 1 series (stationeryprinting.tn.gov.in/extraordinary/YYYY/NNN_Ex_VI_1_YYYY.pdf) | Government of Tamil Nadu | Land acquisition notices for state highways (TN Highways Act 2001, s. 15(1)) and industrial or rail land (TN Act 10 of 1999, s. 3(1)). Each issue is numbered. | **Verified** (Ex VI 1 issues 36, 57, 128, 202 and 295 of 2026 opened and read) | Terms: Open. Indian IP may be needed. Read before automated collection. |
| TN Government Gazette, other series (Ex II 2, for example 132 of 2026) | Government of Tamil Nadu | Other extraordinary notices. Not reviewed. | **Check** | Terms: Open |
| Gati Shakti / NH network data | Gati Shakti Vishwavidyalaya, Digital India | National infrastructure master plan and maps. A 2025 budget item said selected data maps would be shared with the private sector. | **Search only** | Check whether the Tamil Nadu NH alignment is available. Check terms. |

**What this means for the project:**
1. Notices (3A, 3D, awards) come from the central gazette PDFs. TN state-highway notices come from the Ex VI 1 series. Both regimes are needed (see section 4).
2. The official alignment (the map) is still required. Bhoomi Rashi and the gazette schedules may contain it, but this is not yet verified. Owner must supply the sheets (PROJECT.md section 11, item 1).
3. Bhoomi Rashi offers no public data export, so the collector should follow the gazette listing, not scrape Bhoomi Rashi.

---

## 2. Survey, cadastral and GI viewer data (Tamil Nadu)

| Source | Operator | What it provides | Verified | Access and terms |
|---|---|---|---|---|
| **TNGIS GI Viewer (Tamil Nilam GI Viewer)**, tngis.tn.gov.in/apps/gi_viewer/ | Tamil Nadu GIS / Tamil Nilam (NIC) | Parcel boundaries by survey or patta number; cadastral and satellite views; FMB and patta details; ownership details; thematic layers (boundaries, roads, amenities); services for guideline value, EC, FMB sketch, A-Register, patta copy, master plan | **Verified** (page opened) | **Registration required**, free. Per-user request limits: government officials up to 1,000 requests per 24 h. Public users far fewer (for example 25 per hour for some services, 500 per 24 h for land details). Exceeding a limit blocks that service for 2 to 24 h. No download or API documented. **Manual use only.** Automated collection would breach the fair-use limits. |
| TNGIS login (tngis.tn.gov.in/login.html) | TNGIS | Account for the GI viewer | **Search only** | Requires the owner's own account |
| TNGIS Generic Viewer | TNGIS | Road width and access checks | **Search only** (third-party guide) | Check on official site |
| Tamil Nilam (NIC) | NIC / Revenue | Rural land records (FMB, A-Register, Chitta) | Verified via TN Land Survey policy note (2016) | Government use. Do not scrape. |
| CLIP (clip.tn.gov.in) | Revenue and Survey | Patta, Chitta, TSLR, FMB | Named in PROJECT.md section 16 | Web portal. Manual use only. |
| TNREGINET (tnreginet.gov.in) | Registration Department | Encumbrance certificate, guideline value | Named in PROJECT.md section 16 | Requires login. Manual use only. |
| eservices.tn.gov.in | Survey and Settlement | Land record eServices | Named in PROJECT.md section 16 | Manual use only |
| TN Land Survey (tnlandsurvey.tn.gov.in) | Department of Survey and Settlement | Policy notes, department contacts | Verified (policy note) | Check |
| Open geospatial data from TN government (OSM wiki list) | TN MAWS (municipal) | Only five municipal utility and landmark datasets on data.gov.in (Tambaram, Sivaganga, Tiruchirappalli, Pudukottai). No highway or cadastral data. | **Verified** (wiki page opened) | Format and licence not stated on listing. **Not useful** for the corridor. |

**Owner decision and rule:** Only the TNGIS GI viewer is verified as a parcel source, and only for manual lookups. The project can record the survey numbers and results the owner finds by hand (with source and date, PROJECT.md 14.1). A formal written request for data access to the Department of Survey and Settlement or NIC Tamil Nadu is the only route to automation (PROJECT.md section 16, item 4). The `tngis_cadastral` collector stays disabled until that permission is in writing.

**Open cadastral data:** none found for Tamil Nadu. The parcel sites that appeared in search (mypatta.in, landeed.com, 1acre.in, verified.realestate) are private aggregators with unclear data sources and terms. **Excluded** (PROJECT.md section 16).

---

## 3. Road network and map data (open, statewide)

| Source | What it provides | Verified | Access and terms |
|---|---|---|---|
| **OpenStreetMap** (openstreetmap.org), via Overpass Turbo (overpass-turbo.eu) | Roads with `highway` and `ref` tags (NH, SH, district roads), administrative boundaries (state admin_level 4, district admin_level 5), some village boundaries | **Verified** (OSM wiki pages opened for TN datasets and NH network) | Free. **ODbL**: attribution and share-alike on derived databases. Coverage of TN state highways is incomplete. Check `ref` formats (for example `TN SH 79` vs `SH 79`). |
| **Geofabrik** (download.geofabrik.de/asia/india.html) | Daily OSM extracts for India, for clipping to Tamil Nadu in QGIS | **Check** (the page could not be opened from the working environment). Confirm whether a Tamil Nadu extract exists. | Free. ODbL. |
| **HOT Export Tool** (export.hotosm.org) | OSM export in shapefile, GeoJSON and other formats for a drawn area | **Search only** | Free. ODbL. |
| **NCOG / NHAI GIS map** (ncog.gov.in/NHAI/admin/gisModulePublicWeb) | NH map with Bharatmala corridors, NHAI and NHIDCL projects, in-principle approved NHs, toll plazas. A WMS service exists. | **Search only** (forum thread, not opened) | Login needed for some pages. Export to file not confirmed. Licence not stated. Thread notes the NHAI toll data may be out of date. |
| **Sentinel-2** (ESA Copernicus) | Free satellite imagery, 10 m resolution | **Search only** | Open licence. Too coarse for parcel work. |
| Google Maps Platform, Esri imagery | Satellite and map tiles | Not checked | Own terms. Key or account needed. |

---

## 4. Law

| Source | What | Status |
|---|---|---|
| National Highways Act, 1956 (Act 48 of 1956) | Acquisition stages 3A to 3H | Verified in court judgments and Supreme Court case (Civil Appeal 7064/2019). Full text on LegitQuest is an unofficial mirror; check against the official text. |
| Tamil Nadu Highways Act, 2001 (TN Act 34 of 2002), s. 15(1) | Acquisition for state highways. Notices are "notice of acquisition" or "initial" and "final" notices. | **Verified** through the gazette notices that cite it (Ex VI 1 issues 36, 57, 128, 202, 295 of 2026). Read the Act text before relying on stage names. |
| Tamil Nadu Acquisition of Land for Industrial Purposes Act, 1997 (TN Act 10 of 1999), s. 3(1) | Acquisition for industrial and rail purposes (for example SIPCOT, the Tindivanam–Nagari rail line) | **Verified** through the gazette notices. Not a highway regime. |
| Right to Fair Compensation and Transparency in Land Acquisition Act, 2013 (RFCTLARR) | Compensation rules that interact with the NH Act | Referenced in judgments. Check. |
| Digital Personal Data Protection Act, 2023 (No. 22 of 2023) | Data protection | Official text at indiacode.nic.in (PDF). Verified. Commencement status: check. |
| DPDP Rules, 2025 | Implementing rules | Named by NeGD. Not opened. Check. |
| Aadhaar Act, 2016 | Limits on storing the full Aadhaar number | Check against UIDAI text. |
| Land Acquisition Act, 1894 (s. 15) | Source of "15(2)"? | Check. Do not use "15(2)" as an NH stage until verified. |

---

## 5. Auctions

| Source | Use | Status | Terms |
|---|---|---|---|
| Bank e-auction notices (Cholamandalam, Equitas, SBI, SIDBI, TIIC, Karur Vysya) | Secured property auctions | Found by search (PROJECT.md 17.2). Most notices are old. Check each. | Open per site |
| bankeauctions.com | Named in an Equitas notice | Check | Open |

---

## 6. WhatsApp

| Source | Use | Status | Terms |
|---|---|---|---|
| Baileys (WhiskeySockets/Baileys; npm `baileys`) | Read-only listener | Verified. Unofficial. Its notices say it may breach WhatsApp terms and lead to a ban. Owner accepted the risk. Pinned to 6.7.24. | Risk log in SECURITY_AND_LEGAL.md |
| WhatsApp Business / Cloud API | Official alternative (not used) | Verified as an option. Does not cover reading arbitrary group chats. | Check Meta's current terms |

---

## 7. Projects and budgets (corridor)

| Source | What it provides | Status |
|---|---|---|
| Wikipedia pages for NH 544H, Erode Southern Ring Road, Erode Outer Ring Road | Route, length, sanction year and costs, with citations to The Hindu and gazettes | **Secondary.** Contradictions noted in HIGHWAY_PROJECT_REGISTER.md. Check the primary gazette before use. |
| TN Budget 2026-27 and Highways policy notes | Department-wise allocations | **Search only**. Corridor-level figures not found. |
| etenders.gov.in (NHAI tenders) | Tender notices for NH works | **Search only**. Aggregators show generic NHAI listings. No Erode, Bhavani or Perundurai entries found. |

---

## 8. Software and models

| Source | Use | Status |
|---|---|---|
| Gemini API (Google) | OCR and extraction | Check the current model name and pricing (earlier draft named gemini-2.5-flash) |
| Tesseract (Tamil data) | OCR alternative | Check |
| QGIS | Georeferencing and clipping | Check version |
| Overpass Turbo, osmium | OSM export and clipping | Verified as tools (usage only). |

---

## 9. Excluded sources (decided)

| Source | Reason |
|---|---|
| mypatta.in, landeed.com, 1acre.in, verified.realestate | Private aggregators; sources and terms unclear. Not used as owner or parcel source (PROJECT.md section 16). |
| data.gov.in municipal GIS datasets (Tambaram, Sivaganga, Tiruchirappalli, Pudukottai) | Municipal utilities and landmarks only. No corridor value. |

---

## 10. Rules for adding a source

1. Record the owner, URL, what it provides, the terms, and the date checked.
2. Mark it **Verified** only after opening it. Search results are **Search only**.
3. Build a collector only after terms are cleared in writing by the owner.
4. Automated access to a portal with request limits is not allowed. Use manual entry within the limits.
