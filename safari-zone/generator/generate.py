#!/usr/bin/env python3
"""Shirokai Safari: deterministic Java 1.21.1 Anvil + Sponge schematic v3 generator."""
import sys, math, json, gzip, struct, zlib, time, hashlib, argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import numpy as np
from scipy.ndimage import gaussian_filter, zoom
from PIL import Image, ImageDraw, ImageFont
import natural
import finish
import nbtlib as n
from nbtlib import tag as T

SEED=20261120; DATA_VERSION=3955; MIN=-752; SIZE=1504; YMIN=-64; HEIGHT=320
SITES=[('flower_forest',-390,-70,81),('dark_forest',-580,-260,85),('bamboo_jungle',400,30,81),('taiga',-320,-430,91),('forest',-180,-180,82),('jungle',540,230,87),('cherry_grove',80,-250,105),('snowy_taiga',-170,-600,94),('plains',0,0,76),('meadow',-60,-370,109),('savanna',-70,390,83),('snowy_plains',220,-500,88),('ice_spikes',460,-540,86),('stony_peaks',-530,-580,162),('jagged_peaks',70,-690,186),('desert',-300,580,77),('badlands',-590,440,105),('swamp',150,260,65),('mangrove_swamp',330,450,65),('deep_ocean',590,640,33),('warm_ocean',630,410,43)]
BIOMES=[s[0] for s in SITES]+['river','beach','mushroom_fields','dripstone_caves','lush_caves']
BID={b:i for i,b in enumerate(BIOMES)}
COLORS=['#72bd54','#274632','#3f9d54','#597c66','#41904c','#237b3e','#eca3c4','#a4c7bc','#a2c75d','#7dba74','#c4b45f','#e0edf0','#b4dce8','#8b9297','#cbd0d3','#e6cd83','#bf744c','#527f70','#446f50','#28568d','#45b9c2','#448fd1','#f2db9f','#a37baf','#9e8e80','#65b176']
BLOCKS=[]; INDEX={}
def block(s):
    if not s.startswith('minecraft:'): s='minecraft:'+s
    if s not in INDEX: INDEX[s]=len(BLOCKS); BLOCKS.append(s)
    return INDEX[s]
AIR=block('air');STONE=block('stone');DEEP=block('deepslate');BED=block('bedrock');DIRT=block('dirt');GRASS=block('grass_block');SAND=block('sand');WATER=block('water[level=0]');SNOW=block('snow_block');GRAVEL=block('gravel');MUD=block('mud');MYCEL=block('mycelium');RED=block('red_sand');TERRA=block('terracotta');SANDSTONE=block('sandstone');MOSS=block('moss_block');CLAY=block('clay');ICE=block('packed_ice');ICEWATER=block('ice');PATH=block('dirt_path');OAK=block('oak_log[axis=y]');SPRUCE=block('spruce_log[axis=y]');BIRCH=block('birch_log[axis=y]');JUNGLE=block('jungle_log[axis=y]');CHERRY=block('cherry_log[axis=y]');DARK=block('dark_oak_log[axis=y]');MANGROVE=block('mangrove_log[axis=y]')
LEAVES={b:block(b+'_leaves[distance=1,persistent=true,waterlogged=false]') for b in ['oak','spruce','birch','jungle','cherry','dark_oak','mangrove']}
PLANK=block('spruce_planks');BRICK=block('stone_bricks');COBBLE=block('cobblestone');WHITE=block('white_concrete');CYAN=block('cyan_concrete');BLUE=block('light_blue_concrete');LIGHT=block('sea_lantern');FENCE=block('oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]');SLAB=block('oak_slab[type=bottom,waterlogged=false]');SIGN=block('oak_sign[rotation=0,waterlogged=false]');GLASS=block('glass');LADDER=block('ladder[facing=north,waterlogged=false]')
FLOWERS=[block(x) for x in ['poppy','dandelion','allium','azure_bluet','oxeye_daisy','cornflower','pink_tulip','lily_of_the_valley','short_grass','fern']]
BAMBOO=block('bamboo[age=1,leaves=large,stage=1]');CACTUS=block('cactus[age=0]');DEADBUSH=block('dead_bush');LILY=block('lily_pad');KELP=block('kelp[age=25]');SEAGRASS=block('seagrass');GLOW=block('glowstone');HAY=block('hay_block[axis=y]')
CORALS=[block(x+'_coral_block') for x in ['brain','bubble','fire','horn','tube']]
MUSHROOMS=[block('red_mushroom_block'),block('brown_mushroom_block')];STEM=block('mushroom_stem');SMALLMUSH=[block('red_mushroom'),block('brown_mushroom')]
DRIPUP=block('pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]');DRIPDOWN=block('pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]');DRIP=block('dripstone_block');AZALEA=block('flowering_azalea');VINE=block('cave_vines[age=0,berries=true]');GOLD=block('gold_block')
assert len(BLOCKS)<256

