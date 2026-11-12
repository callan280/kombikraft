"""Synthetic tests only: no BMW payload, VM, network or car is required."""
import hashlib,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import source_profile as s
class Admission(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.p=Path(self.temp.name)/'synthetic';self.addCleanup(self.temp.cleanup)
 def image(self,magic=b'\x7fELF\x02\x01',machine=62):
  b=bytearray(64);b[:len(magic)]=magic;struct.pack_into('<H',b,18,machine);return bytes(b)
 def fixture(self,b):self.p.write_bytes(b);return patch.object(s,'SOURCE_SHA256',hashlib.sha256(b).hexdigest())
 def test_reject_unmatched_hash(self):
  self.p.write_bytes(self.image())
  with self.assertRaisesRegex(ValueError,'unsupported firmware'):s.admit_firmware(self.p)
 def test_synthetic_exact_admission(self):
  b=self.image()
  with self.fixture(b):self.assertEqual(s.admit_firmware(self.p),(self.p.resolve(),b))
 def test_reject_wrong_magic_even_matching_digest(self):
  with self.fixture(self.image(b'MZ')):
   with self.assertRaisesRegex(ValueError,'ELF64'):s.admit_firmware(self.p)
 def test_reject_wrong_machine_even_matching_digest(self):
  with self.fixture(self.image(machine=40)):
   with self.assertRaisesRegex(ValueError,'x86-64'):s.admit_firmware(self.p)
 def test_reject_output_source_collision(self):
  self.p.write_bytes(b'fixture')
  with self.assertRaisesRegex(ValueError,'distinct'):s.output_directory(self.p,self.p)
 def test_reject_output_existing_file(self):
  other=self.p.with_name('other');other.write_bytes(b'fixture')
  with self.assertRaisesRegex(ValueError,'directory'):s.output_directory(other,self.p)
 def test_create_separate_output_directory(self):
  p=self.p.with_name('outputs');self.assertTrue(s.output_directory(p,self.p).is_dir())
 def test_cli_requires_explicit_inputs(self):
  with self.assertRaises(SystemExit):s.make_parser('test').parse_args([])
 def test_source_missing_fails_without_output(self):
  with self.assertRaises(FileNotFoundError):s.admit_firmware(self.p)
 def test_reject_forged_map_imports(self):
  expected={'sourceSha256':'fixture','pltLabels':[{'va':'0x10','name':'fixture'}],'ranges':[]}
  actual=dict(expected,pltLabels=[{'va':'0x20','name':'fixture'}])
  with self.assertRaisesRegex(ValueError,'pltLabels'):s.validate_map(actual,expected)
 def test_reject_forged_map_ranges(self):
  expected={'sourceSha256':'fixture','pltLabels':[],'ranges':[{'length':10}]}
  with self.assertRaisesRegex(ValueError,'ranges'):s.validate_map(dict(expected,ranges=[]),expected)
 def test_identical_synthetic_map(self):
  expected={'sourceSha256':'fixture','pltLabels':[],'ranges':[]};self.assertIsNone(s.validate_map(expected,expected))
if __name__=='__main__':unittest.main()
