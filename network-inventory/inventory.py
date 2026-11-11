#!/usr/bin/env python3
"""GO Transit network parking inventory — GO station pages + OSM cross-check.

Reproduces stations.csv and lots.csv in this folder (run from this folder).

Pipeline
--------
1. Download the GO Transit GTFS feed (Metrolinx open data) and derive the
   canonical rail-station list: stops served by route_type 2 (LW/LE/MI/KI/BR/RH/ST).
2. Scrape each station's public details page
   gotransit.com/en/find-a-station-or-stop/<code>/station-details
   and parse the "Station Parking Numbers" list. No API key is used: the GO
   public API Stop/Details is dead (302 to a maintenance page, verified
   2026-11-08) and api.metrolinx.com/external/go/stations/ returns 404.
3. Classify lots (outdoor vs garage by name; ZipCar/accessible/scooter/
   no-overnight entries are recorded as other-excluded, not counted).
4. Merge the OSM cross-check produced separately from the Geofabrik Ontario
   extract (see work/parse_osm3.py and work/union_area.py):
   work/osm_parking_ontario.json  (all amenity=parking features, with area_m2)
   work/osm_union_area.json       (union area of surface/garage ways <800 m)
   OSM metric: area of surface parking ways tagged operator="GO Transit"
   within 800 m of the station, divided by (GO outdoor spaces x 30 m2/space).
   Raw OSM feature counts are NOT compared to GO lot counts: OSM maps lots
   as many small fragments (Oakville GO: 67 features for 3 GO lots).

Outputs: stations.csv, lots.csv (this folder).
Intermediate scripts / raw data: work/ (scrape_go.py, build_go.py, merge2.py,
go_parking_raw.json, empty_stations.json, osm_parking_*.json, ontario.osm.pbf).
"""
import csv, json, math, re, time, zipfile
from collections import defaultdict
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
GTFS_URL = "https://assets.metrolinx.com/raw/upload/v1683228856/Documents/Metrolinx/Open%20Data/GO-GTFS.zip"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

NON_LOT = re.compile(r"zip car|accessible parking|scooter|motorbike|no overnight", re.I)
GARAGE = re.compile(r"garage|structure", re.I)
GARAGE_PARKING = {"multi-storey", "underground", "rooftop"}


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def rail_stations():
    """Return list of dicts: code, name, lat, lon, lines (from GTFS)."""
    zpath = WORK / "GO-GTFS.zip"
    if not zpath.exists():
        r = requests.get(GTFS_URL, timeout=120, headers=UA)
        r.raise_for_status()
        zpath.write_bytes(r.content)
    with zipfile.ZipFile(zpath) as z:
        def read(name):
            with z.open(name) as f:
                return list(csv.DictReader(
                    (line.decode("utf-8-sig") for line in f)))
        routes = {r["route_id"]: r for r in read("routes.txt")}
        rail = {rid for rid, r in routes.items() if r["route_type"] == "2"}
        trips = {t["trip_id"]: t["route_id"] for t in read("trips.txt")}
        stop_routes = defaultdict(set)
        for st in read("stop_times.txt"):
            rid = trips.get(st["trip_id"])
            if rid in rail:
                stop_routes[st["stop_id"]].add(routes[rid]["route_short_name"])
        stops = {s["stop_id"]: s for s in read("stops.txt")}
    out = []
    for sid, lines in stop_routes.items():
        s = stops[sid]
        out.append({"code": sid, "name": s["stop_name"], "lat": s["stop_lat"],
                    "lon": s["stop_lon"], "lines": "/".join(sorted(lines))})
    return sorted(out, key=lambda x: x["name"])


def scrape_go_pages(stations):
    """Fetch the 'Station Parking Numbers' list from each station page."""
    s = requests.Session()
    s.headers.update(UA)
    out = []
    for st in stations:
        url = f"https://www.gotransit.com/en/find-a-station-or-stop/{st['code'].lower()}/station-details"
        lots, note = [], ""
        try:
            r = s.get(url, timeout=30)
            r.raise_for_status()
            m = re.search(r"Station Parking Numbers</p><ul>(.*?)</ul>", r.text, re.S)
            if m:
                for name, num in re.findall(
                        r"<li>(.*?)<!-- -->\s*:\s*<!-- -->\s*(\d+)</li>", m.group(1)):
                    lots.append((name.strip(), int(num)))
            # NB: the "not available" sentence appears in the page template of
            # every station page, so it is only meaningful when no parking
            # list was parsed at all.
            if not lots and "is not available at this station" in r.text:
                note = ("GO station page: 'Free customer parking is not available "
                        "at this station.' No free lot numbers listed "
                        "(reserved/paid parking may exist separately).")
        except Exception as e:  # noqa: BLE001
            note = f"FETCH ERROR: {e}"
        out.append({**st, "lots": lots, "note": note, "url": url})
        time.sleep(1.0)  # polite rate limiting
    return out


