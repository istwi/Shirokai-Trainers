#!/usr/bin/env python3
"""Corrupt biome data in a copy of one real region, restore, compare entire file."""
import sys,io,json,zlib,struct,math,tempfile,shutil,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'deps'))
import nbtlib as n
from nbtlib import tag as T
from restore_biomes import restore
root=Path(sys.argv[1]);region=root/'world/safari/region/r.0.0.mca';original=region.read_bytes()
with tempfile.TemporaryDirectory(prefix='safari-restore-') as tmp:
    world=Path(tmp)/'safari';(world/'region').mkdir(parents=True);shutil.copy2(root/'world/safari/level.dat',world/'level.dat')
    header=bytearray(original[:8192]);body=bytearray();sector=2;corrupt=0
    for index in range(1024):
        loc=int.from_bytes(original[index*4:index*4+4],'big');pos=(loc>>8)*4096
        if not pos:continue
        size=int.from_bytes(original[pos:pos+4],'big');chunk=n.File.parse(io.BytesIO(zlib.decompress(original[pos+5:pos+4+size])))
        for section in chunk['sections']:
            section['biomes']=T.Compound({'palette':T.List[T.String](['minecraft:desert'])});corrupt+=1
        stream=io.BytesIO();chunk.write(stream);compressed=zlib.compress(stream.getvalue(),6);data=struct.pack('>I',len(compressed)+1)+b'\x02'+compressed;nsec=math.ceil(len(data)/4096)
        header[index*4:index*4+4]=((sector<<8)|nsec).to_bytes(4,'big');body.extend(data);body.extend(b'\0'*(nsec*4096-len(data)));sector+=nsec
    target=world/'region'/region.name;target.write_bytes(header+body)
    assert target.read_bytes()!=original
    restore(world,root/'biomes/biome_restore/biomes_4x4x4.npz',True)
    assert target.read_bytes()==original,'Restoration must recover entire region byte-for-byte.'
    report={'passed':True,'corrupted_sections_restored':corrupt,'region':region.name,'entire_region_sha256':hashlib.sha256(original).hexdigest(),'method':'Deliberately replaced all biome palettes in a copy of one generated region, restored them, compared entire MCA byte-for-byte with original. Backup creation verified.'}
    backups=list(Path(tmp).glob('safari-biomes-backup-*'));assert len(backups)==1 and (backups[0]/region.name).exists()
    (root/'validation/restore_test.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
