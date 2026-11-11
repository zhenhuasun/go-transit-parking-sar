import csv, re, time, requests, json
from collections import defaultdict

stations=[]
with open('stations_rail.csv') if False else open('/dev/null') as f: pass
# read rail stations from gtfs
import csv
routes={}
with open('gtfs/routes.txt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f): routes[r['route_id']]=r
rail={rid for rid,r in routes.items() if r['route_type']=='2'}
trips={}
with open('gtfs/trips.txt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f): trips[r['trip_id']]=r['route_id']
stop_routes=defaultdict(set)
with open('gtfs/stop_times.txt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        rid=trips.get(r['trip_id'])
        if rid in rail: stop_routes[r['stop_id']].add(routes[rid]['route_short_name'])
stops={}
with open('gtfs/stops.txt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f): stops[r['stop_id']]=r

s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36","Accept":"text/html,application/xhtml+xml"})
out=[]
for sid in sorted(stop_routes, key=lambda s: stops[s]['stop_name']):
    code=sid.lower()
    url=f"https://www.gotransit.com/en/find-a-station-or-stop/{code}/station-details"
    lots=[]; note=""
    try:
        r=s.get(url, timeout=30); r.raise_for_status()
        html=r.text
        m=re.search(r'Station Parking Numbers</p><ul>(.*?)</ul>', html, re.S)
        if m:
            for name,num in re.findall(r'<li>(.*?)<!-- -->\s*:\s*<!-- -->\s*(\d+)</li>', m.group(1)):
                lots.append((name.strip(), int(num)))
        # parking availability text
        if 'No free parking' in html: note="page: No free parking"
        elif 'Free customer parking' in html: note="page: Free customer parking available"
        elif 'Paid parking' in html: note="page: paid parking mentioned"
        if not lots and 'Parking' not in html: note="page: no Parking section found"
    except Exception as e:
        note=f"FETCH ERROR: {e}"
    st=stops[sid]
    out.append({"code":sid,"name":st['stop_name'],"lat":st['stop_lat'],"lon":st['stop_lon'],
                "lines":"/".join(sorted(stop_routes[sid])),"lots":lots,"note":note,"url":url})
    print(sid, st['stop_name'], lots, note, flush=True)
    time.sleep(1.0)
json.dump(out, open('go_parking_raw.json','w'), indent=1, ensure_ascii=False)
print("DONE", len(out))