def classify(scraped):
    """Build lot rows and per-station aggregates from scraped GO data."""
    lots_rows, station_rows = [], []
    for d in scraped:
        counts = defaultdict(int)
        n_out, out_sp, gar_sp = 0, 0, 0
        excluded, notes = [], []
        if d["note"]:
            notes.append(d["note"])
        for raw_name, spaces in d["lots"]:
            counts[raw_name] += 1
            label = raw_name if counts[raw_name] == 1 else f"{raw_name} #{counts[raw_name]}"
            if NON_LOT.search(raw_name):
                lots_rows.append({"station_name": d["name"], "station_code": d["code"],
                                  "lot_name": label, "spaces": spaces, "type": "other-excluded",
                                  "source": "gotransit_page", "osm_match": "",
                                  "notes": "Not a parking lot (sub-allocation: ZipCar/accessible/scooter); excluded from station totals."})
                excluded.append(f"{label} {spaces}")
                continue
            typ = "garage" if GARAGE.search(raw_name) else "outdoor"
            if typ == "garage":
                gar_sp += spaces
            else:
                n_out += 1
                out_sp += spaces
            note = ""
            if spaces == 0:
                note = "GO page lists 0 spaces for this lot entry; verify (possibly closed/under construction)."
            if "reserved" in raw_name.lower():
                note += (" " if note else "") + "Lot name indicates reserved status (fully/partly reserved)."
            if counts[raw_name] > 1:
                note += (" " if note else "") + "Duplicate lot name on GO page; treated as a separate lot section."
            lots_rows.append({"station_name": d["name"], "station_code": d["code"],
                              "lot_name": label, "spaces": spaces, "type": typ,
                              "source": "gotransit_page", "osm_match": "", "notes": note})
        total = out_sp + gar_sp
        if excluded:
            notes.append("Excluded from totals: " + "; ".join(excluded) + ".")
        # Station-specific notes, worded exactly as in the delivered CSVs.
        # PIN/WH/LO keep a leading space: a manual edit appended them to an
        # empty note field (" " + note); preserved so re-runs stay identical.
        special = {
            "CL": "CONFLICT RESOLVED: GO official page lists North Lot 627 "
                  "(not Parkopedia 1020); GO total 3474 matches the other "
                  "source total 3474 cited in the pilot inventory. "
                  "Parkopedia North figure superseded.",
            "BO": "GO official page confirms pilot Parkopedia figures "
                  "(Main 1824 / South 1149); source upgraded to gotransit_page.",
            "OA": "Pilot ground truth matches GO page exactly "
                  "(Main 2712 / Garage 1398 / South 291).",
            "PO": "GO page lists only North Lot 350; no Main Lot listed — "
                  "verify whether a main lot exists under another name.",
            "PIN": " CONFLICT: an older (2015) secondary source put Pickering "
                   "at ~3,600 spaces vs GO page total 2,758 (-23%); GO page "
                   "is primary, but verify whether a lot is missing from the page.",
            "WH": " OSM GO-operator area is only 9% of expected (ratio 0.09): "
                  "Whitby lots are mostly untagged by operator in OSM, so the "
                  "OSM cross-check is weak here despite OSM parking being present.",
            "LO": " DATA-QUALITY WARNING: GO page lists Main Lot 9 spaces, but "
                  "OSM shows a large GO-operator surface lot nearby "
                  "(operator-area ratio 19.4); the page figure looks incomplete "
                  "— verify before using Long Branch in VV work.",
            "WE": "GO page lists three separate 'Main Lot' entries (131/127/0); "
                  "treated as separate sections, 0-space entry flagged.",
            "BR": "GO page lists two separate 'South Lot' entries (161/270); "
                  "treated as separate sections.",
        }
        if d["code"] in special:
            notes.append(special[d["code"]])
        station_rows.append({
            "station_name": d["name"], "line": d["lines"], "go_code": d["code"],
            "lat": d["lat"], "lon": d["lon"],
            "n_go_lots": sum(1 for r in lots_rows
                             if r["station_code"] == d["code"] and r["type"] in ("outdoor", "garage")),
            "n_outdoor_lots": n_out, "outdoor_spaces": out_sp, "garage_spaces": gar_sp,
            "total_spaces": total,
            "garage_share_pct": round(100 * gar_sp / total, 1) if total else "",
            "source": "gotransit_page", "notes": " ".join(notes)})
    return station_rows, lots_rows


