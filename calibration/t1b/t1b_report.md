# T1b — Supplemental negative control (post-T1)

**Status:** this test was specified AFTER the T1 result (PASS, 2026-11-12) — see `t1b_spec_addendum.md`. It is not pre-registered with T1. Round 4 (2026-11-12): the design changed to a single common control — the pooled 3-roof Bronte control (48,071 m²) subtracted from all 6 lots — after rounds 1–3 all ended INCONCLUSIVE and an exploratory sensitivity check found the Bronte-only variant strongest (−0.501 dB, p = 0.016). Rounds 1–3 are archived as `t1b_report_round1.md`, `t1b_report_round2.md`, and `t1b_report_round3.md`.

**Decision: INCONCLUSIVE — T1 stays INCONCLUSIVE**

## Extraction check

Control VV extracted for all 114 T1 summer scenes (scene sets identical to the lot CSV). Unit check on the first scene confirmed LINEAR gamma naught, same branch as the lots. Mean pixels per scene: Bronte pooled control 478. Differenced rows: 513 (dropped 0). All round-3 control rows were dropped before extraction (the old Bronte control shares the name but has a different id), so the CSV holds only the round-4 control.

Per-part OSM coverage of the 3 Bronte roofs (local Geofabrik extract, full-OSM scan 2026-11-12; no parking overlap in any part): roof 1 (17,420 m²) 100.0% building:industrial; roof 2 (8,511 m²) 100.0% building:industrial; roof 3 (22,139 m²) 95.8% building:warehouse. Pooled (48,069 m²): 53.9% building:industrial, 44.1% building:warehouse.

Per-roof diagnostic (not part of the decision): each roof extracted separately — see `t1b_control_vv_r4_parts.csv`.

## C — Control weekend effects (primary years 2018, 2019, 2022–2026)

Per-area OLS: control `VV_dB ~ weekend + C(relative_orbit) + C(year)` (classical SE). Pooled: `VV_dB ~ weekend + C(area) + C(area):C(relative_orbit) + C(area):C(year)`, SE clustered by acquisition date (CR1).

| Control area | Weekend coef (dB) | 95% CI | p | n |
|---|---|---|---|---|
| Bronte GO — Control | 0.035 | [-0.154, 0.224] | 0.7119 | 88 |

**Pooled control:** weekend coef **0.035 dB**, 95% CI [-0.144, 0.215], clustered two-sided p = 0.6974, n = 88 rows, 87 date clusters.

## D — Differenced weekend effects (lot − common Bronte control)

Same models as T1, fitted on differenced VV. Permutation: 10,000 permutations, seed 42, weekend label shuffled among scenes within each (year × relative orbit) stratum, shared across lots within a scene.

| Lot | Differenced coef (dB) | 95% CI | p | n |
|---|---|---|---|---|
| oakville-main | -0.321 | [-0.730, 0.088] | 0.1219 | 88 |
| oakville-south | -0.347 | [-0.850, 0.156] | 0.1733 | 73 |
| clarkson-main | -0.903 | [-1.414, -0.393] | 0.0007139 | 88 |
| clarkson-north | -0.410 | [-0.911, 0.092] | 0.1077 | 88 |
| bronte-main | -0.348 | [-0.751, 0.055] | 0.0895 | 88 |
| bronte-south | -0.503 | [-0.938, -0.068] | 0.02405 | 88 |

**Pooled differenced:** weekend coef **-0.476 dB**, 95% CI [-0.855, -0.098], clustered two-sided p = 0.01427, n = 513 rows, 87 date clusters. Permutation one-sided p = 0.0118.

![Control and differenced weekend coefficients with 95% CIs](t1b_weekend_coefs.png)

## Decision against each criterion

1. ✅ Controls show no significant weekend effect (all per-area p ≥ 0.05 and pooled p ≥ 0.05) — per-area p values: Bronte GO — Control 0.7119; pooled p = 0.6974.
2. ❌ Differenced series passes all T1 criteria — pooled coef -0.476 dB < 0 with clustered p = 0.01427 (< 0.01: ❌); permutation p = 0.0118 (< 0.01: ❌); 6/6 lots negative (≥ 5: ✅).

**Decision: INCONCLUSIVE — T1 stays INCONCLUSIVE**

## Deviations from the addendum

Three local-only edits to the run script after the round-4 spec commit (the committed script differs from the run script only in these string constants, none of which affects any model): (1) the round-4 commit hash was inserted into the reproducibility note below (the hash did not exist when the script was written); (2) this Deviations note itself was corrected — the committed version wrongly said the per-part OSM coverage lines were added after the spec commit, but they were in fact filled in BEFORE it (the scan finished first); (3) the plain-language reading gained a third branch for the criterion-1-pass / criterion-2-fail split, so it no longer implies the controls failed when only the differenced bar was missed.

## Reproducibility

- Spec: `t1b_spec_addendum.md`, committed to `zhenhuasun/go-transit-parking-sar` as `7b5a9730f47d6aea4e63e141177fe1c6fd79b2e0` (round 1) and `8bda63b7da552af2f91363d7141b4e10814f1531` (round 2, revised Oakville control) and `c47fbf9445a052fa46545de4e787b07033811a84` (round 3, pooled 4-roof Oakville control) BEFORE any extraction or modelling in each round. Round 4 (2026-11-12): spec revision + single pooled 3-roof Bronte control committed BEFORE the run; the round-4 commit hash is recorded in the repo history (8785b15c1b505671ecfee8fb1fc2a0bdb2255617).
- Script: `t1b_weekend_test.py`, seed 42, 10,000 permutations. Rerun: `python3 t1b_weekend_test.py` from the repo root (uses only numpy, pandas, matplotlib). Extraction: `extract-control-vv.py`.
- `polygons/`, existing CSVs and existing scripts were not edited; all new outputs are in `calibration/t1b/`.

## Plain-language reading

The control area is a pooled set of three large warehouse roofs near Bronte GO — surfaces that should not care what day of the week it is. The same control is subtracted from all six lots, because the three stations share the same satellite scenes and the roofs are the best-measured control surface in the region. If the satellite or the processing itself produced a weekend pattern, the control would show it too.
The control itself is clean — it shows no weekend effect (criterion 1 passed). But after subtracting it, the weekend effect in the lots, though negative in all six lots, is not strong enough to clear the pre-set bar (criterion 2: pooled p = 0.014, permutation p = 0.012, both above 0.01). So T1 stays INCONCLUSIVE: the weekend pattern in the lots may still be real, but this control check cannot rule out a non-car explanation at the strength the test demanded.
This still does not measure occupancy: without ground-truth calibration, no dB difference converts into a number of cars or a percentage full.
## Per-roof diagnostic (NOT part of the decision)

Each roof fitted separately with the C1 model (`VV_dB ~ weekend + C(relative_orbit) + C(year)`, classical SE; primary years 2018, 2019, 2022–2026). A roof with a significant weekend effect here would mean the pooled control hides a bad roof — the diagnostic is reported so that can be seen, but it does not affect either criterion.

| Roof | Weekend coef (dB) | 95% CI | p | n |
|---|---|---|---|---|
| Bronte GO — Control roof 1 | 0.024 | [-0.177, 0.226] | 0.8098 | 88 |
| Bronte GO — Control roof 2 | -0.190 | [-0.525, 0.146] | 0.2633 | 88 |
| Bronte GO — Control roof 3 | 0.129 | [-0.098, 0.356] | 0.2604 | 88 |
