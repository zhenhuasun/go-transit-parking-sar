# Quick VV signal check — GO Transit parking lots

Date run: 2026-11-07. Data: Microsoft Planetary Computer STAC, collection
`sentinel-1-rtc` (Sentinel-1 RTC, terrain-corrected gamma naught, VV).
NOT Google Earth Engine, NOT SNAP, NOT SARpanel — a shortcut check only.
Polygons: user-drawn `polygons-user.geojson` (6 outdoor lots, garages excluded).
Script: `quick-vv-check.py` (reproducible; CSV is appended incrementally,
re-runs resume). Analysis/chart: `analyse-vv.py`.
Files: `vv-by-lot-scene.csv` (312 rows = 52 acquisitions × 6 lots),
`vv-time-series.png`, `vv-summary-table.csv`, `vv-by-lot-period-track.csv`.

## Verdict: YES — there is a clear VV signal

Mean VV fell in **all 6 lots** in summer 2020 vs summer 2019, and recovered
to ~2019 levels by summer 2024. The drop is **0.8–2.0 dB**, the recovery
**+1.0 to +2.2 dB**, while the scene-to-scene scatter within a period is
only **~0.5–1.0 dB** (SD of scene means). So the COVID drop is roughly
1.5–3× the scatter, it appears in both relative orbits independently, and
it is the same sign in every lot. That is not noise.

## Results — mean VV_dB, ascending only, both relative orbits pooled

| Lot | Spaces / px | 2019 summer (n=15) | 2020 Apr–May (n=10) | 2020 Jun–Aug (n=14) | 2024 summer (n=13) | 2019→2020 Jun–Aug | 2020→2024 | 2019→2024 |
|---|---|---|---|---|---|---|---|---|
| oakville-main | 2712 / 739 | −10.19 ±0.75 | −11.62 ±0.51 | −11.75 ±0.57 | −10.48 ±0.61 | **−1.56** | +1.27 | −0.29 |
| oakville-south | 291 / 82 | −9.42 ±1.01 | −10.38 ±1.44 | −10.19 ±0.65 | −10.05 ±0.74 | −0.77 | +0.14 | −0.63 |
| clarkson-main | 1274 / 360 | −11.62 ±1.07 | −13.03 ±0.70 | −13.14 ±0.63 | −11.65 ±0.76 | −1.52 | +1.49 | −0.03 |
| clarkson-north | 1020 / 325 | −9.68 ±0.96 | −11.71 ±0.55 | −11.68 ±0.50 | −9.46 ±0.80 | −2.00 | +2.22 | +0.22 |
| bronte-main | 1824 / 575 | −10.71 ±0.83 | −11.86 ±0.54 | −11.82 ±0.97 | −10.45 ±0.63 | −1.11 | +1.37 | +0.26 |
| bronte-south | 1149 / 319 | −10.51 ±0.84 | −11.31 ±0.76 | −11.48 ±0.71 | −10.51 ±0.45 | −0.97 | +0.97 | 0.00 |

Means are the average of per-scene lot means; ± is the SD across scenes in
that period. Median VV shows the same pattern (see CSV; e.g. clarkson-north
median −9.69 → −11.92 → −9.40).

Within-track check (same relative orbit, no pooling): the drop is present
in **both** relative orbits 4 and 77 for **every** lot — e.g. clarkson-north
rel 4: −9.82 → −11.80/−12.02 → −9.53; rel 77: −9.51 → −11.62/−11.34 → −9.41.
Full per-track table: `vv-by-lot-period-track.csv`.

Two further observations:

- **2020 Apr–May ≈ 2020 Jun–Aug** in every lot (within ~0.2 dB). The lots
  did not refill during summer 2020; the collapse lasted the whole summer.
- **2024 ≈ 2019** in 5 of 6 lots (within 0.3 dB). The exception is
  oakville-south, −0.63 dB below 2019 — but it is also the smallest lot
  (82 pixels), the noisiest (scene SD up to 1.44 dB), and its 2020 drop was
  the smallest, so do not over-read it.

## What was actually measured

