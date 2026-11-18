# Highway project and land-acquisition register (Erode, Perundurai, Bhavani corridor)

Last updated: 18 Nov 2026. Companion to SOURCES.md. Status key: **Verified** = read in the primary document. **Secondary** = from Wikipedia or news, with citations to be checked. **Not found** = searched, nothing corridor-specific.

## 1. Corridor projects found

| # | Project | Route and length | Approval and status | Land acquisition | Budget | Status |
|---|---|---|---|---|---|---|
| P1 | NH 544H (Thoppur to Erode) | Start NH 44 near Thoppur; Mecheri, Mettur, Ammapettai, Bhavani; end NH 381A near Erode Central Bus Terminus; junction with NH 544 near Lakshmi Nagar, Erode. 94 km. | Declared NH on 6 Jun 2017 (Gazette of India, per Wikipedia). DPR "Four laning and Strengthening of NH544H" (MoRTH, cited). Thoppur to R.N. Pudur (85 km, 4 packages) sanctioned 2022 for two-lane upgrade (uncited). | No figures found. | Not found | **Secondary.** The Wikipedia page contradicts itself (four-lane in 2017, two-lane in 2022). Check the Gazette of India declaration and MoRTH sanction. |
| P2 | Erode Southern Ring Road | About 15 km semi-ring on Erode's southern suburbs, Kokkarayanpet to Nanjanapuram (Thindal, Perundurai Road). 30 m ROW. | Sanctioned by TN Government in 2006. Opened Feb 2021 in three phases. Maintained by Highways and Minor Ports Department. | About 180 acres, of which 120 acres private patta land (The Hindu, via Wikipedia). | Rs 85 crore, of which about Rs 30 crore for compensation (The Hindu). | **Secondary.** Core section is open. Extensions are at proposal or DPR stage (see P4). |
| P3 | NH 381A four-laning, Eastern Ring Road | About 13 km, Lakkapuram (Parisalthurai) to Veppadai via Kadachanallur. | Proposed as part of Bharatmala. | Not found | Not found | **Secondary, uncited.** |
| P4 | Erode extensions (Perundurai Road to Nasiyanur and Sathy Road, about 10 km; Thindal to Komarapalayam Road, about 15 km under Master Plan 2041) | Proposed | DPR for the west extension estimated at Rs 60 lakh (uncited) | Not found | Not found | **Secondary, uncited.** Low-confidence leads. |

## 2. Tamil Nadu gazette notices reviewed (land acquisition, Ex VI 1 series, 2026)

Source: stationeryprinting.tn.gov.in/extraordinary/2026/. Notices are issued under the **Tamil Nadu Highways Act, 2001, s. 15(1)** for state highways, or the **TN Acquisition of Land for Industrial Purposes Act, 1997, s. 3(1)** for industrial and rail land. They do **not** use the NH Act 3A/3D stages.

| Gazette | Date | Notices | Corridor relevance |
|---|---|---|---|
| 36 Ex VI 1 | 28 Jan 2026 | Thenpennai bridge (Kallakurichi); Korai bridge (Viluppuram); SH-6A Thanipadi road widening, Harur (Dharmapuri), 29 survey numbers with old to new mapping; Southern Railway 4th line, Ennore | None |
| 57 Ex VI 1 | 5 Feb 2026 | Chennai grade separator; Hosur Outer Ring Road (Krishnagiri) with errata | None |
| 128 Ex VI 1 | 27 Feb 2026 | Rasipuram bypass Phase-II (SH 79/SH 95), Ariyagoundampatti village, Namakkal district, 93,923 sq m, 71 entries, survey numbers listed. Cheyyar SIPCOT link road (Kancheepuram). | **Namakkal district is in scope.** The Rasipuram bypass is near the Tiruchengode and Namakkal part of the corridor, but not on the Erode to Bhavani line. Record as nearby. |
| 202 Ex VI 1 | 20 Mar 2026 | SH-6 Tiruvannamalai to Kallakurichi four-laning; Tindivanam to Nagari rail line | None |
| 295 Ex VI 1 | 25 Jun 2026 | SIPCOT notices (Thoothukudi, Ariyalur); Chennai ROB; Poonamallee grade separator; Avinashi to Mettupalayam four-laning (Coimbatore district, Km 34/0 to 38/2, 25 survey numbers); Ariyalur limestone mining | Coimbatore district is adjacent to the corridor, but the notice is not on it |

