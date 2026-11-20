"""Natural terrain details, branching trees and connected 3D cave systems for Safari v2."""
import math, heapq, json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation


def lakes(surface,biome,noise,rng,bid,origin):
    h=surface.astype(np.float32).copy();N=h.shape[0];levels=np.full(h.shape,-320,np.int16);records=[]
    # Named habitats each receive a water feature; extra ponds break up large interiors.
    proposals=[(-355,-80,30,22),(-550,-230,24,32),(-240,-440,25,30),(120,-245,34,24),(270,-520,28,21),(-90,380,32,23),(-270,560,23,19),(490,260,35,25),(335,45,30,32),(-155,-150,24,18),(150,280,35,30),(315,465,33,28),(-580,430,18,23)]
    proposals += [(int(rng.integers(-620,620)),int(rng.integers(-600,600)),int(rng.integers(14,29)),int(rng.integers(12,25))) for _ in range(19)]
    for x,z,rx,rz in proposals:
        ix=x-origin;iz=z-origin
        if ix<70 or iz<70 or ix>N-70 or iz>N-70 or x*x+z*z<110**2:continue
        b=int(biome[iz,ix])
        if b in [bid[k] for k in ['deep_ocean','warm_ocean','river','beach','mushroom_fields','stony_peaks','jagged_peaks']]:continue
        x0,x1=ix-rx-8,ix+rx+9;z0,z1=iz-rz-8,iz+rz+9
        zz,xx=np.mgrid[z0:z1,x0:x1];theta=np.arctan2((zz-iz)/rz,(xx-ix)/rx)
        radial=np.sqrt(((xx-ix)/rx)**2+((zz-iz)/rz)**2)/(1+.1*np.sin(theta*3+rx)+.07*np.cos(theta*5+rz))
        wet=radial<.84;outer=radial<1.15
        patch=h[z0:z1,x0:x1];rim=patch[(radial>.9)&(radial<1.1)]
        water=max(65,int(np.percentile(rim,35))-1);depth=float(rng.uniform(3.5,7.5))
        target=water-depth*np.maximum(0,1-(radial/.86)**2)
        target=np.where(wet,target,np.maximum(water+1,patch))
        blend=np.clip((1.15-radial)/.26,0,1)
        patch[:]=np.where(outer,patch*(1-blend)+target*blend,patch)
        levels[z0:z1,x0:x1][wet]=water
        records.append({'center':[x,water+1,z],'radii':[rx,rz],'water_y':water,'depth':round(depth,1)})
    return np.rint(h).astype(np.int16),levels,records


def astar_route(points,surface,levels,origin):
    """Four-block route grid penalizing sharp slopes; resampled by the caller."""
    N=surface.shape[0];step=4;S=N//step
    coarse=surface[::step,::step].astype(float);water=levels[::step,::step]>coarse
    result=[]
    for start,end in zip(points,points[1:]):
        sx,sz=round((start[0]-origin)/step),round((start[1]-origin)/step)
        ex,ez=round((end[0]-origin)/step),round((end[1]-origin)/step)
        sx,sz,ex,ez=[min(S-2,max(1,v)) for v in [sx,sz,ex,ez]]
        lowx=max(1,min(sx,ex)-20);highx=min(S-2,max(sx,ex)+20)
        lowz=max(1,min(sz,ez)-20);highz=min(S-2,max(sz,ez)+20)
        startnode=(sx,sz);goal=(ex,ez);cost={startnode:0.};parent={};queue=[(0.,sx,sz)];closed=set()
        while queue:
            _,x,z=heapq.heappop(queue)
            if (x,z) in closed:continue
            if (x,z)==goal:break
            closed.add((x,z))
            for dx,dz in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(1,-1),(-1,1)]:
                xx=x+dx;zz=z+dz
                if not(lowx<=xx<=highx and lowz<=zz<=highz):continue
                rise=abs(coarse[zz,xx]-coarse[z,x]);distance=math.hypot(dx,dz)*step
                edge=distance+rise*2.8+max(0,rise-2)**2*1.5+(5 if water[zz,xx] else 0)
                # Small deterministic spatial variation avoids ruler-straight stretches.
                edge+=.3*(1+math.sin(xx*.73+zz*1.17))
                c=cost[(x,z)]+edge
                if c<cost.get((xx,zz),1e20):
                    cost[(xx,zz)]=c;parent[(xx,zz)]=(x,z);heapq.heappush(queue,(c+math.hypot(ex-xx,ez-zz)*step,xx,zz))
        if goal not in parent and goal!=startnode:result.extend([start,end]);continue
        path=[goal]
        while path[-1]!=startnode:path.append(parent[path[-1]])
        path.reverse();world=[(x*step+origin,z*step+origin) for x,z in path]
        # Retain the topology while smoothing stair-shaped grid corners.
        if len(world)>6:
            arr=np.array(world,float);arr[:,0]=gaussian_filter(arr[:,0],1);arr[:,1]=gaussian_filter(arr[:,1],1)
            world=[(int(round(x)),int(round(z))) for x,z in arr]
        world[0]=start;world[-1]=end;result.extend(world[:-1])
    result.append(points[-1]);return result


