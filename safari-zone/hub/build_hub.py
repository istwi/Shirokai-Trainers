"""Standalone Safari hub, Sponge v3, Java 1.21.1. Python: numpy, nbtlib, pillow."""
import sys,json,math,hashlib,zipfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
try: import nbtlib as n
except ImportError:
 sys.path.insert(0,'/workspace/work/safari-generator/deps');import nbtlib as n
from nbtlib import tag as T
OUT=Path(sys.argv[1] if len(sys.argv)>1 else 'hub-output');OUT.mkdir(parents=True,exist_ok=True)
N=112;Y0=70;H=48;MIN=-56;rng=np.random.default_rng(221126)
palette=['minecraft:air'];a=np.zeros((H,N,N),np.uint16);colors=[(0,0,0)]
def b(s):
 s='minecraft:'+s if ':' not in s else s
 if s not in palette:palette.append(s);colors.append(color(s))
 return palette.index(s)
def color(s):
 s=s.split("[")[0]
 if 'leaves' in s:return (188,121,156) if 'cherry' in s else (65,111,53)
 if s.endswith(('poppy','pink_tulip','allium','cornflower','oxeye_daisy','dandelion')):return (219,137,176)
 for k,c in [('water',(61,145,169)),('grass',(103,148,65)),('moss',(90,124,63)),('dirt',(127,100,69)),('gravel',(141,139,132)),('calcite',(219,213,191)),('deepslate',(64,72,77)),('glass',(145,198,193)),('lantern',(247,196,89)),('stone',(139,146,137)),('cobble',(119,129,115)),('spruce',(113,78,47)),('dark_oak',(72,47,31)),('oak',(161,125,76)),('barrel',(144,107,63)),('bricks',(142,146,138))]:
  if k in s:return c
 return (163,165,133)
def put(x,y,z,s):
 if MIN<=x<MIN+N and MIN<=z<MIN+N and Y0<=y<Y0+H:a[y-Y0,z-MIN,x-MIN]=b(s)
def box(x0,y0,z0,x1,y1,z1,s):
 for y in range(y0,y1+1):
  for z in range(z0,z1+1):
   for x in range(x0,x1+1):put(x,y,z,s)
def get(x,y,z):return palette[int(a[y-Y0,z-MIN,x-MIN])]
def disk(cx,cz,r,y,s):
 for z in range(math.floor(cz-r),math.ceil(cz+r)+1):
  for x in range(math.floor(cx-r),math.ceil(cx+r)+1):
   if (x-cx)**2+(z-cz)**2<=r*r:put(x,y,z,s)
box(-56,70,-56,55,73,55,'stone');box(-56,74,-56,55,75,55,'dirt');box(-56,76,-56,55,76,55,'grass_block')
paths=set()
def trail(points,width=2):
 for p,q in zip(points,points[1:]):
  steps=max(abs(q[0]-p[0]),abs(q[1]-p[1]))*3+1
  for t in np.linspace(0,1,steps):
   cx,cz=np.array(p)*(1-t)+np.array(q)*t
   for z in range(round(cz)-width,round(cz)+width+1):
    for x in range(round(cx)-width,round(cx)+width+1):
     if (x-cx)**2+(z-cz)**2<(width+.4)**2:
      put(x,76,z,rng.choice(['dirt_path','dirt_path','coarse_dirt','gravel']));paths.add((x,z))
