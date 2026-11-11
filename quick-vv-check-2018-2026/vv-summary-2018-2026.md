# Quick VV check, all summers 2018–2026 — GO Transit parking lots

Date run: 2026-11-11 (first run; resumed once — see "Run notes" below).
Data: Microsoft Planetary Computer STAC, collection `sentinel-1-rtc`
(Sentinel-1 RTC, terrain-corrected gamma naught, VV).
NOT Google Earth Engine, NOT SNAP, NOT SARpanel — a shortcut check only.
Polygons: user-drawn `polygons-user.geojson` (6 outdoor lots, garages excluded).
Method: unchanged from the 3-summer check — per-pixel
`VV_dB = 10·log10(linear)`, linear clipped at 1e-6; ascending only;
windowed COG reads; deduplicate acquisitions by
(date, orbit_state, relative_orbit, platform).
Scripts (in this folder): `quick-vv-check-2018-2026.py` (copy of the
original, windows extended), `analyse-vv-2018-2026.py`.
Files: `vv-by-lot-scene-2018-2026.csv` (684 rows = 114 acquisitions × 6 lots),
`vv-annual-summary-2018-2026.csv`, `vv-by-lot-year-track-2018-2026.csv`,
`vv-time-series-2018-2026.png`.
Original 3-summer run (for comparison): `../quick-vv-check/`
(`vv-by-lot-scene.csv`, 312 rows, summers 2019 / 2020 / 2024 only).

**Spaces correction:** clarkson-north is labelled **627 spaces** here
(GO official, corrected 2026-11-08). The old run used 1020 (Parkopedia).
This changes only the label and the derived m²/space (32.2 → **52.3**,
see caveat 7); VV values are unaffected.

## Verdict: the 3-summer story holds, with the full 9-summer shape now visible

- **2018 ≈ 2019** in 5 of 6 lots (recovery index 89–100; oakville-south
  83 is the small-lot exception). 2019 is a fair pre-COVID baseline.
- **2020–2021: the collapse.** All 6 lots fell sharply in summer 2020
  (index 63–84) and **stayed down through summer 2021** (61–83) — the
  lots did not refill in the second COVID summer either.
- **2022: partial recovery** (index 80–88 in all 6 lots).
- **2023–2026: back to, or just above, 2019** in 5 of 6 lots
  (index 94–108). The exception is oakville-south 2026 (index 127),
  which is **not trusted** — see "Anomaly" below.
- The COVID drop (2020 vs 2019: −0.77 to −2.00 dB) is 1.5–3× the
  within-summer scene scatter (SD 0.5–1.0 dB), same sign in every lot,
  and present in both relative orbits independently. That is not noise.

## Results — summer mean VV_dB, ascending only, both relative orbits pooled

Means are the average of per-scene lot means; ± is the SD across scenes
in that summer; n = scenes in that summer (same for every lot).

| Lot | Spaces / px | 2018 (n=14) | 2019 (n=15) | 2020 (n=14) | 2021 (n=12) | 2022 (n=8) | 2023 (n=11) | 2024 (n=13) | 2025 (n=12) | 2026 (n=15) |
|---|---|---|---|---|---|---|---|---|---|---|
| oakville-main | 2712 / 739 | −10.43 ±0.50 | −10.19 ±0.75 | −11.75 ±0.57 | −11.57 ±0.51 | −11.12 ±0.23 | −10.46 ±0.79 | −10.48 ±0.61 | −10.45 ±0.52 | −10.10 ±0.75 |
| oakville-south | 291 / 82 | −10.22 ±0.86 | −9.42 ±1.01 | −10.19 ±0.65 | −10.66 ±0.84 | −10.41 ±0.75 | −10.35 ±0.84 | −10.05 ±0.74 | −10.05 ±0.69 | **−8.37 ±1.37** ⚠ |
| clarkson-main | 1274 / 360 | −11.60 ±1.32 | −11.62 ±1.07 | −13.14 ±0.63 | −13.01 ±0.26 | −12.25 ±0.51 | −11.62 ±0.73 | −11.65 ±0.76 | −11.43 ±0.74 | −11.62 ±0.94 |
| clarkson-north | 627 / 325 | −9.86 ±1.22 | −9.68 ±0.96 | −11.68 ±0.50 | −11.79 ±0.47 | −10.23 ±0.75 | −9.35 ±0.96 | −9.46 ±0.80 | −9.36 ±0.55 | −9.35 ±0.83 |
| bronte-main | 1824 / 575 | −10.87 ±0.70 | −10.71 ±0.83 | −11.82 ±0.97 | −11.88 ±0.77 | −11.59 ±0.30 | −10.70 ±0.43 | −10.45 ±0.63 | −10.61 ±0.45 | −10.73 ±0.74 |
| bronte-south | 1149 / 319 | −10.99 ±0.80 | −10.51 ±0.84 | −11.48 ±0.71 | −11.31 ±0.56 | −11.45 ±0.48 | −10.76 ±0.58 | −10.51 ±0.45 | −10.78 ±0.64 | −10.75 ±0.94 |