- **52 distinct acquisitions**, all Sentinel-1A, all **ascending**, relative
  orbits 4 and 77 only, at **23:08–23:16 UTC = 19:08–19:16 EDT** (evening).
  2019 summer: 15 scenes; 2020 Apr–Aug: 24; 2024 summer: 13.
- **VV units — verified, not assumed.** The RTC `vv` asset is gamma naught
  in **linear** power ratio (first window read: min 0.002, p5 0.017,
  median 0.124, p95 0.56, max 333). Conversion applied per pixel:
  `VV_dB = 10·log10(linear)`, linear clipped at 1e-6 (−60 dB floor).
  Reported means/medians/SDs are of per-pixel dB values. Nodata (−32768)
  excluded; per-pixel dB values outside (−60, +20) excluded.
- **Pixel counts are constant per lot** (739 / 82 / 360 / 325 / 575 / 319),
  i.e. every scene covered every lot fully — no partial-coverage gaps.
- **Within-lot pixel scatter** (mean SD of per-pixel VV inside a lot) is
  ~3.0–4.0 dB (speckle + surface heterogeneity). That is why the lot mean
  over hundreds of pixels is the usable quantity, not single pixels.
  Effective resolution is ~20 m vs 10 m pixel spacing, so pixels are
  correlated — the effective independent sample count is lower than n_pixels.
- Absolute VV levels differ between lots (e.g. 2019: oakville-south −9.4
  vs clarkson-main −11.6 dB). That is lot geometry/surroundings, not
  occupancy — **only changes within the same lot are interpretable**.

## Caveats — read before using these numbers

1. **Ascending only, evening only.** A bbox search for June 2019 returned
   **0 descending items** in this collection vs 5 ascending: the Planetary
   Computer `sentinel-1-rtc` collection appears to contain no descending
   passes over this area (and no Sentinel-1B at all — all 52 scenes are
   Sentinel-1A). So there is no descending comparison to make, and every
   value here is a ~19:10 EDT snapshot — after the evening peak, when lots
   are emptying. The signal still shows clearly, but its size at 19:10
   need not equal the size at midday, and the full SARpanel run (which uses
   ASF/SNAP scenes, both orbit directions) may give a different magnitude.
2. **No ground-truth calibration.** A −1.5 dB drop is a relative change in
   backscatter, not an occupancy rate. Converting dB to "% full" needs
   ground truth (counts on known dates, or optical validation). Do not
   quote these numbers as occupancy percentages.
3. **Weather/moisture is a confounder in principle** (wet asphalt raises
   backscatter), but a sustained 5-month drop, identical in sign across
   6 lots × 2 tracks, followed by recovery 4 years later, is not a
   plausible weather artefact. Summer-only windows were used deliberately
   to avoid snow/ice.
4. **oakville-south is thin evidence on its own** (82 pixels, 8,215 m²):
   its drop (−0.8 dB) and its weak recovery (+0.14 dB) are both within
   ~1 SD of its scene scatter. Treat it as supporting, not standalone.
5. **RTC gamma0 ≠ SARpanel sigma0.** SARpanel/SNAP produces sigma0; this
   check used terrain-corrected gamma0 from Planetary Computer. Absolute
   levels are not directly comparable — only the within-lot change pattern
   should be expected to transfer.
6. **VM workaround, documented:** rasterio/GDAL reads needed
   `GDAL_HTTP_UNSAFESSL=YES` because this VM's egress proxy re-signs TLS
   and GDAL's libcurl rejects its certificate even with `CURL_CA_BUNDLE`
   set to the runtime bundle (verified; Python `requests` with the same
   bundle succeeds). Only short-lived Planetary Computer SAS tokens for
   public COGs were sent over those reads.

## Bottom line for the SARpanel decision

The quick check did its job: **the VV proxy moves with parking occupancy
in the expected direction, by ~1–2 dB for a full-to-empty swing, and it
recovers.** That justifies running SARpanel properly — with both orbit
directions, the full 2018–2026 span, and (ideally) a ground-truth
calibration point — rather than stopping here. The 2019-summer trial
configuration already prepared (`sarpanel-go-parking-trial-2019-summer.yaml`)
is the right next step; this check does not replace it.
