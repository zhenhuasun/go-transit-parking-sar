import json, math
feats=json.load(open('osm_parking_ontario.json'))
stations={d['code']:d for d in json.load(open('go_parking_raw.json'))}
def haversine_m(lat1,lon1,lat2,lon2):
    R=6371000.0
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))
GARAGE={'multi-storey','underground','rooftop'}
def is_garage(f):
    return f['tags'].get('parking') in GARAGE or f['tags'].get('building')=='parking'
def clusters(near, thresh):
    # union-find on centroid distance
    n=len(near); parent=list(range(n))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[ra]=rb
    for i in range(n):
        for j in range(i+1,n):
            if haversine_m(near[i]['lat'],near[i]['lon'],near[j]['lat'],near[j]['lon'])<=thresh:
                union(i,j)
    groups={}
    for i in range(n): groups.setdefault(find(i),[]).append(near[i])
    return list(groups.values())

for code, expect in [('OA',3),('CL',3),('BO',2)]:
    st=stations[code]; lat,lon=float(st['lat']),float(st['lon'])
    near=[f for f in feats if haversine_m(lat,lon,f['lat'],f['lon'])<=800]
    print(f"== {code} {st['name']} expect {expect} GO lots, OSM raw {len(near)}")
    for th in [20,30,40,50,75]:
        cl=clusters(near, th)
        # summarize clusters: size, garage?
        summ=[]
        for c in cl:
            g=sum(1 for f in c if is_garage(f))
            summ.append(f"{len(c)}f{'/G' if g else ''}")
        print(f"  thresh {th}m -> {len(cl)} clusters: {sorted(summ, key=lambda s:-int(s.split('f')[0]))}")
