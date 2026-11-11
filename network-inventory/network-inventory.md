# GO Transit network parking inventory — GO API + OSM cross-check

Date: 2026-11-08. Inventory only — no polygons were drawn, no SARpanel run, no VV extraction.
Scope: all GO **rail** stations in the current GTFS feed. GO bus-only terminals / park-and-ride lots were excluded from the rail totals (they were not inventoried).

## Method and sources

1. **Station list (71 rail stations, 7 lines)** — GO Transit GTFS feed, `GO-GTFS.zip`, feed version 20261104 (2026-11-04–2026-11-27), downloaded from Metrolinx's open-data URL (`assets.metrolinx.com/.../GO-GTFS.zip`). Rail stations = stops served by route_type 2 (LW, LE, MI, KI, BR, RH, ST), with line(s) per station taken from `stop_times.txt` + `trips.txt` + `routes.txt`; coordinates from `stops.txt`. This gives 71 stations (the often-quoted "64 stations" is older; the current feed has 71, including Stratford, St. Catharines and seasonal Niagara Falls).
2. **Parking per station (GO official)** — the GO Transit public API `Stop/Details` is **dead**: `api.gotransit.com/v2/Stop/Details` now 302-redirects to a maintenance page, and `api.metrolinx.com/external/go/stations/` returns 404. No key was used (none is recorded, and the task forbids asking for one). Fallback used instead, and it worked for all 71 stations: the public station-details page `gotransit.com/en/find-a-station-or-stop/<code>/station-details`, scraped 2026-11-08, parsing the "Station Parking Numbers" list (`<li>Name: N</li>`). Source per row in the CSVs: `gotransit_page` for every station.
3. **OSM cross-check** — Overpass **failed from this VM on every endpoint tried** (overpass-api.de: HTTP 502 then timeout; mirrors overpass.kumi.systems, overpass.private.coffee, overpass.nchc.org.tw: timeouts). Fallback used instead: Geofabrik Ontario extract `ontario-261107.osm.pbf` (2026-11-07, 979 MB), parsed locally with pyosmium (two passes, no Overpass). All `amenity=parking` features in Ontario were extracted: 95,280 features (2,157 nodes, 92,262 ways, 861 relations), with per-way area computed by shoelace (validated against the pilot polygons to within 0.3%).
   - Key OSM finding: **raw OSM feature counts are not lot counts.** At Oakville GO, OSM has 67 parking features within 800 m for 3 GO lots — lots are mapped as many small fragments (aisles/sections), and the same lot is often mapped both as one big polygon and as subdivided sections. Counting features therefore overstates lots by ~20×. The cross-check below does **not** compare feature counts to lot counts.
   - Metrics used instead (all within 800 m of the GTFS station centroid): `osm_go_operator_area_m2` = summed area of surface parking ways tagged `operator=GO Transit`; `osm_area_ratio` = that area ÷ (GO outdoor spaces × 30 m²/space — the pilot's validated 27–32 m²/space); `osm_garage_present` = any `parking=multi-storey/underground/rooftop` feature; `osm_surface_area_m2` = union area of *all* surface parking ways in the radius (an upper bound — it includes non-GO lots such as plazas, so it is **not** used for matching).
   - `osm_go_match`: `match` = operator-area ratio 0.5–1.5 **and** garage presence agrees with GO; `partial-garage-mismatch` = area ratio in range but garage presence disagrees; `mismatch-area` = GO-operator area exists but ratio outside 0.5–1.5; `present-unverified` = OSM parking exists within 300 m but no GO-operator tags to confirm it is the GO lot; `missing` = no OSM parking within 300 m (none occurred); `n/a-no-go-parking` = GO lists no free parking.
   - Validation of the method on the pilot: Oakville ratio 0.71, Clarkson 1.17, Bronte 0.94 — all `match`, against user-drawn ground-truth polygons.
4. **Classification** — a GO lot is `outdoor` unless its name contains "Garage"/"Structure" (`garage`). Reserved/carpool/accessible/ZipCar/scooter entries are **not** separate lots: "Zip Car" (1–2 spaces), "Accessible Parking Spaces", "Scooters and Motorbikes", "No Overnight Parking" (0) are recorded in `lots.csv` as `other-excluded` and excluded from station totals. Duplicate names on a GO page (Weston: three "Main Lot" entries 131/127/0; Brampton: two "South Lot" entries 161/270) are kept as separate lot sections and flagged.

## Network totals (GO official station pages, 2026-11-08)

| | |
|---|---|
| Rail stations in GTFS feed | **71** (7 lines) |
| Stations with free on-site parking listed | **57** |
| Stations with no free parking listed | **14** |
| GO lots counted (outdoor + garage) | **96** (86 outdoor + 10 garage) |
| Total spaces (free lots listed) | **69,338** |
| Outdoor spaces | **57,606** (83.1%) |
| Garage (indoor) spaces | **11,732** (16.9%) |
| Stations with a garage | 10 |
| Mean outdoor spaces per parking station | ~1,011 |

Per-line totals (stations counted once per line they serve, so Scarborough LE+ST and Union's 7 lines double-count in this table; network total is 69,338):

| Line | Stations | Outdoor | Garage | Total |
|---|---|---|---|---|
| Lakeshore West (LW) | 16 | 14,526 | 3,707 | 18,233 |
| Lakeshore East (LE) | 10 | 11,167 | 4,462 | 15,629 |
| Milton (MI) | 9 | 8,746 | 1,500 | 10,246 |
| Kitchener (KI) | 14 | 7,340 | 0 | 7,340 |
| Stouffville (ST) | 11 | 6,002 | 451 | 6,453 |
| Barrie (BR) | 11 | 5,566 | 847 | 6,413 |
| Richmond Hill (RH) | 7 | 4,884 | 765 | 5,649 |

Note on the total: older GO fact sheets quote ~74,000–80,000 spaces (e.g. April 2019: 75,184 regular + 5,197 reserved). Our 69,338 counts only the free lots listed on current station pages — reserved-only stations contribute 0, and the count is a 2026-11-08 snapshot, not a 2019 figure. Do not mix the two.

## Top-5 largest outdoor lots (single lot, GO official)

| Lot | Spaces |
|---|---|
| Oakville GO — Main Lot | 2,712 |
| Durham College Oshawa GO — Main Lot | 2,390 |
| Bronte GO — Main Lot | 1,824 |
| Appleby GO — North Lot | 1,742 |
| Bramalea GO — Main Lot | 1,724 |

## OSM cross-check result

| osm_go_match | Stations |
|---|---|
| match | 18 |
| partial-garage-mismatch | 8 |
| mismatch-area | 12 |
| present-unverified | 19 |
| n/a-no-go-parking | 14 |
| missing | 0 |

- 40 of 71 stations have at least one GO-operator-tagged OSM parking way within 800 m; the other 31 stations' GO lots are either untagged by operator or absent from OSM.
- **No station with GO parking is missing from OSM entirely** — every one of the 57 has OSM parking within 300 m. OSM coverage is complete in the presence sense; the gaps are in operator tagging, not in mapping.
- The pilot stations all validate as `match` (Oakville 0.71, Clarkson 1.17, Bronte 0.94).

## No free on-site parking (14 stations)

GO station page states "Free customer parking is not available at this station" for all 14. (Reserved/paid parking may exist separately — e.g. Kipling, Kitchener and Kennedy have paid/reserved parking, but no free lot numbers are listed.)

Bloor GO, Danforth GO, Downsview Park GO, Exhibition GO, Hamilton GO Centre, Kennedy GO, Kipling GO, Kitchener GO, Mount Dennis GO, Niagara Falls GO, Oriole GO, St. Catharines GO, Stratford GO, Union Station GO.

Note: this list differs slightly from older published lists (e.g. York University GO no longer appears — it is not a rail stop in the current GTFS feed; Guelph Central GO *does* list a 15-space Main Lot now).

## Garage share > 30% (outdoor VV understates total station occupancy here)

| Station | Garage share | Outdoor | Garage |
|---|---|---|---|
| Bloomington GO | 100% | 0 | 765 |
| Centennial GO | 100% | 0 | 451 |
| Erindale GO | 68.4% | 693 | 1,500 |
| Aurora GO | 61.3% | 535 | 847 |
| Pickering GO | 60.7% | 1,085 | 1,673 |
| Clarkson GO | 45.3% | 1,901 | 1,573 |
| Ajax GO | 44.5% | 1,694 | 1,356 |
| Burlington GO | 35.0% | 1,367 | 736 |
| Whitby GO | 33.9% | 2,797 | 1,433 |
| Oakville GO | 31.8% | 3,003 | 1,398 |

**Bloomington and Centennial have no outdoor parking at all** — their entire listed capacity is a structure/garage, so a VV time series is impossible there; exclude them from any VV scaling.

## Small lots — weak VV signal (< 200 spaces, 18 lots)

Acton Main 46; Allandale Waterfront Main 160; Brampton Innovation District South Lot 161; Cooksville East Lot 119; Guelph Central Main 15; King City North (Partly Reserved) 69, South (Fully Reserved) 122, Station St (West Lot) 155, Church Lot (Open) 50; Long Branch Main 9; Markham East 159, Main 84, West 167; Stouffville Main 83; West Harbour Main 46; Weston Main 131 / 127 / 0. Same caveat as pilot Oakville South (82 px): treat as supporting evidence only, or aggregate to station level. Stations whose *entire* outdoor capacity is < 200 spaces (Acton 46, Guelph Central 15, Long Branch 9, West Harbour 46, Stouffville 376 is above) are poor VV candidates on their own.

## Conflicts and data-quality flags

- **Clarkson GO — RESOLVED.** Pilot inventory cited Parkopedia North Lot 1,020 vs another source totalling 3,474. GO official page now lists North Lot **627**, Main 1,274, Garage 1,573 = **3,474 exactly**. The Parkopedia North figure is superseded; pilot lots.csv/memory should be corrected to 627.
- **Bronte GO — confirmed by GO official.** Pilot figures came from Parkopedia (Main 1,824 / South 1,149, Wikipedia total 2,424 conflicting). GO official page lists Main 1,824 / South 1,149 — source upgraded from secondary to `gotransit_page`. (The Wikipedia 2,424 total is stale/superseded.)
- **Oakville GO — exact match** to pilot ground truth (Main 2,712 / Garage 1,398 / South 291).
- **Pickering GO — conflict, unresolved.** GO page total 2,758 (Main 585 + Structure 1,673 + North 500) vs an older (2015) secondary source of ~3,600 spaces (−23%). GO page is primary, but verify whether a lot is missing from the page before using Pickering.
- **Long Branch GO — suspect page figure.** GO page lists Main Lot **9** spaces, but OSM shows a large GO-operator surface lot nearby (operator-area ratio 19.4). The page figure looks incomplete — verify before using Long Branch.
- **Port Credit GO — only one lot listed.** GO page lists North Lot 350 only; no Main Lot. Operator-area ratio 1.71 suggests more GO parking exists than the page lists — verify.
- **Whitby GO — weak OSM check.** OSM GO-operator area is only 9% of expected (ratio 0.09); Whitby lots are mostly untagged by operator in OSM, so the OSM cross-check is weak here despite OSM parking being present.
- **Weston GO — duplicate names + a 0-space entry.** Three separate "Main Lot" entries (131/127/0) kept as separate sections; the 0-space entry is flagged (possibly closed/under construction).
- **Brampton Innovation District GO — duplicate names.** Two separate "South Lot" entries (161/270) kept as separate sections.
- **King City GO — reserved lots.** All five lots carry reserved annotations (fully/partly reserved, church lot); they are outdoor surface lots, counted as such, with the reserved status noted per lot.

## Per-station summary

`garage%` is garage ÷ total. `OSM` is `osm_go_match`. Full detail (coordinates, lot-by-lot, OSM names) is in `stations.csv` / `lots.csv`.

| Station | Line | Outdoor | Garage | Total | Garage% | OSM |
|---|---|---|---|---|---|---|
| Acton GO | KI | 46 | 0 | 46 | 0 | present-unverified |
| Agincourt GO | ST | 337 | 0 | 337 | 0 | present-unverified |
| Ajax GO | LE | 1,694 | 1,356 | 3,050 | 44.5 | present-unverified |
| Aldershot GO | LW | 1,639 | 0 | 1,639 | 0 | match |
| Allandale Waterfront GO | BR | 160 | 0 | 160 | 0 | mismatch-area |
| Appleby GO | LW | 2,814 | 0 | 2,814 | 0 | match |
| Aurora GO | BR | 535 | 847 | 1,382 | 61.3 | match |
| Barrie South GO | BR | 615 | 0 | 615 | 0 | match |
| Bloomington GO | RH | 0 | 765 | 765 | 100 | present-unverified |
| Bloor GO | KI | 0 | 0 | 0 | — | n/a-no-go-parking |
| Bradford GO | BR | 355 | 0 | 355 | 0 | present-unverified |
| Bramalea GO | KI | 2,370 | 0 | 2,370 | 0 | mismatch-area |
| Brampton Innovation District GO | KI | 1,133 | 0 | 1,133 | 0 | partial-garage-mismatch |
| Bronte GO | LW | 2,973 | 0 | 2,973 | 0 | match |
| Burlington GO | LW | 1,367 | 736 | 2,103 | 35.0 | present-unverified |
| Centennial GO | ST | 0 | 451 | 451 | 100 | present-unverified |
| Clarkson GO | LW | 1,901 | 1,573 | 3,474 | 45.3 | match |
| Confederation GO | LW | 203 | 0 | 203 | 0 | present-unverified |
| Cooksville GO | MI | 1,688 | 0 | 1,688 | 0 | mismatch-area |
| Danforth GO | LE | 0 | 0 | 0 | — | n/a-no-go-parking |
| Dixie GO | MI | 991 | 0 | 991 | 0 | partial-garage-mismatch |
| Downsview Park GO | BR | 0 | 0 | 0 | — | n/a-no-go-parking |
| Durham College Oshawa GO | LE | 2,390 | 0 | 2,390 | 0 | present-unverified |
| East Gwillimbury GO | BR | 642 | 0 | 642 | 0 | match |
| Eglinton GO | LE | 837 | 0 | 837 | 0 | partial-garage-mismatch |
| Erindale GO | MI | 693 | 1,500 | 2,193 | 68.4 | match |
| Etobicoke North GO | KI | 687 | 0 | 687 | 0 | present-unverified |
| Exhibition GO | LW | 0 | 0 | 0 | — | n/a-no-go-parking |
| Georgetown GO | KI | 648 | 0 | 648 | 0 | match |
| Gormley GO | RH | 871 | 0 | 871 | 0 | present-unverified |
| Guelph Central GO | KI | 15 | 0 | 15 | 0 | present-unverified |
| Guildwood GO | LE | 886 | 0 | 886 | 0 | match |
| Hamilton GO Centre | LW | 0 | 0 | 0 | — | n/a-no-go-parking |
| Kennedy GO | ST | 0 | 0 | 0 | — | n/a-no-go-parking |
| King City GO | BR | 636 | 0 | 636 | 0 | mismatch-area |
| Kipling GO | MI | 0 | 0 | 0 | — | n/a-no-go-parking |
| Kitchener GO | KI | 0 | 0 | 0 | — | n/a-no-go-parking |
| Langstaff GO | RH | 1,547 | 0 | 1,547 | 0 | mismatch-area |
| Lisgar GO | MI | 714 | 0 | 714 | 0 | match |
| Long Branch GO | LW | 9 | 0 | 9 | 0 | mismatch-area |
| Malton GO | KI | 697 | 0 | 697 | 0 | partial-garage-mismatch |
| Maple GO | BR | 1,344 | 0 | 1,344 | 0 | partial-garage-mismatch |
| Markham GO | ST | 410 | 0 | 410 | 0 | partial-garage-mismatch |
| Meadowvale GO | MI | 1,652 | 0 | 1,652 | 0 | match |
| Milliken GO | ST | 661 | 0 | 661 | 0 | present-unverified |
| Milton GO | MI | 1,468 | 0 | 1,468 | 0 | present-unverified |
| Mimico GO | LW | 221 | 0 | 221 | 0 | present-unverified |
| Mount Dennis GO | KI | 0 | 0 | 0 | — | n/a-no-go-parking |
| Mount Joy GO | ST | 1,325 | 0 | 1,325 | 0 | match |
| Mount Pleasant GO | KI | 1,486 | 0 | 1,486 | 0 | mismatch-area |
| Newmarket GO | BR | 271 | 0 | 271 | 0 | present-unverified |
| Niagara Falls GO | LW | 0 | 0 | 0 | — | n/a-no-go-parking |
| Oakville GO | LW | 3,003 | 1,398 | 4,401 | 31.8 | match |
| Old Cummer GO | RH | 462 | 0 | 462 | 0 | present-unverified |
| Old Elm GO | ST | 654 | 0 | 654 | 0 | match |
| Oriole GO | RH | 0 | 0 | 0 | — | n/a-no-go-parking |
| Pickering GO | LE | 1,085 | 1,673 | 2,758 | 60.7 | match |
| Port Credit GO | LW | 350 | 0 | 350 | 0 | mismatch-area |
| Richmond Hill GO | RH | 2,004 | 0 | 2,004 | 0 | mismatch-area |
| Rouge Hill GO | LE | 853 | 0 | 853 | 0 | mismatch-area |
| Rutherford GO | BR | 1,008 | 0 | 1,008 | 0 | mismatch-area |
| Scarborough GO | LE/ST | 625 | 0 | 625 | 0 | partial-garage-mismatch |
| St. Catharines GO | LW | 0 | 0 | 0 | — | n/a-no-go-parking |
| Stouffville GO | ST | 376 | 0 | 376 | 0 | present-unverified |
| Stratford GO | KI | 0 | 0 | 0 | — | n/a-no-go-parking |
| Streetsville GO | MI | 1,540 | 0 | 1,540 | 0 | match |
| Union Station GO | all | 0 | 0 | 0 | — | n/a-no-go-parking |
| Unionville GO | ST | 1,614 | 0 | 1,614 | 0 | match |
| West Harbour GO | LW | 46 | 0 | 46 | 0 | present-unverified |
| Weston GO | KI | 258 | 0 | 258 | 0 | partial-garage-mismatch |
| Whitby GO | LE | 2,797 | 1,433 | 4,230 | 33.9 | mismatch-area |

## Recommendation: scaling the VV work

- **Best first expansion — Lakeshore West full line (16 stations).** Same orbit tracks as the pilot, largest outdoor capacity (14,526 spaces), and 5 of its 16 stations already validate as OSM `match`. Skip Bloomington/Centennial equivalents here — LW has no 100%-garage station. Watch: Clarkson/Oakville garage share 32–45% (outdoor-only caveat already known), Long Branch needs its 9-space figure verified first, Port Credit's single listed lot needs verification.
- **Best next lines — Lakeshore East, then Milton.** LE has the second-largest outdoor capacity (11,167) and the most garage-heavy stations (Ajax, Pickering, Whitby) — good for testing the garage-share correction, but Pickering's total needs verification first. MI is almost all-outdoor (only Erindale has a garage, 68% there) and 8,746 outdoor spaces.
- **Least suitable — Kitchener line for VV despite 7,340 outdoor spaces:** 4 of its 14 stations have no free parking at all (Bloor, Kitchener, Mount Dennis, Guelph Central's 15 spaces), and several remaining lots are small (Acton 46, Weston 258 split three ways). Richmond Hill is small (7 stations, 4,884 outdoor) and Barrie/Stouffville are mixed.
- **Exclude outright from VV:** Bloomington GO and Centennial GO (100% garage — no outdoor signal exists), the 14 no-free-parking stations, and the sub-200-space lots unless aggregated to station level.
- **Before drawing any new polygons:** resolve the three flagged page figures (Long Branch 9, Port Credit single lot, Pickering 2,758 vs ~3,600) and correct the pilot Clarkson North figure (1,020 → 627) in the pilot inventory/memory.

## Files

- `stations.csv` — one row per rail station (71 rows) with GO lots/spaces, garage share, and OSM cross-check columns.
- `lots.csv` — one row per GO lot (107 rows: 86 outdoor, 10 garage, 11 other-excluded).
- `network-inventory.md` — this file.
- `inventory.py` — consolidated reproducible script (GTFS download → rail stations → GO page scrape → classification → OSM merge → CSVs). The OSM extract it reads (`work/osm_parking_ontario.json`, `work/osm_union_area.json`) was produced by `work/parse_osm3.py` + `work/union_area.py` from the Geofabrik Ontario extract (`work/ontario.osm.pbf`, 2026-11-07, 979 MB); intermediate scripts and raw scrape output are in `work/` (`scrape_go.py`, `build_go.py`, `go_parking_raw.json`, `empty_stations.json`, `merge2.py`). **Reproducibility verified 2026-11-08:** a fresh `python3 inventory.py` run (re-scraping all 71 GO pages) reproduced `stations.csv` and `lots.csv` byte-identically (md5 `3d8996caa2acd6126382afb2d2bbca35` / `e89cdce1af0183b93397fd253ef3d669`). Note the first verification attempt caught three bugs in `inventory.py` (the "free parking not available" sentence fires on every station page so must be gated on zero parsed lots; two lot-note wordings; hand-added station notes for Pickering/Whitby/Long Branch/Weston/Brampton not yet carried over) — all fixed in the script before the verifying run.
- Pilot files outside this folder were not modified.

## Limitations

- Space counts are a **2026-11-08 snapshot of GO station pages**; lots expand, close for construction, or change reserved status over time (the pilot already documented Bronte South expansions). A 2018–2026 VV series must annotate such changes per station, not assume current capacities held for the whole period.
- GO station pages list **free** lots; reserved/paid-only capacity at the 14 no-free-parking stations is not counted, so network totals understate total parking where paid parking exists.
- OSM cross-check is a **coverage/presence check, not a lot-count check** (see Method §3). `osm_go_match=match` means OSM's GO-operator-tagged area is consistent with GO's spaces; it does not verify individual lot boundaries.
- Station coordinates are GTFS stop points, not lot centroids; the 800 m radius is a search radius, not a lot boundary.
