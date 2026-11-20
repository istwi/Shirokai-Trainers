"""Quality regression checks on generated blocks and feature metadata."""
import sys,json,math
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]);features=json.loads((root/'biomes/natural_features.json').read_text());trees=features['trees'];palette=json.loads((root/'validation/block_palette.json').read_text());a=np.memmap(root/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504));bio=np.load(root/'biomes/biome_restore/biomes_4x4x4.npz');b3=bio['biomes'];names=list(bio['names'])
assert len(features['lakes'])>=20 and len(features['cave_chambers'])>=12
assert len({t['species'] for t in trees})>=8
entropy={}
for axis in [0,2]:
    counts=np.bincount([t['base'][axis]%7 for t in trees],minlength=7);p=counts/counts.sum();h=-sum(float(v)*math.log2(float(v)) for v in p if v);assert h>2.73,h;entropy['xz'[axis//2]]=h
cherries=[t for t in trees if t['species']=='cherry'];assert len({t['height'] for t in cherries})>=4
assert len({t['radius'] for t in cherries})>=3
water=palette.index('minecraft:water[level=0]');lake_results=[]
for lake in features['lakes']:
    x,y,z=lake['center'];ix=x+752;iz=z+752;ry=lake['water_y']+64
    count=int(np.count_nonzero(np.isin(a[ry,iz-12:iz+13,ix-12:ix+13],[water,palette.index('minecraft:ice')])) )
    assert count>=25,(lake,count)
    lake_results.append(count)
checked=[]
routes=json.loads((root/'biomes/routes.json').read_text())
for cave in routes['cave_entrances']:
    for point in [cave['entrance'],cave['chamber']]:
        x,y,z=point;actual=str(names[int(b3[(y+64)//4,(z+752)//4,(x+752)//4])]);assert actual==cave['biome'],(point,actual)
        assert a[y+64,z+752,x+752] in [0,palette.index('minecraft:torch')],(point,'headroom obstructed')
        assert a[y+65,z+752,x+752]==0,(point,'second headroom obstructed')
        checked.append({'point':point,'biome':actual})
report={'passed':True,'trees':len(trees),'species':sorted({t['species'] for t in trees}),'cherry_height_values':sorted({t['height'] for t in cherries}),'cherry_canopy_radius_values':sorted({t['radius'] for t in cherries}),'position_mod7_entropy_bits':entropy,'lakes':len(lake_results),'minimum_water_or_ice_blocks_in_lake_center_window':min(lake_results),'cave_chambers':len(features['cave_chambers']),'cave_biomes_at_entrances_and_landings':checked,'scope':'Checks real generated data, not Minecraft client rendering.'}
(root/'validation/natural_quality.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
