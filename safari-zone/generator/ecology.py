"""Continuous habitat surfaces and natural cave entrances, revision 5."""
import json,numpy as np
from scipy.ndimage import gaussian_filter

def blend_and_detail(a,surface,levels,biome,noise,origin,ymin,block,names,bid,out,cave_marks,passages):
    N=surface.shape[0];zz,xx=np.indices(surface.shape);sy=surface-ymin
    air=block('air');water=block('water[level=0]');grass=block('grass_block');stone=block('stone');gravel=block('gravel');sand=block('sand');clay=block('clay');mud=block('mud');coarse=block('coarse_dirt')
    rng=np.random.default_rng(51013);field=gaussian_filter(rng.normal(size=surface.shape).astype(np.float32),6);field/=field.std()
    waterlevel=np.maximum(63,levels);wet=surface<waterlevel;depth=waterlevel-surface
    bed=np.where(depth+field*1.8>5,stone,np.where(field>.55,clay,gravel)).astype(np.uint8)
    shallow=(depth<3)&(field<.5);bed[shallow]=sand
    swamp=np.isin(biome,[bid['swamp'],bid['mangrove_swamp']]);bed[swamp&(field>.6)]=clay
    # Replace the complete bed, not just decorative samples, including the soil below it.
    for d in range(3):a[sy[wet]-d,zz[wet],xx[wet]]=bed[wet] if d==0 else np.where(bed[wet]==sand,sand,stone)
    sandregion=np.isin(biome,[bid['desert'],bid['beach']]);weight=gaussian_filter(sandregion.astype(np.float32),12)
    edge=(weight>.02)&(weight<.98)&~wet
    current=a[sy,zz,xx];soil=np.isin(current,[grass,sand,block('dirt'),coarse,mud,gravel])
    blend=edge&soil
    value=weight+field*.1
    replacement=np.where(value>.73,sand,np.where(value>.48,gravel,np.where(value>.22,coarse,grass))).astype(np.uint8)
    a[sy[blend],zz[blend],xx[blend]]=replacement[blend]
    # Natural cavity surfaces use the same broad patches across rooms and passages.
    lush=bid['lush_caves'];drip=bid['dripstone_caves'];moss=block('moss_block');tuff=block('tuff');calcite=block('calcite')
    floor_types=[stone,moss,block('dripstone_block'),calcite,tuff,block('rooted_dirt')]
    protected=np.zeros((N,N),bool)
    for passage in passages:
        for x,y,z in passage['points']:
            ix=x-origin;iz=z-origin;protected[max(0,iz-2):iz+3,max(0,ix-2):ix+3]=True
    cave_details=0
    treated=0
    for iy in range(1,min(220,a.shape[0]-1)):
        kinds=np.repeat(np.repeat(cave_marks[iy//4],4,axis=0),4,axis=1)
        candidate=(kinds>=0)&np.isin(a[iy],floor_types)&np.isin(a[iy+1],[air,block('moss_carpet'),block('torch')])
        ly=candidate&(kinds==lush);dy=candidate&(kinds==drip)
        a[iy,ly]=np.where(field[ly]>-.55,moss,stone)
        a[iy,dy]=np.where(field[dy]>1.35,block('dripstone_block'),np.where(field[dy]<-1.55,tuff,stone))
        treated+=int(candidate.sum())
        plants=ly&~protected&(field>.55)&(((xx*17+zz*31)%19)==0)&(a[iy+1]==air)
        a[iy+1,plants]=block('fern');cave_details+=int(plants.sum())
        formations=dy&~protected&(field>.7)&(((xx*13+zz*23)%173)==0)&(a[iy+1]==air)&(a[iy+2]==air)&(a[iy+3]==air)
        a[iy+1,formations]=block('dripstone_block');a[iy+2,formations]=block('pointed_dripstone[thickness=tip,vertical_direction=up,waterlogged=false]');cave_details+=int(formations.sum())
    # Dress existing mouth rock only: no walls or raised decoration outside the hill.
    decorated=0
    for x,z,lushmouth in [(-290,130,True),(110,-340,False)]:
        ix=x-origin;iz=z-origin;top=int(surface[iz,ix])-ymin
        for iy in range(max(1,top-24),min(a.shape[0]-1,top+15)):
            for dx in range(-15,16):
                for dz in range(-15,16):
                    xx1=ix+dx;zz1=iz+dz
                    if a[iy,zz1,xx1] not in [stone,block('dirt'),grass]:continue
                    exposed=(a[iy,zz1,xx1-1]==air or a[iy,zz1,xx1+1]==air or a[iy,zz1-1,xx1]==air or a[iy,zz1+1,xx1]==air)
                    if exposed and field[zz1,xx1]>.2:
                        a[iy,zz1,xx1]=block('mossy_cobblestone') if lushmouth else block('andesite');decorated+=1
    # Ensure the buildable clearing contains no construction or planted decoration.
    center=60;start=-center-origin;end=center-origin+1
    for iy in range(64-ymin,76-ymin):
        patch=a[iy,start:end,start:end];patch[np.isin(patch,[air,water])]=block('dirt')
    a[76-ymin,start:end,start:end]=grass;a[77-ymin:160-ymin,start:end,start:end]=air
    # Narrow dirt routes must not project onto the grass plateau.
    report={'revision':5,'underwater_bed_columns':int(wet.sum()),'underwater_grass_columns':int(np.count_nonzero(a[sy[wet],zz[wet],xx[wet]]==grass)),'soil_transition_columns':int(blend.sum()),'natural_cave_surface_voxels':treated,'entrance_rock_faces_detailed':decorated,'clearing_bounds':[-60,60],'clearing_y':76,'extra_cave_detail_groups':cave_details}
    (out/'validation/ecology.json').write_text(json.dumps(report,indent=2))
