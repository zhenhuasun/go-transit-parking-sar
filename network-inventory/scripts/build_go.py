import json, csv, re
from collections import defaultdict

data = json.load(open('go_parking_raw.json'))
empty = json.load(open('empty_stations.json'))

NON_LOT = re.compile(r'zip car|accessible parking|scooter|motorbike|no overnight', re.I)
GARAGE = re.compile(r'garage|structure', re.I)

lots_rows = []
station_rows = []
for d in sorted(data, key=lambda x: x['name']):
    code, name = d['code'], d['name']
    lots = d['lots']
    counts = defaultdict(int)
    station_notes = []
    n_out, out_sp, gar_sp = 0, 0, 0
    excluded = []
    for raw_name, spaces in lots:
        counts[raw_name] += 1
        label = raw_name
        if counts[raw_name] > 1:
            label = f"{raw_name} #{counts[raw_name]}"
        if NON_LOT.search(raw_name):
            lots_rows.append({"station_name": name, "station_code": code, "lot_name": label,
                "spaces": spaces, "type": "other-excluded",
                "source": "gotransit_page",
                "osm_match": "", "notes": "Not a parking lot (sub-allocation: ZipCar/accessible/scooter); excluded from station totals."})
            excluded.append(f"{label} {spaces}")
            continue
        if GARAGE.search(raw_name):
            typ = "garage"
            gar_sp += spaces
        else:
            typ = "outdoor"
            n_out += 1; out_sp += spaces
        note = ""
        if spaces == 0:
            note = "GO page lists 0 spaces for this lot entry; verify (possibly closed/under construction)."
        if "Reserved" in raw_name or "reserved" in raw_name.lower():
            note += (" " if note else "") + "Lot name indicates reserved status (fully/partly reserved)."
        if counts[raw_name] > 1:
            note += (" " if note else "") + "Duplicate lot name on GO page; treated as a separate lot section."
        lots_rows.append({"station_name": name, "station_code": code, "lot_name": label,
            "spaces": spaces, "type": typ, "source": "gotransit_page",
            "osm_match": "", "notes": note})
    total = out_sp + gar_sp
    share = round(100*gar_sp/total, 1) if total else ""
    if not lots:
        station_notes.append("GO station page: 'Free customer parking is not available at this station.' No free lot numbers listed (reserved/paid parking may exist separately).")
    if excluded:
        station_notes.append("Excluded from totals: " + "; ".join(excluded) + ".")
    if code == "CL":
        station_notes.append("CONFLICT RESOLVED: GO official page lists North Lot 627 (not Parkopedia 1020); GO total 3474 matches the other source total 3474 cited in the pilot inventory. Parkopedia North figure superseded.")
    if code == "BO":
        station_notes.append("GO official page confirms pilot Parkopedia figures (Main 1824 / South 1149); source upgraded to gotransit_page.")
    if code == "OA":
        station_notes.append("Pilot ground truth matches GO page exactly (Main 2712 / Garage 1398 / South 291).")
    if code == "WE":
        station_notes.append("GO page lists three separate 'Main Lot' entries (131/127/0); treated as separate sections, 0-space entry flagged.")
    if code == "BR":
        station_notes.append("GO page lists two separate 'South Lot' entries (161/270); treated as separate sections.")
    if code == "PO":
        station_notes.append("GO page lists only North Lot 350; no Main Lot listed — verify whether a main lot exists under another name.")
    station_rows.append({
        "station_name": name, "line": d['lines'], "go_code": code,
        "lat": d['lat'], "lon": d['lon'],
        "n_go_lots": n_out + (1 if gar_sp else 0) + (sum(1 for r in lots_rows if r['station_code']==code and r['type']=='garage')),
        "n_outdoor_lots": n_out, "outdoor_spaces": out_sp, "garage_spaces": gar_sp,
        "total_spaces": total, "garage_share_pct": share,
        "n_osm_parking": "", "n_osm_surface": "", "n_osm_garage": "",
        "osm_go_match": "", "source": "gotransit_page",
        "notes": " ".join(station_notes)})

# fix n_go_lots: count of counted lots (outdoor + garage rows)
for sr in station_rows:
    sr["n_go_lots"] = sum(1 for r in lots_rows if r['station_code']==sr['go_code'] and r['type'] in ('outdoor','garage'))

with open('lots_go.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=list(lots_rows[0].keys())); w.writeheader(); w.writerows(lots_rows)
with open('stations_go.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=list(station_rows[0].keys())); w.writeheader(); w.writerows(station_rows)

tot_out=sum(r['outdoor_spaces'] for r in station_rows); tot_gar=sum(r['garage_spaces'] for r in station_rows)
print("stations", len(station_rows), "with parking", sum(1 for r in station_rows if r['total_spaces']>0))
print("outdoor spaces", tot_out, "garage", tot_gar, "total", tot_out+tot_gar)
print("lots rows", len(lots_rows), "outdoor lots", sum(1 for r in lots_rows if r['type']=='outdoor'), "garage lots", sum(1 for r in lots_rows if r['type']=='garage'))
print("garage share overall", round(100*tot_gar/(tot_out+tot_gar),1))
print("top outdoor stations:", sorted(((r['station_name'],r['outdoor_spaces']) for r in station_rows), key=lambda x:-x[1])[:8])