trail([(0,-56),(-2,-42),(2,-25),(0,0),(-3,22),(0,40),(0,55)])
trail([(-56,0),(-40,2),(-22,-2),(0,0),(17,-5),(29,-8),(45,-3),(55,0)])
trail([(-29,-19),(-26,-12),(-15,-5)])
trail([(26,-20),(21,-15),(12,-12),(3,-17)])
trail([(-32,17),(-26,12),(-13,14),(-3,22)])
trail([(28,24),(20,20),(13,24),(-3,22)])
# Low spawn terrace, same level as the surrounding walking surface.
disk(0,0,8,76,'stone_bricks');disk(0,0,6,76,'andesite');disk(0,0,2,76,'mossy_stone_bricks');put(0,76,0,'chiseled_stone_bricks')
for x,z in [(-6,-3),(6,3),(-3,6),(3,-6)]:put(x,76,z,'calcite')
fence='spruce_fence[east=false,north=false,south=false,west=false,waterlogged=false]'
def lamp(x,z):
 put(x,76,z,'mossy_cobblestone');box(x,77,z,x,79,z,'spruce_log[axis=y]');put(x,80,z,'lantern[hanging=false,waterlogged=false]')
for x,z in [(-8,-8),(8,8),(-10,10),(10,-10),(-6,-34),(7,36),(-44,-5),(46,5)]:lamp(x,z)
npcs=[];buildings=[]
def house(name,cx,cz,w,d,south=True):
 x0=cx-w//2;x1=cx+w//2;z0=cz-d//2;z1=cz+d//2
 box(x0,75,z0,x1,76,z1,'cobblestone');box(x0+1,76,z0+1,x1-1,76,z1-1,'spruce_planks')
 for y in range(77,82):
  for x in range(x0,x1+1):
   for z in [z0,z1]:put(x,y,z,'calcite' if y>77 else 'stone_bricks')
  for z in range(z0,z1+1):
   for x in [x0,x1]:put(x,y,z,'calcite' if y>77 else 'stone_bricks')
 for x in [x0,x1]:
  for z in [z0,z1]:box(x,77,z,x,82,z,'stripped_spruce_log[axis=y]')
 for y in [79,80]:
  for x in [cx-5,cx-4,cx+4,cx+5]:
   for z in [z0,z1]:put(x,y,z,'glass')
  for z in [cz-2,cz-1,cz+2]:
   for x in [x0,x1]:put(x,y,z,'glass')
 # Gable roof: overhanging stair slopes, deep ridge, timber fascia.
 for x in range(x0-2,x1+3):
  dist=min(x-(x0-2),(x1+2)-x);y=82+dist
  facing='west' if x<=cx else 'east'
  roof='deepslate_tile' if 'cuidado' in name else ('spruce' if 'Pesquisador' in name else 'dark_oak')
  for z in range(z0-2,z1+3):
   put(x,y,z,roof+'_stairs[facing='+facing+',half=bottom,shape=straight,waterlogged=false]')
   if z in [z0-2,z1+2]:put(x,y-1,z,'spruce_log[axis=x]')
  if x0<=x<=x1:
   for yy in range(82,y):
    for z in [z0,z1]:put(x,yy,z,'spruce_planks')
 # Continuous timber ceiling supports interior lamps and ties into wall beams.
 box(x0+1,81,z0+1,x1-1,81,z1-1,'spruce_planks')
 # Timber-framed gables, inset windows and shutters.
 for z in [z0,z1]:
  box(cx,82,z,cx,89,z,'stripped_spruce_log[axis=y]')
  for x in [cx-2,cx-1,cx+1,cx+2]:
   for y in [84,85]:put(x,y,z,'glass')
  for x in range(cx-3,cx+4):put(x,83,z,'spruce_log[axis=x]')
  outside=z+(-1 if z==z0 else 1)
  for x in [cx-6,cx-3,cx+3,cx+6]:
   for y in [79,80]:put(x,y,outside,'spruce_trapdoor[facing='+('north' if z==z0 else 'south')+',half=bottom,open=true,powered=false,waterlogged=false]')
  for x in [cx-5,cx-4,cx+4,cx+5]:
   put(x,78,outside,'moss_block');put(x,79,outside,'pink_tulip')
 # Wide open door and covered porch, entrance matches path grade.
 ez=z1 if south else z0;sign=1 if south else -1
 box(cx-1,77,ez,cx+1,79,ez,'air')
 box(cx-3,76,ez+sign,cx+3,76,ez+sign*3,'spruce_planks') if south else box(cx-3,76,ez-3,cx+3,76,ez-1,'spruce_planks')
 for x in [cx-3,cx+3]:
  box(x,77,ez+sign*3,x,80,ez+sign*3,'stripped_spruce_log[axis=y]');put(x,81,ez+sign*3,'lantern[hanging=false,waterlogged=false]')
 for x in range(cx-3,cx+4):
  for z in range(min(ez,ez+sign*3),max(ez,ez+sign*3)+1):put(x,81,z,'spruce_slab[type=top,waterlogged=false]')
 # Interiors: staffed desk, shelves, seating and overhead light.
 back=cz-2 if south else cz+2
 box(cx-3,77,back,cx+3,77,back,'spruce_planks');box(x0+1,77,cz-3,x0+1,79,cz+3,'bookshelf')
 put(cx,80,cz,'lantern[hanging=true,waterlogged=false]');put(cx,81,cz,'spruce_planks')
 put(x1-2,77,cz-3,'crafting_table');put(x1-2,77,cz+3,'barrel[facing=up,open=false]')
 for x in [cx-4,cx+4]:put(x,77,cz+sign,'spruce_stairs[facing='+('north' if south else 'south')+',half=bottom,shape=straight,waterlogged=false]')
 for x in [cx-5,cx+5]:
  put(x,77,ez+sign,'grass_block');put(x,78,ez+sign,'flowering_azalea')
 # Chimney grounded into roof.
 box(x1-3,81,cz-2,x1-2,94,cz-1,'stone_bricks')
 pos=[cx,77,back-sign];put(cx,76,back-sign,'chiseled_stone_bricks');npcs.append({'role':name,'position':pos})
 buildings.append({'name':name,'center':[cx,cz],'entry':[cx,77,ez+sign*4]})
