# T1b — Supplemental negative control (specification addendum)

## Status — read first

**This addendum was written on 2026-11-12 AFTER seeing the T1 result
(PASS, pooled weekend effect −0.428 dB, 2026-11-12). It is NOT
pre-registered with T1 and must not be presented as pre-planned.**

Reason it exists: T1's Step 3 sensitivity S5 (negative control) was skipped
because no control file existed (`polygons/control-areas.geojson` was
absent). T1b supplies that missing control after the fact. Nothing in T1
— its data, code, or PASS decision — is re-run or altered by T1b. T1b can
only confirm T1's PASS or downgrade it to INCONCLUSIVE (see Decision).

## Revision — round 2 (2026-11-12; no separate T1c)

Round 1 (above) downgraded T1 to INCONCLUSIVE. The user then established
the cause (ground truth, 2026-11-12): part of the Oakville control area
was a building with an active parking lot prior to 2024. That area is
invalidated and replaced; there is no separate T1c — round 2 edits this
addendum and re-runs the same test in `calibration/t1b/`.

- **Replaced:** Oakville GO — Control v1 (id `control-1794494368787`,
  14,009 m²) is removed entirely. Its extracted rows are kept only in
  the round-1 archive `t1b_control_vv_round1.csv` and are not used in
  round 2.
- **New:** Oakville GO — Control v2 (id `control-1794497254064`),
  7,232 m², centroid 43.44529, −79.69016, nearest lot edge 787 m
  (Oakville Main). Valid and closed (7 vertices); no overlap with any
  parking lot or the other controls. Area ≈ 72 pixels at 10 m,
  comparable to the smallest lot (Oakville South, 82 pixels). OSM
  coverage (local Geofabrik extract, full-OSM scan 2026-11-12):
  93.3% building:industrial — a factory/warehouse roof, no parking
  overlap, no other land use recorded.
- **Unchanged:** Bronte and Clarkson controls (same polygons, same
  extracted rows reused from round 1).
- **Distance note:** v2 Oakville is farther from the station than the
  T1b areas (787 m to the nearest lot edge, vs 167–437 m before; ~1.1 km
  to the lot centroids). Accepted under the user's relaxed rule ("as long
  as they are not far away", 2026-11-12): a control needs the same
  scenes and the same local imaging conditions, which it has. The
  distance is recorded here, not hidden.
- **Rules unchanged:** extraction, sample, models, and decision criteria
  below are identical in round 2. Only the Oakville control polygon (and
  its extracted rows) changed.
- **Round-2 decision:** if both criteria hold, T1's PASS is
  **reinstated** (history preserved: PASS → INCONCLUSIVE (round 1) →
  PASS reinstated (round 2)). If either criterion fails, T1 **stays
  INCONCLUSIVE**. The T1 report annotation is updated to the round-2
  outcome; the round-1 report is kept as `t1b_report_round1.md`.

## Control areas (input)

File: `polygons/control-areas.geojson` — user-drawn 2026-11-12 with
`calibration/t1b/control-areas-edit.html`, received as
`go-parking-control-areas.geojson` and copied verbatim (geometry and
properties unchanged).

| Control area | Area | Nearest lot edge | OSM coverage (local Geofabrik extract) |
|---|---|---|---|
| Oakville GO — Control | 14,009 m² | 252 m (Oakville Main) | 100% landuse:retail, 14.2% building |
| Clarkson GO — Control | 8,385 m² | 437 m (Clarkson Main) | 97.4% building:industrial |
| Bronte GO — Control | 22,160 m² | 167 m (Bronte South) | 95.6% building:warehouse |

Validation (2026-11-12, before this addendum was written): all 3 polygons
valid, closed, no overlaps with any parking lot or with each other.
No OSM parking feature overlaps any control polygon (reverse-geocode hits
for "parking" near the centroids were nearest-feature lookups, not
overlaps).

Distance rule: the drawing page asked for "within 500 m of the parking
lot". The user relaxed this on 2026-11-12 ("as long as they are not far
away"). Measured edge distances are 167–437 m; the two centroid distances
just over 500 m (Oakville 528 m, Clarkson 581 m) are to lot centroids, not
edges. Accepted as nearby.

Oakville note (user ground truth, 2026-11-12): the Oakville control area
is a long-time empty car parking area near Oakville GO that has been locked
for many years. It satisfies the control requirement — no parked cars —
and is recorded as such because the map data only labels it "parking"
without saying it is disused.

## Extraction (fixed)

- Same 114 summer scenes as T1, identified by the exact `scene_id` values
  in `quick-vv-check-2018-2026/vv-by-lot-scene-2018-2026.csv` (Jun–Aug
  2018–2026, ascending, relative orbits 4 and 77).
