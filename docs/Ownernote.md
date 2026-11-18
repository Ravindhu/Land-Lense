building your own script to collect survey numbers for a defined region:
1. Use TNREGINET Guideline Value rather than TN e-Services, because it lists all survey numbers per village without requiring a mobile OTP for every lookup.
2. Add polite delays (2–5 seconds between requests) and cache responses locally so you never query the same village twice.
3. Store hierarchically using the structure: District -> Taluk / SRO -> Revenue Village -> Survey Number -> Subdivision.
If you'd like help setting this up, let me know

Here is a step-by-step operating manual you can hand directly to your local agent or surveyor, complete with the exact official portals and instructions for each stage.

Step 1: Download the Section 3A / 3D Gazette Notifications

Goal: Collect the official legal lists containing every survey number being acquired in your target villages.
• Where to go:
	• Bhoomi Rashi Portal – Highway Land Register (Search by State: Tamil Nadu, District, and Project/NH Number to view published 3A and 3D notifications).
	• e-Gazette of India (Use Search Gazette → Select Extraordinary → Search by the NH number, taluk name, or notification number if you already have the S.O. number).
• What your agent must do:
	1. Check if Section 3D is published for your target taluk and villages (Section 3D is the final, locked list; use Section 3A only if 3D is still pending).
	2. Download all pages of the PDF notification for the relevant villages. Note that these gazettes often have dozens of pages of tables listing Taluk, Village, Survey Number, Type of Land (Government/Private), Nature of Land (Wet/Dry/House Site), and Area in Hectares/Sq. Meters.

Step 2: Structure the Survey Numbers Using AI

Goal: Turn raw, multi-page Gazette PDF tables into a clean, searchable Excel/CSV list.
• What your agent must do:
	1. Upload the downloaded 3A or 3D Gazette PDF directly into this AI chat (or split into 15–20 page batches if the file is very large).
	2. Prompt the AI: "Extract all rows for [Village Name] into a downloadable CSV/Excel table with columns: Village, Survey Number, Sub-Division, Land Type, Nature of Land, and Acquired Area (Sq.m)."
	3. Repeat for adjacent villages along the corridor so you have a master spreadsheet of every affected plot in sequence.

Step 3: Plot the Survey Numbers on the Village Cadastral Map

Goal: Visually trace the exact highway footprint, width, and bends across the village to identify which unacquired survey numbers sit right beside the road.
• Where to go:
	• Tamil Nadu GIS (TNGIS) Portal (Provides interactive cadastral/survey number layers overlaid on satellite imagery for Tamil Nadu villages).
	• Tamil Nilam e-Services (Use View FMB Sketch and View Patta / Chitta to pull individual boundary drawings and check if sub-divisions have been updated).
• What your agent must do:
	1. Open the target village on TNGIS or obtain the Village Composite Cadastral Map (available at the Village Administrative Officer / Taluk Survey office).
	2. Highlight every survey number from your Step 2 Excel sheet on the village map.
	3. Identify Target Plots: Once highlighted, you will clearly see the ribbon of acquired land cutting through the village. Note down the unacquired survey numbers touching the outer edges of that ribbon—and check on Tamil Nilam e-Services whether their Patta/FMB already shows a sub-division (e.g., 145/1A vs 145/1B).

Step 4: Cross-Check with Tender Schedules (Access & Elevation Filter)

Goal: Filter out "bad" adjacent plots (like those blocked by high flyover walls) and pick "high-value" plots (those touching ground-level service roads and underpasses).
• Where to go:
	• NHAI Procurement / Tender Portal (Or the tender page you already opened—specifically the Technical Schedules and DCSL STR SVUP CH PDFs).
• What your agent must do:
	1. Open Technical Schedules and check Schedule-A (Annexure-I & II) to match your village boundary with its exact km chainage (for example, Km 18+200 to Km 21+400).
	2. Check the Service Road Table in Schedule-A: Confirm whether a Service Road is planned on the Left Hand Side (LHS) or Right Hand Side (RHS) at your target survey number's chainage. Rule: Only buy plots with planned service road frontage.
	3. Check the VUP / SVUP / Flyover Table (and cross-verify with DCSL STR SVUP CH):
		• Best Spots: Plots within 200–500 meters of a Vehicular Underpass (VUP), Small Vehicular Underpass (SVUP), or major cross-road intersection where local traffic enters and exits the highway.
		• Spots to Avoid: Plots directly alongside elevated Flyover Retaining Walls (RE Walls) or deep cuttings where road visibility and access are cut off.
	4. Final Ground Check: Take the printed FMB sketch and Technical Schedule extract to the site with a private licensed surveyor to confirm that the physical NHAI boundary stones match your target plot's remaining unacquired area before paying an advance.
If you upload your Gazette PDF or Technical Schedules PDF here, I can run Step 2 and Step 4 right now and build the target survey number spreadsheet for your agent.
