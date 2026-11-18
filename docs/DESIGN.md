# Design (DESIGN.md)

Source of truth for the visual design and UX of the owner dashboard. Read `docs/PRD.md` first. This is a single-user, read-mostly tool. It must be clear, calm and trustworthy, not promotional.

## 1. Design principles
1. **Source first.** Every fact shows where it came from and when. A number without a source is not shown as fact.
2. **Official line is the spine.** The official alignment is the strongest visual element. Everything else is measured from it.
3. **Make status obvious.** Pending, target, review, and expired must look different at a glance and never by colour alone.
4. **Privacy by default.** Owner details are hidden until the owner panel is opened. Nothing sensitive appears on the map layer.
5. **Plain language.** Use the terms in `docs/RULES.md`. Avoid marketing words and investment hype.

## 2. Visual direction
- Restrained, utilitarian, dense enough for a map-and-table tool. No decorative gradients, illustrations or stock imagery.
- Light theme by default; dark theme optional and must keep the same meaning for every status colour.
- Map is the main surface; a right-hand panel holds details; a top bar holds filters and status.

## 3. Colour
Define colours as tokens. Do not use raw hex in components.

| Token | Use | Note |
|---|---|---|
| `--color-alignment` | Official highway line | Strongest stroke on the map |
| `--color-zone` | Target zone band | Low-opacity fill with dashed edge |
| `--color-target` | Target parcel | Solid outline plus label |
| `--color-pending` | Stage 3A (pending) | Dashed outline, not a target |
| `--color-review` | Review queue items | Warning icon, never red alone |
| `--color-expired` | Expired auction | Grey with strike-through date |
| `--color-text` | Body text | Meets WCAG AA on background |
| `--color-muted` | Source and date text | Still meets AA |

Every status also has a **shape or label**, so colour is not the only cue. Colour-blind check is required before release.

## 4. Typography
- One sans-serif family for UI and one monospace for survey numbers and IDs (survey numbers must line up).
- Base size 16 px for body; 14 px minimum for source and date lines.
- Tamil script must render. Check the chosen font covers Tamil glyphs before release.

## 5. Spacing and layout
- 8 px spacing scale: 4, 8, 16, 24, 32.
- Desktop: map (fills the viewport), right panel 360 px, top bar 56 px.
- Tablet: panel becomes a bottom sheet.
- Phone: read-only view. Map and target list only. Owner panel is desktop-only.

## 6. Reusable components
| Component | Shows | Rules |
|---|---|---|
| `SourceLine` | Source file, page, gazette date | Appears on every record card and layer legend |
| `StatusBadge` | Pending / Target / Review / Expired | Text plus icon plus colour |
| `TargetCard` | Survey no., village, taluk, district, size (sq ft and cents), stage, distances, side | No owner data |
| `OwnerPanel` | Owner name, masked PAN, Aadhaar last 4, owner source, verified date | Behind login and re-auth on open; audited |
| `ZoneNote` | ROW width, margin (20 ft = 6.096 m), side | Shown on every target |
| `NotAdviceNote` | "Research aid, not advice" | On every layer legend and every score |
| `ReviewQueueRow` | Reason (low OCR, far from line, no match, circular pending) | Action links to the source PDF |
| `FilterBar` | Stage, status, distance, village | Persists in the URL, not browser storage |

## 7. Navigation and forms
- Single screen with map, panel and filters. No deep navigation.
- Tabs in the panel: Targets, Pending, Review, Auctions, Contacts.
- Owner entry is a form in the owner panel. Required fields are marked. Masked PAN is shown as typed in masked form only; full PAN input is rejected by validation.
- Save is explicit. Show "saved" with time, and write the audit entry.

## 8. Loading, empty and error states
| State | Behaviour |
|---|---|
| Loading map | Show the alignment as a skeleton line with "Loading official alignment" text |
| No targets yet | "No targets yet. Targets appear after a notice reaches stage 3D and falls inside the zone." |
| No official map loaded | "Official alignment not loaded for this section. No dots are shown until it is." |
| Sync failed | Banner with last successful sync time and link to the status file |
| Source missing | Record shows "Source missing. Not shown as fact." and is moved to review |
| Auth expired | Redirect to login; keep the current filter in the URL |

## 9. Interactions and motion
- No animation required. If used, keep under 200 ms and respect reduced-motion settings.
- Click a parcel: highlight it, open its TargetCard.
- Hover shows the survey number only. Full details need a click (avoids accidental reads).

## 10. Responsive behaviour
- Breakpoints: 1024 px (desktop), 768 px (tablet), below 768 px (phone, read-only).
- No horizontal scroll on any screen. Survey numbers wrap at slashes.

## 11. Accessibility
- WCAG 2.2 AA contrast for all text and status colours.
- Keyboard: every panel action reachable by Tab; map has keyboard pan and zoom; a list view of targets offers the same content as the map.
- Screen readers: map has a text summary ("12 targets, 3 pending, 2 in review").
- Focus ring visible on every interactive element.
- Tamil and English labels for the main controls.

## 12. Page-level layout guidance
- **Main page:** top bar (filters, last sync, "Research aid, not advice"), map, right panel with tabs.
- **Owner panel:** opens over the right panel after re-authentication. Shows audit note: "Viewed by owner at <time>".
- **Review queue:** table with reason, source link, and resolve action.
- **Status page:** last sync, counts, failed steps, backup status.

## 13. Out of scope for design
- Public or shared views.
- Marketing pages, login branding, illustrations.
- Charts beyond simple counts unless the owner asks.