house('Recepcao / guia Safari',-29,-29,19,15)
house('Centro de cuidado',26,-30,17,15)
house('Pesquisador / missoes',-32,27,17,15,False)
house('Loja / trocas',28,34,17,15,False)
# Pond basin, asymmetric shore and layered mineral bed. Never grass underwater.
pond=set()
for z in range(-4,22):
 for x in range(17,49):
  v=((x-33)/13)**2+((z-8)/10)**2+.12*math.sin(x*.6+z*.3)
  if v<1:
   pond.add((x,z));dep=2 if v<.55 else 1
   put(x,76,z,'water[level=0]');box(x,76-dep+1,z,x,75,z,'water[level=0]')
   put(x,76-dep,z,rng.choice(['gravel','clay','stone','sand','andesite']))
   if v<.5 and rng.random()<.12:put(x,77,z,'lily_pad')
  elif v<1.32 and (x,z) not in paths:put(x,76,z,rng.choice(['grass_block','gravel','moss_block','coarse_dirt']))
# Small timber footbridge over western bay, rail and lantern posts.
for z in range(0,18):
 for x in range(21,25):put(x,77,z,'spruce_planks')
 for x in [20,25]:
  put(x,77,z,'spruce_planks');put(x,78,z,'spruce_fence[east=false,north=true,south=true,west=false,waterlogged=false]')
for x in [20,25]:
 for z in [0,8,17]:
  box(x,74,z,x,79,z,'spruce_log[axis=y]');put(x,80,z,'lantern[hanging=false,waterlogged=false]')
# Two market shelters beside the plaza, each with two NPC positions.
for cx,cz in [(-17,-13),(-18,13)]:
 box(cx-4,76,cz-3,cx+4,76,cz+3,'spruce_planks')
 for x in [cx-4,cx+4]:
  for z in [cz-3,cz+3]:box(x,77,z,x,80,z,'spruce_log[axis=y]')
 for x in range(cx-5,cx+6):
  for z in range(cz-4,cz+5):put(x,81,z,'moss_carpet' if x%3 else 'spruce_slab[type=bottom,waterlogged=false]');put(x,80,z,'spruce_planks')
 box(cx-2,77,cz-1,cx+2,77,cz-1,'barrel[facing=south,open=false]')
 put(cx,79,cz,'lantern[hanging=true,waterlogged=false]')
 for dx in [-2,2]:npcs.append({'role':'Mercador / servico opcional','position':[cx+dx,77,cz-2]})
