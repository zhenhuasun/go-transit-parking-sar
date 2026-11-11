# network-inventory/scripts

Intermediate scripts from the 2026-11-08 network inventory, kept for
provenance. They were run from a working directory containing the raw
downloads (not in this repo — see the main README):

- `ontario.osm.pbf` — Geofabrik Ontario extract, 2026-11-07 (~979 MB)
- `GO-GTFS.zip` — GO Transit GTFS feed, version 20261104, plus the
  extracted GTFS tables

The scripts read those files by relative name (`ontario.osm.pbf`,
`osm_parking_ontario.json`, …), so run them from a directory holding the
downloads. The final outputs, `stations.csv` and `lots.csv`, are reproduced
by the top-level `inventory.py` in `network-inventory/` and are already
included in this repo.

- `scrape_go.py` — scrape parking numbers from GO station-details pages
- `build_go.py` — derive the rail-station list from the GTFS feed
- `parse_osm.py` / `parse_osm2.py` / `parse_osm3.py` — successive OSM
  parsing passes (parse_osm3.py is the one whose output was used)
- `merge.py` / `merge2.py` — merge GO and OSM results
- `crosscheck.py`, `cluster_test.py`, `union_area.py` — diagnostics
