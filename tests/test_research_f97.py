"""Admission regressions using authored inputs, without firmware or Unicorn."""
import contextlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from kombikraft.research.f97 import PROFILE,read_input,run
from kombikraft.research.f97.__main__ import main

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('norboot',ROOT/'tools/extract_norboot_bank.py')
norboot=importlib.util.module_from_spec(spec);spec.loader.exec_module(norboot)


class MaterialAdmission(unittest.TestCase):
    def test_profile_does_not_claim_arbitrary_firmware_support(self):
        self.assertEqual(set(PROFILE),{'id','bank','scene','nor'})
        for role in ('bank','scene','nor'):self.assertEqual(len(PROFILE[role]),64)

    def test_wrong_input_rejected_without_emulator_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'authored-input';p.write_bytes(b'not firmware')
            with patch.dict('sys.modules',{'unicorn':None}):
                for role in ('bank','scene','nor'):
                    with self.assertRaisesRegex(ValueError,'unsupported source hash'):read_input(p,role)
                with self.assertRaisesRegex(ValueError,'unsupported source hash'):run(b'',b'',b'')

    def test_oversized_input_rejected_before_read(self):
        with patch.object(Path,'stat') as stat,patch.object(Path,'read_bytes') as read:
            stat.return_value.st_size=65*1024*1024
            with self.assertRaisesRegex(ValueError,'64 MiB'):read_input('input','bank')
            read.assert_not_called()

    def test_failed_admission_does_not_create_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/'source';source.write_bytes(b'authored wrong input')
            output=Path(temporary)/'new'/'receipt.json'
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main(['--bank',str(source),'--scene',str(source),'--nor',str(source),'--output',str(output)])
            self.assertFalse(output.parent.exists())

    def test_existing_receipt_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'receipt.json';p.write_text('keep')
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main(['--bank','missing','--scene','missing','--nor','missing','--output',str(p)])
            self.assertEqual(p.read_text(),'keep')


class NorbootAdmission(unittest.TestCase):
    def image(self):
        payload=b'authored'
        return b'NORboot\0'+struct.pack('<2I',0x14,1)+struct.pack('<6I',40,0x20000,len(payload),7,16,4)+payload

    def test_selected_table_record(self):
        row=norboot.record(self.image(),0,0)
        self.assertEqual((row['packedOffset'],row['decodedBytes'],row['word4']),(40,7,16))

    def test_truncation_and_index_rejected(self):
        for image,offset,index in [(self.image()[:-1],0,0),(self.image(),-1,0),(self.image(),0,1)]:
            with self.assertRaises(ValueError):norboot.record(image,offset,index)

    def test_unsupported_lengths_and_flags(self):
        for position,value in [(28,0),(32,6),(36,0),(24,128*1024*1024)]:
            image=bytearray(self.image());struct.pack_into('<I',image,position,value)
            with self.assertRaises(ValueError):norboot.record(image,0,0)

    def test_literal_lz4_decode_with_local_library(self):
        import ctypes.util
        if not ctypes.util.find_library('lz4'):self.skipTest('No local liblz4')
        payload=b'\x80authored'
        image=b'NORboot\0'+struct.pack('<2I',0x14,1)+struct.pack('<6I',40,0x20000,len(payload),8,16,4)+payload
        self.assertEqual(norboot.decode(image,norboot.record(image,0,0)),b'authored')


if __name__=='__main__':unittest.main()
