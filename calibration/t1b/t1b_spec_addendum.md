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

## Revision — round 3 (2026-11-12; no separate T1c)

Round 2 also downgraded T1 to INCONCLUSIVE (Oakville v2 control showed
a weekend effect, −0.885 dB, p = 0.0064, present in every year
2018–2026). The user then drew a new Oakville control as a pooled set
of roofs and checked each roof's historical imagery himself (no major
overhaul). There is no separate T1c — round 3 edits this addendum and
re-runs the same test.

- **Sent:** Oakville GO — Control, pooled MultiPolygon, 5 parts,
  12,032 m² (user export `control-areas-v3-user.geojson`, 2026-11-12).
- **Dropped before the run:** part 2 (3,286 m², centroid 43.44552,
  −79.69048). Validation found 3,244 m² of it (99%) lies inside the
  failed round-2 Oakville roof (7,232 m², centroid 43.44529, −79.69016)
  — a sub-section of the same factory roof. Pooling it in would
  re-import the round-2 confounder. The user chose to drop it
  (2026-11-12, "Drop part 2, run with the other 4").
- **New:** Oakville GO — Control v3 (id `control-oakville-pooled`),
  pooled MultiPolygon, 4 parts, 8,747 m². Parts: 2,176 m² (centroid
  43.46179, −79.67509; nearest lot edge 829 m), 1,794 m² (43.44700,
  −79.69352; 779 m), 1,643 m² (43.44757, −79.69325; 718 m), 3,133 m²
  (43.44544, −79.70348; 1,511 m). Valid MultiPolygon; the 4 parts do not
  overlap each other or any parking lot. Area ≈ 87 pixels at 10 m,
  comparable to the smallest lot (Oakville South, 82 pixels). OSM
  coverage (local Geofabrik extract, full-OSM scan 2026-11-12) of the
  5-part set as sent (12,033 m²): 40.9% building:retail, 38.1%
  building:industrial, 28.6% landuse:industrial (overlaps the building
  footprints), 17.9% building:yes "Longo's" — and **no parking overlap
  anywhere**. The 4-part set as run is a subset of that scan, so it
  also has no parking overlap; its building mix is retail-heavier
  because the dropped part 2 was the industrial factory roof. A
  per-part scan is running to record each part's coverage exactly.
- **Unchanged:** Bronte and Clarkson controls (same polygons, same
  extracted rows reused from rounds 1–2).
- **Distance note:** the v3 parts sit 718–1,511 m from the nearest lot
  edge — farther than round 2's 787 m. Accepted under the user's relaxed
  rule ("as long as they are not far away", 2026-11-12): a control needs
  the same scenes and the same local imaging conditions, which it has.
  The distances are recorded here, not hidden.
- **Historical imagery:** the user checked each of the 5 roofs'
  historical images himself before sending them ("no major overhaul",
  2026-11-12). Recorded as user ground truth; the assistant did not
  independently verify the imagery.
- **Rules unchanged:** extraction, sample, models, and decision criteria
  below are identical in round 3. Only the Oakville control polygon (and
  its extracted rows) changed.
- **Round-3 decision:** if both criteria hold, T1's PASS is
  **reinstated** (history preserved: PASS → INCONCLUSIVE (round 1) →
  INCONCLUSIVE (round 2) → PASS reinstated (round 3)). If either
  criterion fails, T1 **stays INCONCLUSIVE**. The T1 report annotation
  is updated to the round-3 outcome; the round-1 and round-2 reports
  are kept as `t1b_report_round1.md` and `t1b_report_round2.md`.

## Revision — round 4 (2026-11-12; no separate T1c)

Rounds 1–3 all downgraded T1 to INCONCLUSIVE. The controls improved
each round (round 3 finally passed criterion 1), but criterion 2 never
cleared the p < 0.01 bar (round 3: pooled differenced −0.369 dB,
p = 0.075). An exploratory sensitivity check (2026-11-12,
`t1b_sensitivity_common_control.py`, not part of any decision) then
differenced all 6 lots against each single control in turn: Bronte-only
gave −0.501 dB (clustered p = 0.016, perm p = 0.017), Clarkson-only
−0.372 dB (p = 0.125), Oakville-only −0.226 dB (p = 0.307) — all still
short of 0.01, but Bronte-only was the strongest by a wide margin.

The user then proposed the design change on physical grounds
(2026-11-12): the Bronte roofs are the region's best control surface
— one huge single unchanged warehouse roof (22,160 m², 224 px/scene,
95.6% warehouse) — while Clarkson's is too small (8,385 m², 85 px)
and Oakville's are too mixed (4 small roofs of different kinds). Two
more big unchanged rooftops exist near Bronte. Round 4 therefore
replaces the per-station mapping with a single common control for all
6 lots. There is no separate T1c — round 4 edits this addendum and
re-runs the same test.

- **Design change:** a single common control — the pooled Bronte
  control — is subtracted from all 6 lots. Rationale: the three
  stations are 4–9 km apart and share the same Sentinel-1 scenes,
  relative orbits, and ~19:10 acquisition times, so scene-level
  artefacts (orbit geometry, incidence angle, calibration, regional
  moisture) are common across stations; a control measured at Bronte
  estimates that artefact level for Oakville and Clarkson too. What
  the single control gives up is station-matched pairing: a confounder
  that exists only at one station and only on weekends would not be
  caught. That insurance is only worth having if the station controls
  are clean themselves, and Oakville's never have been — the
  per-station design's noise is what round 3's criterion-2 failure was
  made of (Oakville control −0.209 dB wiping out both Oakville lots).
