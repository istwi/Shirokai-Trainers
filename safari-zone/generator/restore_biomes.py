#!/usr/bin/env python3
"""Offline restore of generated biome IDs. Never run against an online world."""
import sys,struct,zlib,math,shutil,datetime,argparse,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import numpy as np, nbtlib as n
from nbtlib import tag as T

def packed(a,bits):
    a=np.asarray(a,dtype=np.uint64).ravel();per=64//bits
    a=np.pad(a,(0,(-len(a))%per)).reshape(-1,per)
    result=np.bitwise_or.reduce(a<<(np.arange(per,dtype=np.uint64)*np.uint64(bits)),axis=1)
    return T.LongArray(result.view(np.int64))
def restore(world,data,confirm=False,level_dat=None):
    assert confirm,'Pare o servidor e use --server-stopped para confirmar.'
    level=n.load(level_dat or world/'level.dat');assert int(level['Data']['DataVersion'])==3955,'Esperado Minecraft 1.21.1.'
    archive=np.load(data);biomes=archive['biomes'];names=list(archive['names']);ox,oy,oz=map(int,archive['origin'])
    backup=world.parent/('safari-biomes-backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir()
    count=0
    for path in sorted((world/'region').glob('r.*.*.mca')):
        source=path.read_bytes();header=bytearray(8192);body=bytearray();sector=2;changed=False
        for index in range(1024):
            loc=int.from_bytes(source[index*4:index*4+4],'big');offset=(loc>>8)*4096
            if not offset:continue
            size=int.from_bytes(source[offset:offset+4],'big');method=source[offset+4]
            assert method==2,'Este restaurador suporta apenas chunks zlib.'
            root=n.File.parse(io.BytesIO(zlib.decompress(source[offset+5:offset+4+size])))
            cx,cz=int(root['xPos']),int(root['zPos']);ix=(cx*16-ox)//4;iz=(cz*16-oz)//4
            if 0<=ix<=biomes.shape[2]-4 and 0<=iz<=biomes.shape[1]-4:
                for section in root['sections']:
                    sy=(int(section['Y'])*16-oy)//4
                    if not 0<=sy<=biomes.shape[0]-4:continue
                    values=biomes[sy:sy+4,iz:iz+4,ix:ix+4];u,inv=np.unique(values,return_inverse=True)
                    tag=T.Compound({'palette':T.List[T.String](['minecraft:'+str(names[int(v)]) for v in u])})
                    if len(u)>1:tag['data']=packed(inv,max(1,(len(u)-1).bit_length()))
                    section['biomes']=tag
                changed=True;count+=1
            stream=io.BytesIO();root.write(stream);compressed=zlib.compress(stream.getvalue(),6)
            chunk=struct.pack('>I',len(compressed)+1)+b'\x02'+compressed;sectors=math.ceil(len(chunk)/4096)
            assert sectors<256
            header[index*4:index*4+4]=((sector<<8)|sectors).to_bytes(4,'big')
            header[4096+index*4:4100+index*4]=source[4096+index*4:4100+index*4]
            body.extend(chunk);body.extend(b'\0'*(sectors*4096-len(chunk)));sector+=sectors
        if changed:
            shutil.copy2(path,backup/path.name)
            tmp=path.with_suffix('.restore-tmp');tmp.write_bytes(header+body);tmp.replace(path)
    print(f'{count} chunks restaurados; backup: {backup}')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--world',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--level-dat',type=Path);p.add_argument('--server-stopped',action='store_true');args=p.parse_args();restore(args.world,args.data,args.server_stopped,args.level_dat)