# Hand-placed woodland groups leave doors and routes open.
def tree(cx,cz,cherry=False):
 log='cherry_log[axis=y]' if cherry else 'oak_log[axis=y]';leaf=('cherry' if cherry else 'oak')+'_leaves[distance=1,persistent=true,waterlogged=false]'
 box(cx,77,cz,cx,83,cz,log)
 for y,r in [(81,3),(82,4),(83,4),(84,3),(85,2)]:
  for z in range(cz-r,cz+r+1):
   for x in range(cx-r,cx+r+1):
    if (x-cx)**2+(z-cz)**2<=r*r and (x!=cx or z!=cz):put(x,y,z,leaf)
for i,(x,z) in enumerate([(-48,-45),(-47,-22),(-48,19),(-46,45),(-15,44),(12,49),(47,46),(47,27),(49,-23),(43,-47),(7,-47),(-11,-48),(-47,8)]):tree(x,z,i%3==0)
# Flower and shrub clusters, no scatter on walking surfaces or inside houses.
for _ in range(1200):
 x,z=map(int,rng.integers(-53,54,2))
 if get(x,76,z)!='minecraft:grass_block' or get(x,77,z)!='minecraft:air':continue
 if any(abs(x-h['center'][0])<14 and abs(z-h['center'][1])<13 for h in buildings):continue
 if (x,z) in paths or x*x+z*z<115:continue
 if rng.random()<.6:put(x,77,z,rng.choice(['short_grass','fern','allium','oxeye_daisy','cornflower','pink_tulip']))
 elif rng.random()<.5:put(x,77,z,'flowering_azalea')
# Benches facing plaza; no obstruction of principal circulation.
for x,z,face in [(-10,3,'east'),(10,3,'west'),(-5,12,'north'),(6,-13,'south')]:
 for dz in [-1,0,1]:put(x,77,z+dz,'spruce_stairs[facing='+face+',half=bottom,shape=straight,waterlogged=false]')
# A quieter second pool and grounded rock / flower gardens at the perimeter.
for z in range(3,14):
 for x in range(-43,-26):
  v=((x+35)/7)**2+((z-8)/4)**2+.12*math.sin(x+z)
  if v<1:
   put(x,75,z,rng.choice(['gravel','clay','andesite']));put(x,76,z,'water[level=0]')
   if v<.5 and rng.random()<.16:put(x,77,z,'lily_pad')
for cx,cz in [(-49,-9),(-12,-36),(12,39),(44,18),(-44,34),(39,-11)]:
 for dx,dz,h in [(0,0,2),(1,0,1),(-1,1,1),(0,1,1)]:
  if get(cx+dx,76,cz+dz)=='minecraft:grass_block':
   box(cx+dx,77,cz+dz,cx+dx,76+h,cz+dz,'mossy_cobblestone' if dx else 'andesite')
# Palette normalize from official defaults when not explicitly provided.
registry_path=Path('/workspace/work/minecraft-registry/reports/reports/blocks.json')
if registry_path.exists():
 registry=json.loads(registry_path.read_text())
 for i,state in enumerate(palette):
  name,_,props=state.partition('[');assert name in registry,name
  given=dict(p.split('=') for p in props.rstrip(']').split(',')) if props else {}
  assert any(all(st.get('properties',{}).get(k)==v for k,v in given.items()) for st in registry[name]['states']),state
# Keep all biome cells untouched when pasted normally; optional plains biome data is omitted.
def varints(v):
 out=bytearray()
 for n0 in v.ravel():
  v0=int(n0)
  while v0>=128:out.append((v0&127)|128);v0>>=7
  out.append(v0)
 return bytes(out)