- Same collection (`sentinel-1-rtc`) and same VV processing as
  `quick-vv-check-2018-2026.py`: per-pixel `VV_dB = 10*log10(linear)`,
  linear clipped at 1e-6; per-scene control mean is the mean of per-pixel
  dB values; same nodata / out-of-range exclusions; same unit check on
  the first scene (assert the linear branch, abort otherwise).
- Script: `calibration/t1b/extract-control-vv.py`. Output:
  `calibration/t1b/t1b_control_vv.csv` (one row per control area per scene:
  `control_id, control_name, station, scene_id, date, datetime_utc,
  orbit_state, relative_orbit, platform, n_pixels, mean_VV_dB,
  median_VV_dB, std_VV_dB`).
- Missing-scene rule: if a scene cannot be read for a control area, drop
  that scene from the differenced analysis for that station's lots and
  record the dropped scenes in the report. Control-only models use all
  available scenes.

## Sample and models (fixed)

Primary sample, as in T1: years 2018, 2019, 2022–2026 (drop 2020–2021
lockdown summers), Jun–Aug only. The Oakville South 2026 exclusion
applies to lot rows only; control areas have all years. Weekend =
Saturday, Sunday, or holiday (Canada Day Jul 1, Jul 2 observed if Jul 1
is a Sunday; Civic Holiday, first Monday of August) — same definition
as T1.

Station mapping (fixed): Oakville Main and Oakville South are differenced
against the Oakville control; Clarkson Main and Clarkson North against
the Clarkson control; Bronte Main and Bronte South against the Bronte
control.

- **C1 — per-area OLS:** control `VV_dB ~ weekend + C(relative_orbit) +
  C(year)`, classical SE. One model per control area (3 models).
- **C2 — pooled control OLS:** control `VV_dB ~ weekend + C(area) +
  C(area):C(relative_orbit) + C(area):C(year)`, SE clustered by
  acquisition date (CR1, t with G−1 df).
- **D1 — per-lot differenced OLS:** `(lot VV_dB − same-station control
  VV_dB) ~ weekend + C(relative_orbit) + C(year)`, classical SE.
  One model per lot (6 models).
- **D2 — pooled differenced OLS:** differenced `VV_dB ~ weekend + C(lot)
  + C(lot):C(relative_orbit) + C(lot):C(year)`, SE clustered by
  acquisition date (CR1). Permutation test identical to T1 Step 2c:
  shuffle the weekend label among scenes within each (year ×
  relative_orbit) stratum, label shared across lots within a scene,
  10,000 permutations, seed 42, one-sided p (fraction ≤ observed).

## Decision (pre-specified here, applied mechanically)

T1's PASS **stands** if BOTH hold:

1. **Controls show no significant weekend effect:** all 3 per-area
   weekend coefficients have two-sided p ≥ 0.05, AND the pooled control
   weekend coefficient has two-sided p ≥ 0.05. Either sign counts — a
   significant positive weekend effect in a control fails this criterion
   just as a negative one does.
2. **Differenced series passes all T1 criteria:** pooled differenced
   weekend coefficient < 0 with clustered two-sided p < 0.01;
   permutation one-sided p < 0.01; ≥ 5 of 6 lots have a negative
   differenced per-lot weekend coefficient (Oakville South uses
   2018–2025 only).

**Fallback:** if either criterion fails, T1 is downgraded to
**INCONCLUSIVE** (not FAIL). The T1 report's PASS is annotated, not
rewritten; the T1b report records the downgrade and the reason.

**Round 2:** the same two criteria are applied to the revised control
set. If both hold, T1's PASS is **reinstated**; if either fails, T1
**stays INCONCLUSIVE**. Round 1's INCONCLUSIVE (Oakville v1 control)
is preserved in `t1b_report_round1.md` and is not erased by a round-2
pass.

## Outputs (`calibration/t1b/`)

- `t1b_spec_addendum.md` — this file (committed before any extraction
  or modelling; round-2 revision committed before the round-2 run).
- `extract-control-vv.py` — extraction script (unchanged; resume
  behaviour extracts only the new Oakville control in round 2).
- `t1b_control_vv.csv` — extracted per-scene control VV (round 2:
  Bronte/Clarkson rows reused from round 1, Oakville v2 rows fresh;
  Oakville v1 rows removed).
- `t1b_weekend_test.py` — single reproducible analysis script, seed 42.
- `t1b_results.csv` — every coefficient from every model (current round).
- `t1b_report.md` — control results, differenced results, decision
  against each criterion, deviations list, plain-language reading
  (current round).
- `t1b_results_round1.csv`, `t1b_report_round1.md`,
  `t1b_control_vv_round1.csv` — round-1 archive (INCONCLUSIVE), kept
  unchanged.
- `control-areas-v2.geojson` — the revised control set (staging copy;
  the committed copy is `polygons/control-areas.geojson`).

## Deviations from this addendum

None (to be filled in if any occur during the run).
