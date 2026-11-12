#!/usr/bin/env python3
"""Check what OSM features the user's T1b control polygons cover.

Reads the local Geofabrik Ontario PBF (already on disk from the network
inventory) with pyosmium, extracts building / parking / landuse ways in
the control-area bboxes, and reports the fraction of each control polygon
covered by each feature class. Validation only — not part of the
pre-registered T1b run.
"""
import json
import math
import sys

import osmium
from shapely.geometry import Polygon, shape

CTRL = sys.argv[1] if len(sys.argv) > 1 else "/home/hatch/workspace/user/files/go-parking-control-areas.geojson"
PBF = sys.argv[2] if len(sys.argv) > 2 else "/home/hatch/workspace/go-parking-sarpanel/network-inventory/work/ontario.osm.pbf"

ctrl = json.load(open(CTRL))
bboxes = []
for f in ctrl["features"]:
    geom = f["geometry"]
    if geom["type"] == "Polygon":
        rings = geom["coordinates"]
    elif geom["type"] == "MultiPolygon":
        rings = [ring for poly in geom["coordinates"] for ring in poly]
    else:
        continue
    lons = [c[0] for ring in rings for c in ring]
    lats = [c[1] for ring in rings for c in ring]
    bboxes.append((min(lats) - 0.001, min(lons) - 0.001,
                   max(lats) + 0.001, max(lons) + 0.001))


def in_any_bbox(lat, lon):
    return any(s <= lat <= n and w <= lon <= e for s, w, n, e in bboxes)


class Handler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.ways = []

    def node(self, n):
        if n.location.valid and in_any_bbox(n.location.lat, n.location.lon):
            self.nodes[n.id] = (n.location.lon, n.location.lat)

    def way(self, w):
        tags = dict(w.tags)
        cls = None
        if "building" in tags:
            cls = "building:" + str(tags.get("building"))
        elif tags.get("amenity") == "parking":
            cls = "parking"
        elif "landuse" in tags:
            cls = "landuse:" + str(tags.get("landuse"))
        else:
            return
        pts = [self.nodes.get(ref.ref) for ref in w.nodes]
        if any(p is None for p in pts) or len(pts) < 4:
            return
        if pts[0] != pts[-1]:
            return  # only closed ways form areas
        self.ways.append({"class": cls, "name": tags.get("name", ""),
                          "pts": pts})


def _ring_area_m2(coords):
    lat0 = sum(c[1] for c in coords) / len(coords)
    kx = 111320 * math.cos(math.radians(lat0))
    ky = 110540
    pts = [(c[0] * kx, c[1] * ky) for c in coords]
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def area_m2(geom):
    """Planar area in m2; handles Polygon and MultiPolygon (minus holes)."""
    if geom.is_empty:
        return 0.0
    geoms = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    total = 0.0
    for poly in geoms:
        if poly.geom_type != "Polygon":
            continue
        total += _ring_area_m2(list(poly.exterior.coords))
        for ring in poly.interiors:
            total -= _ring_area_m2(list(ring.coords))
    return total


def main():
    h = Handler()
    h.apply_file(PBF, locations=True)
    print(f"nodes in bboxes: {len(h.nodes)}, ways kept: {len(h.ways)}")
    for f in ctrl["features"]:
        cp = shape(f["geometry"])
        total = area_m2(cp)
        print(f"\n=== {f['properties'].get('name')} — area {total:.0f} m2 ===")
        cov = {}
        for w in h.ways:
            try:
                wp = Polygon(w["pts"])
            except Exception:
                continue
            if not wp.is_valid or wp.is_empty:
                continue
            inter = cp.intersection(wp)
            if inter.is_empty:
                continue
            frac = area_m2(inter) / total if total else 0
            if frac < 0.005:
                continue
            key = (w["class"], w["name"])
            cov[key] = cov.get(key, 0.0) + frac
        if not cov:
            print("  no OSM building/parking/landuse overlap found")
        for (cls, name), frac in sorted(cov.items(), key=lambda kv: -kv[1]):
            print(f"  {frac*100:5.1f}%  {cls}  {name!r}")


if __name__ == "__main__":
    main()
