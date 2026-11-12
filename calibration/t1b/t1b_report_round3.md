# T1b — Supplemental negative control (post-T1)

**Status:** this test was specified AFTER the T1 result (PASS, 2026-11-12) — see `t1b_spec_addendum.md`. It is not pre-registered with T1. Round 3 (2026-11-12): the Oakville control was replaced again — a pooled 4-roof control, after part 2 of the user's 5-roof set was dropped for overlapping the failed round-2 roof; Bronte and Clarkson controls are unchanged. Rounds 1–2 are archived as `t1b_report_round1.md` and `t1b_report_round2.md`.

**Decision: INCONCLUSIVE — T1 stays INCONCLUSIVE**

## Extraction check

Control VV extracted for all 114 T1 summer scenes (scene sets identical to the lot CSV). Unit check on the first scene confirmed LINEAR gamma naught, same branch as the lots. Mean pixels per scene: Bronte control 224, Clarkson control 85, Oakville control 95. Differenced rows: 513 (dropped 0).

Per-part OSM coverage of the Oakville v3 control (local Geofabrik extract, full-OSM scan 2026-11-12; no parking overlap in any part): part 1 (2,176 m²) 99.1% building:yes "Longo's"; part 3 (1,794 m²) 100% building:retail; part 4 (1,644 m²) 96.3% building:industrial; part 5 (3,134 m²) 100% building:retail. Dropped part 2 (3,286 m²) was 91.3% building:industrial — the failed round-2 factory roof.

## C — Control weekend effects (primary years 2018, 2019, 2022–2026)

Per-area OLS: control `VV_dB ~ weekend + C(relative_orbit) + C(year)` (classical SE). Pooled: `VV_dB ~ weekend + C(area) + C(area):C(relative_orbit) + C(area):C(year)`, SE clustered by acquisition date (CR1).

| Control area | Weekend coef (dB) | 95% CI | p | n |
|---|---|---|---|---|
| Bronte GO — Control | 0.061 | [-0.162, 0.284] | 0.5862 | 88 |
| Clarkson GO — Control | -0.066 | [-0.389, 0.257] | 0.6845 | 88 |
| Oakville GO — Control | -0.209 | [-0.506, 0.087] | 0.1641 | 88 |

**Pooled control:** weekend coef **-0.071 dB**, 95% CI [-0.294, 0.152], clustered two-sided p = 0.526, n = 264 rows, 87 date clusters.

## D — Differenced weekend effects (lot − same-station control)

Same models as T1, fitted on differenced VV. Permutation: 10,000 permutations, seed 42, weekend label shuffled among scenes within each (year × relative orbit) stratum, shared across lots within a scene.

| Lot | Differenced coef (dB) | 95% CI | p | n |
|---|---|---|---|---|
| oakville-main | -0.077 | [-0.513, 0.360] | 0.7277 | 88 |
| oakville-south | -0.062 | [-0.618, 0.493] | 0.8233 | 73 |
| clarkson-main | -0.802 | [-1.344, -0.259] | 0.00429 | 88 |
| clarkson-north | -0.309 | [-0.856, 0.239] | 0.2657 | 88 |
| bronte-main | -0.374 | [-0.802, 0.054] | 0.08601 | 88 |
| bronte-south | -0.529 | [-1.001, -0.058] | 0.02836 | 88 |

**Pooled differenced:** weekend coef **-0.369 dB**, 95% CI [-0.775, 0.038], clustered two-sided p = 0.07489, n = 513 rows, 87 date clusters. Permutation one-sided p = 0.0615.

![Control and differenced weekend coefficients with 95% CIs](t1b_weekend_coefs_round3.png)

## Decision against each criterion

1. ✅ Controls show no significant weekend effect (all per-area p ≥ 0.05 and pooled p ≥ 0.05) — per-area p values: Bronte GO — Control 0.5862, Clarkson GO — Control 0.6845, Oakville GO — Control 0.1641; pooled p = 0.526.
2. ❌ Differenced series passes all T1 criteria — pooled coef -0.369 dB < 0 with clustered p = 0.07489 (< 0.01: ❌); permutation p = 0.0615 (< 0.01: ❌); 6/6 lots negative (≥ 5: ✅).

**Decision: INCONCLUSIVE — T1 stays INCONCLUSIVE**

## Deviations from the addendum

Two local-only edits to the run script after the round-3 spec commit (the committed script at `c47fbf94` differs from the run script only in these two string constants, neither of which affects any model): the round-3 commit hash was inserted into the reproducibility note above (the hash did not exist when the script was written), and the per-part OSM coverage lines were added to the Extraction check section (the per-part scan finished after the spec commit).

Plain-language reading edited after the run to reflect the round-3 split (criterion 1 passed, criterion 2 failed); the generic template text implied the controls had failed.

## Reproducibility

- Spec: `t1b_spec_addendum.md`, committed to `zhenhuasun/go-transit-parking-sar` as `7b5a9730f47d6aea4e63e141177fe1c6fd79b2e0` (round 1) and `8bda63b7da552af2f91363d7141b4e10814f1531` (round 2, revised Oakville control) BEFORE any extraction or modelling in each round. Round 3 (2026-11-12): spec revision + 4-part Oakville control committed BEFORE the run; the round-3 commit hash is recorded in the repo history (c47fbf9445a052fa46545de4e787b07033811a84).
- Script: `t1b_weekend_test.py`, seed 42, 10,000 permutations. Rerun: `python3 t1b_weekend_test.py` from the repo root (uses only numpy, pandas, matplotlib). Extraction: `extract-control-vv.py`.
- `polygons/`, existing CSVs and existing scripts were not edited; all new outputs are in `calibration/t1b/`.

## Plain-language reading

The control areas are surfaces near each station that should not care what day of the week it is — warehouse and factory roofs. If the satellite or the processing itself produced a weekend pattern, the controls would show it too.
This round the controls passed — none of the three shows a significant weekend effect (pooled −0.071 dB, p = 0.53), so there is no sign of a satellite-side weekend artefact. But subtracting the controls leaves a weekend effect (−0.37 dB, all 6 lots negative) that is not strong enough to clear the pre-set bar (p = 0.075, needs < 0.01), so T1 stays INCONCLUSIVE: the pattern in the lots may still be real, but this check cannot confirm it at the required strength.
This still does not measure occupancy: without ground-truth calibration, no dB difference converts into a number of cars or a percentage full.