"""Geology, living reef colonies and mushroom habitat, Safari revision 6."""
import json,math,numpy as np

def enrich(a,surface,biome,chambers,passages,origin,ymin,block,bid,out):
    N=surface.shape[0];air=block('air');water=block('water[level=0]');stone=block('stone');rng=np.random.default_rng(61717)
    protected=np.zeros((N,N),bool)
    for p in passages:
        for x,y,z in p['points']:
            ix=x-origin;iz=z-origin;protected[max(0,iz-5):iz+6,max(0,ix-5):ix+6]=True
    # Reserve surface trails and bridges while detailing aquatic/island habitats.
    surface_protected=np.zeros((N,N),bool)
    from scipy.ndimage import binary_dilation
    # Read actual surface routes from their material; include a narrow safety verge.
    for iy in range(64-ymin,105-ymin):
        surface_protected|=np.isin(a[iy],[block('dirt_path'),block('spruce_planks')])
    surface_protected=binary_dilation(surface_protected,iterations=3)
    pillars=[];mounds=0
    for room in chambers:
        x,y,z=room['center'];rx,ry,rz=room['radii']
        for _ in range(6):
            theta=float(rng.uniform(0,math.tau));radius=float(rng.uniform(.4,.73));ix=x-origin+round(math.cos(theta)*rx*radius);iz=z-origin+round(math.sin(theta)*rz*radius)
            if protected[iz-4:iz+5,ix-4:ix+5].any():continue
            low=max(1,y-ry-ymin-3);high=min(a.shape[0]-1,y+ry-ymin+3)
            opens=np.flatnonzero(a[low:high,iz,ix]==air)
            if len(opens)<5:continue
            floor=int(opens[0])+low;ceiling=int(opens[-1])+low
            if ceiling-floor<7:continue
            for yy in range(floor,ceiling+1):
                t=(yy-floor)/max(1,ceiling-floor);r=1.3+2.2*abs(2*t-1)**1.6+.3*math.sin(yy*.7)
                leanx=.9*math.sin(t*math.pi);leanz=.7*math.sin(t*math.tau)
                for dx in range(-4,5):
                    for dz in range(-4,5):
                        if (dx-leanx)**2+(dz-leanz)**2<r*r and not protected[iz+dz,ix+dx]:a[yy,iz+dz,ix+dx]=stone if (dx+dz+yy)%7 else block('andesite')
            pillars.append([ix+origin,floor+ymin,iz+origin,ceiling+ymin])
        for _ in range(14):
            ix=x-origin+int(rng.integers(-rx+5,rx-4));iz=z-origin+int(rng.integers(-rz+5,rz-4))
            if protected[iz-5:iz+6,ix-5:ix+6].any():continue
            opens=np.flatnonzero(a[max(1,y-ry-ymin):y+6-ymin,iz,ix]==air)
            if not len(opens):continue
            fy=int(opens[0])+max(1,y-ry-ymin);height=int(rng.integers(2,5));radius=int(rng.integers(3,6))
            for dy in range(height):
                rr=radius*(1-dy/(height+1))
                for dx in range(-radius,radius+1):
                    for dz in range(-radius,radius+1):
                        if dx*dx+dz*dz<rr*rr and not protected[iz+dz,ix+dx]:a[fy:fy+dy+1,iz+dz,ix+dx]=block('moss_block') if room['biome']=='lush_caves' and dy==height-1 else stone
            mounds+=1
    # Replace single coral blocks with dense colonies anchored in the seabed.
    corals=['brain','bubble','fire','horn','tube'];coral_ids=[block(c+'_coral_block') for c in corals]
    warm=biome==bid['warm_ocean'];reefs=[];fans=0
    for yy in range(32-ymin,63-ymin):
        layer=a[yy];m=np.isin(layer,coral_ids);layer[m]=water
    for _ in range(450):
        ix=int(rng.integers(12,N-12));iz=int(rng.integers(12,N-12))
        # More attempts inside the actual warm-ocean extent, not a regular lattice.
        candidates=np.argwhere(warm) if _==0 else candidates
        if not len(candidates):break
        iz,ix=map(int,candidates[int(rng.integers(0,len(candidates)))])
        if ix<9 or iz<9 or ix>N-10 or iz>N-10 or surface_protected[iz,ix]:continue
        fy=int(surface[iz,ix])+1-ymin
        if surface[iz,ix]>56 or a[fy,iz,ix]!=water:continue
        c=corals[int(rng.integers(0,5))];core=block(c+'_coral_block');fan=block(c+'_coral_fan[waterlogged=true]');height=int(rng.integers(2,5))
        for dy in range(height):
            for dx,dz in [(0,0),(1,0),(0,1),(-1,0),(0,-1)]:
                if a[fy+dy,iz+dz,ix+dx] in [water,core]:a[fy+dy,iz+dz,ix+dx]=core
        for arm in range(int(rng.integers(3,6))):
            theta=float(rng.uniform(0,math.tau));length=int(rng.integers(2,5));dy=height-1
            for j in range(length+1):
                dx=round(math.cos(theta)*j);dz=round(math.sin(theta)*j);yy=fy+dy+round(j*.3)
                if a[yy,iz+dz,ix+dx] not in [water,core]:continue
                a[yy,iz+dz,ix+dx]=core
                if a[yy+1,iz+dz,ix+dx]==water:a[yy+1,iz+dz,ix+dx]=fan;fans+=1
        reefs.append([ix+origin,fy+ymin,iz+origin])
    # Mushroom understory and asymmetric shelf mushrooms rooted in the mycelium.
    mush=biome==bid['mushroom_fields'];locations=np.argwhere(mush);small=0;shelves=0
    for _ in range(2300):
        iz,ix=map(int,locations[int(rng.integers(0,len(locations)))])
        if surface_protected[iz,ix]:continue
        fy=int(surface[iz,ix])+1-ymin
        if a[fy,iz,ix]!=air:continue
        a[fy,iz,ix]=block('red_mushroom' if rng.random()<.45 else 'brown_mushroom');small+=1
    for _ in range(65):
        iz,ix=map(int,locations[int(rng.integers(0,len(locations)))])
        if not(8<ix<N-8 and 8<iz<N-8) or surface_protected[iz-5:iz+6,ix-5:ix+6].any():continue
        fy=int(surface[iz,ix])+1-ymin
        if a[fy,iz,ix]!=air:continue
        h=int(rng.integers(3,9));cap=block('red_mushroom_block') if rng.random()<.6 else block('brown_mushroom_block');stem=block('mushroom_stem')
        a[fy:fy+h,iz,ix]=stem
        for dy in range(-1,2):
            for dx in range(-4,5):
                for dz in range(-3,4):
                    if ((dx-.5)/4)**2+(dz/3)**2+(dy/2.2)**2<1 and a[fy+h+dy,iz+dz,ix+dx]==air:a[fy+h+dy,iz+dz,ix+dx]=cap
        shelves+=1
    report={'revision':6,'rock_pillars':len(pillars),'pillar_positions':pillars,'rock_mounds':mounds,'coral_colonies':len(reefs),'coral_fans':fans,'coral_colony_positions':reefs,'mushroom_understory':small,'extra_mushroom_canopies':shelves}
    (out/'validation/landforms.json').write_text(json.dumps(report,indent=2))
