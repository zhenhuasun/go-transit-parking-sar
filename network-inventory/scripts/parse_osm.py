import osmium, json, math

# Collect parking features: nodes directly, ways via centroid of member nodes,
# relations (multipolygon) via centroid of member way nodes (approx).
class ParkingHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}   # id -> (lat, lon) for nodes that are part of parking ways (kept small: only parking way members)
        self.parking_ways = []  # (id, tags dict, [node ids])
        self.parking_nodes = [] # (id, tags, lat, lon)
        self.parking_rels = []  # (id, tags, [way ids])
    def node(self, n):
        if 'amenity' in n.tags and n.tags.get('amenity') == 'parking':
            self.parking_nodes.append((n.id, dict(n.tags), n.location.lat, n.location.lon))
    def way(self, w):
        if w.tags.get('amenity') == 'parking':
            self.parking_ways.append((w.id, dict(w.tags), [nd.ref for nd in w.nodes]))
    def relation(self, r):
        if r.tags.get('amenity') == 'parking':
            ways=[m.ref for m in r.members if m.type=='w']
            self.parking_rels.append((r.id, dict(r.tags), ways))

h = ParkingHandler()
h.apply_file('ontario.osm.pbf', locations=True)
print("parking nodes:", len(h.parking_nodes), "ways:", len(h.parking_ways), "relations:", len(h.parking_rels))

# Second pass to get coordinates of way member nodes
class NodeCollector(osmium.SimpleHandler):
    def __init__(self, wanted):
        super().__init__()
        self.wanted = wanted; self.coords = {}
    def node(self, n):
        if n.id in self.wanted:
            self.coords[n.id] = (n.location.lat, n.location.lon)
wanted=set()
for _,_,refs in h.parking_ways: wanted.update(refs)
print("way member nodes to collect:", len(wanted))
nc = NodeCollector(wanted)
nc.apply_file('ontario.osm.pbf', locations=True)
print("collected:", len(nc.coords))

def centroid(pts):
    return (sum(p[0] for p in pts)/len(pts), sum(p[1] for p in pts)/len(pts))

feats=[]
for nid, tags, lat, lon in h.parking_nodes:
    feats.append({"osm_type":"node","osm_id":nid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"tags":tags})
for wid, tags, refs in h.parking_ways:
    pts=[nc.coords[r] for r in refs if r in nc.coords]
    if not pts: continue
    lat,lon=centroid(pts)
    feats.append({"osm_type":"way","osm_id":wid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"tags":tags})
# relations: centroid of member way centroids
way_cent={wid: (sum(nc.coords[r][0] for r in refs if r in nc.coords)/max(1,sum(1 for r in refs if r in nc.coords)),
                sum(nc.coords[r][1] for r in refs if r in nc.coords)/max(1,sum(1 for r in refs if r in nc.coords)))
          for wid,tags,refs in h.parking_ways}
for rid, tags, ways in h.parking_rels:
    pts=[way_cent[w] for w in ways if w in way_cent]
    if not pts: continue
    lat,lon=centroid(pts)
    feats.append({"osm_type":"relation","osm_id":rid,"name":tags.get("name",""),"parking":tags.get("parking",""),
                  "capacity":tags.get("capacity",""),"lat":lat,"lon":lon,"tags":tags})
print("total parking features:", len(feats))
json.dump(feats, open('osm_parking_ontario.json','w'), ensure_ascii=False)
print("saved osm_parking_ontario.json")