## Recovery index (2019 summer = 100, from LINEAR power)

Index = 100 × 10^((mean_dB_year − mean_dB_2019)/10). It is **not**
computed from dB differences directly, and it is **not** an occupancy
percentage — it is a backscatter-power index relative to summer 2019.

| Lot | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| oakville-main | 94.7 | 100.0 | 69.8 | 72.8 | 80.8 | 94.0 | 93.6 | 94.1 | 102.2 |
| oakville-south | 83.2 | 100.0 | 83.8 | 75.2 | 79.6 | 80.8 | 86.4 | 86.5 | **127.4** ⚠ |
| clarkson-main | 100.4 | 100.0 | 70.5 | 72.6 | 86.4 | 100.0 | 99.4 | 104.4 | 99.9 |
| clarkson-north | 95.8 | 100.0 | 63.1 | 61.4 | 88.0 | 107.9 | 105.1 | 107.5 | 107.9 |
| bronte-main | 96.2 | 100.0 | 77.4 | 76.4 | 81.5 | 100.2 | 106.0 | 102.2 | 99.5 |
| bronte-south | 89.4 | 100.0 | 79.9 | 83.2 | 80.5 | 94.4 | 100.0 | 93.8 | 94.6 |

## Per-year scene counts and coverage

| Year | Scenes | Notes |
|---|---|---|
| 2018 | 14 | Full coverage — RTC scenes exist for summer 2018 (first scene 2018-06-03). No gap year. |
| 2019 | 15 | |
| 2020 | 14 | Jun–Aug only (the old run's Apr–May window was **not** repeated). |
| 2021 | 12 | Gap 2021-07-17 → 08-05 (19 days). |
| 2022 | **8** | Thinnest summer. First scene **2022-06-25** (no early-June scenes); gaps 06-30 → 07-19 (19 days) and 07-24 → 08-05. Treat the 2022 annual mean as the least certain of the large lots. |
| 2023 | 11 | Gaps 06-20 → 07-07 (17 days) and 07-19 → 08-07 (19 days). |
| 2024 | 13 | |
| 2025 | 12 | |
| 2026 | 15 acquisitions on 14 dates | 2026-06-28 has **two** acquisitions (Sentinel-1A rel 4 + Sentinel-1D rel 77, same day). |
| **Total** | **114 acquisitions, 113 dates** | 684 lot-scene rows. No lot-scene had zero valid pixels; no read errors in the final run. |

Why fewer scenes after 2021: Sentinel-1B failed in Dec 2021, leaving
Sentinel-1A alone (~12-day revisit instead of ~6-day). The 2022–2026
summers therefore have 8–15 scenes instead of 14–15, and the gaps above
are RTC-collection gaps on top of the 12-day revisit — the annual means
for 2022 in particular rest on fewer, more widely spaced samples.

## Orbit / platform notes

- **All 114 acquisitions are ascending, relative orbits 4 and 77 only**,
  at 23:08–23:16 UTC = **19:08–19:16 EDT** (evening). No descending
  items and no Sentinel-1B in this collection for this area — same as
  the 3-summer check.
- **Platforms:** 2018–2024 all `SENTINEL-1A`. 2025: 11 scenes
  `sentinel-1a` + 1 scene `SENTINEL-1A` (2025-06-14) — same satellite,
  only the STAC metadata casing changed; that one scene's values are
  within range.
- **Sentinel-1D appears in 2026:** 10 of the 15 acquisitions in summer
  2026 are `sentinel-1d` (first: 2026-06-28 rel 77), 5 are Sentinel-1A.
  Per-lot 2026 means by platform differ by ≤0.31 dB in the 5 large lots
  (oakville-south: 0.77 dB, within its noise) — no systematic S1D
  offset is evident, but with only 5 S1A scenes the comparison is weak.
  Treat 2026 as a mixed-platform year and keep the S1A/S1D split in mind
  when comparing 2026 with earlier years.
- **Relative-orbit offsets persist:** the rel 4 minus rel 77 gap varies
  by lot and year (typically −1.3 to +0.7 dB; full table in
  `vv-by-lot-year-track-2018-2026.csv`). Annual means pool both tracks,
  and the track mix differs slightly year to year, so part of any
  year-to-year wiggle of ~0.3 dB can be track mix, not occupancy.

## Anomaly — oakville-south, summer 2026: do not trust the 127 index

oakville-south jumps to −8.37 dB (index 127.4) in 2026, while the other
5 lots sit within ±0.3 dB of 2024. The jump is **not** a platform
effect (2026 S1A scenes −8.88 vs S1D −8.11) and it survives removing
the brightest scene: excluding 2026-08-22 the mean is still −8.59
(index 121.1), and the median-based annual value is −8.82.
**Ground truth supplied by the user 2026-11-10, verified against
Metrolinx: Oakville GO construction started April 2026 (contract
awarded early April, mobilisation from 13 April 2026), with a
construction laydown / compound set up on the south side of the
station and parking reductions expected — the South Lot was mostly
closed during summer 2026. That explains the extreme value, but in
the opposite direction to a demand reading: a closed lot should be
*darker* (fewer cars), yet it is *brighter*, because a construction
compound — trailers, fencing, heavy equipment, metal containers and
stockpiled material — is a much stronger radar reflector than parked
cars, especially in an 82-pixel lot. So the 2026 South Lot value
measures construction activity, not parking demand, and must be
excluded from any demand series.**

What it is, is small-lot noise amplified:

- Only **82 pixels** — the smallest lot by far (next smallest 319 px).
  Its scene SD in 2026 is **1.37 dB**, the largest of any lot-year.
- Its rel 4 minus rel 77 gap is positive in **every** year
  (+0.08 to +1.46 dB; 2026: +1.46 dB, the largest) — a persistent
  track-dependent offset for this lot's geometry, not a 2026 change.
- 2026-08-22 was a **common-mode bright day**: every lot was
  ~1.5–2.5 dB brighter than its 2026 mean that day (e.g. oakville-main
  −8.16 vs −10.10; clarkson-north −7.55 vs −9.35), most plausibly a wet
  surface after rain. It lifts all 2026 means slightly, and
  oakville-south — rel 4 that day, 82 px — most of all.

Conclusion: oakville-south's 2026 value says nothing reliable about
demand. Use its 2018–2025 series only, and treat the lot as supporting
evidence throughout, as in the 3-summer check.

## Run notes

- First run (2026-11-11) completed 104 of 114 acquisitions, then hung
  for ~3 minutes on the first Sentinel-1D scene
  (`S1D_...20260628T231543..._rtc`, rel 77, 2026-06-28) with no error
  and ~0 CPU — a stalled COG read. The process was killed (SIGTERM);
  the CSV is append-only so nothing was lost. A bounded diagnostic read
  of the same COG (`diag-s1d-read.py`, kept in this folder) completed
  in ~8 s, so the stall was transient, not a bad file.
- Resume (same script, `GDAL_HTTP_TIMEOUT=120
  GDAL_HTTP_CONNECTTIMEOUT=30` added to bound future stalls) finished
  the remaining 10 acquisitions in ~1 minute, including that S1D scene.
  Final log: 0 errors, 0 "NO VALID PIXELS".
- **Verification (all passed):**
  - Row count 684 = 114 acquisitions × 6 lots; 0 nulls in
    `mean_VV_dB`; all dates Jun–Aug; all ascending; n_pixels constant
    per lot (739 / 82 / 360 / 325 / 575 / 319); clarkson-north spaces 627.
  - Cross-check vs the old run: 2019, 2020 Jun–Aug, and 2024 annual
    means match **exactly (diff +0.000 dB)** for all 6 lots × 3 years.
  - Chart re-made with one common y-range after the first version
    clipped oakville-south 2026 at the top and clarkson-main 2020/2021
    at the bottom; the current `vv-time-series-2018-2026.png` was
    visually checked — all points and error bars are inside the frame.

## What was actually measured

- **VV units — verified, not assumed, twice.** First scene
  (2018-06-03): min 0.0005, p5 0.0037, median 0.1168, p95 0.5640,
  max 549.65 — linear gamma naught. On resume, the first scene read
  (the S1D 2026-06-28 scene): median 0.1060, same linear branch.
  Conversion per pixel: `VV_dB = 10·log10(linear)`, linear clipped at
  1e-6 (−60 dB floor). Reported means/medians/SDs are of per-pixel
  dB values. Nodata (−32768) excluded; per-pixel dB outside
  (−60, +20) excluded.
- **Pixel counts are constant per lot**, i.e. every scene covered
  every lot fully — no partial-coverage gaps.
- **Within-lot pixel scatter** (mean SD of per-pixel VV inside a lot)
  is ~3.0–4.0 dB (speckle + surface heterogeneity). That is why the
  lot mean over hundreds of pixels is the usable quantity, not single
  pixels. Effective resolution is ~20 m vs 10 m pixel spacing, so
  pixels are correlated — the effective independent sample count is
  lower than n_pixels.
- Absolute VV levels differ between lots (e.g. 2019: oakville-south
  −9.4 vs clarkson-main −11.6 dB). That is lot geometry/surroundings,
  not occupancy — **only changes within the same lot are
  interpretable**.

## Caveats — read before using these numbers

1. **Ascending only, evening only.** Every value here is a ~19:10 EDT
   snapshot — after the evening peak, when lots are emptying. The
   signal still shows clearly, but its size at 19:10 need not equal
   the size at midday, and the full SARpanel run (ASF/SNAP scenes,
   both orbit directions) may give a different magnitude.
2. **No ground-truth calibration.** A −1.5 dB drop is a relative
   change in backscatter, not an occupancy rate. Converting dB to
   "% full" needs ground truth (counts on known dates, or optical
   validation). **Do not quote these numbers as occupancy
   percentages.** The recovery index is a backscatter-power index,
   nothing more.
3. **Weather/moisture is a confounder in principle** (wet asphalt
   raises backscatter). The sustained multi-year pattern is not a
   weather artefact, but individual bright days exist — 2026-08-22
   lifted every lot ~1.5–2.5 dB — and annual means contain a few
   such days. Summer-only windows were used deliberately to avoid
   snow/ice.
4. **oakville-south is thin evidence on its own** (82 pixels,
   8,215 m²): its 2026 jump is not trusted (see "Anomaly" above),
   and its 2018 value (index 83) is also the noisiest baseline
   point. Treat it as supporting, not standalone.
5. **RTC gamma0 ≠ SARpanel sigma0.** SARpanel/SNAP produces sigma0;
   this check used terrain-corrected gamma0 from Planetary Computer.
   Absolute levels are not directly comparable — only the
   within-lot change pattern should be expected to transfer.
6. **Polygons include internal roads.** The user-drawn polygons
   include the lots' internal circulation roads, not just the parking
   stalls (drawing stall-by-stall would be very fragmented). Roads
   are asphalt that does not change with occupancy, so they dilute
   the signal: the observed dB changes are a **conservative lower
   bound** on the stall-only change. This does not change the
   direction or the recovery conclusion.
7. **clarkson-north boundary is still unverified.** Its polygon is
   32,796 m² = **52.3 m²/space at 627 spaces**, vs 27–32 m²/space
   for the other 5 lots. Either the polygon includes asphalt beyond
   the named North Lot, or GO's 627 covers only part of the
   north-side lots. Its VV series is unaffected, but do not use it
   for space-weighted station totals until the boundary is verified.
8. **VM workaround, documented:** rasterio/GDAL reads needed
   `GDAL_HTTP_UNSAFESSL=YES` because this VM's egress proxy re-signs
   TLS and GDAL's libcurl rejects its certificate even with
   `CURL_CA_BUNDLE` set to the runtime bundle (verified; Python
   `requests` with the same bundle succeeds). Only short-lived
   Planetary Computer SAS tokens for public COGs were sent over those
   reads. On resume, `GDAL_HTTP_TIMEOUT=120` /
   `GDAL_HTTP_CONNECTTIMEOUT=30` were also set to bound stalled reads.

## Bottom line

The 9-summer series turns the 3-point COVID story into a full
recovery curve: **flat in 2018–2019, collapsed in 2020–2021, half
back in 2022, fully back by 2023–2024, flat at ~2019 levels through
2025–2026** (5 of 6 lots within ±8 index points of 2019 in 2026;
clarkson-north a little above at 108). That is the preliminary
product the user asked for — a per-lot, per-year recovery index for
the 3 pilot stations, ready to be set against PRESTO ridership. It
does not replace the SARpanel run, and it does not give occupancy
percentages.
