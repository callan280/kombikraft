"""Versioned name contract; optional original-code runs require local inputs."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from kombikraft.research.f97 import read_input,scene_bindings

HAS_UNICORN=importlib.util.find_spec('unicorn')is not None

@unittest.skipUnless(HAS_UNICORN,'Optional Unicorn dependency is not installed')
class UniformV2Admission(unittest.TestCase):
    def test_unsupported_source_cannot_enter_native_name_fixture(self):
        from kombikraft.research.f97 import _uniform_loader_v2 as unit
        with patch.object(unit,'_name_case')as execute:
            with self.assertRaisesRegex(ValueError,'bank: unsupported source hash'):
                unit.name_regressions(b'authored invalid bank',b'',b'',0)
            execute.assert_not_called()

    def test_other_profiles_cannot_reuse_admitted_bank_identity(self):
        from kombikraft.research.f97 import _uniform_loader_v2 as unit
        from kombikraft.research.f97 import PROFILE
        with patch.object(unit,'sha',return_value=PROFILE['bank']),patch.object(unit,'_name_case')as execute:
            with self.assertRaisesRegex(ValueError,'scene: unsupported source hash'):
                unit.name_regressions(b'authored',b'wrong scene',b'',0)
            execute.assert_not_called()


@unittest.skipUnless(HAS_UNICORN and all(os.environ.get('KOMBIKRAFT_F97_'+name)for name in('BANK','SCENE','NOR')),'Optional admitted local firmware inputs are not configured')
class UniformV2OriginalCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank,cls.scene,cls.nor=[read_input(os.environ['KOMBIKRAFT_F97_'+role.upper()],role)for role in('bank','scene','nor')]
        cls.pool,cls.rows=scene_bindings(cls.bank,cls.scene,cls.nor)

    def test_original_lookup_distinguishes_source_names_and_rejects_bad_origin(self):
        from kombikraft.research.f97 import _uniform_loader_v2 as unit
        runs=unit.name_regressions(self.bank,self.scene,self.nor,self.pool)
        self.assertEqual(len(runs),4)
        self.assertEqual(sum(r['acceptedCallerFixture']for r in runs),2)
        self.assertEqual(sum(r['rejectedRawOriginWitness']for r in runs),2)
        for run in runs:
            actual={r['name']:r for r in run['originalNameLookupResults']}
            if run['acceptedCallerFixture']:
                self.assertEqual(actual['u_SLDActive']['valueHex'],'00000000')
                self.assertEqual(actual['u_SLDLimit']['valueHex'],'0000803f')
                self.assertTrue(all(r['found']for r in actual.values()))
            else:
                self.assertFalse(any(r['found']for r in actual.values()))
                self.assertEqual(run['nativeEntryCount'],3)
            self.assertGreater(run['originalInstructionsByPhase']['native-name-lookup'],0)

    def test_all_v1_numeric_fixtures_remain_exact_with_real_name_lookup(self):
        from kombikraft.research.f97 import _uniform_loader as historical,_uniform_loader_v2 as successor
        count=0
        for row in self.rows:
            for fill in(0,0xa5):
                for value in(1,0,.375):
                    previous=historical.observe(self.bank,self.scene,self.nor,self.pool,row,fill,value)
                    current=successor.observe(self.bank,self.scene,self.nor,self.pool,row,fill,value)
                    self.assertEqual(previous['uniformBytesHex'],current['uniformBytesHex'])
                    self.assertTrue(current['nativeCStringNameVerified'])
                    self.assertTrue(current['originalNameLookupExecuted'])
                    count+=1
        self.assertEqual(count,66)

if __name__=='__main__':unittest.main()