def caves(a,surface,origin,ymin,block,bid,rng):
    N=surface.shape[0];H=a.shape[0];mark=np.full((H//4,N//4,N//4),-1,np.int8)
    air=block('air');stone=block('stone');moss=block('moss_block');drip=block('dripstone_block')
    water=block('water[level=0]');calcite=block('calcite');tuff=block('tuff');clay=block('clay')
    passages=[];chambers=[]
    floor_requests={}
    def ellipsoid(x,y,z,rx,ry,rz,kind,exposed=False):
        ix=int(round(x))-origin;iz=int(round(z))-origin;iy=int(round(y))-ymin
        x0=max(0,int(ix-rx-2));x1=min(N,int(ix+rx+3));z0=max(0,int(iz-rz-2));z1=min(N,int(iz+rz+3));y0=max(1,int(iy-ry-2));y1=min(H-1,int(iy+ry+3))
        zz,xx=np.mgrid[z0:z1,x0:x1];yy=np.arange(y0,y1)[:,None,None]+ymin
        r=((xx[None]-ix)/rx)**2+((zz[None]-iz)/rz)**2+((yy-y)/ry)**2
        wobble=.065*np.sin((xx[None]+yy)*.53)+.045*np.cos((zz[None]-yy)*.43)
        mask=r<1+wobble
        if not exposed:mask&=yy<surface[z0:z1,x0:x1][None]-7
        patch=a[y0:y1,z0:z1,x0:x1];patch[mask]=air
        # Mark actual carved quart cells, including the elevated natural entrances.
        points=np.nonzero(mask)
        if len(points[0]):mark[(points[0]+y0)//4,(points[1]+z0)//4,(points[2]+x0)//4]=bid[kind]
    def walkway(x,y,z,kind):
        ix=int(round(x))-origin;iz=int(round(z))-origin;iy=int(round(y))-ymin
        if not(3<ix<N-3 and 3<iz<N-3):return
        for dx in [-1,0,1]:
            for dz in [-1,0,1]:floor_requests.setdefault((ix+dx,iz+dz),{})[iy]=bid[kind]
    def tunnel(points,kind,entrance=False):
        path=[]
        for p,q in zip(points,points[1:]):
            steps=max(1,int(max(abs(q[0]-p[0]),abs(q[2]-p[2]),abs(q[1]-p[1]))))
            for j in range(steps):
                t=j/steps;x=p[0]+(q[0]-p[0])*t;z=p[2]+(q[2]-p[2])*t;y=p[1]+(q[1]-p[1])*t
                # Wandering centerline with a continuous walkable grade.
                z+=2.2*math.sin(t*math.pi)*math.sin(x/21)
                radius=5.5+1.6*math.sin(x/17+z/29)
                ellipsoid(x,y+3,z,radius,6.0+1.4*math.cos(z/27),radius*.9,kind,entrance)
                path.append([int(round(x)),int(round(y)),int(round(z))])
        path.append(list(map(int,points[-1])))
        for x,y,z in path:walkway(x,y,z,kind)
        passages.append({'kind':kind,'points':path,'entrance':entrance});return path
    groups={
      'lush_caves':[(-150,27,185),(-335,22,220),(-440,25,150),(-360,30,45),(-235,25,-20),(-150,28,90)],
      'dripstone_caves':[(280,27,-340),(285,25,-285),(360,22,-420),(225,28,-520),(75,24,-440),(30,27,-275)]}
    for kind,rooms in groups.items():
        for x,y,z in rooms:
            rx=int(rng.integers(22,35));rz=int(rng.integers(20,34));ry=int(rng.integers(14,21))
            ellipsoid(x,y+5,z,rx,ry,rz,kind);chambers.append({'biome':kind,'center':[x,y+5,z],'radii':[rx,ry,rz]})
            # Side chambers at varied heights produce branching and overhangs.
            dx=int(rng.integers(-35,36));dz=int(rng.integers(-35,36))
            ellipsoid(x+dx,y+11,z+dz,rx*.55,ry*.6,rz*.55,kind)
            tunnel([(x,y,z),(x+dx,y+3,z+dz)],kind)
        for p,q in zip(rooms,rooms[1:]+rooms[:1]):tunnel([p,q],kind)
        tunnel([rooms[0],rooms[3]],kind)
    tunnel([(-150,28,90),(-60,23,15),(20,24,-100),(30,27,-275)],'dripstone_caves')
    entries=[]
    for kind,x,z in [('lush_caves',-290,130),('dripstone_caves',110,-340)]:
        start=int(surface[z-origin,x-origin])+1
        target=groups[kind][0]
        # Curving, long graded descent: obvious rock mouth instead of an invisible stair slot.
        controls=[(x,start,z),(x+28,start-9,z+15),(x+55,start-25,z-2),(x+90,max(29,start-43),z+14),target]
        path=tunnel(controls,kind,True)
        entries.append({'biome':kind,'entrance':[x,start,z],'staircase':path,'chamber':target})
    # Reapply walking floors after intersections to avoid chambers interrupting their grade.
    for passage in passages:
        for x,y,z in passage['points']:walkway(x,y,z,passage['kind'])
    # Distinct stone surfaces and native cave decorations throughout the carved space.
    palette_ids={name:block(name) for name in ['moss_block','rooted_dirt','clay','calcite','tuff','dripstone_block','glow_lichen[down=false,east=false,north=false,south=false,up=true,waterlogged=false,west=false]','flowering_azalea','azalea','small_dripleaf[facing=north,half=lower,waterlogged=false]']}
    plants=[block('azalea'),block('flowering_azalea'),block('moss_carpet')]
    ceiling_vine=block('cave_vines[age=0,berries=true]');tipvine=block('cave_vines_plant[berries=true]')
    dsup=block('pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]');dsdown=block('pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]')
    for chamber in chambers:
        x,y,z=chamber['center'];rx,ry,rz=chamber['radii'];kind=chamber['biome']
        for _ in range(950):
            xx=x+int(rng.integers(-rx,rx+1));zz=z+int(rng.integers(-rz,rz+1));ix=xx-origin;iz=zz-origin
            column=a[max(0,y-ry-ymin-2):min(H,y+ry-ymin+3),iz,ix];base=max(0,y-ry-ymin-2)
            airspots=np.flatnonzero(column==air)
            if not len(airspots):continue
            fy=int(airspots[0])+base;cy=int(airspots[-1])+base
            if fy<=1 or fy>=H-2 or cy>=H-1:continue
            if kind=='lush_caves':
                a[fy-1,iz,ix]=moss if rng.random()<.78 else clay
                if a[fy+1,iz,ix]==air and rng.random()<.4:a[fy,iz,ix]=plants[int(rng.integers(0,len(plants)))]
                if rng.random()<.4:
                    length=int(rng.integers(1,6))
                    for iy in range(max(fy+4,cy-length+1),cy+1):a[iy,iz,ix]=tipvine
                    a[cy,iz,ix]=ceiling_vine
            else:
                a[fy-1,iz,ix]=drip if rng.random()<.7 else calcite
                if rng.random()<.24:a[fy,iz,ix]=dsup
                if rng.random()<.32:a[cy,iz,ix]=dsdown
                if rng.random()<.12:a[min(H-1,cy+1),iz,ix]=calcite
                if rng.random()<.1:a[cy,iz,ix]=palette_ids['glow_lichen[down=false,east=false,north=false,south=false,up=true,waterlogged=false,west=false]']
        # Dig a basin below the lowest surrounding rock lip, so water is held
        # by terrain rather than resting on an elevated clay platform.
        poolx=x+rx//2;poolz=z;floors=[]
        low=max(1,int(y-ry-4)-ymin);high=min(H,int(y+ry+3)-ymin)
        for dz in range(-7,8):
            for dx in range(-8,9):
                radial=(dx/6)**2+(dz/5)**2
                if not 1.0<radial<1.6:continue
                column=a[low:high,poolz+dz-origin,poolx+dx-origin]
                opens=np.flatnonzero(column==air)
                if len(opens):floors.append(int(opens[0])+low)
        if floors:
            level=max(3,min(floors)-2)
            for dz in range(-5,6):
                for dx in range(-6,7):
                    if (dx/6)**2+(dz/5)**2>1:continue
                    ix=poolx+dx-origin;iz=poolz+dz-origin
                    column=a[low:high,iz,ix];opens=np.flatnonzero(column==air)
                    if not len(opens):continue
                    opening=int(opens[0])+low
                    a[level-2,iz,ix]=clay if kind=='lush_caves' else calcite
                    a[level-1:level+1,iz,ix]=water
                    a[level+1:max(level+2,opening+2),iz,ix]=air
    # Finish with free headroom on the continuous walking centerlines.
    for passage in passages:
        for x,y,z in passage['points']:walkway(x,y,z,passage['kind'])
    # Keep separate floors when a deep tunnel passes beneath an entrance.
    # Collapse only nearby requests, then grade adjacent floors on the same level.
    layers={};heights={};kinds={}
    for (ix,iz),requested in floor_requests.items():
        groups=[]
        for value in sorted(requested):
            if not groups or value-groups[-1][-1]>=5:groups.append([value])
            else:groups[-1].append(value)
        layers[(ix,iz)]=[min(group) for group in groups]
        for layer,group in enumerate(groups):
            key=(ix,iz,layer);height=min(group)
            if height+ymin<50:
                # Follow the chamber floor instead of projecting an elevated walkway.
                j=height-1
                while j>1 and int(a[j,iz,ix]) in [air,water]:j-=1
                height=j+1
            heights[key]=height;kinds[key]=requested[min(group)]
    initial=dict(heights);queue=[(h,*key) for key,h in heights.items()];heapq.heapify(queue)
    while queue:
        h,ix,iz,layer=heapq.heappop(queue);key=(ix,iz,layer)
        if heights[key]!=h:continue
        for dx,dz in [(-1,0),(1,0),(0,-1),(0,1)]:
            for other,original in enumerate(layers.get((ix+dx,iz+dz),[])):
                if abs(original-layers[(ix,iz)][layer])>5:continue
                neighbor=(ix+dx,iz+dz,other)
                if h+1<heights[neighbor]:heights[neighbor]=h+1;heapq.heappush(queue,(h+1,*neighbor))
    for (ix,iz,layer),iy in heights.items():a[iy:iy+4,iz,ix]=air
    for key,iy in heights.items():
        ix,iz,_=key
        # A graded path is a rock shelf attached to the cave floor, never a thin slab.
        floor_material=moss if kinds[key]==bid['lush_caves'] else drip
        j=iy-2
        while j>0 and int(a[j,iz,ix]) in [air,water]:a[j,iz,ix]=stone;j-=1
        a[iy-1,iz,ix]=floor_material
        mark[iy//4,iz//4,ix//4]=kinds[key]
    def corrected(point):
        x,y,z=point;ix=x-origin;iz=z-origin
        layer=min(range(len(layers[(ix,iz)])),key=lambda i:abs(layers[(ix,iz)][i]-(y-ymin)))
        return [x,int(heights[(ix,iz,layer)])+ymin,z]
    for passage in passages:
        for point in passage['points']:point[:]=corrected(point)
    for chamber in chambers:
        x,y,z=chamber['center'];chamber['walk_at']=corrected([x,y-5,z])
    for entry in entries:
        entry['chamber']=corrected(entry['chamber']);entry['entrance']=corrected(entry['entrance'])
    return mark,entries,passages,chambers


def trees(a,surface,biome,forbidden,detail,rng,origin,ymin,block,bid,levels):
    N=surface.shape[0];H=a.shape[0];air=block('air');water=block('water[level=0]')
    species={k:'oak' for k in ['forest','flower_forest','plains','meadow','swamp']}
    species.update({'savanna':'acacia','dark_forest':'dark_oak','taiga':'spruce','snowy_taiga':'spruce','jungle':'jungle','bamboo_jungle':'jungle','cherry_grove':'cherry','mangrove_swamp':'mangrove'})
    reverse={v:k for k,v in bid.items()};occupied=np.zeros((N,N),bool);records=[];counts={k:0 for k in bid}
    base_density={'dark_forest':.88,'jungle':.78,'bamboo_jungle':.43,'forest':.72,'taiga':.62,'snowy_taiga':.58,'flower_forest':.36,'mangrove_swamp':.6,'swamp':.28,'cherry_grove':.4,'plains':.018,'meadow':.025,'savanna':.12}
    logs={sp:{axis:block(f'{sp}_log[axis={axis}]') for axis in 'xyz'} for sp in set(species.values())|{'birch'}}
    leaves={sp:block(sp+'_leaves[distance=1,persistent=true,waterlogged=false]') for sp in logs}
    leafy=set(leaves.values());snow=block('snow');snowfull=block('snow_block')
    def put(x,y,z,b):
        ix=int(round(x))-origin;iz=int(round(z))-origin;iy=int(round(y))-ymin
        if 0<=ix<N and 0<=iz<N and 0<=iy<H:a[iy,iz,ix]=b
    def limb(p,q,sp):
        length=max(1,int(np.linalg.norm(np.subtract(q,p))*2));d=np.subtract(q,p)
        axis='y' if abs(d[1])>=max(abs(d[0]),abs(d[2])) else ('x' if abs(d[0])>abs(d[2]) else 'z')
        for t in np.linspace(0,1,length+1):put(*(np.array(p)+(np.array(q)-p)*t),logs[sp][axis])
    def crown(x,y,z,rx,ry,rz,sp,seed):
        ix=int(round(x))-origin;iz=int(round(z))-origin;iy=int(round(y))-ymin
        r=int(math.ceil(max(rx,rz)))+1;rY=int(math.ceil(ry))+1
        x0=max(0,ix-r);x1=min(N,ix+r+1);z0=max(0,iz-r);z1=min(N,iz+r+1);y0=max(0,iy-rY);y1=min(H,iy+rY+1)
        zz,xx=np.mgrid[z0:z1,x0:x1];yy=np.arange(y0,y1)[:,None,None]
        distance=((xx[None]-ix)/rx)**2+((zz[None]-iz)/rz)**2+((yy-iy)/ry)**2
        variation=.12*np.sin(xx[None]*1.6+zz[None]*.9+yy*1.3+seed)
        m=distance<1+variation;patch=a[y0:y1,z0:z1,x0:x1]
        empty=(patch==air)|np.isin(patch,list(leafy));patch[m&empty]=leaves[sp]
    forbidden=binary_dilation(forbidden,iterations=2) | binary_dilation(surface<=np.maximum(63,levels),iterations=5)
    for _ in range(105000):
        ix=int(rng.integers(15,N-15));iz=int(rng.integers(15,N-15));name=reverse[int(biome[iz,ix])]
        if name not in species or forbidden[iz,ix] or occupied[iz,ix]:continue
        density=base_density[name]*float(np.clip(.65+detail[iz,ix]*.3,.12,1.15))
        if rng.random()>density:continue
        y=int(surface[iz,ix])+1;x=ix+origin;z=iz+origin
        if y<64 or a[y-ymin-1,iz,ix] in [air,water] or a[y-ymin,iz,ix] not in [air,water]:continue
        sp=species[name]
        if sp=='oak' and name in ['forest','flower_forest'] and rng.random()<.2:sp='birch'
        if sp=='spruce':h=int(rng.integers(7,17));radius=int(rng.integers(3,5))
        elif sp=='jungle':h=int(rng.integers(8,18))+(7 if rng.random()<.15 else 0);radius=4
        elif sp=='dark_oak':h=int(rng.integers(6,11));radius=5
        elif sp=='cherry':h=int(rng.integers(4,8));radius=int(rng.integers(4,7))
        else:h=int(rng.integers(4,10));radius=int(rng.integers(3,5))
        spacing=int(rng.integers(3,7));occupied[iz-spacing:iz+spacing+1,ix-spacing:ix+spacing+1]=True
        bend=rng.uniform(0,2*math.pi);lean=float(rng.uniform(.3,2.8));trunkend=(x+math.cos(bend)*lean,y+h,z+math.sin(bend)*lean)
        limb((x,y,z),trunkend,sp)
        if sp in ['dark_oak','jungle'] and (sp=='dark_oak' or h>18):
            for dx,dz in [(1,0),(0,1),(1,1)]:limb((x+dx,y,z+dz),(trunkend[0]+dx,trunkend[1],trunkend[2]+dz),sp)
        variant=''
        if sp=='spruce':
            variant='pine' if rng.random()<.35 else 'spruce';bottom=int(h*.5) if variant=='pine' else 2
            for dy in range(bottom,h+2,2):
                rr=max(.9,radius*(1-(dy-bottom)/(h+2-bottom)))
                cx=x+math.cos(bend)*lean*dy/h;cz=z+math.sin(bend)*lean*dy/h
                crown(cx,y+dy,cz,rr+float(rng.uniform(-.4,.4)),.9,rr,sp,dy+x)
            crown(*trunkend,1,1.4,1,sp,x)
            if name=='snowy_taiga':put(trunkend[0],y+h+2,trunkend[2],snow)
        else:
            branches=int(rng.integers(3,6)) if sp in ['cherry','acacia','dark_oak','jungle'] else int(rng.integers(1,4))
            crown(*trunkend,radius*.68,1.5 if sp in ['cherry','acacia'] else 2.3,radius*.75,sp,x)
            for branch in range(branches):
                theta=bend+branch*2*math.pi/branches+float(rng.uniform(-.5,.5));length=float(rng.uniform(2,radius+1.2))
                by=y+h-float(rng.uniform(.3,2.4));end=(trunkend[0]+math.cos(theta)*length,by+float(rng.uniform(0,1.8)),trunkend[2]+math.sin(theta)*length)
                limb((x,y+max(2,h-3),z),end,sp)
                cr=float(rng.uniform(2,3.4));vertical=float(rng.uniform(1,1.8)) if sp in ['cherry','acacia'] else float(rng.uniform(1.5,2.8))
                crown(*end,cr,vertical,cr*float(rng.uniform(.8,1.3)),sp,z+branch)
            if sp=='mangrove':
                root=block('mangrove_roots[waterlogged=false]')
                for theta in np.arange(0,6.28,1.05):limb((x,y+2,z),(x+math.cos(theta)*3,y-1,z+math.sin(theta)*3),sp)
        records.append({'biome':name,'species':sp,'base':[x,y,z],'height':h,'radius':radius,'variant':variant,'lean':round(lean,2)})
        counts[name]+=1
    # Non-tree features are also sampled freely, never on a repeated lattice.
    bamboo=block('bamboo[age=1,leaves=large,stage=1]');ice=block('packed_ice');cactus=block('cactus[age=0]')
    for _ in range(19000):
        ix=int(rng.integers(12,N-12));iz=int(rng.integers(12,N-12));name=reverse[int(biome[iz,ix])]
        if forbidden[iz,ix]:continue
        y=int(surface[iz,ix])+1;iy=y-ymin
        if y<65 or a[iy-1,iz,ix] in [air,water] or a[iy,iz,ix]!=air:continue
        if name=='bamboo_jungle':a[iy:iy+int(rng.integers(4,15)),iz,ix]=bamboo
        elif name=='desert' and rng.random()<.12:
            if np.all(a[iy:iy+4,iz-1:iz+2,ix-1:ix+2]==air):a[iy:iy+int(rng.integers(1,4)),iz,ix]=cactus
        elif name=='ice_spikes' and rng.random()<.16:
            h=int(rng.integers(8,24));slope=float(rng.uniform(.03,.13))
            for dy in range(h):
                rr=max(0,round(2.5*(1-dy/h)));cx=ix+round(slope*dy)
                a[iy+dy,iz-rr:iz+rr+1,cx-rr:cx+rr+1]=ice
        elif name=='mushroom_fields' and rng.random()<.55:
            h=int(rng.integers(4,10));r=int(rng.integers(2,5));a[iy:iy+h,iz,ix]=block('mushroom_stem')
            cap=block('red_mushroom_block') if rng.random()<.55 else block('brown_mushroom_block')
            for dy in range(-1,2):
                rr=r-abs(dy);zz,xx=np.mgrid[-rr:rr+1,-rr:rr+1];patch=a[iy+h+dy,iz-rr:iz+rr+1,ix-rr:ix+rr+1];patch[xx*xx+zz*zz<=rr*rr+1]=cap
    return counts,records


def vegetation(a,surface,biome,forbidden,noise,levels,rng,origin,ymin,block,bid):
    N=surface.shape[0];air=block('air');water=block('water[level=0]')
    grass=block('short_grass');fern=block('fern');moss=block('moss_carpet')
    flowers=[block(x) for x in ['poppy','dandelion','allium','azure_bluet','oxeye_daisy','cornflower','pink_tulip']]
    fern_tall=[block('large_fern[half=lower]'),block('large_fern[half=upper]')];grass_tall=[block('tall_grass[half=lower]'),block('tall_grass[half=upper]')]
    petals=[block(f'pink_petals[facing={f},flower_amount={n}]') for f in ['north','east','south','west'] for n in [1,2,3,4]]
    reverse={v:k for k,v in bid.items()};leafy={i for i in range(256) if False}
    for _ in range(850):
        ix=int(rng.integers(10,N-10));iz=int(rng.integers(10,N-10));b=reverse[int(biome[iz,ix])]
        if forbidden[iz-3:iz+4,ix-3:ix+4].any() or b not in ['forest','flower_forest','jungle','dark_forest','cherry_grove','taiga']:continue
        iy=int(surface[iz,ix])+1-ymin
        if a[iy,iz,ix]!=air or a[iy-1,iz,ix]==air:continue
        leaf=block(('cherry' if b=='cherry_grove' else 'oak')+'_leaves[distance=1,persistent=true,waterlogged=false]')
        radius=int(rng.integers(1,3))
        for dy in range(2):
            for dx in range(-radius,radius+1):
                for dz in range(-radius,radius+1):
                    if dx*dx+dz*dz+dy*dy<=radius*radius and a[iy+dy,iz+dz,ix+dx]==air:a[iy+dy,iz+dz,ix+dx]=leaf
    for _ in range(340000):
        ix=int(rng.integers(8,N-8));iz=int(rng.integers(8,N-8));b=reverse[int(biome[iz,ix])]
        if forbidden[iz,ix]:continue
        y=int(surface[iz,ix])+1;iy=y-ymin;wet=y<=max(63,int(levels[iz,ix]))
        if not wet and a[iy,iz,ix]==air and a[iy-1,iz,ix] not in [air,water]:
            if b=='cherry_grove':
                if rng.random()<.7:a[iy,iz,ix]=petals[int(rng.integers(0,len(petals)))]
                else:a[iy,iz,ix]=grass
            elif b in ['desert','badlands']:
                if rng.random()<.07:a[iy,iz,ix]=block('dead_bush')
            elif b=='mushroom_fields':
                if rng.random()<.25:a[iy,iz,ix]=block('red_mushroom' if rng.random()<.4 else 'brown_mushroom')
            elif b not in ['snowy_taiga','snowy_plains','ice_spikes','jagged_peaks','stony_peaks','beach','deep_ocean','warm_ocean','river']:
                cluster=float(noise[iz,ix]);fchance=.48 if b=='flower_forest' else .18 if b=='meadow' else .025
                if rng.random()<fchance and cluster>-.25:a[iy,iz,ix]=flowers[(int(abs(cluster)*3)+int(rng.integers(0,3)))%len(flowers)]
                elif rng.random()<.24 and a[iy+1,iz,ix]==air:
                    duo=fern_tall if b in ['taiga','forest','dark_forest','jungle','bamboo_jungle','swamp'] else grass_tall
                    a[iy,iz,ix]=duo[0];a[iy+1,iz,ix]=duo[1]
                else:a[iy,iz,ix]=fern if b in ['taiga','dark_forest','jungle','bamboo_jungle'] else grass
        if wet and a[iy,iz,ix]==water:
            if b=='warm_ocean' and rng.random()<.23:
                a[iy,iz,ix]=block(['brain','bubble','fire','horn','tube'][int(rng.integers(0,5))]+'_coral_block')
            elif rng.random()<.3:a[iy,iz,ix]=block('seagrass')
        level=max(63,int(levels[iz,ix]));ly=level-ymin+1
        if b in ['swamp','mangrove_swamp'] and wet and a[ly,iz,ix]==air and rng.random()<.12:a[ly,iz,ix]=block('lily_pad')


def repair_route_floors(a,routes,surface,levels,origin,ymin,block):
    """Resolve height disagreements at path junctions without widening the trails."""
    from scipy.ndimage import minimum_filter
    N=surface.shape[0];field=np.full((N,N),30000,np.int16)
    for route in routes:
        for x,y,z in route['points']:
            ix=x-origin;iz=z-origin
            patch=field[max(0,iz-1):iz+2,max(0,ix-1):ix+2];patch[:]=np.minimum(patch,y-ymin)
    valid=field<30000
    for _ in range(40):
        lower=minimum_filter(field,size=3,mode='constant',cval=30000)+1
        nxt=np.where(valid,np.minimum(field,lower),30000).astype(np.int16)
        if np.array_equal(nxt,field):break
        field=nxt
    zz,xx=np.indices(field.shape);valid&=((xx+origin)**2+(zz+origin)**2>61**2)
    for iy in np.unique(field[valid]):
        mask=valid&(field==iy);a[iy:iy+3,mask]=block('air')
        deck=surface[mask]<np.maximum(63,levels[mask]);old=a[iy-1,mask].copy()
        soil=np.isin(old,[block('air'),block('water[level=0]'),block('short_grass'),block('tall_grass[half=lower]'),block('tall_grass[half=upper]')])
        old[soil]=block('dirt_path');old[deck]=block('spruce_planks');a[iy-1,mask]=old
    for route in routes:
        for point in route['points']:
            x,y,z=point;iy=int(field[z-origin,x-origin]);point[1]=iy+ymin
