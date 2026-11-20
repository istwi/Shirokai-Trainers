import sys,json,numpy as np
from pathlib import Path
r=Path(sys.argv[1]);a=np.memmap(r/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504));p=json.loads((r/'validation/block_palette.json').read_text());data=json.loads((r/'biomes/routes.json').read_text());features=json.loads((r/'biomes/natural_features.json').read_text());water=p.index('minecraft:water[level=0]');bad=[];checked=0
for path in data['underground_passages']:
 for x,y,z in path['points']:
  iy=y+64;ix=x+752;iz=z+752;checked+=1
  if a[iy-2,iz,ix] in [0,water]:bad.append([x,y,z])
assert not bad,('cave floors lacking foundation',bad[:10])
wettrees=[]
for t in features['trees']:
 x,y,z=t['base'];patch=a[y+64:y+66,z+751:z+754,x+751:x+754]
 if np.any(patch==water):wettrees.append(t['base'])
assert not wettrees,wettrees[:10]
report={'passed':True,'cave_floor_samples_supported':checked,'tree_bases_with_adjacent_water':len(wettrees),'trees_checked':len(features['trees'])};(r/'validation/supports.json').write_text(json.dumps(report,indent=2));print(report)
