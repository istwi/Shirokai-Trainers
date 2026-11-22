"""26 biome-themed Pokemon Center shells for Java 1.21.1 / Sponge v3.
No NPC entities or functional mod machines are installed by this generator.
"""
import sys,json,math,hashlib
from pathlib import Path
import numpy as np
try:import nbtlib as n
except ImportError:
 sys.path.insert(0,'/workspace/work/safari-generator/deps');import nbtlib as n
from nbtlib import tag as T
from collections import deque
OUT=Path(sys.argv[1] if len(sys.argv)>1 else 'Pokecentros-Safari');OUT.mkdir(parents=True,exist_ok=True)
REG=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/workspace/work/minecraft-registry/reports/reports/blocks.json')
registry=json.loads(REG.read_text()) if REG.exists() else None
# biome, wood, masonry, roof, secondary walls, flora, extra accent
THEMES=[
('plains','oak','cobblestone','deepslate_tiles','oak_planks','poppy','mossy_cobblestone'),
('forest','oak','mossy_cobblestone','deepslate_tiles','oak_planks','fern','moss_block'),
('flower_forest','birch','mossy_cobblestone','deepslate_tiles','birch_planks','allium','flowering_azalea'),
('dark_forest','dark_oak','mossy_stone_bricks','deepslate_tiles','dark_oak_planks','red_mushroom','moss_block'),
('bamboo_jungle','jungle','mossy_cobblestone','dark_prismarine','bamboo_planks','fern','moss_block'),
('jungle','jungle','mossy_stone_bricks','dark_prismarine','jungle_planks','fern','moss_block'),
('taiga','spruce','cobblestone','deepslate_tiles','spruce_planks','fern','mossy_cobblestone'),
('cherry_grove','cherry','stone_bricks','deepslate_tiles','cherry_planks','pink_tulip','flowering_azalea'),
('snowy_taiga','spruce','stone_bricks','deepslate_tiles','spruce_planks','fern','snow_block'),
('meadow','birch','cobblestone','deepslate_tiles','birch_planks','cornflower','mossy_cobblestone'),
('savanna','acacia','stone_bricks','mud_bricks','acacia_planks','dead_bush','coarse_dirt'),
('snowy_plains','spruce','stone_bricks','deepslate_tiles','birch_planks','fern','snow_block'),
('ice_spikes','spruce','stone_bricks','deepslate_tiles','stripped_birch_wood','fern','packed_ice'),
('stony_peaks','spruce','stone_bricks','deepslate_tiles','spruce_planks','fern','andesite'),
('jagged_peaks','spruce','cobbled_deepslate','deepslate_tiles','spruce_planks','fern','snow_block'),
('desert','acacia','sandstone','cut_red_sandstone','smooth_sandstone','dead_bush','cut_sandstone'),
('badlands','acacia','red_sandstone','mud_bricks','orange_terracotta','dead_bush','terracotta'),
('swamp','oak','mossy_cobblestone','deepslate_tiles','oak_planks','fern','mud'),
('mangrove_swamp','mangrove','mud_bricks','deepslate_tiles','mangrove_planks','fern','muddy_mangrove_roots'),
('deep_ocean','spruce','prismarine_bricks','dark_prismarine','spruce_planks','cornflower','prismarine'),
('warm_ocean','jungle','sandstone','dark_prismarine','jungle_planks','poppy','prismarine'),
('river','oak','mossy_stone_bricks','deepslate_tiles','oak_planks','fern','gravel'),
('beach','jungle','sandstone','cut_sandstone','birch_planks','dead_bush','smooth_sandstone'),
('mushroom_fields','dark_oak','mossy_cobblestone','deepslate_tiles','mushroom_stem','red_mushroom','mycelium'),
('dripstone_caves','spruce','dripstone_block','deepslate_tiles','spruce_planks','brown_mushroom','calcite'),
('lush_caves','oak','mossy_stone_bricks','dark_prismarine','oak_planks','flowering_azalea','moss_block')]
STAIRS={'deepslate_tiles':'deepslate_tile','dark_prismarine':'dark_prismarine','cut_red_sandstone':'red_sandstone','cut_sandstone':'sandstone','mud_bricks':'mud_brick'}
def varints(values):
 data=bytearray()
 for v in values.ravel():
  v=int(v)
  while v>=128:data.append((v&127)|128);v>>=7
  data.append(v)
 return bytes(data)
def decode(data):
 vals=[];v=shift=0
 for k in np.asarray(data,np.int8).view(np.uint8):
  v|=(int(k)&127)<<shift
  if k&128:shift+=7
  else:vals.append(v);v=shift=0
 assert shift==0
 return np.array(vals,np.uint16)
