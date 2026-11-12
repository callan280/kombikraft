"""Authored admission/coordinate checks; original firmware remains local."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from kombikraft.research.f97 import PROFILE
from kombikraft.research.f97.extended import EXTENDED_PROFILE,admit,admit_bitmaps,main,read_bitmaps,read_data_bank,run
from kombikraft.research.f97._widget_bindings import extract

ROOT=Path(__file__).resolve().parents[1]
digest=lambda b:hashlib.sha256(b).hexdigest()


class ExtendedAdmission(unittest.TestCase):
    def test_profile_prints_without_emulator(self):
        with patch.dict('sys.modules',{'unicorn':None}),contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['--profile']),0)
        profile=json.loads(output.getvalue())
        self.assertEqual(profile['bank'],PROFILE['bank']);self.assertEqual(len(profile['bitmaps']),19)
        self.assertEqual(len(profile['dataBank']),64)

    def test_invalid_api_bank_rejected_before_optional_imports(self):
        with patch.dict('sys.modules',{'unicorn':None}):
            for suite in ('all','image-sampling','loaded-images','controller','widgets'):
                with self.assertRaisesRegex(ValueError,'bank: unsupported source hash'):run(b'authored',suite=suite)

    def test_all_suite_admits_data_and_bitmaps_before_emulator(self):
        sample=b'authored';d=digest(sample)
        with patch.dict(PROFILE,{key:d for key in ('bank','scene','nor')}),patch.dict('sys.modules',{'unicorn':None}):
            with self.assertRaisesRegex(ValueError,'dataBank: unsupported source hash'):
                run(sample,sample,sample,b'wrong',{})
            with patch.dict(EXTENDED_PROFILE,{'dataBank':d}):
                with self.assertRaisesRegex(ValueError,'all19 named bitmap'):
                    run(sample,sample,sample,sample,{})

    def test_each_bitmap_hash_is_admitted(self):
        wrong={key:b'authored' for key in EXTENDED_PROFILE['bitmaps']}
        with self.assertRaisesRegex(ValueError,'Unsupported source bitmap hash'):admit_bitmaps(wrong)
        with self.assertRaisesRegex(ValueError,'all19'):admit_bitmaps({})

    def test_data_limit_precedes_read(self):
        with patch.object(Path,'stat') as stat,patch.object(Path,'read_bytes') as read:
            stat.return_value.st_size=65*1024*1024
            with self.assertRaisesRegex(ValueError,'64MiB'):read_data_bank('input')
            read.assert_not_called()

    def test_manifest_duplicate_missing_and_hash_admission(self):
        with tempfile.TemporaryDirectory() as temporary:
            h=Path(temporary);p=h/'manifest.json'
            p.write_text(json.dumps({'resources':[]}))
            with self.assertRaisesRegex(ValueError,'all19'):read_bitmaps(p)
            name=next(iter(EXTENDED_PROFILE['bitmaps']));(h/'bitmap.bin').write_bytes(b'authored')
            entry={'name':name,'kind':'0x7','decodedFile':'bitmap.bin'}
            p.write_text(json.dumps({'resources':[entry,entry]}))
            with self.assertRaisesRegex(ValueError,'Duplicate'):read_bitmaps(p)
            rows=[{'name':n,'kind':'0x7','decodedFile':'bitmap.bin'} for n in EXTENDED_PROFILE['bitmaps']]
            p.write_text(json.dumps({'resources':rows}))
            with self.assertRaisesRegex(ValueError,'Unsupported source bitmap hash'):read_bitmaps(p)

    def test_cli_failed_admission_leaves_no_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            h=Path(temporary);p=h/'bank';p.write_bytes(b'authored');out=h/'new'/'receipt.json'
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main(['--suite','controller','--bank',str(p),'--output',str(out)])
            self.assertFalse(out.parent.exists())

    def test_cli_preserves_existing_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            p=Path(temporary)/'receipt.json';p.write_text('preserve')
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                main(['--suite','controller','--bank','missing','--output',str(p)])
            self.assertEqual(p.read_text(),'preserve')

    def test_exported_observer_file_identities(self):
        manifest=json.loads((ROOT/'research/f97-extended-source-manifest.json').read_text())
        for row in manifest['files']:
            self.assertEqual(digest((ROOT/'src/kombikraft/research/f97'/row['destination']).read_bytes()),row['exportSha256'])


class WidgetStringOrigin(unittest.TestCase):
    def fixture(self):
        node=struct.pack('<3I',12,0x947,3)
        value=b'/Scene:ki_3d_high/Group:RootNode\0'
        record_at=len(node);string_at=record_at+36
        widget=struct.pack('<9I',36+2+len(value),0xa01,1,1,0,0,1,2,string_at+12)
        scene=node+widget+struct.pack('<H',len(value))+value
        return scene,{'1':'Example','2':'Node','3':'RootNode'},{0x947:'Group',0xa01:'Widget'}

    def test_reference_targets_length_record_not_truncated_path(self):
        scene,strings,classes=self.fixture();nodes,widgets,joins=extract(scene,strings,classes)
        binding=widgets[0]['bindings'][0]
        self.assertEqual(binding['sourceValue'],'/Scene:ki_3d_high/Group:RootNode')
        self.assertEqual(binding['sourceStringRecordOffset'],binding['encodedValueReference']-12)
        self.assertEqual(binding['sourceValueOffset'],binding['sourceStringRecordOffset']+2)
        self.assertEqual(binding['targetHeaderOffset'],0)
        self.assertEqual(joins,{'sceneNodes':1,'sceneRoot':0,'literalStringProperties':0})

    def test_wrong_unadjusted_reference_is_rejected(self):
        scene,strings,classes=self.fixture();wrong=bytearray(scene)
        original=struct.unpack_from('<I',wrong,12+32)[0]
        struct.pack_into('<I',wrong,12+32,original-12)
        with self.assertRaises(AssertionError):extract(bytes(wrong),strings,classes)


if __name__=='__main__':unittest.main()