def compound(**kw): return T.Compound(kw)
def nbtbytes(root, name=''):
    import io
    out=io.BytesIO(); n.File(root,root_name=name).write(out); return out.getvalue()
def signed_longs(a): return T.LongArray(np.asarray(a,dtype=np.uint64).view(np.int64))
def pack(values,bits):
    a=np.asarray(values,dtype=np.uint64).ravel(); per=64//bits
    a=np.pad(a,(0,(-len(a))%per)).reshape(-1,per)
    return signed_longs(np.bitwise_or.reduce(a << (np.arange(per,dtype=np.uint64)*np.uint64(bits)),axis=1))
def blockstate(s):
    name,_,props=s.partition('['); out=compound(Name=T.String(name))
    if props: out['Properties']=T.Compound({k:T.String(v) for k,v in (p.split('=') for p in props.rstrip(']').split(','))})
    return out

def build(out):
    t=time.time(); out.mkdir(parents=True,exist_ok=True)
    for sub in ['world/safari/region','schematics','biomes/biome_restore','maps','validation']: (out/sub).mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(SEED)
    Z,X=np.mgrid[MIN:MIN+SIZE,MIN:MIN+SIZE].astype(np.float32)
    def noise(scale):
        a=rng.normal(size=(math.ceil(SIZE/scale)+3,)*2)
        b=zoom(a,SIZE/a.shape[0],order=3)[:SIZE,:SIZE].astype(np.float32)
        return b/np.std(b)
    large=noise(155); detail=noise(39); fine=noise(10); micro=noise(4); texture=noise(23)
    wx=X+38*np.sin(Z/135)+23*np.sin(X/211)+detail*9; wz=Z+37*np.sin(X/153)+detail*7
    best=np.full((SIZE,SIZE),1e20,np.float32); biome=np.zeros((SIZE,SIZE),np.uint8)
    weights=np.zeros_like(X); heights=np.zeros_like(X)
    for i,(b,x,z,h) in enumerate(SITES):
        dist=(wx-x)**2+(wz-z)**2
        mask=dist<best; biome[mask]=i; best[mask]=dist[mask]
        w=np.exp(-dist/19000); weights+=w; heights+=w*h
    surface=heights/np.maximum(weights,1e-20)+large*9+detail*4.2+fine*1.15+micro*.32
    mountain=np.isin(biome,[BID['stony_peaks'],BID['jagged_peaks']]);surface+=mountain*(np.maximum(0,detail*14+large*9)+np.maximum(0,1-np.abs(fine))**2*7)
    # Ocean shelf and irregular mushroom island.
    ocean=np.isin(biome,[BID['deep_ocean'],BID['warm_ocean']])
    surface[ocean]=np.minimum(surface[ocean],49+detail[ocean]*3)
    coastal=gaussian_filter(ocean.astype(np.float32),10)
    softened=gaussian_filter(surface,12)
    transition=(coastal>.02)&(coastal<.98)
    surface[transition]=softened[transition]
    island_r=np.sqrt((X-626)**2+(Z-622)**2)
    island=island_r<65+6*np.sin(X/19)+5*np.sin(Z/21)
    surface[island]=67+13*np.maximum(0,1-island_r[island]/75)+detail[island]*3.2+fine[island]*.6
    biome[island]=BID['mushroom_fields'];ocean[island]=False
    # Edge shelf joins the flat-ocean generator outside the authored area.
    edge=np.minimum.reduce([X-MIN,Z-MIN,MIN+SIZE-1-X,MIN+SIZE-1-Z]); ew=np.clip(edge/36,0,1)
    surface=33*(1-ew)+surface*ew; biome[edge<20]=BID['deep_ocean'];ocean[edge<20]=True
    coast=(~ocean)&(~island)&(coastal>.06)&(coastal<.94)&(surface<67.5)&(np.isin(biome,[BID['jungle'],BID['mangrove_swamp'],BID['swamp']]))
    biome[coast]=BID['beach'];surface[coast]=64+np.maximum(0,surface[coast]-64)*.7
    # Meandering river connecting all the way to the surrounding ocean.
    river_x=-105+155*np.sin(Z/215)+42*np.sin(Z/83)
    rd=np.abs(X-river_x); river=(rd<9)&(~ocean)&(~island)&(X*X+Z*Z>90**2)
    bank=(rd<95)&(~ocean)&(~island)&(X*X+Z*Z>90**2)
    factor=np.clip((rd-7)/88,0,1);factor=factor*factor*(3-2*factor);surface[bank]=59*(1-factor[bank])+surface[bank]*factor[bank]
    biome[river]=BID['river'];surface[river]=58+fine[river]*.6
    hubr=np.sqrt(X*X+Z*Z); clearing_distance=np.maximum(np.abs(X),np.abs(Z)); blend=np.clip((clearing_distance-64)/105,0,1);blend=blend*blend*(3-2*blend)
    surface=76*(1-blend)+surface*blend;biome[clearing_distance<72]=BID['plains']
    surface=gaussian_filter(surface,1.3)
    surface=np.clip(np.rint(surface),31,221).astype(np.int16)
    surface,lake_levels,lake_records=natural.lakes(surface,biome,texture,rng,BID,MIN)
    print('Terrain, heterogeneous relief and',len(lake_records),'organic lakes prepared',flush=True)
    # Array order Y,Z,X matches Minecraft section/schematic ordering.
    a=np.memmap(out/'terrain.work',mode='w+',dtype=np.uint8,shape=(HEIGHT,SIZE,SIZE))
    for iy in range(HEIGHT):
        y=iy+YMIN
        a[iy]=np.where(y<=surface,DEEP if y<0 else STONE,np.where((y<=63)|(y<=lake_levels),WATER,AIR))
        if y==YMIN:a[iy]=BED
    top=np.full((SIZE,SIZE),GRASS,np.uint8)
    for names,b in [(['desert','beach'],SAND),(['badlands'],RED),(['swamp','mangrove_swamp'],MUD),(['mushroom_fields'],MYCEL),(['stony_peaks','jagged_peaks'],STONE),(['snowy_taiga','snowy_plains','ice_spikes'],SNOW),(['deep_ocean','warm_ocean','river'],SAND)]:
        top[np.isin(biome,[BID[v] for v in names])]=b
    # Native ground palettes in irregular patches, with exposed rock on steeper slopes.
    slope=np.hypot(*np.gradient(surface.astype(np.float32)))
    forest=np.isin(biome,[BID[b] for b in ['forest','dark_forest','taiga','snowy_taiga','jungle','bamboo_jungle']])
    top[np.isin(biome,[BID['taiga'],BID['dark_forest']])&(texture>.8)]=block('podzol')
    top[forest&(texture>1.5)&(fine>.6)]=block('coarse_dirt')
    top[forest&(fine>2.1)&(texture>.7)]=block('rooted_dirt')
    upland=np.isin(biome,[BID[b] for b in ['meadow','cherry_grove','stony_peaks','jagged_peaks']])
    top[upland&(slope>1.8)&(fine>.05)]=STONE
    top[upland&(slope>2.6)&(texture>.4)]=block('andesite')
    wet=surface<lake_levels;top[wet&(texture<0)]=CLAY;top[wet&(texture>=0)]=GRAVEL
    zz,xx=np.indices((SIZE,SIZE)); sy=surface-YMIN
    for depth in range(1,5):a[sy-depth,zz,xx]=np.where(top==SAND,SANDSTONE,np.where(top==RED,TERRA,np.where(top==STONE,STONE,DIRT)))
    a[sy,zz,xx]=top
    # Stratified badlands.
    bad=biome==BID['badlands']
    strata=[TERRA,block('orange_terracotta'),block('yellow_terracotta'),block('white_terracotta'),block('red_terracotta')]
    for y in range(50,130):
        mask=bad&(surface>y+4);a[y-YMIN,mask]=strata[(y//4)%len(strata)]
    cave_marks,cave_entries,cave_passages,cave_chambers=natural.caves(a,surface,MIN,YMIN,block,BID,rng)
    # Freeze surface water in cold habitats.
    cold=np.isin(biome,[BID[b] for b in ['snowy_taiga','snowy_plains','ice_spikes']])
    for water_y in np.unique(np.maximum(lake_levels,63)):
        freeze=cold&(surface<water_y)&(np.maximum(lake_levels,63)==water_y)
        a[int(water_y)-YMIN,freeze]=ICEWATER
    positions=[];tiles=[]
    def local(x,z):return int(x)-MIN,int(z)-MIN
    def setb(x,y,z,b):
        ix,iz=local(x,z)
        if 0<=ix<SIZE and 0<=iz<SIZE and YMIN<=y<YMIN+HEIGHT:a[y-YMIN,iz,ix]=b
    def cub(x0,y0,z0,x1,y1,z1,b):
        x0,x1=max(x0,MIN),min(x1,MIN+SIZE-1);z0,z1=max(z0,MIN),min(z1,MIN+SIZE-1)
        if x1>=x0 and z1>=z0:a[max(y0-YMIN,0):min(y1-YMIN+1,HEIGHT),z0-MIN:z1-MIN+1,x0-MIN:x1-MIN+1]=b
    def ground(x,z):ix,iz=local(x,z);return int(surface[iz,ix])
    def sign(x,y,z,text):
        setb(x,y,z,SIGN)
        messages=[json.dumps({'text':line,'color':'dark_green'}) for line in (text.split('|')+['']*4)[:4]]
        tiles.append(compound(id=T.String('minecraft:sign'),x=T.Int(x),y=T.Int(y),z=T.Int(z),is_waxed=T.Byte(1),front_text=compound(messages=T.List[T.String](messages),color=T.String('black'),has_glowing_text=T.Byte(0)),back_text=compound(messages=T.List[T.String](['{"text":""}']*4),color=T.String('black'),has_glowing_text=T.Byte(0))))
    def lamp(x,y,z):
        cub(x,y,z,x,y+2,z,FENCE);setb(x,y+3,z,LIGHT);setb(x,y+4,z,SLAB)
    # Routes are graded to a max 1-block rise per step and never terminate in water.
    route_mask=np.zeros((SIZE,SIZE),bool);routes=[]
    def route(points,width=5,kind='trilha',end_foot=None):
        if points[0]==(0,0):
            tx,tz=points[-1];gate=(60 if tx>0 else -60,0) if abs(tx)>abs(tz) else (0,60 if tz>0 else -60)
            points=[(0,0),gate]+natural.astar_route([gate]+points[1:],surface,lake_levels,MIN)[1:]
        else:points=natural.astar_route(points,surface,lake_levels,MIN)
        samples=[]
        for (x0,z0),(x1,z1) in zip(points,points[1:]):
            steps=max(abs(x1-x0),abs(z1-z0));length=max(1,math.hypot(x1-x0,z1-z0));amp=0 if max(abs(x0),abs(x1),abs(z0),abs(z1))<=60 else min(12,length*.06)
            samples.extend([(round(x0+(x1-x0)*j/max(1,steps)-(z1-z0)/length*amp*math.sin(math.pi*j/max(1,steps))),round(z0+(z1-z0)*j/max(1,steps)+(x1-x0)/length*amp*math.sin(math.pi*j/max(1,steps)))) for j in range(steps)])
        samples.append(points[-1]); desired=np.array([max(64,ground(x,z),int(lake_levels[z-MIN,x-MIN])+1) for x,z in samples],dtype=np.int16)
        if end_foot is not None:desired[-1]=end_foot-1
        desired[0]=desired[0]
        for _ in range(2):
            for i in range(1,len(desired)):desired[i]=min(desired[i],desired[i-1]+1)
            for i in range(len(desired)-2,-1,-1):desired[i]=min(desired[i],desired[i+1]+1)
        for (x,z),y in zip(samples,desired):
            y=int(y);r=width//2
            for dx in range(-r,r+1):
                for dz in range(-r,r+1):
                    ix,iz=local(x+dx,z+dz)
                    if not(1<=ix<SIZE-1 and 1<=iz<SIZE-1):continue
                    gy=int(surface[iz,ix]);bridge=gy<max(63,int(lake_levels[iz,ix]))
                    # Rounded, irregular path verges; a three-block walking core stays continuous.
                    radius=width*.5+.25*math.sin((x+dx)*.8+(z+dz)*.53)
                    if (dx*dx+dz*dz)>radius*radius and (abs(dx)>1 or abs(dz)>1):continue
                    cub(x+dx,y+1,z+dz,x+dx,y+5,z+dz,AIR)
                    if not bridge and y>gy:cub(x+dx,gy,z+dz,x+dx,y-1,z+dz,DIRT)
                    material=PATH
                    if not bridge:
                        rvalue=(math.sin((x+dx)*12.9898+(z+dz)*78.233)*43758.5453)%1
                        if rvalue<.18:material=block('coarse_dirt')
                        elif rvalue<.24:material=GRAVEL
                    setb(x+dx,y,z+dz,PLANK if bridge else material)
                    if bridge and abs(dx)==r and abs(dz)==r:setb(x+dx,y+1,z+dz,FENCE)
                    route_mask[iz,ix]=True
            samples_y=[x,y+1,z];positions.append(samples_y)
        routes.append({'kind':kind,'width':width,'points':[[x,int(y)+1,z] for (x,z),y in zip(samples,desired)]})
    # A loop and radial routes ensure every surface habitat has a walking connection.
    ring=[(-420,-420),(0,-510),(420,-420),(520,0),(410,380),(0,520),(-460,390),(-520,0),(-420,-420)]
    route(ring,5,'circuito principal')
    for x,z in [(-420,0),(0,-510),(420,0),(0,520)]:
        route([(0,0),(int(x*.4)+12,int(z*.4)-10),(x,z)],5,'caminho principal')
    for b,x,z,h in SITES:
        if x*x+z*z<100**2 or b in ['deep_ocean','warm_ocean']:continue
        nearest=min(routes[0]['points'],key=lambda p:(p[0]-x)**2+(p[2]-z)**2)
        route([(nearest[0],nearest[2]),(x,z)],3,'acesso '+b)
    route([(410,380),(626,622)],5,'ponte unica ilha dos cogumelos')
    # Detour loop, waterfall access and trails to actual cave entrances.
    route([(-390,-70),(-480,90),(-290,210),(0,260),(150,260)],3,'trilha de floresta e pantano')
    for cave in cave_entries:
        x,start,z=cave['entrance'];route([(0,0),(x,z)],3,'entrada '+cave['biome'],end_foot=start)
        sign(x-5,start,z,'CAVERNA NATURAL|'+cave['biome'].replace('_',' ')+'|Entrada sinalizada')
    for passage in cave_passages:
        if passage['entrance']:
            for x,y,z in passage['points']:route_mask[max(0,z-MIN-3):z-MIN+4,max(0,x-MIN-3):x-MIN+4]=True
    # Tree and decoration passes avoid all walking corridors.
    forbidden=route_mask.copy();forbidden|=clearing_distance<72
    from scipy.ndimage import binary_dilation
    forbidden=binary_dilation(forbidden,iterations=4)
    tree_types={b:('oak',OAK) for b in ['forest','flower_forest','plains','meadow','savanna','swamp']}
    tree_types.update({'dark_forest':('dark_oak',DARK),'taiga':('spruce',SPRUCE),'snowy_taiga':('spruce',SPRUCE),'jungle':('jungle',JUNGLE),'bamboo_jungle':('jungle',JUNGLE),'cherry_grove':('cherry',CHERRY),'mangrove_swamp':('mangrove',MANGROVE)})
    for wx,wz in [(490,170),(420,110)]:
        forbidden[wz-MIN-16:wz-MIN+17,wx-MIN-16:wx-MIN+17]=True
    counts,tree_records=natural.trees(a,surface,biome,forbidden,texture,rng,MIN,YMIN,block,BID,lake_levels)
    natural.vegetation(a,surface,biome,forbidden,texture,lake_levels,rng,MIN,YMIN,block,BID)
    # Fallen trunks and mossy boulders use scattered, non-repeating positions.
    for _ in range(650):
        ix=int(rng.integers(15,SIZE-15));iz=int(rng.integers(15,SIZE-15));x=ix+MIN;z=iz+MIN;y=int(surface[iz,ix])+1
        if forbidden[iz-6:iz+7,ix-6:ix+7].any() or y<=max(63,int(lake_levels[iz,ix])) or a[y-YMIN-1,iz,ix] in [AIR,WATER]:continue
        b=BIOMES[int(biome[iz,ix])]
        if b in tree_types:
            length=int(rng.integers(3,7))
            if np.ptp(surface[iz,ix:ix+length])>0:continue
            for j in range(length):setb(x+j,y,z,block('oak_log[axis=x]'))
            setb(x+length//2,y+1,z,MOSS)
        elif b not in ['desert','ice_spikes','snowy_plains','beach','deep_ocean','warm_ocean']:
            for dy in range(3):
                for dx in range(-2,3):
                    for dz in range(-2,3):
                        if dx*dx+dz*dz+dy*dy<6:setb(x+dx,y+dy,z+dz,block('mossy_cobblestone') if rng.random()<.5 else STONE)
    print('Irregular branched trees',sum(counts.values()),'lakes',len(lake_records),'cave chambers',len(cave_chambers),flush=True)
    # Small ruins, shelters and lookouts, all integrated with the path network.
    for b,x,z in [('desert',-300,580),('jungle',540,230),('badlands',-590,440)]:
        y=max(64,ground(x,z));material=SANDSTONE if b=='desert' else BRICK
        for dx in [-9,9]:
            for dz in [-9,9]:cub(x+dx,y,z+dz,x+dx+1,y+int(rng.integers(3,7)),z+dz+1,material)
        for dx in range(-8,9):setb(x+dx,y,z-9,material)
    for b,x,z,h in SITES:
        y=max(64,ground(x,z));sign(x-3,y+1,z,b.upper().replace('_',' ')+'|SHIROKAI SAFARI')
    # The operator builds their own hub: leave only a clear grass plateau.
    cub(-60,77,-60,60,125,60,AIR)
    cub(-60,76,-60,60,76,60,GRASS)
    natural.repair_route_floors(a,routes,surface,lake_levels,MIN,YMIN,block)
    finish.finish(a,routes,surface,lake_levels,MIN,YMIN,block,out)
    finish.details(a,routes,surface,lake_levels,MIN,YMIN,block,out)
    import design
    design.polish(a,routes,cave_passages,surface,lake_levels,MIN,YMIN,block,out)
    import ecology
    ecology.blend_and_detail(a,surface,lake_levels,biome,texture,MIN,YMIN,block,BIOMES,BID,out,cave_marks,cave_passages)
    tiles=[t for t in tiles if abs(int(t['x']))>60 or abs(int(t['z']))>60]
    import landforms
    landforms.enrich(a,surface,biome,cave_chambers,cave_passages,MIN,YMIN,block,BID,out)
    # Reconcile descent surfaces after all decoration and surface-road operations.
    import cave_ramps,copy
    ramp_entries=copy.deepcopy(cave_entries)
    for entry in ramp_entries:entry['chamber'][1]+=2
    ramp_field=cave_ramps.apply(a,ramp_entries,cave_passages,MIN,YMIN,block)
    for passage in cave_passages:
        if passage['entrance']:
            for point in passage['points']:
                x,y,z=point;point[1]=int(ramp_field[z-MIN,x-MIN])+YMIN
    for entry in cave_entries:
        for label in ['entrance','chamber']:
            x,y,z=entry[label];value=int(ramp_field[z-MIN,x-MIN])
            if value<30000:entry[label][1]=value+YMIN
    for iy in range(1,220):
        layer=a[iy];layer[layer==block('torch')]=AIR
    design.polish(a,routes,cave_passages,surface,lake_levels,MIN,YMIN,block,out)
    # Biome volume, 4x4x4 voxels. Sections use actual registry names.
    quart=biome[::4,::4].copy();b3=np.broadcast_to(quart,(HEIGHT//4,SIZE//4,SIZE//4)).copy()
    # Apply cave biomes exactly where the carved passages and chambers exist, including entrances.
    marked=cave_marks>=0;b3[marked]=cave_marks[marked]
    np.savez_compressed(out/'biomes/biome_restore/biomes_4x4x4.npz',biomes=b3,names=np.array(BIOMES),origin=np.array([MIN,YMIN,MIN]))
    (out/'biomes/routes.json').write_text(json.dumps({'routes':routes,'cave_entrances':cave_entries,'underground_passages':cave_passages},ensure_ascii=False))
    np.save(out/'surface.work.npy',surface)
    (out/'biomes/natural_features.json').write_text(json.dumps({'revision':6,'trees':tree_records,'lakes':lake_records,'cave_chambers':cave_chambers}))
    print('Hub, routes, caves, shelters and decorations complete',flush=True)
    export_world(out,a,b3,tiles)
    export_schematics(out,a,b3,tiles)
    layout(out,biome,surface,route_mask)
    coordinates=[]
    for i,b in enumerate(BIOMES):
        if b in ['lush_caves','dripstone_caves']:
            target=next(c for c in cave_entries if c['biome']==b);sample=target['chamber'];coord=[sample[0],sample[1]+2,sample[2]];area=None
        else:
            coords=np.argwhere(np.repeat(np.repeat(quart,4,axis=0),4,axis=1)==i);assert len(coords)>0,b
            preferred=np.array([next((s[2] for s in SITES if s[0]==b),coords[len(coords)//2,0]+MIN),next((s[1] for s in SITES if s[0]==b),coords[len(coords)//2,1]+MIN)])-MIN
            k=np.argmin(np.sum((coords-preferred)**2,axis=1));iz,ix=map(int,coords[k]);coord=[ix+MIN,max(64,int(surface[iz,ix]))+1,iz+MIN];area=int(len(coords))
        coordinates.append({'biome':'minecraft:'+b,'visit':coord,'surface_area_blocks':area,'color':COLORS[i]})
    (out/'biomes/biome_coordinates.json').write_text(json.dumps({'minecraft':'1.21.1','bounds':{'x':[-750,749],'z':[-750,749]},'generated_chunk_bounds':[-752,751],'spawn':[0,77,0],'biomes':coordinates},indent=2,ensure_ascii=False))
    (out/'validation/build.json').write_text(json.dumps({'seed':SEED,'seconds':round(time.time()-t),'blocks':len(BLOCKS),'chunks':(SIZE//16)**2,'minecraft_data_version':DATA_VERSION,'biomes':BIOMES,'tree_counts':counts},indent=2))
    a.flush();del a
    print('COMPLETE',round(time.time()-t),'seconds',flush=True)

def export_world(out,a,b3,tiles):
    palettes=[blockstate(b) for b in BLOCKS];tilemap={}
    for t in tiles:tilemap.setdefault((int(t['x'])//16,int(t['z'])//16),[]).append(t)
    regions={};created=0
    for cz in range(MIN//16,(MIN+SIZE)//16):
        for cx in range(MIN//16,(MIN+SIZE)//16):
            ix=cx*16-MIN;iz=cz*16-MIN;sections=[]
            for si in range(HEIGHT//16):
                vol=a[si*16:si*16+16,iz:iz+16,ix:ix+16];u,inv=np.unique(vol,return_inverse=True)
                bs=compound(palette=T.List[T.Compound]([palettes[int(v)] for v in u]))
                if len(u)>1:bs['data']=pack(inv,max(4,(len(u)-1).bit_length()))
                bv=b3[si*4:si*4+4,iz//4:iz//4+4,ix//4:ix//4+4];bu,bi=np.unique(bv,return_inverse=True)
                bios=compound(palette=T.List[T.String](['minecraft:'+BIOMES[int(v)] for v in bu]))
                if len(bu)>1:bios['data']=pack(bi,max(1,(len(bu)-1).bit_length()))
                sections.append(compound(Y=T.Byte(si+YMIN//16),block_states=bs,biomes=bios))
            height=np.max(np.where(a[:,iz:iz+16,ix:ix+16]!=AIR,np.arange(HEIGHT)[:,None,None]+1,0),axis=0)
            chunk=compound(DataVersion=T.Int(DATA_VERSION),xPos=T.Int(cx),zPos=T.Int(cz),yPos=T.Int(-4),Status=T.String('minecraft:full'),LastUpdate=T.Long(0),InhabitedTime=T.Long(0),isLightOn=T.Byte(0),sections=T.List[T.Compound](sections),block_entities=T.List[T.Compound](tilemap.get((cx,cz),[])),Heightmaps=compound(WORLD_SURFACE=pack(height,9),MOTION_BLOCKING=pack(height,9)),fluid_ticks=T.List[T.Compound]([]),block_ticks=T.List[T.Compound]([]),PostProcessing=T.List[T.List]([T.List[T.Short]([]) for _ in range(HEIGHT//16)]),structures=compound(starts=compound(),References=compound()))
            compressed=zlib.compress(nbtbytes(chunk),6);body=struct.pack('>I',len(compressed)+1)+b'\x02'+compressed
            regions.setdefault((cx//32,cz//32),[]).append((cx%32+cz%32*32,body))
            created+=1
        if (cz-MIN//16)%10==0:print('World chunks',created,'/',(SIZE//16)**2,flush=True)
    for (rx,rz),chunks in regions.items():
        header=bytearray(8192);payload=bytearray();sector=2
        for index,body in chunks:
            count=math.ceil(len(body)/4096);assert count<256
            header[index*4:index*4+4]=((sector<<8)|count).to_bytes(4,'big');payload.extend(body);payload.extend(b'\0'*(count*4096-len(body)));sector+=count
        (out/f'world/safari/region/r.{rx}.{rz}.mca').write_bytes(header+payload)
    ocean_generator=compound(type=T.String('minecraft:flat'),settings=compound(biome=T.String('minecraft:deep_ocean'),lakes=T.Byte(0),features=T.Byte(0),layers=T.List[T.Compound]([compound(height=T.Int(1),block=T.String('minecraft:bedrock')),compound(height=T.Int(95),block=T.String('minecraft:stone')),compound(height=T.Int(2),block=T.String('minecraft:sand')),compound(height=T.Int(30),block=T.String('minecraft:water'))]),structure_overrides=T.List[T.String]([])))
    dims=compound(**{'minecraft:overworld':compound(type=T.String('minecraft:overworld'),generator=ocean_generator),'minecraft:the_nether':compound(type=T.String('minecraft:the_nether'),generator=compound(type=T.String('minecraft:noise'),settings=T.String('minecraft:nether'),biome_source=compound(type=T.String('minecraft:multi_noise'),preset=T.String('minecraft:nether')))),'minecraft:the_end':compound(type=T.String('minecraft:the_end'),generator=compound(type=T.String('minecraft:noise'),settings=T.String('minecraft:end'),biome_source=compound(type=T.String('minecraft:the_end'))))})
    data=compound(DataVersion=T.Int(DATA_VERSION),Version=compound(Id=T.Int(DATA_VERSION),Name=T.String('1.21.1'),Series=T.String('main'),Snapshot=T.Byte(0)),LevelName=T.String('safari'),version=T.Int(19133),SpawnX=T.Int(0),SpawnY=T.Int(77),SpawnZ=T.Int(0),SpawnAngle=T.Float(180),GameType=T.Int(2),Difficulty=T.Byte(2),initialized=T.Byte(1),allowCommands=T.Byte(1),hardcore=T.Byte(0),Time=T.Long(0),DayTime=T.Long(1000),LastPlayed=T.Long(int(time.time()*1000)),GameRules=compound(doMobSpawning=T.String('true'),doDaylightCycle=T.String('true'),doWeatherCycle=T.String('true'),spawnRadius=T.String('0'),doFireTick=T.String('false')),WorldGenSettings=compound(seed=T.Long(SEED),generate_features=T.Byte(0),bonus_chest=T.Byte(0),dimensions=dims),DataPacks=compound(Enabled=T.List[T.String](['vanilla']),Disabled=T.List[T.String]([])))
    n.File(compound(Data=data)).save(out/'world/safari/level.dat',gzipped=True)
    (out/'world/safari/icon.png').write_bytes(b'') # replaced by layout crop below
    (out/'validation/block_palette.json').write_text(json.dumps(BLOCKS,indent=2))

# Sponge v3 uses VarInt block and biome data in YZX order, in a Schematic compound.
def varints(array):
    values=np.asarray(array).ravel()
    if values.max(initial=0)<128:return values.astype(np.uint8).tobytes()
    lo=(values&127).astype(np.uint8);hi=values>=128
    result=np.empty(len(values)+int(hi.sum()),np.uint8);loc=np.arange(len(values))+np.cumsum(hi)-hi
    result[loc]=lo|np.where(hi,128,0).astype(np.uint8);result[loc[hi]+1]=(values[hi]>>7).astype(np.uint8)
    return result.tobytes()

def export_schematics(out,a,b3,tiles):
    manifest=[]
    def export(name,x0,z0,w,d,y0=YMIN,height=HEIGHT):
        ix=x0-MIN;iz=z0-MIN;v=a[y0-YMIN:y0-YMIN+height,iz:iz+d,ix:ix+w];used=np.unique(v);lookup=np.zeros(256,np.uint8);lookup[used]=np.arange(len(used),dtype=np.uint8)
        pdata=T.Compound({BLOCKS[int(k)]:T.Int(i) for i,k in enumerate(used)})
        entities=[]
        for t in tiles:
            x,y,z=int(t['x']),int(t['y']),int(t['z'])
            if x0<=x<x0+w and z0<=z<z0+d and y0<=y<y0+height:
                properties=T.Compound({k:val for k,val in t.items() if k not in ['id','x','y','z']})
                entities.append(compound(Id=t['id'],Pos=T.IntArray([x-x0,y-y0,z-z0]),Data=properties))
        # v3 biome array is full block resolution; source biomes are quart cells.
        yy=(np.arange(y0,y0+height)-YMIN)//4;zz=(np.arange(z0,z0+d)-MIN)//4;xx=(np.arange(x0,x0+w)-MIN)//4
        bios=b3[np.ix_(yy,zz,xx)]
        schem=compound(Version=T.Int(3),DataVersion=T.Int(DATA_VERSION),Width=T.Short(w),Height=T.Short(height),Length=T.Short(d),Offset=T.IntArray([0,0,0]),Metadata=compound(Name=T.String(name),Author=T.String('Shirokai Safari Generator'),Date=T.Long(int(time.time()*1000)),**{'WorldEdit':compound(Version=T.String('7.3'),EditingPlatform=T.String('enginehub:fabric'),Origin=T.IntArray([x0,y0,z0]))}),Blocks=compound(Palette=pdata,Data=T.ByteArray(np.frombuffer(varints(lookup[v]),dtype=np.int8)),BlockEntities=T.List[T.Compound](entities)),Biomes=compound(Palette=T.Compound({'minecraft:'+b:T.Int(i) for i,b in enumerate(BIOMES)}),Data=T.ByteArray(np.frombuffer(varints(bios),dtype=np.int8))))
        n.File(compound(Schematic=schem)).save(out/'schematics'/f'{name}.schem',gzipped=True)
        manifest.append({'file':name+'.schem','paste_at':[x0,y0,z0],'size':[w,height,d],'blocks':w*height*d})
    for rz,z0 in enumerate(range(-750,750,250)):
        for rx,x0 in enumerate(range(-750,750,250)):
            name=f'safari_{rz:02d}_{rx:02d}';export(name,x0,z0,250,250);print('Schematic',name,flush=True)
    export('safari_clearing',-60,-60,120,120,64,48)
    (out/'schematics/manifest.json').write_text(json.dumps({'format':'Sponge v3','paste':'Stand at paste_at, //schem load sponge.3 file then //paste -b. Do not use -a for full terrain restoration.','tiles':manifest},indent=2))

def layout(out,biome,surface,paths):
    rgb=np.array([tuple(bytes.fromhex(c[1:])) for c in COLORS],np.uint8)[biome]
    light=np.clip(.8+np.gradient(surface.astype(float))[0]*.07-np.gradient(surface.astype(float))[1]*.05,.45,1.2)
    rgb=np.clip(rgb*light[:,:,None],0,255).astype(np.uint8);rgb[paths]=[220,190,135]
    im=Image.fromarray(rgb);draw=ImageDraw.Draw(im)
    try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
    except OSError:font=ImageFont.load_default()
    for b,x,z,h in SITES:
        draw.text((x-MIN,z-MIN),b,fill='white',stroke_width=2,stroke_fill='black',font=font,anchor='mm')
    draw.text((626-MIN,622-MIN),'mushroom_fields',fill='white',stroke_width=2,stroke_fill='black',font=font,anchor='mm')
    draw.rectangle((MIN*-1-60,MIN*-1-60,MIN*-1+60,MIN*-1+60),outline='white',width=3)
    draw.text((752,752),'CLAREIRA LIVRE',fill='white',stroke_width=2,stroke_fill='black',font=font,anchor='mm')
    draw.text((30,20),'SHIROKAI SAFARI / NORTE ↑ / Minecraft 1.21.1 / 1.500 × 1.500',fill='white',stroke_width=2,stroke_fill='black',font=font)
    im.save(out/'maps/safari_layout.png');im.crop((680,680,824,824)).resize((64,64)).save(out/'world/safari/icon.png')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='Shirokai-Safari');args=p.parse_args();build(Path(args.output))