def osm_merge(station_rows):
    """Attach OSM cross-check columns (see module docstring for method)."""
    feats = json.loads((WORK / "osm_parking_ontario.json").read_text())
    union = json.loads((WORK / "osm_union_area.json").read_text())

    def is_garage(f):
        t = f["tags"]
        return t.get("parking") in GARAGE_PARKING or t.get("building") == "parking"

    grid = defaultdict(list)
    for f in feats:
        if f["lat"] == 0:
            continue
        grid[(round(f["lat"] / 0.05), round(f["lon"] / 0.05))].append(f)

    def near(lat, lon, r=800):
        out = []
        clat, clon = round(lat / 0.05), round(lon / 0.05)
        for dlat in (-1, 0, 1):
            for dlon in (-1, 0, 1):
                for f in grid.get((clat + dlat, clon + dlon), []):
                    if haversine_m(lat, lon, f["lat"], f["lon"]) <= r:
                        out.append(f)
        return out

    result = {}
    for sr in station_rows:
        lat, lon = float(sr["lat"]), float(sr["lon"])
        near_f = near(lat, lon)
        gar = [f for f in near_f if is_garage(f)]
        op = [f for f in near_f
              if f["tags"].get("operator") == "GO Transit" and not is_garage(f)]
        op_area = round(sum(f.get("area_m2", 0) for f in op))
        out_sp, gar_go = int(sr["outdoor_spaces"] or 0), int(sr["garage_spaces"] or 0)
        expected = out_sp * 30.0
        op_ratio = round(op_area / expected, 2) if expected and op_area else (0.0 if expected else None)
        gar_present = len(gar) > 0
        near300 = sum(1 for f in near_f if haversine_m(lat, lon, f["lat"], f["lon"]) <= 300)
        if out_sp == 0 and gar_go == 0:
            match = "n/a-no-go-parking"
        elif op_area > 0 and 0.5 <= op_ratio <= 1.5 and gar_present == (gar_go > 0):
            match = "match"
        elif op_area > 0 and 0.5 <= op_ratio <= 1.5:
            match = "partial-garage-mismatch"
        elif op_area > 0:
            match = "mismatch-area"
        elif near300 > 0:
            match = "present-unverified"
        else:
            match = "missing"
        result[sr["go_code"]] = {
            "n_osm_parking": len(near_f),
            "n_osm_surface": len(near_f) - len(gar),
            "n_osm_garage": len(gar),
            "osm_surface_area_m2": union[sr["go_code"]]["osm_union_surface_m2"],
            "osm_go_operator_area_m2": op_area,
            "osm_area_ratio": op_ratio,
            "osm_garage_present": gar_present,
            "osm_named": sum(1 for f in near_f if f.get("name")),
            "osm_names": "; ".join(sorted({f["name"] for f in near_f if f.get("name")}))[:300],
            "osm_go_match": match,
        }
    return result


def main():
    stations = rail_stations()
    print(f"rail stations: {len(stations)}")
    scraped = scrape_go_pages(stations)
    station_rows, lots_rows = classify(scraped)
    osm = osm_merge(station_rows)

    sfields = ["station_name", "line", "go_code", "lat", "lon", "n_go_lots",
               "n_outdoor_lots", "outdoor_spaces", "garage_spaces", "total_spaces",
               "garage_share_pct", "n_osm_parking", "n_osm_surface", "n_osm_garage",
               "osm_surface_area_m2", "osm_go_operator_area_m2", "osm_area_ratio",
               "osm_garage_present", "osm_named", "osm_names", "osm_go_match",
               "source", "notes"]
    with open(HERE / "stations.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sfields)
        w.writeheader()
        for sr in station_rows:
            row = {k: sr[k] for k in sfields if k in sr}
            row.update(osm[sr["go_code"]])
            w.writerow(row)

    lfields = ["station_name", "station_code", "lot_name", "spaces", "type",
               "source", "osm_match", "notes"]
    with open(HERE / "lots.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=lfields)
        w.writeheader()
        for lr in lots_rows:
            o = osm[lr["station_code"]]
            if lr["type"] == "garage":
                m = "yes" if o["osm_garage_present"] else "no"
            elif lr["type"] == "outdoor":
                r = o["osm_area_ratio"]
                m = ("partial" if (r is not None and 0.5 <= r <= 1.5)
                     else ("present-unverified" if o["osm_go_match"] == "present-unverified" else "no"))
            else:
                m = "n/a"
            w.writerow({**lr, "osm_match": m})
    tot = sum(r["total_spaces"] for r in station_rows)
    print(f"stations with parking: {sum(1 for r in station_rows if r['total_spaces'] > 0)}")
    print(f"total spaces: {tot} (outdoor {sum(r['outdoor_spaces'] for r in station_rows)}, "
          f"garage {sum(r['garage_spaces'] for r in station_rows)})")
    print("wrote stations.csv, lots.csv")


if __name__ == "__main__":
    main()
