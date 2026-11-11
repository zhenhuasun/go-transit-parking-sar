# Project Prompt (portable version)

---

I am a data scientist in the marketing department at Metrolinx, responsible for customer insight, fare strategy and ridership forecasting. I want to do a study: **use satellite radar data to reconstruct GO train station parking-lot usage for 2018–2026**, because GO only publishes parking capacity — no occupancy, no historical record, and no sensors in its outdoor lots.

**Core idea**

Use Sentinel-1 synthetic aperture radar (SAR) VV backscatter as a proxy for parking demand. The principle: smooth asphalt acts like a mirror, reflecting the radar pulse away, so an empty lot looks "dark"; car bodies are metal and form corner reflectors with the ground, bouncing the radar pulse back, so a full lot looks "bright". A lot's mean VV traced over time is a long-term demand trend line.

**Work completed**

1. **Pilot**: three stations — Oakville, Clarkson, Bronte — 6 outdoor lots in total. Each outdoor lot is a separate polygon; indoor parking structures are excluded entirely (SAR cannot see inside). I drew the polygons myself on satellite imagery; they are verified closed, with no self-intersections and no overlaps, at 27–32 m² per space, which is reasonable including internal aisles. Oakville Main 2,712 spaces, South 291; Clarkson Main 1,274, North 627 (GO official figure, corrected from Parkopedia's 1,020); Bronte Main 1,824, South 1,149. Clarkson North's polygon is 52 m²/space — its boundary needs re-checking.

2. **Quick signal check**: Microsoft Planetary Computer Sentinel-1 RTC data (γ⁰), 52 ascending scenes, comparing the summers of 2019, 2020 and 2024. All 6 lots fell 0.8–2.0 dB in summer 2020 vs 2019 (Oakville Main −1.56 dB, Clarkson North −2.00 dB), and by 2024, 5 of the 6 had recovered to within 0.3 dB of 2019. The signal is real, but dB cannot be converted into an occupancy percentage — there is no ground-truth calibration.

3. **Network inventory**: 71 train stations, 57 with free parking, 14 without; 69,338 spaces, of which 57,606 outdoor (83.1%) and 11,732 garage (16.9%), across 96 lots. Bloomington and Centennial are 100% garage, so VV cannot measure them; 18 lots are under 200 spaces, so their signal is weak.

**Key limits — these must go into any report**

- Sentinel-1 land imaging over Oakville is ascending-only, passing at 19:08–19:16 in summer and 18:08–18:16 in winter. It measures the **evening residual at the tail of the return peak**, not peak occupancy, and summer and winter cannot be compared directly.
- dB is a relative index: it can only describe trends, rankings and recovery (2019 = 100). It cannot directly say "occupancy is X%" or "we need to build N spaces".
- Outdoor only — garages are invisible; when bad weather pushes cars into a garage, outdoor VV falls, but total station demand may not have fallen.

**The business question I want to answer**

This is not retelling the ridership-recovery story with a different dataset. PRESTO tells me how much total ridership recovered; what I want to answer is what PRESTO cannot: **how did the people who drive to the station recover, and where does that diverge from total ridership?** That divergence decides whether budget goes to expanding parking or to feeder buses, which persistently idle lots can be developed, and which persistently saturated lots to review first. A parking structure costs CAD 40–47 million — the value of this judgement is in avoiding building the wrong thing.

**Next steps**

Please plan and execute in this order:

1. First build a **preliminary report** from the Microsoft data, extending the time range to all summers 2018–2026, with each lot's annual recovery index and charts, and three statements on the cover: "preliminary validation, γ⁰, evening residual index around 19:10".
2. Do **ground-truth calibration**: count cars on historical optical imagery or in the field on several known dates, and build a dB-to-vehicle-count conversion. No percentages can be reported without this step.
3. In parallel, learn the **SARpanel formal chain** (github.com/ryjayne89/sarpanel, pinned to version a1c17c1): trial run on summer 2019 first, then the full range, cross-validated against the Microsoft results. The formal project uses SARpanel as the main chain and Microsoft as the secondary chain; never mix the two chains' absolute dB values into one series.
4. Expand to **all GO stations with outdoor parking** (57 stations, 86 outdoor lots): generate drafts in one batch, review line by line, then produce the divergence table against PRESTO.
5. Finally, build the **business product**: parking index vs PRESTO ridership comparison, recovery rankings, and a one-page leadership brief that leads with the decision, not the method.

**Do not do**: do not expand to other Canadian cities for now, do not build a dashboard before calibration, do not state dB as occupancy.
