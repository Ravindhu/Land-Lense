# Sources

Status key: **Verified** = checked in web search (Nov 2026). **Check** = not yet verified; confirm before use. **Terms: open** = read the site's terms before building a collector.

## Law
| Source | What | Status |
|---|---|---|
| National Highways Act, 1956 (Act 48 of 1956) | Acquisition stages 3A–3H | Verified in court judgments and Supreme Court case (Civil Appeal 7064/2019). Full text on LegitQuest is an unofficial mirror; check against official text. |
| Right to Fair Compensation and Transparency in Land Acquisition Act, 2013 (RFCTLARR) | Compensation rules that interact with NH Act | Referenced in judgments. Check. |
| Digital Personal Data Protection Act, 2023 (No. 22 of 2023) | Data protection | Official text: indiacode.nic.in (PDF). Verified. Commencement by notification: check current status. |
| DPDP Rules, 2025 | Implementing rules | Named by NeGD; not opened. Check. |
| Aadhaar Act, 2016 | Limits on storing full Aadhaar | Check against UIDAI text. |
| Land Acquisition Act, 1894 (s. 15) | Source of "15(2)"? | Check. Do not use "15(2)" as an NH stage until verified. |

## Gazettes
| Source | Use | Status | Terms |
|---|---|---|---|
| egazette.gov.in (Gazette of India, Part II Sec 3(ii)) | Central 3A, 3D, corrigenda | Verified (MoRTH notices with Gazette IDs and PDF links) | Open |
| Gazette of India (MoRTH) recent uploads, Category 6 | Listing for collector | Verified listing pages exist | Open |
| TN Government Gazette (stationeryprinting.tn.gov.in) | TN notices, Highways G.O.s | Check (cited in earlier draft) | Open. Indian IP may be needed. |

## Survey and cadastral
| Source | Use | Status | Terms |
|---|---|---|---|
| TNGIS (tngis.tn.gov.in) | Parcel boundaries, GI Viewer | Verified (site live; support: tngis.support@tn.gov.in). Official viewer is a GI Viewer app. | Open. Read before any automated access. |
| TNGIS generic viewer (tngis.tn.gov.in/generic_viewer) | Road width and access checks | Named by a third-party guide. Check on official site. | Open |
| Tamil Nilam (NIC software) | Rural land records (FMB, A-Register, Chitta) | Verified via TN Land Survey policy note 2016 | Government use; do not scrape |
| FMB sketches via TNGIS eServices | Field measurement books | Named by third parties only. Check on official portal. | Open |
| TN Land Survey department (tnlandsurvey.tn.gov.in) | Department of Survey and Settlement, policy notes | Verified | Check |

## Registration and land records (owner data)
| Source | Use | Status | Terms |
|---|---|---|---|
| TNREGINET (tnreginet.gov.in) | Encumbrance certificate, guideline value | Named in PROJECT.md section 16. Requires login. | Open. Manual use only. |
| CLIP (clip.tn.gov.in) | Patta, Chitta, TSLR, FMB | Named in PROJECT.md section 16 | Open. Manual use only. |
| eservices.tn.gov.in | Survey and settlement eServices | Named in PROJECT.md section 16 | Open |
| Third-party apps (verified.realestate, LandLens) | Not used as an owner source | Excluded by owner decision (PROJECT.md 16) | N/A |

For a machine-readable owner source, write to the Department of Survey and Settlement or NIC Tamil Nadu requesting data access for personal, non-commercial use (PROJECT.md section 16, item 4).

## Auctions
| Source | Use | Status | Terms |
|---|---|---|---|
| Bank e-auction notices (Cholamandalam, Equitas, SBI, SIDBI, TIIC, Karur Vysya) | Secured property auctions | Found by search (PROJECT.md 17.2). Most notices old. Check each. | Open per site |
| bankeauctions.com | Named by Equitas notice | Check | Open |

## WhatsApp
| Source | Use | Status | Terms |
|---|---|---|---|
| Baileys (WhiskeySockets/Baileys; npm `baileys`) | Read-only listener | Verified. Unofficial; its own notices say it may breach WhatsApp terms and lead to a ban. Owner accepted risk. | Risk log in SECURITY_AND_LEGAL.md |
| WhatsApp Business / Cloud API | Official alternative (not used) | Verified as an option; does not cover reading arbitrary group chats | Check Meta's current terms |

## Maps
| Source | Use | Status | Terms |
|---|---|---|---|
| Google Maps Platform | Satellite tiles, if used | Not checked | Check. Needs key. |
| OpenStreetMap / satellite tile providers | Alternative tiles | Not checked | Check; attribution required |

## Software and models
| Source | Use | Status |
|---|---|---|
| Gemini API (Google) | OCR and extraction | Check current model name and pricing before use (earlier draft named gemini-2.5-flash) |
| Tesseract (Tamil data) | OCR alternative | Check |
| QGIS | Georeferencing | Check version |

## Rules for adding a source
1. Record the owner, URL, what it provides, the terms, and the date checked.
2. Mark it Verified only after you open it.
3. Build a collector only after terms are Open-cleared by the owner.
