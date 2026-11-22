"""Texture-based isometric preview of actual generated blocks, not a game screenshot."""
import sys,math,json,io,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import numpy as np
from PIL import Image,ImageDraw

def render(root,assets,cx,cz,name,span=64):
    palette=json.loads((root/'palette.json').read_text());volume=np.load(root/'blocks.npy');H,D,W=volume.shape;span=W
    noncubes=['air','short_grass','fern','tall_grass','large_fern','pink_petals','oak_sign','poppy','dandelion','allium','azure_bluet','oxeye_daisy','cornflower','pink_tulip','lily_of_the_valley','dead_bush','red_mushroom','brown_mushroom','moss_carpet']
    noncube_ids=[i for i,name in enumerate(palette) if name.split(':')[1].split('[')[0] in noncubes]
    solid=~np.isin(volume,noncube_ids)
    # Expose top, east and south surfaces; render them from back to front.
    entries=[]
    for y,z,x in zip(*np.nonzero(solid)):
        bid=int(volume[y,z,x]);s=palette[bid].split(':')[1].split('[')[0]
        if s in ['short_grass','fern','tall_grass','large_fern','pink_petals','oak_sign','poppy','dandelion','allium','azure_bluet','oxeye_daisy','cornflower','pink_tulip','lily_of_the_valley','dead_bush','red_mushroom','brown_mushroom','moss_carpet']:continue
        for face,dy,dz,dx in [('top',1,0,0),('east',0,0,1),('south',0,1,0)]:
            yy,zz,xx=y+dy,z+dz,x+dx
            if yy>=H or zz>=D or xx>=W or not solid[yy,zz,xx]:entries.append((int(x+z+y)*4,int(x),int(y),int(z),face,s))
    entries.sort();scale=10;offx=(span+3)*scale;offy=(65+4)*scale
    im=Image.new('RGBA',((span*2+8)*scale,(span+75)*scale),(174,209,235,255));textures={};jar=zipfile.ZipFile(assets)
    def project(x,y,z):return (offx+(x-z)*scale,offy+(x+z)*scale*.5-y*scale)
    def texture(s,face):
        key=s,face
        if key in textures:return textures[key]
        tex=s
        if s.endswith('_log'):tex=s+'_top' if face=='top' else s
        elif s in ['grass_block','podzol','mycelium']:tex=s+'_top' if face=='top' else (s+'_side' if s!='mycelium' else 'mycelium_side')
        elif s=='dirt_path':tex='dirt_path_top' if face=='top' else 'dirt_path_side'
        elif s=='water':tex='water_still'
        elif s=='lily_pad':tex='lily_pad'
        elif s=='flowering_azalea':tex='flowering_azalea_top'
        elif s=='lantern':tex='gold_block'
        elif s in ['snow_block','snow']:tex='snow'
        elif s.endswith('_fence'):tex=s.replace('_fence','_planks')
        elif s.endswith('_stairs'):tex=s.replace('_stairs','_planks')
        elif s.endswith('_slab'):tex=s.replace('_slab','_planks')
        path='assets/minecraft/textures/block/'+tex+'.png'
        try:t=Image.open(io.BytesIO(jar.read(path))).convert('RGBA');t=t.crop((0,0,t.width,t.width)).resize((16,16),Image.Resampling.NEAREST)
        except KeyError:t=Image.new('RGBA',(16,16),(122,137,112,255))
        rgb=np.asarray(t).copy();factor={'top':1.,'east':.73,'south':.88}[face]
        if s=='water':rgb[:,:,:3]=(rgb[:,:,:3].astype(float)*np.array([.23,.57,.78])).astype(np.uint8)
        if s=='lily_pad':rgb[:,:,:3]=(rgb[:,:,:3].astype(float)*np.array([.3,.6,.22])).astype(np.uint8)
        if s=='grass_block' and face=='top':rgb[:,:,:3]=(rgb[:,:,:3].astype(float)*np.array([.52,.73,.32])).astype(np.uint8)
        if s.endswith('_leaves') and s not in ['cherry_leaves','azalea_leaves','flowering_azalea_leaves']:
            rgb[:,:,:3]=(rgb[:,:,:3].astype(float)*np.array([.42,.66,.28])).astype(np.uint8)
        rgb[:,:,:3]=(rgb[:,:,:3]*factor).astype(np.uint8);t=Image.fromarray(rgb);textures[key]=t;return t
    for _,x,y,z,face,s in entries:
        if face=='top':vertices=[project(x,y+1,z),project(x+1,y+1,z),project(x+1,y+1,z+1),project(x,y+1,z+1)]
        elif face=='east':vertices=[project(x+1,y+1,z),project(x+1,y+1,z+1),project(x+1,y,z+1),project(x+1,y,z)]
        else:vertices=[project(x+1,y+1,z+1),project(x,y+1,z+1),project(x,y,z+1),project(x+1,y,z+1)]
        bx=int(math.floor(min(v[0] for v in vertices)));by=int(math.floor(min(v[1] for v in vertices)));bw=int(math.ceil(max(v[0] for v in vertices)))-bx+1;bh=int(math.ceil(max(v[1] for v in vertices)))-by+1
        pts=np.array([[vertices[i][0]-bx,vertices[i][1]-by,1] for i in [0,1,3]])
        uv=np.linalg.solve(pts,np.array([[0,0],[16,0],[0,16]],float))
        coeff=(uv[0,0],uv[1,0],uv[2,0],uv[0,1],uv[1,1],uv[2,1])
        transformed=texture(s,face).transform((bw,bh),Image.Transform.AFFINE,coeff,Image.Resampling.NEAREST)
        mask=Image.new('L',(bw,bh),0);ImageDraw.Draw(mask).polygon([(v[0]-bx,v[1]-by) for v in vertices],fill=255)
        alpha=np.minimum(np.array(transformed.getchannel('A')),np.array(mask));transformed.putalpha(Image.fromarray(alpha));im.alpha_composite(transformed,(bx,by))
    background=np.array([174,209,235]);pixels=np.array(im)[:,:,:3]
    ys,xs=np.nonzero(np.any(pixels!=background,axis=2))
    if len(xs):im=im.crop((max(0,int(xs.min())-20),max(0,int(ys.min())-50),min(im.width,int(xs.max())+21),min(im.height,int(ys.max())+21)))
    bbox=Image.new('RGB',im.size,(174,209,235));bbox.paste(im,mask=im.getchannel('A'));draw=ImageDraw.Draw(bbox);draw.rectangle((0,0,bbox.width,40),fill='black');draw.text((12,12),'HUB SAFARI / volumes simplificados e texturas reais; nao e captura do Minecraft',fill='white')
    path=root/'maps'/('preview_'+name+'.png');bbox.save(path);return path
if __name__=='__main__':
    print(render(Path(sys.argv[1]),Path(sys.argv[2]),0,0,'hub_floresta',112))
