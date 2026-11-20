"""Detail pass with intentional bridge edges, cave lighting and grounded furniture."""
import json,numpy as np

def polish(a,routes,passages,surface,levels,origin,ymin,block,out):
    air=block('air');water=block('water[level=0]');wood=block('spruce_planks');log=block('stripped_spruce_log[axis=y]');lantern=block('lantern[hanging=false,waterlogged=false]');torch=block('torch');N=surface.shape[0]
    voids={air,water,block('seagrass'),block('kelp[age=25]')};posts=set();rail=set();lights=0
    def put(x,y,z,b):
        ix=x-origin;iz=z-origin;iy=y-ymin
        if 0<=ix<N and 0<=iz<N and 0<=iy<a.shape[0]:a[iy,iz,ix]=b
    def foundation(x,y,z,b):
        ix=x-origin;iz=z-origin;iy=y-ymin-1
        while iy>0 and int(a[iy,iz,ix]) in voids:a[iy,iz,ix]=b;iy-=1
    for route in routes:
        pts=route['points'];wet_samples=0
        for i,(x,y,z) in enumerate(pts):
            ix=x-origin;iz=z-origin
            if surface[iz,ix]>=max(63,int(levels[iz,ix])):continue
            wet_samples+=1;prev=pts[max(0,i-3)];nxt=pts[min(len(pts)-1,i+3)]
            along_z=abs(nxt[2]-prev[2])>abs(nxt[0]-prev[0]);dx,dz=(1,0) if along_z else (0,1)
            fence=block('spruce_fence[east='+('false' if along_z else 'true')+',north='+('true' if along_z else 'false')+',south='+('true' if along_z else 'false')+',waterlogged=false,west='+('false' if along_z else 'true')+']')
            for side in [-1,1]:
                px=x+dx*3*side;pz=z+dz*3*side
                put(px,y-1,pz,wood);put(px,y,pz,fence);rail.add((px,y,pz))
                if wet_samples%9==0:
                    put(px,y-1,pz,log);put(px,y,pz,log);put(px,y+1,pz,log);put(px,y+2,pz,lantern);foundation(px,y-1,pz,log);posts.add((px,y,pz));lights+=1
                    facing=('east' if side>0 else 'west') if along_z else ('south' if side>0 else 'north')
                    put(px+dx*side,y-1,pz+dz*side,block('spruce_trapdoor[facing='+facing+',half=top,open=true,powered=false,waterlogged=false]'))
        # Avoid furnishing dry paths with bridge structures.
    allowed={block(b) for b in ['stone','deepslate','moss_block','dripstone_block','calcite','tuff','clay','dirt','coarse_dirt','gravel','grass_block','stone_bricks']}
    cave_lights=[]
    for passage in passages:
        for i,(x,y,z) in enumerate(passage['points']):
            if i%12:continue
            for dx,dz in [(2,0),(-2,0),(0,2),(0,-2),(3,0),(-3,0)]:
                ix=x+dx-origin;iz=z+dz-origin;iy=y-ymin
                if not(1<ix<N-1 and 1<iz<N-1):continue
                if int(a[iy-1,iz,ix]) in allowed and a[iy,iz,ix]==air:
                    a[iy,iz,ix]=torch;cave_lights.append([x+dx,y,z+dz]);break
    # Replace the long bare plaza grid with gardens and a continuous planted border.
    grass=block('grass_block');flowers=[block(n) for n in ['allium','oxeye_daisy','cornflower','lily_of_the_valley']];leaf=block('flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]')
    for x in range(-58,59):
        for z in range(-58,59):
            if abs(x)<7 or abs(z)<7:continue
            if (-50<=x<=-19 or 18<=x<=50) and -49<=z<=-23:continue
            if ((x+37)/12)**2+((z-32)/10)**2<1 or ((x-37)/12)**2+((z-32)/10)**2<1:continue
            ix=x-origin;iz=z-origin;iy=76-ymin
            if a[iy+1,iz,ix]!=air:continue
            if (x*x+z*z>46**2 and x*x+z*z<52**2) or (abs(x)>53 or abs(z)>53):
                a[iy,iz,ix]=grass
                if (x*7+z*13)%11==0:a[iy+1,iz,ix]=flowers[(x+z)%4]
    (out/'validation/design.json').write_text(json.dumps({'detailed_bridge_posts':len(posts),'bridge_rail_cells':len(rail),'bridge_lanterns':lights,'cave_torches':len(cave_lights),'cave_torch_positions':cave_lights,'ocean_routes':[r['kind'] for r in routes if 'ilha dos cogumelos' in r['kind']]},indent=2))