def build(theme):
 biome,wood,base,roof,wall,flora,accent=theme
 root=OUT/biome;root.mkdir(exist_ok=True);W,D,H=33,30,30;Y0=-4
 a=np.zeros((H,D,W),np.uint16);pal=['minecraft:air'];be=[]
 def B(s):
  s=s if s.startswith('minecraft:') else 'minecraft:'+s
  if s not in pal:pal.append(s)
  return pal.index(s)
 def put(x,y,z,s):
  assert 0<=x<W and 0<=z<D and Y0<=y<H+Y0,(x,y,z,s)
  a[y-Y0,z,x]=B(s)
 def box(x0,y0,z0,x1,y1,z1,s):
  for y in range(y0,y1+1):
   for z in range(z0,z1+1):
    for x in range(x0,x1+1):put(x,y,z,s)
 def get(x,y,z):return pal[int(a[y-Y0,z,x])]
 log=wood+'_log[axis=y]';beam=wood+'_log[axis=x]';plank=wood+'_planks'
 def fence(x,y,z,ew=False,ns=False):put(x,y,z,wood+'_fence[east='+str(ew).lower()+',west='+str(ew).lower()+',north='+str(ns).lower()+',south='+str(ns).lower()+',waterlogged=false]')
 def lamp(x,y,z,hanging=False):put(x,y,z,'lantern[hanging='+str(hanging).lower()+',waterlogged=false]')
 # Compact foundations / no terrain slab around the building.
 box(3,-4,7,24,0,23,base);box(4,0,8,23,0,22,plank)
 for y in range(1,13):
  mat=base if y<6 else wall
  for x in range(3,25):
   for z in [7,23]:put(x,y,z,mat)
  for z in range(7,24):
   for x in [3,24]:put(x,y,z,mat)
 for x in [3,13,24]:
  for z in [7,23]:box(x,0,z,x,12,z,log)
 for z in [12,18]:
  for x in [3,24]:box(x,0,z,x,12,z,log)
 box(3,6,7,24,6,23,plank);box(3,12,7,24,12,23,plank)
 for z in [7,23]:box(3,5,z,24,5,z,beam);box(3,12,z,24,12,z,beam)
 # Tall windows on both floors and side walls, timber lintels and shutters.
 for low,high in [(2,4),(8,11)]:
  for z in [7,23]:
   for x in [6,7,10,11,21,22]:
    for y in range(low,high+1):put(x,y,z,'glass_pane[east=true,west=true,north=false,south=false,waterlogged=false]')
  for x in [3,24]:
   for z in [9,10,15,16,20,21]:
    for y in range(low,high+1):put(x,y,z,'glass_pane[east=false,west=false,north=true,south=true,waterlogged=false]')
 for x in [5,8,9,12,20,23]:
  for y in [9,10]:put(x,y,24,wood+'_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]')
 def door(x,y,z,facing):
  for half,yy in [('lower',y),('upper',y+1)]:put(x,yy,z,wood+'_door[facing='+facing+',half='+half+',hinge=left,open=false,powered=false]')
 door(18,1,23,'south');door(18,7,23,'south');door(24,7,17,'east')
 # Arch-like entrance frame and sensible single door leaf below emblem.
 for x in [16,20]:box(x,1,24,x,3,24,log)
 box(16,4,24,20,4,24,beam)
 box(14,-4,24,20,0,29,base)
 # Front balcony anchored to log columns, plus slender side walk to stair landing.
 box(3,6,24,25,6,26,plank);box(25,6,17,25,6,25,plank);box(25,6,16,30,6,18,plank)
 for x in [3,13,25]:box(x,-4,26,x,5,26,log)
 for x in range(3,26):
  fence(x,7,26,ew=True)
 for z in range(19,26):fence(26,7,z,ns=True)
 for z in [24,25]:fence(3,7,z,ns=True)
 fence(30,7,17,ns=True)
 for x in [3,13,25]:put(x,7,26,log);lamp(x,8,26)
 # Main staircase outside right elevation; landing connected to upstairs doorway.
 for i in range(6):
  z=24-i
  for x in range(27,30):
   box(x,-4,z,x,i-1,z,base)
   put(x,i,z,wood+'_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
  for x in [26,30]:
   box(x,-4,z,x,i,z,log);fence(x,i+1,z,ns=True)
 box(26,-4,25,30,0,28,base)
 box(20,-4,29,30,0,29,base)
 for x in [27,30]:box(x,-4,17,x,5,17,log)
 for x in range(26,31):fence(x,7,16,ew=True)
 # Small roof over stair landing, tied to solid posts, as in the reference.
 for x in [25,30]:box(x,7,18,x,10,18,log)
 box(25,11,16,31,11,19,plank)
 for x in [25,30]:lamp(x,10,18,True)
 # Low long gable on right wing, high perpendicular gable on left.
 rs=STAIRS[roof]
 snow=biome in ['snowy_taiga','snowy_plains','ice_spikes','jagged_peaks']
 roofs=[]
 for z in range(5,26):
  y=13+min(z-5,25-z)//2;face='north' if z<15 else 'south'
  for x in range(14,27):
   put(x,y,z,rs+'_stairs[facing='+face+',half=bottom,shape=straight,waterlogged=false]');roofs.append((x,y,z))
   if x==26:put(x,y-1,z,plank)
 for x in range(2,17):
  y=13+min(x-2,16-x);face='east' if x<9 else 'west'
  for z in range(5,26):
   put(x,y,z,rs+'_stairs[facing='+face+',half=bottom,shape=straight,waterlogged=false]');roofs.append((x,y,z))
   if x in [2,16] or z in [5,25]:put(x,y,z,wood+'_stairs[facing='+face+',half=bottom,shape=straight,waterlogged=false]')
  for yy in range(13,y):
   for z in [7,23]:put(x,yy,z,wall)
 # Front gable frame / loft window.
 box(9,13,23,9,18,23,log)
 for x in [7,8,10,11]:
  for y in [14,15]:put(x,y,23,'glass')
 box(5,13,23,13,13,23,beam)
 # Chimney solidly rooted on masonry floor, with capped top.
 box(21,1,10,22,19,11,'stone_bricks');box(20,20,9,23,20,12,'brick_slab[type=bottom,waterlogged=false]')
 if snow:
  for x,y,z in roofs:
   if (x==9 or (x>16 and z==15)) and get(x,y+1,z)=='minecraft:air':put(x,y+1,z,'snow_block')
  for x in range(25,32):
   for z in range(16,20):put(x,12,z,'snow[layers=1]')
 # Habitat accent inserts in the lower side wall (not scattered outside).
 for x in [3,24]:
  for z in [13,14]:
   for y in [1,2,3]:put(x,y,z,accent if accent not in ['flowering_azalea','moss_block','coarse_dirt'] else base)
 # Native block Pokeball sign on front, small and unmistakable.
 for dx in range(-2,3):
  for dy in range(-2,3):
   if abs(dx)+abs(dy)>3:continue
   put(18+dx,11+dy,25,'red_concrete' if dy>0 else ('black_concrete' if dy==0 else 'white_concrete'))
 put(18,11,25,'white_concrete')
 # Interiors: reception / healing equipment bays, seating, cabinets, upper lounge.
 box(15,1,11,20,1,11,plank)
 for x in [15,20]:put(x,2,11,'polished_andesite_slab[type=bottom,waterlogged=false]')
 for x in [7,10]:
  put(x,1,10,'smooth_quartz');put(x,2,10,'red_carpet');put(x,1,9,'red_concrete')
  box(x,1,12,x,1,14,'white_wool');put(x,1,12,'red_wool')
 for y in [1,2,7,8]:box(4,y,9,4,y,15,'bookshelf')
 for x in [7,10,16,20]:put(x,7,10,'barrel[facing=up,open=false]')
 for x in [7,10,16,21]:put(x,7,20,wood+'_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]')
 box(15,7,14,19,7,15,plank);put(15,8,14,'flower_pot')
 for x,z in [(8,17),(18,17)]:
  put(x,5,z,plank);lamp(x,4,z,True);put(x,11,z,plank);lamp(x,10,z,True)
 for x in [4,13,23]:
  box(x,4,24,x,4,25,plank);lamp(x,3,25,True)
 # Raised planters are grounded and kept clear of entrances.
 soil='sand' if biome in ['desert','badlands','beach'] else ('mycelium' if biome=='mushroom_fields' else 'grass_block')
 for x in [5,6,10,11,22,23]:
  put(x,0,27,base);put(x,1,27,soil);put(x,2,27,flora)
  put(x,1,28,wood+'_trapdoor[facing=south,half=bottom,open=true,powered=false,waterlogged=false]')
 if biome in ['swamp','mangrove_swamp','river','deep_ocean','warm_ocean']:
  box(3,-4,7,24,-1,23,'air')
  for z in [7,15,23]:
   box(3,-1,z,24,-1,z,beam)
   for x in [3,13,24]:box(x,-4,z,x,-2,z,log)
  for x in [3,13,24]:box(x,-4,26,x,-1,26,log)
 if biome in ['jungle','bamboo_jungle','mangrove_swamp','swamp','lush_caves']:
  for x in [3,13]:
   for y in range(8,12):put(x,y,24,'vine[east=false,north=true,south=false,west=false,up=false]')
 if biome=='mushroom_fields':
  for x in [4,12]:put(x,7,25,'red_mushroom');put(x,6,25,'mycelium')
 if biome in ['dripstone_caves','lush_caves']:
  for x in [4,23]:put(x,0,28,accent);put(x,1,28,flora)
 # All container block entities explicitly encoded, empty by design.
 for i,s in enumerate(pal):
  if any(s.startswith('minecraft:'+k) for k in ['barrel[','flower_pot']):
   for yy,z,x in zip(*np.nonzero(a==i)):
    entity='barrel' if 'barrel' in s else 'flower_pot'
    if entity=='barrel':be.append(T.Compound(Id=T.String('minecraft:barrel'),Pos=T.IntArray([int(x),int(yy),int(z)]),Data=T.Compound(Items=T.List[T.Compound]([]))))
 if registry:
  for s in pal:
   name,_,props=s.partition('[');assert name in registry,s
   given=dict(v.split('=') for v in props.rstrip(']').split(',')) if props else {}
   assert any(all(st.get('properties',{}).get(k)==v for k,v in given.items()) for st in registry[name]['states']),s
 C=T.Compound
 schem=C(Version=T.Int(3),DataVersion=T.Int(3955),Width=T.Short(W),Height=T.Short(H),Length=T.Short(D),Offset=T.IntArray([0,-4,0]),Metadata=C(Name=T.String('Pokecentro '+biome),Author=T.String('Shirokai Safari'),**{'WorldEdit':C(Origin=T.IntArray([0,0,0]))}),Blocks=C(Palette=C({s:T.Int(i) for i,s in enumerate(pal)}),Data=T.ByteArray(np.frombuffer(varints(a),np.int8)),BlockEntities=T.List[T.Compound](be)))
 path=root/('pokecentro_'+biome+'.schem');n.File(C(Schematic=schem)).save(path,gzipped=True)
 # End-to-end data verification, closed doors treated as openable for access.
 loaded=n.load(path)['Schematic'];assert np.array_equal(decode(loaded['Blocks']['Data']).reshape(a.shape),a)
 assert list(loaded['Offset'])==[0,-4,0]
 def passable(s):return s=='minecraft:air' or any(k in s for k in ['_door[','_carpet','lantern[','vine[','red_mushroom','brown_mushroom'])
 def stand(x,y,z):
  return 0<=x<W and 0<=z<D and -3<=y<=22 and passable(get(x,y,z)) and passable(get(x,y+1,z)) and not passable(get(x,y-1,z)) and 'glass_pane' not in get(x,y-1,z)
 spawn=(18,1,25);assert stand(*spawn)
 seen={spawn};q=deque(seen)
 while q:
  x,y,z=q.popleft()
  for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
   for dy in [0,1,-1]:
    p=x+dx,y+dy,z+dz
    if p not in seen and stand(*p):seen.add(p);q.append(p)
 points={'entrada':[18,1,24],'recepcionista':[18,1,10],'cura_1':[7,1,11],'cura_2':[10,1,11],'varanda':[18,7,25],'sala_superior':[18,7,19],'pesquisador':[18,7,13],'topo_escada':[28,7,18],'base_escada':[28,1,25]}
 for k,p in points.items():assert tuple(p) in seen,(biome,k,p)
 lamps=0
 for i,s in enumerate(pal):
  if 'lantern[' not in s:continue
  for yy,z,x in zip(*np.nonzero(a==i)):
   delta=1 if 'hanging=true' in s else -1
   assert int(a[yy+delta,z,x])!=0,(biome,'unsupported light',x,yy,z)
   lamps+=1
 report={'biome':biome,'passed':True,'size':[W,H,D],'offset':[0,-4,0],'verified_blocks':int(a.size),'official_states_checked':registry is not None,'reachable_points':points,'supported_lanterns':lamps,'door_assumption':'doors openable, voxel navigation uses one-block steps; stairs models not simulated','runtime_minecraft_test':False}
 (root/'validation.json').write_text(json.dumps(report,indent=2));(root/'palette.json').write_text(json.dumps(pal,indent=2));np.save(root/'blocks.npy',a)
 return report
reports=[]
for theme in THEMES:
 report=build(theme);reports.append(report);print(theme[0],report['passed'],flush=True)
(OUT/'manifest.json').write_text(json.dumps({'format':'Sponge v3','minecraft':'1.21.1','reference':'two stories, timber frame, stone base, tall windows, front balcony, right exterior staircase','functional_services_installed':False,'centers':reports},indent=2))
