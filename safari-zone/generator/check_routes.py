import sys,json
from pathlib import Path
import numpy as np
from collections import deque
root=Path(sys.argv[1]);data=json.loads((root/'biomes/routes.json').read_text());palette=json.loads((root/'validation/block_palette.json').read_text());a=np.memmap(root/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504));N=1504;P=N*N
mask=np.zeros((N,N),bool);mask[692:813,692:813]=True
for route in data['routes']:
    for x,y,z in route['points']:
        ix=x+752;iz=z+752;mask[max(iz-4,0):iz+5,max(ix-4,0):ix+5]=True
for passage in data.get('underground_passages',[]):
    for x,y,z in passage['points']:
        ix=x+752;iz=z+752;mask[max(0,iz-3):iz+4,max(0,ix-3):ix+4]=True
for cave in data['cave_entrances']:
    for x,y,z in cave['staircase']:
        ix=x+752;iz=z+752;mask[iz-3:iz+4,ix-3:ix+4]=True
passable=[];solid=[]
for i,s in enumerate(palette):
    b=s.split('[')[0].split(':')[1]
    p=b in ['air','short_grass','fern','poppy','dandelion','allium','azure_bluet','oxeye_daisy','cornflower','pink_tulip','lily_of_the_valley','oak_sign','red_mushroom','brown_mushroom','cave_vines','dead_bush','moss_carpet','pink_petals','tall_grass','large_fern','hanging_roots','glow_lichen','spore_blossom','torch','wall_torch']
    passable.append(p);solid.append(not p and b not in ['water','seagrass','kelp','oak_fence','pointed_dripstone','cactus'] and not b.endswith('_leaves'))
passable=np.array(passable);solid=np.array(solid);nodes=set()
for iy in range(1,319):
    valid=mask&solid[a[iy-1]]&passable[a[iy]]&passable[a[iy+1]]
    flat=np.flatnonzero(valid);nodes.update(map(int,iy*P+flat))
start=(77+64)*P+752*N+752;assert start in nodes
q=deque([start]);seen={start}
while q:
    v=q.popleft();iy,r=divmod(v,P);iz,ix=divmod(r,N)
    for delta in [-1,1,-N,N]:
        for dy in [0,-P,P]:
            w=v+delta+dy
            if w in nodes and w not in seen:seen.add(w);q.append(w)
reached_columns={(v%N,(v//N)%N,v//P) for v in seen}
results=[]
for route in data['routes']:
    x,y,z=route['points'][-1];ix=x+752;iz=z+752
    near=[v for v in seen if abs(v%N-ix)<=3 and abs((v//N)%N-iz)<=3]
    results.append({'route':route['kind'],'destination':[x,y,z],'reachable':bool(near)})
for cave in data['cave_entrances']:
    x,y,z=cave['staircase'][-1];ix=x+752;iz=z+752
    near=[v for v in seen if abs(v%N-ix)<=3 and abs((v//N)%N-iz)<=3 and v//P<100]
    results.append({'route':cave['biome']+' stairs','destination':[x,y,z],'reachable':bool(near)})
features_path=root/'biomes/natural_features.json'
if features_path.exists():
    for chamber in json.loads(features_path.read_text())['cave_chambers']:
        x,y,z=chamber.get('walk_at',chamber['center']);ix=x+752;iz=z+752
        nearby=any(abs(nx-ix)<=4 and abs(nz-iz)<=4 and abs(ny-(y+64))<=3 for nx,nz,ny in reached_columns)
        results.append({'route':chamber['biome']+' chamber','destination':[x,y,z],'reachable':nearby})
np.save(root/'reachable.work.npy',np.fromiter(seen,dtype=np.int64))
report={'walkable_nodes_in_route_corridors':len(nodes),'reachable_nodes':len(seen),'destinations':results,'all_destinations_reachable':all(v['reachable'] for v in results),'method':'3D BFS, two blocks of passable headroom, solid floor, maximum step one block. Checks route corridors and cave stairs, not swimming/flying.'}
(root/'validation/routes.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if not report["all_destinations_reachable"]: raise SystemExit("Disconnected destination detected")
