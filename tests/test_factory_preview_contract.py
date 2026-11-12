"""Authored admission/mutation checks; actual source replay is separate."""
from copy import deepcopy
from pathlib import Path
import json
import struct
import unittest

from kombikraft.assets import AssetPack
from kombikraft.factory.preview_contract import SourceCcPreviewContract


PACK = Path(__file__).resolve().parents[1] / 'assets/viewer-pack'


def fixture(row=None, configuration=(2, 1, 1)):
    ccid = row['ccid'] if row else 0
    record = struct.pack('<H', ccid) + bytes(62)
    payload = bytearray(72)
    icon = None
    if row:
        icon = {'sourceProfile': 'gss-5c58-160.002.002', **row['primaryIcon']}
        struct.pack_into('<Q', payload, 0, 0x31000000)
        struct.pack_into('<Q', payload, 8, 0x31000200)
        struct.pack_into('<Q', payload, 16, int(icon['descriptorVa'], 16))
    payload[64] = row['textSelector'] if row else 255
    payload[66] = row['iconSelector'] if row else 255
    return {'sourceProfile': 'gss-5c58-160.002.002', 'selectedCcid': ccid,
            'selectedRecord64Hex': record.hex(), 'sourcePayload72Hex': payload.hex(),
            'originalPayloadConsumerObserved': True, 'payloadReadbackMatchesConsumer': True,
            'originalGraphicsReady': False, 'sourceLanguageOrdinal': configuration[0],
            'sourceVariantIndex': configuration[1], 'sourceCollectionBankOrdinal': configuration[2],
            'textLines': row['textLines'] if row else [None, None], 'primaryIcon': icon,
            'collectionSlots': [], 'iconSelector': payload[66], 'textSelector': payload[64],
            'iconSelectorHelperRGBA': row['iconSelectorHelperRGBA'] if row else [1., 1., 1., 1.],
            'textSelectorHelperRGBA': row['textSelectorHelperRGBA'] if row else [1., 1., 1., 1.]}


class PreviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = AssetPack(PACK)
        cls.contract = SourceCcPreviewContract(cls.pack)
        cls.rows = cls.contract.contract['records']

    def test_all_reviewed_records_both_configurations_and_real_null_clear_shape(self):
        for row in self.rows:
            for config in ((2, 0, 0), (2, 1, 1)):
                with self.subTest(ccid=row['ccid'], config=config):
                    plan = self.contract.plan(fixture(row, config))
                    self.assertEqual((plan['status'], plan['action']), ('supported', 'show'), plan)
                    self.assertEqual(plan['popup']['originalLines'], row['textLines'])
                    self.assertTrue(plan['popup']['originalControllerComputed'])
                    self.assertFalse(plan['factoryGraphics'])
                    self.assertFalse(plan['vehicleCompatibilityVerified'])
        clear = self.contract.plan(fixture())
        self.assertEqual((clear['status'], clear['action'], clear['popup']), ('supported', 'clear', None))

    def test_missing_or_different_assets_do_not_invent_a_popup(self):
        self.assertFalse(SourceCcPreviewContract().status()['available'])
        self.assertEqual(SourceCcPreviewContract().plan(fixture(self.rows[0]))['status'], 'unsupported')
        pack = self.pack
        class ChangedPack:
            def read(self, route):
                raw = pack.read(route)
                return raw + b'changed' if route.endswith('BMWTARG.ttf') else raw
        altered = SourceCcPreviewContract(ChangedPack())
        self.assertFalse(altered.status()['available'])
        self.assertEqual(altered.plan(fixture(self.rows[0]))['status'], 'unsupported')

    def test_changed_source_state_is_not_a_known_popup_or_clear(self):
        mutations = [('sourceProfile', 'another'), ('sourceLanguageOrdinal', 1),
                     ('sourceVariantIndex', 2), ('sourceCollectionBankOrdinal', 2),
                     ('originalPayloadConsumerObserved', False), ('payloadReadbackMatchesConsumer', False),
                     ('originalGraphicsReady', True), ('selectedCcid', True),
                     ('textLines', ['Different source text', '']), ('primaryIcon', None),
                     ('iconSelector', 3), ('textSelector', 2), ('collectionSlots', [{'slot': 0}]),
                     ('iconSelectorHelperRGBA', [1, 181/255, 0, 1]),
                     ('textSelectorHelperRGBA', [float('nan'), 1, 1, 1]),
                     ('selectedRecord64Hex', '00'), ('sourcePayload72Hex', '00')]
        for key, value in mutations:
            with self.subTest(key=key):
                selected = deepcopy(fixture(self.rows[0])); selected[key] = value
                plan = self.contract.plan(selected)
                self.assertEqual(plan['status'], 'unsupported')
                self.assertIsNone(plan['action']); self.assertIsNone(plan['popup'])
        clear = fixture(); clear['textLines'] = ['', '']
        self.assertEqual(self.contract.plan(clear)['status'], 'unsupported')

    def test_unknown_and_collection_states_have_no_fallback_clear(self):
        for ccid in (34, 65535):
            selected = fixture(self.rows[0]); selected['selectedCcid'] = ccid
            selected['selectedRecord64Hex'] = (struct.pack('<H', ccid) + bytes(62)).hex()
            plan = self.contract.plan(selected)
            self.assertEqual(plan['status'], 'unsupported')
            self.assertIsNone(plan['action']); self.assertIsNone(plan['popup'])

    def test_published_contract_and_visual_metadata_agree(self):
        manifest = json.loads(self.pack.read('/design/original-cc/manifest.json'))
        entries = {r['ccid']: r for r in manifest['entries']}
        for row in self.rows:
            actual = entries[row['ccid']]
            for key, value in row['popup'].items():
                self.assertEqual(actual[key], value)


if __name__ == '__main__':
    unittest.main()
