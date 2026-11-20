"""Structural support, shoreline detailing and regression checks for revision 3."""
import numpy as np,json
from scipy.ndimage import binary_dilation

def settle_column(a,ix,iz,iy,material,air,water):
    # Close the gap to the first existing rock/soil below the walking surface.
    j=iy-1
    while j>0 and int(a[j,iz,ix]) in (air,water):a[j,iz,ix]=material;j-=1

def finish(a,routes,surface,levels,origin,ymin,block,out):
    N=surface.shape[0];air=block('air');water=block('water[level=0]');stone=block('stone');dirt=block('dirt');logs=block('spruce_log[axis=y]')
    supports=[]
    for route in routes:
        for i,(x,y,z) in enumerate(route['points']):
            ix=x-origin;iz=z-origin;iy=y-ymin-1
            wet=surface[iz,ix]<max(63,int(levels[iz,ix]))
            if wet:
                if i%7==0:
                    for dx in [-1,1]:
                        settle_column(a,ix+dx,iz,iy,logs,air,water)
                        supports.append([x+dx,y-1,z])
            else:
                for dx in [-2,-1,0,1,2]:
                    for dz in [-2,-1,0,1,2]:settle_column(a,ix+dx,iz+dz,iy,dirt,air,water)
    # Mirantes: actual foundations under the four corners, down to rock.
    for x,z in [(-530,-580),(70,-690)]:
        for dx in [7,17]:
            for dz in [-5,5]:
                ix=x+dx-origin;iz=z+dz-origin
                decks=np.flatnonzero(a[:,iz,ix]==block('spruce_planks'))
                for iy in decks:settle_column(a,ix,iz,int(iy),logs,air,water);supports.append([x+dx,int(iy)+ymin,z+dz])
    # Water margins: mixed sediment, reeds, small rocks and low shrubs, no trees in water.
    wet=surface<np.maximum(63,levels);shore=binary_dilation(wet,iterations=5)&~wet
    rng=np.random.default_rng(20261123);zz,xx=np.nonzero(shore)
    reed=block('sugar_cane[age=0]');gravel=block('gravel');sand=block('sand');clay=block('clay');moss=block('mossy_cobblestone')
    for k in range(0,len(xx),3):
        ix=int(xx[k]);iz=int(zz[k]);y=int(surface[iz,ix]);iy=y-ymin
        if not(4<ix<N-4 and 4<iz<N-4) or a[iy+1,iz,ix]!=air:continue
        if y>max(63,int(levels[iz,ix]))+4:continue
        if rng.random()<.35:a[iy,iz,ix]=gravel if rng.random()<.6 else sand
        neighbors=[(ix-1,iz),(ix+1,iz),(ix,iz-1),(ix,iz+1)]
        adjacent=any(a[iy,z,x]==water for x,z in neighbors)
        if adjacent and a[iy,iz,ix] in [sand,dirt,block('grass_block')] and rng.random()<.23:
            a[iy+1:iy+1+int(rng.integers(1,4)),iz,ix]=reed
        elif rng.random()<.025:a[iy+1,iz,ix]=moss
    # Remove isolated mineral decoration blocks and unsupported dripstone tips.
    targets=[block('calcite'),block('dripstone_block')];tipup=block('pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]');tipdown=block('pointed_dripstone[thickness=tip,vertical_direction=down,waterlogged=false]')
    removed=0
    for iy in range(1,a.shape[0]-1):
        layer=a[iy];candidate=np.isin(layer,targets)
        unsupported=candidate&(a[iy-1]==air)&(a[iy+1]==air)
        unsupported[:,1:]&=layer[:,:-1]==air;unsupported[:,:-1]&=layer[:,1:]==air
        unsupported[1:,:]&=layer[:-1,:]==air;unsupported[:-1,:]&=layer[1:,:]==air
        removed+=int(unsupported.sum());layer[unsupported]=air
        layer[(layer==tipup)&(a[iy-1]==air)]=air;layer[(layer==tipdown)&(a[iy+1]==air)]=air
    # Remove hanging mineral/tip clusters that have no attachment to the cave.
    mineral=np.array(targets+[tipup,tipdown],dtype=np.uint8)
    for iy in range(1,a.shape[0]-2):
        ys,xs=np.nonzero(np.isin(a[iy],mineral)&(a[iy-1]==air))
        for iz,ix in zip(ys,xs):
            if not(1<=ix<N-1 and 1<=iz<N-1):continue
            end=iy
            while end<a.shape[0]-1 and int(a[end,iz,ix]) in mineral:end+=1
            if a[end,iz,ix]!=air:continue
            attached=False
            for dx,dz in [(-1,0),(1,0),(0,-1),(0,1)]:
                side=a[iy:end,iz+dz,ix+dx]
                if np.any((side!=air)&~np.isin(side,mineral)):attached=True;break
            if not attached:removed+=end-iy;a[iy:end,iz,ix]=air
    report={'revision':3,'bridge_and_lookout_support_columns':len(supports),'isolated_mineral_blocks_removed':removed,'water_margin_cells':int(shore.sum())}
    (out/'validation/structure_fixes.json').write_text(json.dumps(report,indent=2))