**Not yet checked:** Other 2026 Ex VI 1 issues (for example 12, 56, 213, 276, 287, 293), and the 2021 and 2023 issues. Any notice for Erode, Bhavani, Perundurai, Gobichettipalayam, Tiruchengode or Namakkal would appear in this series, so the collector should scan all issues.

## 3. Data format facts (from the notices, for the data model)

- Each notice lists survey numbers in the printed order, with sub-division numbers (for example 77/2B, 77/2C). Some notices give old to new mapping (for example 48/3A2 to 48/3A2B). The data model must store **old and new** survey numbers together.
- The same survey number can appear twice in one schedule (for example 77/2 and 131/3B). Keep each entry as a separate row.
- Notices give area in sq m (dry, wet, Manai, Natham), sometimes with ha. Row width is **not** stated in any TN gazette notice reviewed.
- Km ranges appear in some notices and not others.
- Dates in these notices: gazette date only. No hearing or possession dates.
- Plans are available for inspection at the Special District Revenue Officer (LA) Highways office and the Special Tahsildar (LA) Highways unit. Those offices are named in each notice and are the place to ask for the schedule and plan maps.

## 4. Not found

- **Budget allocation** for the corridor: no figure located. Likely places: TN Highways and Minor Ports Department policy note (assembly, annual) and the MoRTH or NHAI budget and Parliament answers. Still to search.
- **Corridor-specific NHAI tenders** (etenders.gov.in): searches returned generic NHAI tenders with no Erode, Bhavani or Perundurai entries.
- **Official alignment maps** for NH 544H or any corridor section: not found online.
- **Parliament answers** on Tamil Nadu land acquisition for these projects: the search returned other states and years only.

## 5. Connecting the dots: what can be done now and what is still missing

**Can be done now (with sources):**
1. Use OpenStreetMap (ODbL) for the existing NH 544H and NH 381A centrelines. This is the existing road, not the proposed alignment. It is enough to check route direction and junctions.
2. Use the NH 544H waypoints (Thoppur, Mecheri, Mettur, Ammapettai, Bhavani, Erode) as a coarse corridor boundary only. Mark it "secondary" in the UI.
3. Build the notice dot register from TN Ex VI 1 gazettes, using the old-to-new survey mapping, with Namakkal and Erode districts as in-scope.

**Still missing, to form the line:**
1. **Official schedule maps** for the NH 544H (and any state highway) sections. Owner must supply them, or they must be downloaded from the gazette or the Special DRO (LA) offices.
2. **Row width per section** from the gazette declaration or the notice schedule.
3. **Gazette of India notice** for the NH 544H declaration (6 Jun 2017) and the 2022 sanction, to confirm the lane count and chainage.
4. **Budget and approval records**: MoRTH sanction letter, TN policy note, and the award stage if any.

## 6. Design implication (important)

The project design (PROJECT.md section 6, and DATABASE.md) assumes NH Act stages (3A, 3D). Most gazette notices for TN roads, including Erode-area roads, use the **TN Highways Act 2001, s. 15(1)**. The app needs a regime field per project:
- `nh_act`: stages 3A, 3C, 3D, 3E, 3G, 3H (approval stage 3D).
- `tn_highways_act`: s. 15(1) notice (treated as the final notice for the approval rule). Owner decision needed on which stage counts as "approved" for state highways.
- `tn_industrial_act`: s. 3(1), for non-highway land (not a target).

Owner decision needed: confirm the approval stage for TN Highways Act projects.

## 7. Next steps

1. Owner confirms which project to start with (NH 544H, Erode Southern Ring Road, or both).
2. Search the TN Ex VI 1 issues not yet read for the corridor districts. Build the notice register.
3. Search the TN policy note and MoRTH budget for the corridor budget figures.
4. Owner supplies the official schedule maps for the chosen section.
