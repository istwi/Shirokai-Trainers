import sys,json,numpy as np
from pathlib import Path
r=Path(sys.argv[1]);d=json.loads((r/'validation/landforms.json').read_text());assert d['rock_pillars']>=8;assert d['rock_mounds']>=20;assert d['coral_colonies']>=50;assert d['coral_fans']>=100;assert d['mushroom_understory']>=500;assert d['extra_mushroom_canopies']>=10
p=json.loads((r/'validation/block_palette.json').read_text());a=np.memmap(r/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504));surface=np.load(r/'surface.work.npy');bio=np.load(r/'biomes/biome_restore/biomes_4x4x4.npz');names=list(bio['names']);macro=np.repeat(np.repeat(bio['biomes'][60],4,axis=0),4,axis=1);sand=p.index('minecraft:sand');ratios={}
for name in ['savanna','mangrove_swamp']:
 z,x=np.nonzero(macro==names.index(name));fraction=float(np.mean(a[surface[z,x]+64,z,x]==sand));assert fraction<.16,(name,fraction);ratios[name]=fraction
for x,y,z,top in d['pillar_positions']:
 col=a[y+64:top+65,z+752,x+752];assert np.all(col!=0)
(r/'validation/landforms_tests.json').write_text(json.dumps({'passed':True,'pillars':d['rock_pillars'],'mounds':d['rock_mounds'],'coral_colonies':d['coral_colonies'],'coral_fans':d['coral_fans'],'mushroom_understory':d['mushroom_understory'],'mushroom_canopies':d['extra_mushroom_canopies'],'sand_ground_fraction':ratios},indent=2));print('Landforms checks passed',ratios)
