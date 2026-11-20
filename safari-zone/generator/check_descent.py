"""Verify legal standing space along each descent, using the independently flooded graph."""
import sys,json,numpy as np
from pathlib import Path
r=Path(sys.argv[1]);N=1504;P=N*N;seen=set(map(int,np.load(r/'reachable.work.npy')));data=json.loads((r/'biomes/routes.json').read_text());bad=[];checked=0
for c in data['cave_entrances']:
 for point in c['staircase']:
  x,y,z=point;checked+=1
  near=any((y+64+dy)*P+(z+752+dz)*N+x+752+dx in seen for dx in range(-3,4) for dz in range(-3,4) for dy in range(-2,3))
  if not near:bad.append(point)
assert not bad,('Descent without nearby reachable standing space',bad[:15])
(r/'validation/descent_tests.json').write_text(json.dumps({'passed':True,'descent_samples_checked':checked,'unreachable_descent_samples':0,'tolerance':'3 blocks horizontal, 2 vertical, valid floor and 2-block headroom; max navigation step 1'},indent=2));print('Descent checks passed',checked)
