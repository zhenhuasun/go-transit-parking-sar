import json, csv, math
from collections import defaultdict

feats=json.load(open('osm_parking_ontario.json'))
stations=json.load(open('go_parking_raw.json'))
go_stations={r['station_name']:r for r in csv.DictReader(open('stations_go.csv'))}

def haversine_m(lat1,lon1,lat2,lon2):
    R=6371000.0
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

GARAGE_PARKING={'multi-storey','underground','rooftop'}
def is_garage(f):
    t=f['tags']
    if t.get('parking') in GARAGE_PARKING: return True
    if t.get('building')=='parking': return True
    if t.get('amenity')=='parking' and t.get('parking')=='multi-storey': return True
    return False

# sanity: Oakville
for st in stations:
    if st['code']=='OA':
        lat,lon=float(st['lat']),float(st['lon'])
        near=[f for f in feats if haversine_m(lat,lon,f['lat'],f['lon'])<=800]
        print("Oakville OSM within 800m:", len(near))
        for f in sorted(near, key=lambda x: haversine_m(lat,lon,x['lat'],x['lon'])):
            print("  ", round(haversine_m(lat,lon,f['lat'],f['lon'])), "m", f['osm_type'], f['osm_id'], repr(f['name']), "parking=",f['parking'], "capacity=",f['capacity'], "garage?", is_garage(f))
