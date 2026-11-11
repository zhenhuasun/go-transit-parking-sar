import osmium, json

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

h=Pass1()
h.apply_file('ontario.osm.pbf')
print("parking nodes:", len(h.parking_nodes), "ways:", len(h.parking_ways), "relations:", len(h.parking_rels), flush=True)

wanted=set()
for _,_,refs in h.parking_ways: wanted.update(refs)
print("way member nodes wanted:", len(wanted), flush=True)

class Pass2(osmium.SimpleHandler):
    def __init__(self, wanted):
        super().__init__(); self.wanted=wanted; self.coords={}
    def node(self, n):
        if n.id in self.wanted:
            self.coords[n.id]=(n.location.lat, n.location.lon)
nc=Pass2(wanted)
nc.apply_file('ontario.osm.pbf')
print("collected node coords:", len(nc.coords), flush=True)

def centroid(pts):
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

feats=[]
for nid, tags, lat, lon in h.parking_nodes:
    feats.append({"osm_type":"node","osm_id":nid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"tags":tags})
way_cent={}
for wid, tags, refs in h.parking_ways:
    pts=[nc.coords[r] for r in refs if r in nc.coords]
    if not pts: continue
    lat,lon=centroid(pts); way_cent[wid]=(lat,lon)
    feats.append({"osm_type":"way","osm_id":wid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"tags":tags})
for rid, tags, ways in h.parking_rels:
    pts=[way_cent[w] for w in ways if w in way_cent]
    if not pts: continue
    lat,lon=centroid(pts)
    feats.append({"osm_type":"relation","osm_id":rid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"tags":tags})
print("total parking features:", len(feats), flush=True)
json.dump(feats, open('osm_parking_ontario.json','w'), ensure_ascii=False)
print("saved osm_parking_ontario.json", flush=True)
