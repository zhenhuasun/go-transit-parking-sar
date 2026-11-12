#!/usr/bin/env python3
"""Candidate control-roof shortlist near Oakville GO.

Scans the local Ontario OSM extract for large building footprints near
Oakville GO station and ranks them as T1b control-roof candidates.

Criteria (a priori, no VV data used):
- large footprint (edge pixels are a smaller share of the total);
- industrial / warehouse / commercial (flat roofs);
- no overlap with a GO parking lot or an OSM parking area.

Output: printed table + candidates.geojson (building footprints).
Run: python3 find-roof-candidates.py [pbf_path]
"""
import json
import math
import sys

import osmium
from shapely.geometry import Polygon, shape

PBF = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/hatch/workspace/go-parking-sarpanel/network-inventory/work/ontario.osm.pbf"
LOTS = "/home/hatch/workspace/go-transit-parking-sar/polygons/polygons-user.geojson"
OUT = "/home/hatch/workspace/go-transit-parking-sar/calibration/t1b/roof-candidates.geojson"

# bbox around Oakville GO (station ~43.45425, -79.68491)
MINLON, MINLAT, MAXLON, MAXLAT = -79.72, 43.43, -79.65, 43.48
STATION = (43.45425, -79.68491)  # lat, lon


def area_m2(geom):
    coords = list(geom.exterior.coords)
    lat0 = sum(c[1] for c in coords) / len(coords)
    kx = 111320 * math.cos(math.radians(lat0))
    ky = 110540
    pts = [(c[0] * kx, c[1] * ky) for c in coords]
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def perim_m(geom):
    coords = list(geom.exterior.coords)
    lat0 = sum(c[1] for c in coords) / len(coords)
    kx = 111320 * math.cos(math.radians(lat0))
    ky = 110540
    pts = [(c[0] * kx, c[1] * ky) for c in coords]
    return sum(math.hypot(x2 - x1, y2 - y1)
               for (x1, y1), (x2, y2) in zip(pts, pts[1:]))


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class Handler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.buildings = []   # (tags, [node refs])
        self.parkings = []    # [node refs]

    def node(self, n):
        if MINLON <= n.location.lon <= MAXLON and MINLAT <= n.location.lat <= MAXLAT:
            self.nodes[n.id] = (n.location.lon, n.location.lat)

    def way(self, w):
        tags = dict(w.tags)
        if "building" in tags:
            refs = [nd.ref for nd in w.nodes]
            if len(refs) >= 4 and refs[0] == refs[-1]:
                self.buildings.append((tags, refs))
        elif tags.get("amenity") == "parking":
            refs = [nd.ref for nd in w.nodes]
            if len(refs) >= 4 and refs[0] == refs[-1]:
                self.parkings.append(refs)


def main():
    h = Handler()
    h.apply_file(PBF, locations=True)
    print(f"nodes in bbox: {len(h.nodes)}, buildings: {len(h.buildings)}, "
          f"parking areas: {len(h.parkings)}")

    lots = json.load(open(LOTS))
    lot_geoms = [shape(f["geometry"]) for f in lots["features"]]
    park_geoms = []
    for refs in h.parkings:
        pts = [h.nodes[r] for r in refs if r in h.nodes]
        if len(pts) >= 4:
            try:
                park_geoms.append(Polygon(pts))
            except Exception:
                pass

    rows = []
    for tags, refs in h.buildings:
        pts = [h.nodes[r] for r in refs if r in h.nodes]
        if len(pts) < 4:
            continue
        try:
            g = Polygon(pts)
        except Exception:
            continue
        if not g.is_valid or g.is_empty:
            continue
        a = area_m2(g)
        if a < 5000:
            continue
        c = g.centroid
        dist = haversine_m(STATION[0], STATION[1], c.y, c.x)
        if dist > 2500:
            continue
        per = perim_m(g)
        inset10 = max(0.0, a - per * 10)  # rough area left after a 10 m inset
        overlaps_lot = any(g.intersects(lg) for lg in lot_geoms)
        overlaps_park = any(g.intersects(pg) for pg in park_geoms)
        rows.append({
            "name": tags.get("name", ""),
            "building": tags.get("building", ""),
            "area_m2": round(a),
            "perim_m": round(per),
            "inset10_m2": round(inset10),
            "dist_station_m": round(dist),
            "centroid": (round(c.y, 5), round(c.x, 5)),
            "overlaps_lot": overlaps_lot,
            "overlaps_parking": overlaps_park,
            "geom": g,
        })
    rows.sort(key=lambda r: -r["area_m2"])
    print(f"\n{'building':<12} {'area m2':>8} {'inset10':>8} {'dist m':>6}  name / centroid")
    feats = []
    for r in rows[:20]:
        flag = "  <-- overlaps lot/parking, skip" if (r["overlaps_lot"] or r["overlaps_parking"]) else ""
        print(f"{r['building']:<12} {r['area_m2']:>8} {r['inset10_m2']:>8} "
              f"{r['dist_station_m']:>6}  {r['name']} {r['centroid']}{flag}")
        feats.append({"type": "Feature",
                      "properties": {k: v for k, v in r.items() if k != "geom"},
                      "geometry": r["geom"].__geo_interface__})
    json.dump({"type": "FeatureCollection", "features": feats},
              open(OUT, "w"), indent=2)
    print(f"\nwrote {OUT} ({len(feats)} candidates)")


if __name__ == "__main__":
    main()
