import sys,json,numpy as np
from pathlib import Path
r=Path(sys.argv[1]);p=json.loads((r/'validation/block_palette.json').read_text());a=np.memmap(r/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504));e=json.loads((r/'validation/ecology.json').read_text());assert e['underwater_grass_columns']==0;assert e['underwater_bed_columns']>100000
assert np.all(a[140,692:813,692:813]==p.index('minecraft:grass_block'))
assert np.all(a[141:224,692:813,692:813]==p.index('minecraft:air'))
# A natural passage floor must not contain constructed road blocks.
bad={p.index(s) for s in ['minecraft:dirt_path','minecraft:spruce_planks','minecraft:stone_bricks']};data=json.loads((r/'biomes/routes.json').read_text());samples=0
for passage in data['underground_passages']:
 if passage['entrance']:continue
 for x,y,z in passage['points']:
  assert int(a[y+63,z+752,x+752]) not in bad
  samples+=1
report={'passed':True,'central_grass_plateau_blocks':121*121,'central_construction_voxels':0,'underwater_grass_columns':0,'natural_passage_samples_without_road_blocks':samples,'soil_transition_columns':e['soil_transition_columns'],'extra_cave_details':e['extra_cave_detail_groups']};(r/'validation/ecology_tests.json').write_text(json.dumps(report,indent=2));print(report)
