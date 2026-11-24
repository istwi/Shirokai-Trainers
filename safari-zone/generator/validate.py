#!/usr/bin/env python3
import sys,io,json,math,zlib,struct,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import numpy as np, nbtlib as n
from collections import Counter,deque

def unpack(data,bits,count):
    a=np.asarray(data,dtype=np.int64).view(np.uint64);per=64//bits
    return ((a[:,None]>>(np.arange(per,dtype=np.uint64)*np.uint64(bits)))&((1<<bits)-1)).ravel()[:count]
def decode(data,count):
    a=np.asarray(data,dtype=np.int8).view(np.uint8)
    if not np.any(a>=128):assert len(a)==count;return a
    result=np.zeros(count,np.uint32);o=0;shift=0
    for b in a:
        result[o]|=(int(b)&127)<<shift
        if b<128:o+=1;shift=0
        else:shift+=7;assert shift<=28
    assert o==count and shift==0
    return result

def validate(out,official=None,registry=None):
    report={};seen=set();count=0;sections=0;samples=0
    build=json.loads((out/'validation/build.json').read_text());palette=json.loads((out/'validation/block_palette.json').read_text())
    source=np.memmap(out/'terrain.work',mode='r',dtype=np.uint8,shape=(320,1504,1504)) if (out/'terrain.work').exists() else None
    if registry:
        blocks=json.loads(Path(registry).read_text())
        for s in palette:
            name,_,props=s.partition('[');assert name in blocks,name
            given=dict(v.split('=') for v in props.rstrip(']').split(',')) if props else {}
            assert any(all(state.get('properties',{}).get(k)==v for k,v in given.items()) for state in blocks[name]['states']),s
        report['official_blockstates_validated']=len(palette)
    official_names=set(json.loads(Path(official).read_text())) if official else None
    expected=np.load(out/'biomes/biome_restore/biomes_4x4x4.npz');biomes=expected['biomes'];names=list(expected['names'])
    if official_names:assert {'minecraft:'+str(b) for b in names}<=official_names
    for path in sorted((out/'world/safari/region').glob('*.mca')):
        file=path.read_bytes();occupied={0,1}
        for i in range(1024):
            location=int.from_bytes(file[i*4:i*4+4],'big');offset=location>>8;sectors=location&255
            if not offset:continue
            extent=set(range(offset,offset+sectors));assert not extent&occupied;occupied|=extent
            pos=offset*4096;length=int.from_bytes(file[pos:pos+4],'big');assert length+4<=sectors*4096;assert file[pos+4]==2
            root=n.File.parse(io.BytesIO(zlib.decompress(file[pos+5:pos+4+length])))
            assert int(root['DataVersion'])==3955 and str(root['Status'])=='minecraft:full'
            cx,cz=int(root['xPos']),int(root['zPos']);ix=cx*16+752;iz=cz*16+752
            for section in root['sections']:
                sy=int(section['Y'])*16+64;bs=section['block_states'];bp=bs['palette'];bios=section['biomes'];bpal=bios['palette']
                bvalues=unpack(bios['data'],max(1,(len(bpal)-1).bit_length()),64) if len(bpal)>1 else np.zeros(64,dtype=np.uint8)
                actual=np.array([str(v) for v in bpal])[bvalues].reshape(4,4,4)
                expect=np.array(['minecraft:'+str(v) for v in names])[biomes[sy//4:sy//4+4,iz//4:iz//4+4,ix//4:ix//4+4]]
                assert np.array_equal(actual,expect),(cx,cz,sy)
                seen.update(map(str,bpal));sections+=1
                if len(bp)>1:
                    vals=unpack(bs['data'],max(4,(len(bp)-1).bit_length()),4096);assert vals.max()<len(bp)
                else:vals=np.zeros(4096,dtype=np.uint8)
                if source is not None:
                    for point in [0,777,4095]:
                        p=bp[int(vals[point])];state=str(p['Name']);properties=p.get('Properties',{})
                        if properties:state+='['+','.join(k+'='+str(v) for k,v in sorted(properties.items()))+']'
                        original=palette[int(source[sy+point//256,iz+(point//16)%16,ix+point%16])]
                        def normalized(s):
                            name,_,props=s.partition('[');return name,sorted(props.rstrip(']').split(',')) if props else []
                        assert normalized(state)==normalized(original),(cx,cz,sy,point);samples+=1
            count+=1
        print('Validated region',path.name,flush=True)
    assert count==8836 and len(seen)==26
    report.update(chunks=count,sections=sections,actual_biomes=sorted(seen),world_roundtrip_block_samples=samples)
    manifest=json.loads((out/'schematics/manifest.json').read_text());schems=0;blocks_total=0
    for tile in manifest['tiles']:
        root=n.load(out/'schematics'/tile['file'])['Schematic'];assert int(root['Version'])==3 and int(root['DataVersion'])==3955
        w,h,d=map(int,[root['Width'],root['Height'],root['Length']]);assert [w,h,d]==tile['size'];size=w*h*d
        b=root['Blocks'];data=decode(b['Data'],size);assert int(data.max())<len(b['Palette'])
        bio=root['Biomes'];bd=decode(bio['Data'],size);assert int(bd.max())<len(bio['Palette'])
        x,y,z=tile['paste_at'];ix=x+752;iz=z+752;iy=y+64
        if source is not None:
            lookup=np.zeros(len(b['Palette']),np.uint8)
            for name,k in b['Palette'].items():lookup[int(k)]=palette.index(name)
            assert np.array_equal(lookup[data].reshape(h,d,w),source[iy:iy+h,iz:iz+d,ix:ix+w]),tile['file']
        expected_b=biomes[np.ix_(np.arange(iy,iy+h)//4,np.arange(iz,iz+d)//4,np.arange(ix,ix+w)//4)]
        assert np.array_equal(bd.reshape(h,d,w),expected_b),tile['file']
        blocks_total+=size;schems+=1
    assert schems==37
    report.update(schematics=schems,schematic_blocks_roundtripped=blocks_total,schematic_biomes_roundtripped=blocks_total)
    report['minecraft_runtime_load']='V1 loaded by operator; Current revision not loaded in a Minecraft client/server in this environment.'
    report['worldedit_runtime_paste']='NOT EXECUTED: structurally validated against Sponge v3 specification'
    report['multiworld_import']='Isaiah Multiworld 1.14.2 identified from supplied JAR; Current revision import not executed on operator server.'
    report['cobblemon_spawn']='NOT EXECUTED: depends on server datapacks and conditions'
    (out/'validation/validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--official-biomes');p.add_argument('--official-blocks');a=p.parse_args();validate(a.output,a.official_biomes,a.official_blocks)