- **New:** Bronte GO — Control v4 (id `control-bronte-pooled`),
  pooled MultiPolygon, 3 parts, 48,071 m². Parts: 17,420 m² (centroid
  43.40964, −79.72724; nearest lot edge 642 m, Bronte South),
  8,511 m² (43.41434, −79.72802; 330 m, Bronte South), 22,140 m²
  (43.41376, −79.72377; 20 m, Bronte South). Part 3 is the re-traced
  round 1–3 Bronte roof (99.5% overlap with the committed polygon;
  the round-1 table's "167 m" for that roof was a centroid distance —
  its edge distance is 20 m, same as part 3). Valid MultiPolygon; the
  3 parts do not overlap each other or any parking lot. Area ≈ 481
  pixels at 10 m. OSM coverage (local Geofabrik extract, full-OSM
  scan 2026-11-12) of the pooled set (48,069 m²): 53.9%
  building:industrial, 44.1% building:warehouse — 98.0% building
  in total — and **no parking overlap anywhere**. Per-part:
  roof 1 (17,420 m²) 100.0% building:industrial; roof 2
  (8,511 m²) 100.0% building:industrial; roof 3 (22,139 m²)
  95.8% building:warehouse.
- **Historical imagery:** the user described the two new roofs as big
  and unchanged (2026-11-12), and re-traced the existing Bronte roof
  from the round-4 drawing page's reference outline. Recorded as user
  ground truth; the assistant did not independently verify the
  imagery.
- **Replaced:** all three round-3 controls (Bronte, Clarkson, Oakville
  pooled) are removed entirely. Their extracted rows are kept only in
  the round-3 archive `t1b_control_vv_round3.csv` and are not used in
  round 4. Note the old Bronte control shares the name "Bronte GO —
  Control" with the new pooled control but has a different id
  (`control-1794494256535` vs `control-bronte-pooled`); all old rows
  are dropped before extraction so the two are never mixed.
- **Diagnostic only (not part of the decision):** each of the 3 roofs
  is extracted separately (`extract-control-vv-parts.py`, output
  `t1b_control_vv_r4_parts.csv`) and its weekend coefficient reported
  in the round-4 report, so one bad roof cannot hide inside the pool.
  The diagnostic does not affect either criterion.
- **Rules unchanged:** extraction, sample, models, and decision
  criteria below are identical in round 4, with two mechanical
  adaptations for the single-control design: criterion 1 is evaluated
  on the one pooled control (the per-area and pooled models are the
  same series, differing only in classical vs clustered SE); D1/D2
  difference every lot against the same Bronte control. The 0.01 bar
  is unchanged.
- **Round-4 decision:** if both criteria hold, T1's PASS is
  **reinstated** (history preserved: PASS → INCONCLUSIVE (rounds 1–3)
  → PASS reinstated (round 4)). If either criterion fails, T1 **stays
  INCONCLUSIVE**. The T1 report annotation is updated to the round-4
  outcome; the round-1–3 reports are kept as `t1b_report_round1.md`,
  `t1b_report_round2.md`, and `t1b_report_round3.md`.

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

**Round 3:** the same two criteria are applied to the revised control
set (pooled 4-roof Oakville control, part 2 dropped — see Revision —
round 3). If both hold, T1's PASS is **reinstated**; if either fails,
T1 **stays INCONCLUSIVE**. Rounds 1–2 INCONCLUSIVE verdicts are
preserved in `t1b_report_round1.md` and `t1b_report_round2.md` and are
not erased by a round-3 pass.

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
- `t1b_results_round2.csv`, `t1b_report_round2.md`,
  `t1b_control_vv_round2.csv`, `t1b_weekend_coefs_round2.png` —
  round-2 archive (INCONCLUSIVE), kept unchanged.
- `t1b_results_round3.csv`, `t1b_report_round3.md`,
  `t1b_control_vv_round3.csv`, `t1b_weekend_coefs_round3.png` —
  round-3 archive (INCONCLUSIVE), kept unchanged.
- `control-areas-v2.geojson` — the round-2 control set (staging copy;
  the committed copy is `polygons/control-areas.geojson`).
- `control-areas-v3-user.geojson` — the user's 5-part Oakville export
  as received (round 3 input; part 2 dropped before the run).
- `control-areas-v3.geojson` — the round-3 control set as run (4-part
  pooled Oakville control; the committed copy is
  `polygons/control-areas.geojson`).
- `control-areas-v4-user.geojson` — the user's 3-part Bronte export
  as received (round 4 input; identical to the set as run).
- `control-areas-v4.geojson` — the round-4 control set as run
  (3-part pooled Bronte control; the committed copy is
  `polygons/control-areas.geojson`).
- `control-areas-v4-parts.geojson` — the 3 Bronte roofs as separate
  Polygon features (per-roof diagnostic input, not the decision).
- `extract-control-vv-parts.py` — per-roof diagnostic extraction
  (output `t1b_control_vv_r4_parts.csv`).

## Deviations from this addendum

None (to be filled in if any occur during the run).
