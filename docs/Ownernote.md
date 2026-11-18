building your own script to collect survey numbers for a defined region:
1. Use TNREGINET Guideline Value rather than TN e-Services, because it lists all survey numbers per village without requiring a mobile OTP for every lookup.
2. Add polite delays (2–5 seconds between requests) and cache responses locally so you never query the same village twice.
3. Store hierarchically using the structure: District -> Taluk / SRO -> Revenue Village -> Survey Number -> Subdivision.
If you'd like help setting this up, let me know