import osmium, json, math
from shapely.geometry import Polygon
from shapely.ops import unary_union

feats=json.load(open('osm_parking_ontario.json'))
stations=json.load(open('go_parking_raw.json'))
def hav(lat1,lon1,lat2,lon2):
    R=6371000.0; p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))
# ways whose centroid within 1200m of any station
refs=json.load(open('osm_parking_ways_refs.json'))["ways"]
by_id={wid:(tags, r) for wid,tags,r in refs}
wanted_ways=[]
for f in feats:
    if f['osm_type']!='way': continue
    for st in stations:
        if hav(float(st['lat']),float(st['lon']),f['lat'],f['lon'])<=1200:
            wanted_ways.append(f['osm_id']); break
print("ways near stations:", len(wanted_ways), flush=True)
wanted_nodes=set()
for wid in wanted_ways:
    wanted_nodes.update(by_id[wid][1])
print("nodes wanted:", len(wanted_nodes), flush=True)
class Pass(osmium.SimpleHandler):
    def __init__(self, wanted):
        super().__init__(); self.wanted=wanted; self.coords={}
    def node(self, n):
        if n.id in self.wanted: self.coords[n.id]=(n.location.lat, n.location.lon)
p=Pass(wanted_nodes); p.apply_file('ontario.osm.pbf')
print("coords collected:", len(p.coords), flush=True)

def to_xy(lat, lon, lat0, lon0):
    R=6371000.0
    return ((lon-lon0)*math.pi/180*R*math.cos(math.radians(lat0)), (lat-lat0)*math.pi/180*R)
out={}
for st in stations:
    slat, slon = float(st['lat']), float(st['lon'])
    polys_surf=[]; polys_gar=[]
    for f in feats:
        if f['osm_type']!='way': continue
        if hav(slat,slon,f['lat'],f['lon'])>800: continue
        wid=f['osm_id']
        if wid not in by_id: continue
        tags, refs_ = by_id[wid]
        pts=[p.coords[r] for r in refs_ if r in p.coords]
        if len(pts)<4: continue
        xy=[to_xy(la,lo,slat,slon) for la,lo in pts]
        try: poly=Polygon(xy)
        except Exception: continue
        if not poly.is_valid: poly=poly.buffer(0)
        if poly.is_empty or poly.area<=0: continue
        if tags.get('parking') in ('multi-storey','underground','rooftop') or tags.get('building')=='parking':
            polys_gar.append(poly)
        else:
            polys_surf.append(poly)
    u_surf=unary_union(polys_surf) if polys_surf else None
    u_gar=unary_union(polys_gar) if polys_gar else None
    out[st['code']]={
        "osm_union_surface_m2": round(u_surf.area) if u_surf else 0,
        "osm_union_garage_m2": round(u_gar.area) if u_gar else 0,
        "osm_union_surface_n": len(polys_surf), "osm_union_garage_n": len(polys_gar)}
    print(st['code'], st['name'], "surf union", out[st['code']]['osm_union_surface_m2'],
          "gar union", out[st['code']]['osm_union_garage_m2'], flush=True)
json.dump(out, open('osm_union_area.json','w'), indent=1)
print("saved osm_union_area.json", flush=True)
