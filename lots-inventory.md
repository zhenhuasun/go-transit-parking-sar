# GO Parking SAR Pilot — Three-Station Outdoor Lot Inventory

Date: 2026-11-07
Scope: Oakville GO, Clarkson GO, Bronte GO, 2018–2026 (confirmed by user 2026-11-07)
Rule: **one polygon per outdoor lot; indoor parking garages excluded** — SAR cannot see cars inside a building.

## 1. Oakville GO — 214 Cross Ave, Oakville

GO official space counts: Main Lot 2712, Parking Garage 1398, South Lot 291.

| Lot | Type | Spaces | Centroid (approx.) | SAR handling |
|---|---|---|---|---|
| Main Lot | Outdoor | 2712 | 43.45612, -79.68378 | ✅ Main analysis target. Note: 148–222 Cross Ave is three adjoining large outdoor lots; merge into one polygon first, then decide whether to split. |
| South Lot | Outdoor | 291 | 43.45555, -79.68223 | ⚠️ Small, few pixels, large speckle noise; run it, but weight it low. Centroid is very close to Main Lot, the geocoder may be inaccurate — verify against satellite imagery before drawing the polygon. |
| Parking Garage | Indoor structure | 1398 | To verify (geocoder wrongly returned Church St Parkade, unusable) | ❌ Excluded. About 32% of station spaces; VV cannot see occupancy inside the structure at all. |

## 2. Clarkson GO — 1110 Southdown Rd, Mississauga

| Lot | Type | Spaces | Centroid (approx.) | SAR handling |
|---|---|---|---|---|
| Main Lot | Outdoor | 1274 (Parkopedia) | 43.5123, -79.63185 | ✅ Main south lot, extending south from the east side of the station building. |
| North Lot | Outdoor | **627 (GO official, verified 2026-11-08)** | 43.51393, -79.63511 (2070 Bromsgrove Rd) | ✅ North side, across the tracks; count separately from Main Lot. Sources refer to north parking lots (plural), so the polygon may cover more than one lot — check while drawing. |
| Garage | Indoor structure | 1573 (GO official) | Same geocoder coordinates as Main Lot, not credible, to verify | ❌ Excluded. 45.3% of station spaces, the biggest confounder: in winter / rain, cars move into the garage, outdoor VV falls, but total station occupancy may not have fallen. |

Note (corrected 2026-11-08): GO official now lists North Lot **627** (not Parkopedia's 1020); Main 1274 + North 627 + Garage 1573 = **3474**, exactly matching another source's station total, so Parkopedia's 1020 is superseded. **But there is an unresolved contradiction**: the user-drawn North Lot polygon is 32,796 m², which is 52.3 m²/space at 627 spaces, far above the 27–32 m²/space of the other 5 lots; at 1020 it would be 32.2. The polygon may include asphalt beyond the North Lot (or GO's 627 may be only part of it). The VV mean itself is unaffected by the space count, but the North Lot's actual boundary must be verified before any space-weighted / station-total calculation.

## 3. Bronte GO — 2104 Wyecroft Rd, Oakville

| Lot | Type | Spaces | Centroid (approx.) | SAR handling |
|---|---|---|---|---|
| Main / East Lot | Outdoor | 1824 (Parkopedia) | 43.41864, -79.72498 | ✅ Main north lot. Planning documents call it East Parking Lot, U-shaped around the buildings at 2070/2100 Wyecroft. |
| South Lot | Outdoor | 1149 (Parkopedia) | 43.416254, -79.721525 (2135 Speers Rd) | ✅ South side, across the tracks, entered from Speers Rd; count separately from the north side. |
| Parking Garage | — | — | — | No reliable source confirms an indoor structure at Bronte; treated as no garage for now, to be added if the user confirms one. |

Note: Wikipedia lists Bronte station at 2424 spaces, inconsistent with Parkopedia's two lots totalling 2973; the South Lot was about 175 spaces in 2011, with a build target of 300, plus 200 more added in 2016, so space counts have changed over time. **For a long time series, lot boundaries / space counts themselves change — annotate expansion years on the time axis, do not treat them as fixed.**

## To do (next steps)

1. User confirms the time range (confirmed 2018–2026, 2026-11-07).
2. Draw a precise polygon for each of the 6 outdoor lots from satellite imagery / OSM (no bounding boxes, to avoid including tracks, station buildings, roads and trees).
3. Verify the exact locations of Oakville Garage and Clarkson Garage, for exclusion only (draw a mask, not for analysis).
4. Generate the SARpanel config: 6 polygons × 1 date range; one VV time series per lot, plus one station-level outdoor total (space-weighted).
5. Annotate known change points: Bronte South Lot expansion, Clarkson / Oakville construction / closure periods (if any).

## Sources and confidence

- GO official Oakville space counts: Main 2712 / Garage 1398 / South 291.
- Clarkson Main 1274 / Garage 1573 and Bronte's two lots 1824 / 1149 were verified against GO official in the 2026-11-08 network inventory; Clarkson North was corrected from Parkopedia's 1020 to GO official 627, see the note above.
- Bronte South Lot coordinates 43.416254, -79.721525 come from a listing; all other centroids come from the geocoder, are approximate only, and are not polygons.
