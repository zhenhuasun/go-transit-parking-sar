import json, csv, math
from collections import defaultdict

feats=json.load(open('osm_parking_ontario.json'))
stations_go=list(csv.DictReader(open('stations_go.csv')))
lots_go=list(csv.DictReader(open('lots_go.csv')))

def haversine_m(lat1,lon1,lat2,lon2):
    R=6371000.0
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))
GARAGE={'multi-storey','underground','rooftop'}
def is_garage(f):
    t=f['tags']
    return t.get('parking') in GARAGE or t.get('building')=='parking'

# index feats by rough grid for speed (1-degree cells are too coarse; use 0.02 deg cells)
grid=defaultdict(list)
for f in feats:
    if f['lat']==0: continue  # relations: centroid unknown, excluded from spatial sums
    grid[(round(f['lat']/0.05), round(f['lon']/0.05))].append(f)

def near_station(lat, lon, r=800):
    out=[]
    clat, clon = round(lat/0.05), round(lon/0.05)
    for dlat in (-1,0,1):
        for dlon in (-1,0,1):
            for f in grid.get((clat+dlat, clon+dlon), []):
                if haversine_m(lat,lon,f['lat'],f['lon'])<=r: out.append(f)
    return out

osm_by_station={}
for sr in stations_go:
    lat,lon=float(sr['lat']),float(sr['lon'])
    near=near_station(lat,lon)
    surf=[f for f in near if not is_garage(f)]
    gar=[f for f in near if is_garage(f)]
    surf_area=sum(f.get('area_m2',0) for f in surf)
    named=sum(1 for f in near if f.get('name'))
    out_sp=int(sr['outdoor_spaces'] or 0)
    expected=out_sp*30.0
    ratio=round(surf_area/expected,2) if expected else (None if not near else 0)
    gar_go=int(sr['garage_spaces'] or 0)
    gar_present=len(gar)>0
    if out_sp==0 and gar_go==0:
        match = "n/a-no-go-parking"
    elif surf_area==0 and out_sp>0:
        match="missing"
    elif ratio is not None and 0.5<=ratio<=1.5 and gar_present==(gar_go>0):
        match="match"
    elif ratio is not None and 0.5<=ratio<=1.5:
        match="partial-garage-mismatch"
    else:
        match="mismatch"
    osm_by_station[sr['go_code']]={
        "n_osm_parking":len(near),"n_osm_surface":len(surf),"n_osm_garage":len(gar),
        "osm_surface_area_m2":round(surf_area),"osm_named":named,
        "osm_area_ratio":ratio,"osm_garage_present":gar_present,"osm_go_match":match,
        "osm_names":"; ".join(sorted({f['name'] for f in near if f.get('name')}))[:300],
    }

# write final stations.csv
fieldnames=["station_name","line","go_code","lat","lon","n_go_lots","n_outdoor_lots","outdoor_spaces",
 "garage_spaces","total_spaces","garage_share_pct","n_osm_parking","n_osm_surface","n_osm_garage",
 "osm_surface_area_m2","osm_area_ratio","osm_garage_present","osm_named","osm_names","osm_go_match","source","notes"]
with open('../stations.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
    for sr in stations_go:
        o=osm_by_station[sr['go_code']]
        row={k:sr[k] for k in fieldnames if k in sr}
        row.update(o)
        # keep osm_go_match from o (overrides blank)
        w.writerow(row)

# lots.csv osm_match: garage lots -> yes if garage feature present at station, else no;
# outdoor lots -> partial if station area ratio in [0.5,1.5], else no; stations with no GO parking n/a
with open('../lots.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=["station_name","station_code","lot_name","spaces","type","source","osm_match","notes"])
    w.writeheader()
    for lr in lots_go:
        o=osm_by_station[lr['station_code']]
        if lr['type']=='garage':
            m="yes" if o['osm_garage_present'] else "no"
        elif lr['type']=='outdoor':
            r=o['osm_area_ratio']
            m="partial" if (r is not None and 0.5<=r<=1.5) else "no"
        else:
            m="n/a"
        w.writerow({**lr, "osm_match":m})

# summary stats
from collections import Counter
print(Counter(osm_by_station[c]['osm_go_match'] for c in osm_by_station))
print("total OSM surface area within 800m of all stations (double counts overlaps):",
      sum(o['osm_surface_area_m2'] for o in osm_by_station.values()))
for code in ('OA','CL','BO'):
    print(code, osm_by_station[code])
# stations where OSM area ratio is extreme
print("\narea ratio <0.5 (OSM missing area):")
for sr in stations_go:
    o=osm_by_station[sr['go_code']]
    if o['osm_area_ratio'] is not None and o['osm_area_ratio']<0.5 and int(sr['outdoor_spaces'])>0:
        print(" ", sr['station_name'], "ratio", o['osm_area_ratio'], "outdoor", sr['outdoor_spaces'], "osm_area", o['osm_surface_area_m2'], "n_osm", o['n_osm_parking'])
print("\narea ratio >1.5 (extra non-GO parking in radius):")
for sr in stations_go:
    o=osm_by_station[sr['go_code']]
    if o['osm_area_ratio'] is not None and o['osm_area_ratio']>1.5:
        print(" ", sr['station_name'], "ratio", o['osm_area_ratio'], "outdoor", sr['outdoor_spaces'], "osm_area", o['osm_surface_area_m2'], "n_osm", o['n_osm_parking'])
print("\nno-parking stations with OSM parking nearby:")
for sr in stations_go:
    o=osm_by_station[sr['go_code']]
    if int(sr['total_spaces'])==0 and o['n_osm_parking']>0:
        print(" ", sr['station_name'], "n_osm", o['n_osm_parking'], "names:", o['osm_names'][:150])
