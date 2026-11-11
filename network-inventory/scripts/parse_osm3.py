import osmium, json, math

class Pass1(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.parking_nodes=[]; self.parking_ways=[]; self.parking_rels=[]
    def node(self, n):
        if n.tags.get('amenity')=='parking':
            self.parking_nodes.append((n.id, dict(n.tags), n.location.lat, n.location.lon))
    def way(self, w):
        if w.tags.get('amenity')=='parking':
            self.parking_ways.append((w.id, dict(w.tags), [nd.ref for nd in w.nodes]))
    def relation(self, r):
        if r.tags.get('amenity')=='parking':
            self.parking_rels.append((r.id, dict(r.tags), [m.ref for m in r.members if m.type=='w']))
h=Pass1(); h.apply_file('ontario.osm.pbf')
print("parking nodes:", len(h.parking_nodes), "ways:", len(h.parking_ways), "relations:", len(h.parking_rels), flush=True)
json.dump({"ways":h.parking_ways,"rels":h.parking_rels}, open('osm_parking_ways_refs.json','w'))

wanted=set()
for _,_,refs in h.parking_ways: wanted.update(refs)
class Pass2(osmium.SimpleHandler):
    def __init__(self, wanted):
        super().__init__(); self.wanted=wanted; self.coords={}
    def node(self, n):
        if n.id in self.wanted: self.coords[n.id]=(n.location.lat, n.location.lon)
nc=Pass2(wanted); nc.apply_file('ontario.osm.pbf')
print("collected node coords:", len(nc.coords), flush=True)

def way_area_m2(pts):
    # equirectangular shoelace around centroid, metres
    if len(pts)<3: return 0.0
    lat0=sum(p[0] for p in pts)/len(pts); lon0=sum(p[1] for p in pts)/len(pts)
    R=6371000.0; xy=[((lon-lon0)*math.pi/180*R*math.cos(math.radians(lat0)), (lat-lat0)*math.pi/180*R) for lat,lon in pts]
    a=0.0
    for i in range(len(xy)):
        x1,y1=xy[i]; x2,y2=xy[(i+1)%len(xy)]; a+=x1*y2-x2*y1
    return abs(a)/2

def centroid(pts): return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))
feats=[]
for nid, tags, lat, lon in h.parking_nodes:
    feats.append({"osm_type":"node","osm_id":nid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"area_m2":0,"tags":tags})
way_area={}
for wid, tags, refs in h.parking_ways:
    pts=[nc.coords[r] for r in refs if r in nc.coords]
    if not pts: continue
    lat,lon=centroid(pts); area=way_area_m2(pts); way_area[wid]=area
    feats.append({"osm_type":"way","osm_id":wid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"area_m2":round(area,1),"tags":tags})
for rid, tags, ways in h.parking_rels:
    pts=[]
    area=sum(way_area.get(w,0) for w in ways)
    # centroid from member way centroids (approx): recompute from way_area keys not stored; use feats lookup
    print("relation", rid, "member ways", len(ways), "area", round(area), flush=True)
    # store relation with centroid 0,0 and area; excluded from station area sums (avoid double count)
    feats.append({"osm_type":"relation","osm_id":rid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":0,"lon":0,"area_m2":round(area,1),"tags":tags})
print("total parking features:", len(feats), flush=True)
json.dump(feats, open('osm_parking_ontario.json','w'), ensure_ascii=False)
print("saved osm_parking_ontario.json", flush=True)
