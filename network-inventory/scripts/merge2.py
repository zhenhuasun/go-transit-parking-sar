import json, csv, math
from collections import Counter, defaultdict

feats=json.load(open('osm_parking_ontario.json'))
union=json.load(open('osm_union_area.json'))
stations_go=list(csv.DictReader(open('stations_go.csv')))
lots_go=list(csv.DictReader(open('lots_go.csv')))

def hav(lat1,lon1,lat2,lon2):
    R=6371000.0; p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))
GARAGE={'multi-storey','underground','rooftop'}
def is_garage(f):
    t=f['tags']
    return t.get('parking') in GARAGE or t.get('building')=='parking'

grid=defaultdict(list)
for f in feats:
    if f['lat']==0: continue
    grid[(round(f['lat']/0.05), round(f['lon']/0.05))].append(f)
def near_station(lat, lon, r=800):
    out=[]; clat, clon = round(lat/0.05), round(lon/0.05)
    for dlat in (-1,0,1):
        for dlon in (-1,0,1):
            for f in grid.get((clat+dlat, clon+dlon), []):
                if hav(lat,lon,f['lat'],f['lon'])<=r: out.append(f)
    return out

osm_by_station={}
for sr in stations_go:
    lat,lon=float(sr['lat']),float(sr['lon'])
    near=near_station(lat,lon)
    surf=[f for f in near if not is_garage(f)]
    gar=[f for f in near if is_garage(f)]
    op=[f for f in near if f['tags'].get('operator')=='GO Transit' and not is_garage(f)]
    op_area=round(sum(f.get('area_m2',0) for f in op))
    out_sp=int(sr['outdoor_spaces'] or 0); gar_go=int(sr['garage_spaces'] or 0)
    expected=out_sp*30.0
    op_ratio=round(op_area/expected,2) if expected and op_area else (0.0 if expected else None)
    gar_present=len(gar)>0
    near300=sum(1 for f in near if hav(lat,lon,f['lat'],f['lon'])<=300)
    u=union[sr['go_code']]
    if out_sp==0 and gar_go==0:
        match="n/a-no-go-parking"
    elif op_area>0 and 0.5<=op_ratio<=1.5 and gar_present==(gar_go>0):
        match="match"
    elif op_area>0 and 0.5<=op_ratio<=1.5:
        match="partial-garage-mismatch"
    elif op_area>0:
        match="mismatch-area"
    elif near300>0:
        match="present-unverified"
    else:
        match="missing"
    osm_by_station[sr['go_code']]={
        "n_osm_parking":len(near),"n_osm_surface":len(surf),"n_osm_garage":len(gar),
        "osm_surface_area_m2":u['osm_union_surface_m2'],
        "osm_go_operator_area_m2":op_area,"osm_area_ratio":op_ratio,
        "osm_garage_present":gar_present,"osm_named":sum(1 for f in near if f.get('name')),
        "osm_names":"; ".join(sorted({f['name'] for f in near if f.get('name')}))[:300],
        "osm_go_match":match,
    }

# Pickering conflict note (older 2015 source: 3,600 spaces vs GO page 2,758)
for sr in stations_go:
    if sr['go_code']=='PIN':
        sr['notes'] += " CONFLICT: an older (2015) secondary source put Pickering at ~3,600 spaces vs GO page total 2,758 (-23%); GO page is primary, but verify whether a lot is missing from the page."

fieldnames=["station_name","line","go_code","lat","lon","n_go_lots","n_outdoor_lots","outdoor_spaces",
 "garage_spaces","total_spaces","garage_share_pct","n_osm_parking","n_osm_surface","n_osm_garage",
 "osm_surface_area_m2","osm_go_operator_area_m2","osm_area_ratio","osm_garage_present","osm_named","osm_names","osm_go_match","source","notes"]
with open('../stations.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
    for sr in stations_go:
        row={k:sr[k] for k in fieldnames if k in sr}
        row.update(osm_by_station[sr['go_code']])
        w.writerow(row)

with open('../lots.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=["station_name","station_code","lot_name","spaces","type","source","osm_match","notes"])
    w.writeheader()
    for lr in lots_go:
        o=osm_by_station[lr['station_code']]
        if lr['type']=='garage':
            m="yes" if o['osm_garage_present'] else "no"
        elif lr['type']=='outdoor':
            r=o['osm_area_ratio']
            m="partial" if (r is not None and 0.5<=r<=1.5) else ("present-unverified" if o['osm_go_match']=="present-unverified" else "no")
        else:
            m="n/a"
        w.writerow({**lr, "osm_match":m})

print(Counter(osm_by_station[c]['osm_go_match'] for c in osm_by_station))
print("stations with GO-operator OSM area:", sum(1 for o in osm_by_station.values() if o['osm_go_operator_area_m2']>0))
for code in ('OA','CL','BO'):
    print(code, osm_by_station[code])
print("\nmatch stations:")
for sr in stations_go:
    if osm_by_station[sr['go_code']]['osm_go_match']=='match': print(" ", sr['station_name'], osm_by_station[sr['go_code']]['osm_area_ratio'])
print("\npresent-unverified (no GO-operator tags):")
for sr in stations_go:
    if osm_by_station[sr['go_code']]['osm_go_match']=='present-unverified': print(" ", sr['station_name'])
print("\nmissing (no OSM parking within 300m):")
for sr in stations_go:
    if osm_by_station[sr['go_code']]['osm_go_match']=='missing': print(" ", sr['station_name'])
print("\nmismatch-area:")
for sr in stations_go:
    if osm_by_station[sr['go_code']]['osm_go_match']=='mismatch-area': print(" ", sr['station_name'], osm_by_station[sr['go_code']]['osm_area_ratio'])