def details(a,routes,surface,levels,origin,ymin,block,out):
    N=surface.shape[0];air=block('air');water=block('water[level=0]');rng=np.random.default_rng(93814)
    protected=np.zeros((N,N),bool)
    for route in routes:
        for x,y,z in route['points']:
            ix=x-origin;iz=z-origin;protected[max(0,iz-4):iz+5,max(0,ix-4):ix+5]=True
    wet=surface<np.maximum(63,levels);shore=binary_dilation(wet,iterations=9)&~wet
    zz,xx=np.nonzero(shore&~protected);placed=0
    leaves=block('oak_leaves[distance=1,persistent=true,waterlogged=false]');moss=block('mossy_cobblestone');stone=block('stone');dirt=block('dirt')
    for _ in range(min(1800,len(xx))):
        k=int(rng.integers(0,len(xx)));ix=int(xx[k]);iz=int(zz[k]);iy=int(surface[iz,ix])-ymin
        if not(5<ix<N-5 and 5<iz<N-5) or a[iy+1,iz,ix]!=air or surface[iz,ix]<max(63,int(levels[iz,ix])):continue
        if rng.random()<.55:
            # Grounded rock outcrop, embedded one block into the soil.
            for dx,dz in [(0,0),(1,0),(0,1),(-1,0)]:
                if protected[iz+dz,ix+dx]:continue
                gy=int(surface[iz+dz,ix+dx])-ymin
                if abs(gy-iy)>1:continue
                a[gy:gy+2,iz+dz,ix+dx]=moss if rng.random()<.5 else stone
        else:
            for dx in [-1,0,1]:
                for dz in [-1,0,1]:
                    if protected[iz+dz,ix+dx]:continue
                    gy=int(surface[iz+dz,ix+dx])-ymin
                    if a[gy+1,iz+dz,ix+dx]==air:a[gy+1,iz+dz,ix+dx]=leaves
        placed+=1
    rests=0
    for x,z in [(-405,-55),(96,-230),(-335,-410),(555,245),(-100,395)]:
        ix=x-origin;iz=z-origin;iy=int(surface[iz,ix])-ymin
        if wet[iz-4:iz+5,ix-4:ix+5].any() or protected[iz-4:iz+5,ix-4:ix+5].any():continue
        # Compact stone clearing and a wood bench, fully founded on terrain.
        for dx in range(-3,4):
            for dz in range(-2,3):
                settle_column(a,ix+dx,iz+dz,iy,stone,air,water)
                a[iy,iz+dz,ix+dx]=block('gravel');a[iy+1:iy+4,iz+dz,ix+dx]=air
        for dx in range(-2,3):a[iy+1,iz+1,ix+dx]=block('spruce_planks')
        a[iy+1,iz-1,ix]=block('campfire[facing=north,lit=false,signal_fire=false,waterlogged=false]');rests+=1
    (out/'validation/extra_details.json').write_text(json.dumps({'shore_rock_and_shrub_groups':placed,'grounded_rest_areas':rests},indent=2))
