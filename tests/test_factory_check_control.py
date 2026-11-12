"""Authored admission tests; ordinary test data only, no firmware required."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from kombikraft.factory.check_control import (
    EXTRA,OriginalCcControllerBackend,cc_fixture,check_control_manifest_template,
    load_check_control_banks,FactoryExecutionError,FactoryInputError,SourceBank)


class CheckControlAdmissionTests(unittest.TestCase):
    def test_selected_id_fixture(self):
        native,wire,quality,mode,origin=cc_fixture({'ccid':2051})
        self.assertEqual(len(native),66);self.assertEqual(len(wire),67)
        self.assertEqual(native[:2],b'\x03\x08');self.assertEqual(wire[:2],b'\x08\x03')
        self.assertEqual((quality,mode),(0,None))

    def test_native66_preserves_tail_and_changes_only_word_endianness(self):
        native=struct.pack('<8H',*range(1000,1008))+bytes(range(50))
        got,wire,quality,mode,origin=cc_fixture({'record66Hex':native.hex(),'quality':133,'mode':2})
        self.assertEqual(got,native)
        self.assertEqual(wire,struct.pack('>8H',*range(1000,1008))+native[16:]+b'\x85')
        self.assertEqual((quality,mode),(133,2))

    def test_ambiguous_unknown_and_malformed_fixture_rejected(self):
        bad=[None,[],{}, {'ccid':1,'record66Hex':'00'*66},{'ccid':1,'other':0},
             {'ccid':True},{'ccid':-1},{'ccid':65536},{'record66Hex':'00'*65},
             {'record66Hex':'gg'*66},{'ccid':1,'quality':True},{'ccid':1,'quality':256},
             {'ccid':1,'mode':1},{'ccid':1,'mode':False}]
        for row in bad:
            with self.subTest(row=row),self.assertRaises(FactoryExecutionError):cc_fixture(row)

    def test_auxiliary_hash_admission_precedes_unicorn_or_core(self):
        wrong=SourceBank(EXTRA[0],EXTRA[1],EXTRA[2],b'authored fixture')
        with patch.dict('sys.modules',{'unicorn':None}),self.assertRaises(FactoryInputError):
            OriginalCcControllerBackend([],wrong)

    def test_command_envelope_rejected_before_execution(self):
        backend=object.__new__(OriginalCcControllerBackend)
        commands=({'signal':'other','raw':0},{'signal':[],'raw':0},{'signal':'bc'},
                  {'signal':'bc','raw':1,'extra':0})
        for command in commands:
            with self.subTest(command=command),self.assertRaises(FactoryExecutionError):backend.command(command)

    def test_auxiliary_metadata_and_set_admission_precede_file_load(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest=Path(directory,'manifest.json')
            template=check_control_manifest_template()
            for change in ('missing','extra','base','digest'):
                value=json.loads(json.dumps(template))
                if change=='missing':value['banks'].pop()
                elif change=='extra':value['banks'].append({'name':'unreviewed'})
                elif change=='base':value['banks'][-1]['base']='0x1000'
                else:value['banks'][-1]['sha256']='0'*64
                manifest.write_text(json.dumps(value))
                with patch('kombikraft.factory.check_control.load_banks',return_value=()), \
                     patch('kombikraft.factory.check_control.validate_bank_file') as validate, \
                     self.assertRaises(FactoryInputError):
                    load_check_control_banks(manifest,directory)
                validate.assert_not_called()

    def test_template_cli_works_without_site_packages_or_unicorn(self):
        source=Path(__file__).resolve().parents[1]/'src'
        env=dict(os.environ,PYTHONPATH=str(source))
        result=subprocess.run([sys.executable,'-S','-m','kombikraft.factory.check_control_cli',
                               '--manifest-template'],capture_output=True,text=True,env=env,check=True)
        template=json.loads(result.stdout)
        self.assertEqual(template,check_control_manifest_template())
        self.assertEqual(len(template['banks']),14)
        self.assertTrue(all(set(row)=={'name','file','base','sha256'} for row in template['banks']))


if __name__=='__main__':unittest.main()
