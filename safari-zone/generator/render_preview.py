import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
root=Path(sys.argv[1]);palette=json.loads((root/'validation/block_palette.json').read_text());a=np.memmap(root/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504));v=a[:,672:832,672:832]
height=np.max(np.where(v!=0,np.arange(320)[:,None,None],0),axis=0);zz,xx=np.indices(height.shape);ids=v[height,zz,xx]
colors=[]
for state in palette:
    name=state.split(':')[1].split('[')[0]
    c=(111,140,81)
    if 'stone' in name or 'brick' in name or name=='gravel':c=(133,141,145)
    if 'log' in name or 'fence' in name or 'sign' in name:c=(109,79,51)
    if 'planks' in name or 'slab' in name or 'path' in name:c=(166,135,88)
    if 'white' in name:c=(238,243,242)
    if 'cyan' in name:c=(37,149,155)
    if 'light_blue' in name:c=(95,185,215)
    if 'water'==name:c=(49,125,187)
    if 'leaves' in name:c=(53,123,66)
    if 'glass' in name:c=(175,214,219)
    if 'sea_lantern' in name:c=(216,243,210)
    if name in ['poppy','pink_tulip','allium']:c=(232,105,145)
    colors.append(c)
rgb=np.array(colors,dtype=np.uint8)[ids];shade=np.clip(.92+np.gradient(height.astype(float))[0]*.04-np.gradient(height.astype(float))[1]*.04,.55,1.15)
im=Image.fromarray(np.clip(rgb*shade[:,:,None],0,255).astype(np.uint8)).resize((1280,1280),Image.Resampling.NEAREST);draw=ImageDraw.Draw(im);draw.rectangle((0,0,1280,26),fill='black');draw.text((10,7),'HUB / vista superior dos blocos gerados / norte acima / nao e captura do jogo',fill='white');im.save(root/'maps/hub_topdown.png')
