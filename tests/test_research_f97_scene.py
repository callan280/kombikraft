"""Admission/serialization checks plus optional original-source integration."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from kombikraft.research.f97 import PROFILE
from kombikraft.research.f97.extended import EXTENDED_PROFILE
from kombikraft.research.f97 import scene
from kombikraft.research.f97._scene_profile import SCENE_PROFILE

ROOT=Path(__file__).resolve().parents[1]

class SceneAdmission(unittest.TestCase):
    def test_profile_available_without_optional_emulator(self):
        with patch.dict('sys.modules',{'unicorn':None}),contextlib.redirect_stdout(io.StringIO())as output:
            self.assertEqual(scene.main(['--profile']),0)
        data=json.loads(output.getvalue())
        self.assertEqual(data['bank'],PROFILE['bank'])
        self.assertEqual(data['dataBank'],EXTENDED_PROFILE['dataBank'])
        self.assertFalse(data['normalFactoryState'])
        self.assertEqual(data['entryBankOffsets']['propertySuffixStopBefore'],0x3fa808)

    def test_wrong_bank_rejected_before_optional_imports(self):
        with patch.dict('sys.modules',{'unicorn':None}),patch.object(scene,'source_tables')as parse:
            with self.assertRaisesRegex(ValueError,'bank: unsupported source hash'):
                scene.run(b'authored',b'',b'',b'')
            parse.assert_not_called()

    def test_fourth_input_admitted_before_parsing_or_emulation(self):
        authored=b'authored';digest=hashlib.sha256(authored).hexdigest()
        with patch.dict(PROFILE,{key:digest for key in('bank','scene','nor')}),patch.dict('sys.modules',{'unicorn':None}),patch.object(scene,'source_tables')as parse:
            with self.assertRaisesRegex(ValueError,'dataBank: unsupported source hash'):
                scene.run(authored,authored,authored,b'wrong fourth input')
            parse.assert_not_called()

    def test_wrong_scene_coverage_cannot_enter_emulator(self):
        from kombikraft.research.f97 import _widget_bindings
        with patch.object(scene,'admit'),patch.object(scene,'source_tables',return_value=({},{})),patch.object(_widget_bindings,'extract',return_value=([],[],{})),patch.dict('sys.modules',{'unicorn':None}):
            with self.assertRaisesRegex(ValueError,'Unsupported source node coverage'):
                scene.run(b'authored',b'',b'',b'')

    def test_json_domain_normalizes_metadata_but_preserves_numeric_bits(self):
        data={'static':[(0x10625cc,200)],'matrix':[-0.0,1.25],'word':0xffffffff}
        got=scene._json_domain(data)
        self.assertEqual(got['static'],[[0x10625cc,200]])
        self.assertEqual(struct.pack('<2f',*got['matrix']),struct.pack('<2f',*data['matrix']))
        self.assertEqual(got['word'],0xffffffff)

    def test_failed_cli_admission_creates_no_receipt_or_parent(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary);source=root/'input';source.write_bytes(b'authored wrong input');output=root/'new'/'receipt.json'
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                scene.main(['--bank',str(source),'--scene',str(source),'--nor',str(source),'--data-bank',str(source),'--output',str(output)])
            self.assertFalse(output.parent.exists())

    def test_existing_receipt_remains_unchanged(self):
        with tempfile.TemporaryDirectory()as temporary:
            output=Path(temporary)/'receipt.json';output.write_text('preserve')
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                scene.main(['--bank','missing','--scene','missing','--nor','missing','--data-bank','missing','--output',str(output)])
            self.assertEqual(output.read_text(),'preserve')

    def test_authored_export_file_identities(self):
        manifest=json.loads((ROOT/'research/f97-scene-source-manifest.json').read_text())
        for row in manifest['files']:
            self.assertEqual(hashlib.sha256((ROOT/'src/kombikraft/research/f97'/row['destination']).read_bytes()).hexdigest(),row['exportSha256'])


HAS_SOURCE=importlib.util.find_spec('unicorn')is not None and all(os.environ.get('KOMBIKRAFT_F97_'+role)for role in('BANK','SCENE','NOR','DATA_BANK'))
@unittest.skipUnless(HAS_SOURCE,'Optional admitted local source inputs are not configured')
class OriginalSceneIntegration(unittest.TestCase):
    def test_original_tree_policies_cameras_and_source_footprints(self):
        bank,source,nor=[scene.read_input(os.environ['KOMBIKRAFT_F97_'+role.upper()],role)for role in('bank','scene','nor')]
        data=scene.read_data_bank(os.environ['KOMBIKRAFT_F97_DATA_BANK'])
        result=scene.run(bank,source,nor,data)
        self.assertEqual(result['counts']['originalPropertySuffixExecutions'],984)
        self.assertEqual(result['counts']['originalModelCameraProducts'],3760)
        self.assertFalse(result['limits']['normalOperatingOrCodingStateProved'])
        self.assertFalse(result['limits']['originalEnabledCollectorOrOuterTraversalExecuted'])
        self.assertFalse(result['limits']['installationAllowed'])
        self.assertTrue(result['summary']['nativeWorldBytesExactAcrossFills'])
        for group in result['cases'].values():
            self.assertEqual(len(group),2)
            for case in group:
                self.assertFalse(case['denials'])
                for span in case['executedOriginalSourceRanges']:
                    self.assertEqual(hashlib.sha256(bank[span['bankOffsetStart']:span['endExclusive']]).hexdigest(),span['sha256'])

if __name__=='__main__':unittest.main()
