# GO Parking SAR Pilot — User-Drawn Polygon Validation Report

Date: 2026-11-07 (addendum 2026-11-08 below)

## 2026-11-08 addendum: Clarkson North space-count correction

After the network inventory checked GO official, Clarkson North Lot was corrected from Parkopedia's 1020 to GO official **627** (Main 1274 + North 627 + Garage 1573 = 3474). At 627, this polygon's area ratio is 32,796 / 627 = **52.3 m²/space**, which no longer falls in the 27–32 range of the table below. The polygon geometry itself is unchanged and the validation conclusions (closed, no self-intersections, no overlaps) still hold, but the North Lot boundary needs re-checking before any space-weighting: it may include asphalt beyond the North Lot, or GO's 627 may be only one of several north-side lots. The other 5 lots' area ratios are unaffected.
File: `polygons-user.geojson` (exported by the user from the editable satellite map; original file `workspace/user/files/go-parking-lots-user.geojson`)
Time range: 2018-01-01 to 2026-11-07

## Validation result: all passed

- 6 features, all Polygon, all closed, no self-intersections (edge-crossing check), no overlaps between the 6 lots (edge-crossing check).
- Each lot's area / space ratio is 27–32 m²/space, very consistent, indicating the polygons trace real parking-lot asphalt rather than surrounding roads / buildings. The draft rectangles' ratios were 47–70 m²/space, clearly too large.

| Lot | Vertices | Area | Spaces | m²/space | Centroid shift (vs draft) |
|---|---|---|---|---|---|
| Oakville GO — Main Lot | 24 | 74,151 m² | 2712 | 27.3 | 234 m |
| Oakville GO — South Lot | 14 | 8,215 m² | 291 | 28.2 | 208 m |
| Clarkson GO — Main Lot | 19 | 36,264 m² | 1274 | 28.5 | 156 m |
| Clarkson GO — North Lot | 19 | 32,796 m² | 1020 | 32.2 | 52 m |
| Bronte GO — Main / East Lot | 22 | 58,212 m² | 1824 | 31.9 | 150 m |
| Bronte GO — South Lot | 13 | 31,869 m² | 1149 | 27.7 | 44 m |

## Key corrections (vs draft)

- **Oakville South Lot (former red placeholder box) resolved**: centroid moved about 208 m south, now south of the tracks (43.45373, -79.68281), area 8,215 m² / 291 spaces = 28.2 m²/space, consistent with the other lots. No longer a placeholder.
- **Oakville Main Lot**: no longer a rectangle; traced along the actual boundary with 24 points, area shrank from the draft 126,783 m² to 74,151 m².
- **Bronte Main / East Lot**: 22 points, area shrank from 128,355 m² to 58,212 m², U-shape traced along the actual boundary.
- **Clarkson Main / North, Bronte South**: areas about half the draft rectangles, matching the real lot shapes.

## Next steps (SARpanel)

1. Run `plan` first: `python -m sarpanel.cli plan configs/go_parking_2018_2026.yaml`, to see how many scenes 2018–2026 holds and how large the download is, before deciding whether to run it all.
   - Note: 9 years, 3 stations, 6 small lots — expect plenty of scenes; the README recommends a short trial run first, then expanding to the full range.
   - Recommended: trial a short window first (e.g. 2019-06-01 to 2019-08-31) to verify the workflow, then run the full range.
2. Prerequisites (README steps 3–4): ESA SNAP installed (`gpt -h` works), NASA Earthdata account + token (`EARTHDATA_TOKEN`).
3. Config file: `sarpanel-go-parking-2018-2026.yaml`, aoi.source points to `polygons-user.geojson`, id_column is `id`, target_crs is UTM 17N `EPSG:32617`, spacing 10 m, VV+VH, GRD.
