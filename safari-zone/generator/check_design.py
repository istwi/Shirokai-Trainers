import sys,json,numpy as np
from pathlib import Path
r=Path(sys.argv[1]);d=json.loads((r/'validation/design.json').read_text());assert len(d['ocean_routes'])==1;assert d['bridge_lanterns']>10 and d['cave_torches']>40
p=json.loads((r/'validation/block_palette.json').read_text());a=np.memmap(r/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504));s=np.load(r/'surface.work.npy');b=np.load(r/'biomes/biome_restore/biomes_4x4x4.npz');names=list(b['names']);forest=np.repeat(np.repeat(b['biomes'][60],4,axis=0),4,axis=1)==names.index('forest');z,x=np.nonzero(forest);ground=a[s[z,x]+64,z,x];ratio=float(np.mean(ground==p.index('minecraft:grass_block')));assert ratio>.70,ratio
light=p.index('minecraft:torch');supported=0
for x,y,z in d['cave_torch_positions']:
 iy=y+64;ix=x+752;iz=z+752
 assert a[iy,iz,ix]==light and a[iy-1,iz,ix] not in [0,p.index('minecraft:water[level=0]')];supported+=1
report={'passed':True,'ocean_routes':d['ocean_routes'],'bridge_lanterns':d['bridge_lanterns'],'supported_cave_torches':supported,'forest_grass_ground_fraction':ratio};(r/'validation/design_tests.json').write_text(json.dumps(report,indent=2));print(report)
