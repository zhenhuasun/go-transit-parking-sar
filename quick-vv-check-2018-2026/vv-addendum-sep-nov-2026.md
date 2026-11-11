# Addendum — Sep–Nov 2026 autumn check and per-scene charts

Date run: 2026-11-11. Data and method: identical to the summer 2018–2026
run — Microsoft Planetary Computer `sentinel-1-rtc`, VV gamma0 linear,
per-pixel `VV_dB = 10·log10(linear)`, ascending only, windowed COG reads,
same 6 user-drawn polygons. Script: `quick-vv-check-sep-nov-2026.py`
(copy of the summer script, window changed only). Log:
`run-log-sep-nov-2026.txt`.

**These autumn values are NOT part of the summer recovery index.**
They are a separate check, kept in a separate file
(`vv-by-lot-scene-sep-nov-2026.csv`, 60 rows = 10 acquisitions × 6 lots).
Autumn (Sep–Nov, ~18:10 EST, colder, wetter) is not comparable to summer
(Jun–Aug, ~19:10 EDT) as an annual mean — only the two construction
questions below are tested with them, and only against the summer 2026
and 2019 summer baselines as a rough reference.

## Sep–Nov 2026 results

10 acquisitions, all **ascending**, relative orbits 4 and 77, all
**Sentinel-1D** (no Sentinel-1A scenes in this window in the RTC
collection), at ~23:08–23:16 UTC = ~18:08–18:16 EST.
Dates: Sep 3, 8, 15, 20, 27; Oct 2, 9, 14, 21; Nov 2.
No read errors, 0 nulls in `mean_VV_dB`, n_pixels constant per lot
(739 / 82 / 360 / 325 / 575 / 319).

| Lot | Sep–Nov 2026 mean (n=10) | Summer 2026 mean (n=15) | 2019 summer mean | Sep–Nov minus summer 2026 |
|---|---|---|---|---|
| oakville-main | −10.21 ±0.78 | −10.10 ±0.75 | −10.19 | −0.11 |
| oakville-south | **−8.35 ±1.42** | **−8.37 ±1.37** | −9.42 | +0.02 |
| clarkson-main | −11.84 ±0.85 | −11.62 ±0.94 | −11.62 | −0.22 |
| clarkson-north | −9.93 ±0.92 | −9.35 ±0.83 | −9.68 | −0.58 |
| bronte-main | −10.65 ±0.81 | −10.73 ±0.74 | −10.71 | +0.08 |
| bronte-south | −10.43 ±0.77 | −10.75 ±0.94 | −10.51 | +0.32 |

Monthly split (Oakville): oakville-main Sep −10.19 (n=5), Oct −10.29 (n=4),
Nov −9.99 (n=1); oakville-south Sep −8.15 (n=5), Oct −8.51 (n=4),
Nov −8.65 (n=1). No other lot shows a Sep→Oct→Nov trend larger than
~0.6 dB.

Space-weighted station aggregates (linear-power mean, weights = spaces;
Clarkson North weight provisional — boundary unverified):
Oakville summer 2026 −9.84 vs autumn −9.98; Clarkson −10.66 vs −11.11;
Bronte −10.69 vs −10.56. All within ~0.5 dB of summer 2026 — no
station-level autumn step.

## Test 1 — Oakville South: did it return after the September completion?

**No. The radar does not support a return to normal after September.**

User ground truth: south-lot work completed in September 2026. If the
construction compound had been removed and the lot reopened, the
autumn mean should have dropped back toward the 2019 summer level
(−9.42 dB). It did not:

- Sep–Nov mean −8.35 dB — essentially identical to summer 2026
  (−8.37 dB), and 1.07 dB brighter than 2019.
- By month: Sep −8.15, Oct −8.51, Nov −8.65 (n=1) — no downward
  trend toward −9.42.
- Scene by scene (oakville-south, mean VV_dB):
  Sep 3 −8.77, Sep 8 −8.73, Sep 15 −5.01, Sep 20 −10.68,
  Sep 27 −7.56, Oct 2 −7.98, Oct 9 −8.91, Oct 14 −8.82,
  Oct 21 −8.34, Nov 2 −8.65.
  Only one scene (Sep 20, −10.68) is near the 2019 level; the other
  nine are −5.0 to −8.9 dB.
- Excluding the common-mode bright day Sep 15 (see below), the
  autumn mean is still −8.72 dB — 0.70 dB above 2019.
- Within-track check (removes the known rel-orbit offset):
  autumn rel 4 −7.87 vs rel 77 −9.05; summer 2019 rel 4 −8.90 vs
  rel 77 −10.01. Both tracks are still ~1.0 dB (rel 4) and ~1.0 dB
  (rel 77) brighter than 2019. So the failure to return is not a
  track-mix artefact.

