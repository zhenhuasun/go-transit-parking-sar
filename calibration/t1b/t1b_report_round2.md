# T1b — Supplemental negative control (post-T1)

**Status:** this test was specified AFTER the T1 result (PASS, 2026-11-12) — see `t1b_spec_addendum.md`. It is not pre-registered with T1. Round 2 (2026-11-12): the Oakville control was replaced after round 1 downgraded T1 to INCONCLUSIVE; Bronte and Clarkson controls are unchanged. Round 1 is archived as `t1b_report_round1.md`.

**Decision: INCONCLUSIVE — T1 stays INCONCLUSIVE**

## Extraction check

Control VV extracted for all 114 T1 summer scenes (scene sets identical to the lot CSV). Unit check on the first scene confirmed LINEAR gamma naught, same branch as the lots. Mean pixels per scene: Bronte control 224, Clarkson control 85, Oakville control 71. Differenced rows: 513 (dropped 0).

## C — Control weekend effects (primary years 2018, 2019, 2022–2026)

Per-area OLS: control `VV_dB ~ weekend + C(relative_orbit) + C(year)` (classical SE). Pooled: `VV_dB ~ weekend + C(area) + C(area):C(relative_orbit) + C(area):C(year)`, SE clustered by acquisition date (CR1).

| Control area | Weekend coef (dB) | 95% CI | p | n |
|---|---|---|---|---|
| Bronte GO — Control | 0.061 | [-0.162, 0.284] | 0.5862 | 88 |
| Clarkson GO — Control | -0.066 | [-0.389, 0.257] | 0.6845 | 88 |
| Oakville GO — Control | -0.885 | [-1.515, -0.256] | 0.006413 | 88 |

**Pooled control:** weekend coef **-0.297 dB**, 95% CI [-0.548, -0.046], clustered two-sided p = 0.02115, n = 264 rows, 87 date clusters.

## D — Differenced weekend effects (lot − same-station control)

Same models as T1, fitted on differenced VV. Permutation: 10,000 permutations, seed 42, weekend label shuffled among scenes within each (year × relative orbit) stratum, shared across lots within a scene.

| Lot | Differenced coef (dB) | 95% CI | p | n |
|---|---|---|---|---|
| oakville-main | 0.599 | [-0.049, 1.247] | 0.06939 | 88 |
| oakville-south | 0.642 | [-0.049, 1.333] | 0.06789 | 73 |
| clarkson-main | -0.802 | [-1.344, -0.259] | 0.00429 | 88 |
| clarkson-north | -0.309 | [-0.856, 0.239] | 0.2657 | 88 |
| bronte-main | -0.374 | [-0.802, 0.054] | 0.08601 | 88 |
| bronte-south | -0.529 | [-1.001, -0.058] | 0.02836 | 88 |

**Pooled differenced:** weekend coef **-0.155 dB**, 95% CI [-0.554, 0.245], clustered two-sided p = 0.444, n = 513 rows, 87 date clusters. Permutation one-sided p = 0.3113.

![Control and differenced weekend coefficients with 95% CIs](t1b_weekend_coefs.png)

## Decision against each criterion

1. ❌ Controls show no significant weekend effect (all per-area p ≥ 0.05 and pooled p ≥ 0.05) — per-area p values: Bronte GO — Control 0.5862, Clarkson GO — Control 0.6845, Oakville GO — Control 0.006413; pooled p = 0.02115.
2. ❌ Differenced series passes all T1 criteria — pooled coef -0.155 dB < 0 with clustered p = 0.444 (< 0.01: ❌); permutation p = 0.3113 (< 0.01: ❌); 4/6 lots negative (≥ 5: ❌).

**Decision: INCONCLUSIVE — T1 stays INCONCLUSIVE**

## Deviations from the addendum

Report-text fixes only (no model or data change): after the first round-2 run, the script's hardcoded round-1 pixel counts were replaced with values computed from the control CSV (Oakville 140 → 71), and the plain-language reading's reference to the invalidated v1 parking area was removed. The script was re-run; the decision and all coefficients are unchanged.

## Reproducibility

- Spec: `t1b_spec_addendum.md`, committed to `zhenhuasun/go-transit-parking-sar` as `7b5a9730f47d6aea4e63e141177fe1c6fd79b2e0` (round 1) and `8bda63b7da552af2f91363d7141b4e10814f1531` (round 2, revised Oakville control) BEFORE any extraction or modelling in each round.
- Script: `t1b_weekend_test.py`, seed 42, 10,000 permutations. Rerun: `python3 t1b_weekend_test.py` from the repo root (uses only numpy, pandas, matplotlib). Extraction: `extract-control-vv.py`.
- `polygons/`, existing CSVs and existing scripts were not edited; all new outputs are in `calibration/t1b/`.

## Plain-language reading

The control areas are surfaces near each station that should not care what day of the week it is — warehouse and factory roofs. If the satellite or the processing itself produced a weekend pattern, the controls would show it too.
The test did not fully confirm that (see the decision above), so T1 is downgraded to INCONCLUSIVE: the weekend pattern in the lots may still be real, but this control check cannot rule out a non-car explanation.
This still does not measure occupancy: without ground-truth calibration, no dB difference converts into a number of cars or a percentage full.
## Appendix — post-hoc diagnostic on the revised Oakville control (NOT part of the decision)

The revised Oakville control (factory/warehouse roof, 93.3% building:industrial)
shows a weekend effect of its own: −0.885 dB, p = 0.0064. An independent
refit (numpy OLS, classical SE) gives −0.854 dB, SE 0.274, t = −3.11 — this
is not a pipeline bug.

Weekend-minus-weekday mean VV by year (all 9 summers, Jun–Aug):

| Year | Weekend − weekday (dB) |
|---|---|
| 2018 | −1.16 |
| 2019 | −0.86 |
| 2020 | −0.62 |
| 2021 | −0.70 |
| 2022 | −0.88 |
| 2023 | −2.07 |
| 2024 | −0.30 |
| 2025 | −0.21 |
| 2026 | −0.71 |

Unlike the invalidated v1 control, the effect is present in every year —
there is no clean break. Weekday level drifts from −5.5 dB (2018) to −7.6 dB
(2025), then jumps to −4.3 dB in 2026 (+3.3 dB in one year), which suggests
a surface change at the site in 2026. The 6.7% of the polygon that is not
building:industrial (~485 m²) is unaccounted for in OSM and could hold
vehicles (a yard, loading dock, or parking strip).

This appendix is a diagnostic only. It does not change the decision, and no
re-subsetting or re-testing follows from it without a new written spec.