c=T.Compound
root=c(Schematic=c(Version=T.Int(3),DataVersion=T.Int(3955),Width=T.Short(N),Height=T.Short(H),Length=T.Short(N),Offset=T.IntArray([0,0,0]),Metadata=c(Name=T.String('Safari Woodland Hub'),Author=T.String('Shirokai'),**{'WorldEdit':c(Origin=T.IntArray([-56,70,-56]))}),Blocks=c(Palette=c({s:T.Int(i) for i,s in enumerate(palette)}),Data=T.ByteArray(np.frombuffer(varints(a),np.int8)),BlockEntities=T.List[T.Compound]([]))))
n.File(root).save(OUT/'safari_hub_floresta.schem',gzipped=True)
np.save(OUT/'blocks.npy',a);(OUT/'palette.json').write_text(json.dumps(palette,indent=2))
(OUT/'hub_layout.json').write_text(json.dumps({'paste_at':[-56,70,-56],'size':[N,H,N],'spawn':[0,77,0],'buildings':buildings,'npc_locations':npcs},indent=2,ensure_ascii=False))
# Verify actual geometry with walking flood fill and roundtrip entire schematic.
from collections import deque
passable={b(s) for s in ['air','short_grass','fern','allium','oxeye_daisy','cornflower','pink_tulip','lantern[hanging=true,waterlogged=false]']}
def stand(x,y,z):
 if not(-55<=x<=54 and -55<=z<=54 and 72<=y<=110):return False
 floor=get(x,y-1,z)
 return int(a[y-Y0,z-MIN,x-MIN]) in passable and int(a[y+1-Y0,z-MIN,x-MIN]) in passable and int(a[y-1-Y0,z-MIN,x-MIN]) not in passable and not any(s in floor for s in ['water','leaves'])
seen={(0,77,0)};q=deque(seen)
while q:
 x,y,z=q.popleft()
 for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
  for dy in [0,1,-1]:
   p=(x+dx,y+dy,z+dz)
   if p not in seen and stand(*p):seen.add(p);q.append(p)
for npc in npcs:assert tuple(npc['position']) in seen,npc
for h in buildings:assert tuple(h['entry']) in seen,h
assert all((x,77,z) in seen for x,z in [(0,-54),(0,54),(-54,0),(54,0)])
f=n.load(OUT/'safari_hub_floresta.schem')['Schematic'];data=bytes(np.asarray(f['Blocks']['Data'],np.int8).view(np.uint8));vals=[];v=shift=0
for byt in data:
 v|=(byt&127)<<shift
 if byt&128:shift+=7
 else:vals.append(v);v=shift=0
assert np.array_equal(np.array(vals,np.uint16).reshape(a.shape),a)
report={'passed':True,'npc_spaces':len(npcs),'buildings':len(buildings),'all_npcs_reachable':True,'four_edge_connections':True,'schematic_blocks_roundtrip':int(a.size),'block_states_checked_against_official_registry':registry_path.exists(),'minecraft_client_inspection':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
# Accurate topmost occupied-voxel plan (technical preview).
solid=a!=0;top=H-1-np.argmax(solid[::-1],axis=0);ids=a[top,np.arange(N)[:,None],np.arange(N)[None,:]]
col=np.array([color(s) for s in palette],np.uint8);rgb=col[ids];im=Image.fromarray(rgb).resize((896,896),Image.Resampling.NEAREST);im=ImageOps.expand(im,border=(30,60,30,55),fill=(239,235,221)) if False else im
canvas=Image.new('RGB',(956,1020),(239,235,221));canvas.paste(im,(30,65));draw=ImageDraw.Draw(canvas);draw.text((30,20),'SAFARI / HUB FLORESTA - planta dos blocos gerados | NORTE ^',fill=(40,53,40));draw.text((30,980),'Spawn central | 4 casas | 8 espacos para NPCs | lago e ponte | 112 x 112 blocos',fill=(40,53,40));canvas.save(OUT/'hub_planta.png')
print(json.dumps(report))