Interpretation: either the compound / equipment was still present
through Oct–Nov, or the "completed" work left a surface that is
still bright in radar (e.g. fresh works, stored material, or a
changed surface), or the lot reopened but with a different
use. **The public record does not resolve this** — no Metrolinx/GO
source found confirming a September completion date for the south
lot (see parent verification 2026-11-11). The radar evidence says:
whatever changed in September, it did not restore the lot's
pre-construction backscatter by Nov 2. Keep Oakville South 2026
excluded from any demand series; do not treat Sep–Nov as a
"recovered" baseline. A further check (Dec 2026–Jan 2027 scenes,
or an on-site look) is needed before using this lot again.

## Test 2 — Oakville Main (north lot): any step from the Aug/Sep north work?

**No detectable lot-wide step — consistent with the work, not proof
against it.**

GO Transit page (updated Aug 7, 2026): 100 north-lot spots
inaccessible, +40 for Platform 1 work. 100 spots is ~3.7% of the
2,712-space Main Lot, so a lot-mean effect of at most a few tenths
of a dB is expected — below the scene scatter (SD 0.75–0.78 dB).

- Sep–Nov mean −10.21 vs summer 2026 −10.10 vs 2019 −10.19:
  differences ≤0.11 dB — no step.
- Monthly: Sep −10.19, Oct −10.29, Nov −9.99 (n=1) — flat.
- Scene by scene, Aug 27 (last summer scene, −9.51) through
  Nov 2 (−9.99): no break at the Aug/Sep boundary; values stay in
  the −9.6 to −11.1 dB range seen all summer, apart from the Sep 15
  bright day.
- Conclusion: the north work is too small a fraction of the Main
  Lot polygon to move its mean. The Main Lot series remains usable
  for demand, with an annotation that ~100 spots were closed from
  Aug 2026. A pixel-level (sub-lot) check would be needed to see
  the closed area itself — the lot mean cannot.

## Common-mode bright day: 2026-09-15

Every lot was ~2 dB brighter on Sep 15 than its autumn mean
excluding that day: bronte-main +2.27, bronte-south +2.06,
clarkson-main +2.19, clarkson-north +2.36, oakville-main +1.84,
oakville-south +3.70 dB. Most plausibly a wet surface after rain
(same pattern as 2026-08-22 in the summer run, +1.5–2.5 dB).
It lifts the Sep–Nov means by ~0.2 dB; excluding it does not
change either test conclusion (South −8.72, Main −10.39).

## Caveats

1. Autumn ≠ summer: different local time (~18:10 EST vs ~19:10
   EDT), colder/wetter surface, shorter days. Do not compare
   Sep–Nov means with summer means as if they were the same
   season, and do not add them to the summer recovery index.
2. All 10 autumn acquisitions are Sentinel-1D; summers 2018–2024
   are all Sentinel-1A, summer 2026 is mixed (10 S1D / 5 S1A).
   No systematic S1D offset was found in the large lots
   (≤0.31 dB in summer 2026), but the autumn sample has no S1A
   scenes to compare against.
3. Oakville South remains the weakest lot (82 px, SD 1.42 dB in
   autumn). Its rel 4 minus rel 77 gap persists in autumn
   (+1.18 dB), same as summer 2026 (+1.46 dB).
4. Clarkson North boundary still unverified (52.3 m²/space);
   its space weight in the station aggregate is provisional.
5. Polygons include internal roads (conservative lower bound on
   dB changes), as in the summer run. RTC gamma0 ≠ SARpanel
   sigma0; no ground-truth calibration — no occupancy percentages.

## Per-scene charts (also in this folder)

- Per lot (6): `vv-per-scene-<lot>.png` — every acquisition
  2018–2026, summer circles connected in date order, autumn
  squares Sep–Nov 2026 as a separate series (not connected to
  summer), dashed grey line = lot's 2019 summer mean. Oakville
  South chart shades the Apr–Sep 2026 construction compound.
- Per station (3): `vv-per-scene-station-<station>.png` — both
  lots of the station on shared axes, plus a black dashed
  space-weighted station aggregate (linear-power mean,
  weights = spaces; Clarkson North provisional). Dotted lines =
  each lot's 2019 summer mean.
- Script: `make-per-scene-charts.py`. Verification: the script
  asserts summer 2019/2020/2024 means match
  `vv-annual-summary-2018-2026.csv` exactly for all 6 lots
  before plotting; all 9 PNGs were visually checked — points,
  labels and legends inside the frame (one overlap on the
  Oakville South autumn/construction labels was found and fixed
  by moving the autumn label to the bottom of the band).
- Note on the charts: summer points are connected across the
  Sep–May gaps between summers, because they are plotted in
  date order. Those long lines are not measurements — no scenes
  exist in winter in this dataset by design (summer-only).

## Bottom line

- South lot: **did not return to normal after September** in the
  radar data (Sep–Nov −8.35 dB vs 2019 −9.42 dB). The September
  completion claim is not supported by the radar; keep 2026
  excluded for this lot.
- North/Main lot: **no detectable step** from the Aug/Sep north
  work at lot-mean level, as expected for ~100 of 2,712 spots.
  The Main Lot series stays usable, annotated.
- Other 4 lots: Sep–Nov within ~0.6 dB of summer 2026 — no
  autumn anomaly.
