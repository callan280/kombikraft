"""Synthetic tests only: no firmware, VM, private source or device access."""
from pathlib import Path
import hashlib,json,shutil,tempfile,unittest
from validate_layout import validate,zeros_hash
from make_bridge import build


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'fixture.dat').write_bytes(b'authored synthetic input')
        self.row={'name':'authored_input','address':'0x1000','bytes':24,'readonly':True,
                  'file':'fixture.dat','sha256':hashlib.sha256(b'authored synthetic input').hexdigest()}
    def tearDown(self):self.temp.cleanup()
    def test_resolves_without_mutating_input(self):
        original={'regions':[self.row]};before=json.dumps(original)
        actual=validate(original,self.root);self.assertTrue(Path(actual['regions'][0]['file']).is_absolute())
        self.assertEqual(before,json.dumps(original))
    def test_modified_file_rejected(self):
        (self.root/'fixture.dat').write_bytes(b'x'*24)
        with self.assertRaises(ValueError):validate({'regions':[self.row]},self.root)
    def test_overlap_rejected(self):
        other=dict(self.row,name='second',address='0x1001')
        with self.assertRaises(ValueError):validate({'regions':[self.row,other]},self.root)
    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):validate({'regions':[dict(self.row,file='../outside.dat')]},self.root)
    def test_overflow_rejected(self):
        with self.assertRaises(ValueError):validate({'regions':[dict(self.row,address='0xfffffffffffffff0')]},self.root)
    def test_exact_zero_window(self):
        row={'name':'authored_zero','address':'0x2fd3','bytes':19,'readonly':False,'sha256':zeros_hash(19)}
        self.assertEqual(validate({'regions':[row]},self.root)['regions'][0]['bytes'],19)
    @unittest.skipUnless(shutil.which('clang'),'clang is required for authored assembly test')
    def test_authored_bridge_matches_tested_bytes(self):
        bridge,rom=build(self.root/'bridge',shutil.which('clang'))
        self.assertEqual(len(bridge),96);self.assertEqual(rom[0xfff0:0xfff5],bytes.fromhex('ea00800000'))
        self.assertEqual(hashlib.sha256(bridge).hexdigest(),'a5e0b5a4a0ae60bea55a199eb3277757c23da87de6ce588614e8e5815c4a7ba2')


if __name__=='__main__':unittest.main()
