import unittest,io,tempfile,shutil,struct,zlib,math
from pathlib import Path
import numpy as np
from generate import pack,varints
from validate import unpack,decode
from restore_biomes import restore

class EncodingTests(unittest.TestCase):
    def test_non_crossing_minecraft_bit_packing(self):
        rng=np.random.default_rng(42)
        for bits in [1,2,3,4,5,6,9,13]:
            for count in [64,256,4096]:
                values=rng.integers(0,1<<bits,count,dtype=np.uint64)
                self.assertTrue(np.array_equal(unpack(pack(values,bits),bits,count),values))
    def test_sponge_varint_boundary(self):
        values=np.array([0,1,127,128,129,255,16383],np.uint16)
        # Generator uses only uint8 palettes; at most 256 entries.
        values=values[:-1]
        encoded=varints(values)
        self.assertTrue(np.array_equal(decode(np.frombuffer(encoded,dtype=np.int8),len(values)),values))
    def test_restore_requires_explicit_shutdown_confirmation(self):
        with self.assertRaises(AssertionError):restore(Path('missing'),Path('missing'),False)

if __name__=='__main__':unittest.main()
