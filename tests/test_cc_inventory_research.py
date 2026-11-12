"""Admission and failed-execution evidence for the optional source inventory."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kombikraft.research.check_control_inventory import catalogue, run, validate_selection


def clear_result():
    payload = bytearray(72)
    payload[64] = payload[66] = 255
    return {'selected': {'selectedCcid': 0, 'payloadReadbackMatchesConsumer': True,
                         'originalPayloadConsumerObserved': False,
                         'sourceProfile': 'gss-5c58-160.002.002', 'sourceLanguageOrdinal': 2,
                         'sourceVariantIndex': 1, 'sourceCollectionBankOrdinal': 1,
                         'originalGraphicsReady': False, 'sourcePayload72Hex': payload.hex(),
                         'textLines': [None, None], 'primaryIcon': None, 'collectionSlots': [],
                         'iconSelector': 255, 'textSelector': 255}}


class InventoryTests(unittest.TestCase):
    def test_original_inventory_preserves_placeholder_and_unaliased_boundary(self):
        value, digest = catalogue()
        entries = {e['ccid']: e for e in value['entries']}
        self.assertEqual(len(entries), 966)
        self.assertEqual(value['unaliasedRecordIndex'], 966)
        self.assertEqual(entries[37]['originalTextTemplates'], ['Trigger %0', ''])
        self.assertNotIn(65535, entries)
        self.assertEqual(len(digest), 64)
        self.assertFalse(value['currentCarApplicabilityVerified'])

    def test_clear_rejects_hidden_pointer_and_collection_despite_null_display_fields(self):
        baseline = clear_result()
        validate_selection(baseline, 0)
        payload = bytearray.fromhex(baseline['selected']['sourcePayload72Hex'])
        payload[32] = 1
        baseline['selected']['sourcePayload72Hex'] = payload.hex()
        with self.assertRaisesRegex(ValueError, 'pointers'):
            validate_selection(baseline, 0)
        baseline = clear_result()
        baseline['selected']['collectionSlots'] = [{'slot': 0}]
        with self.assertRaisesRegex(ValueError, 'content'):
            validate_selection(baseline, 0)

    def test_source_identity_and_live_graphics_cannot_be_relabelled(self):
        for key, value in [('sourceVariantIndex', True), ('sourceLanguageOrdinal', 3),
                           ('sourceProfile', 'another-profile'), ('originalGraphicsReady', True)]:
            result = clear_result()
            result['selected'][key] = value
            with self.assertRaises(ValueError):
                validate_selection(result, 0)

    def test_existing_destination_or_unknown_id_never_starts_original_code(self):
        with tempfile.TemporaryDirectory() as directory, patch('kombikraft.research.check_control_inventory.SourceControllerProcess') as worker:
            destination = Path(directory) / 'existing'
            destination.mkdir()
            with self.assertRaises(FileExistsError):
                run('unused', 'unused', destination, [14])
            with self.assertRaises(ValueError):
                run('unused', 'unused', Path(directory) / 'unknown', [65535])
            worker.assert_not_called()

    def test_worker_failure_leaves_failed_receipt_and_no_success_claim(self):
        with tempfile.TemporaryDirectory() as directory, patch('kombikraft.research.check_control_inventory.SourceControllerProcess', side_effect=RuntimeError('source failed')):
            destination = Path(directory) / 'new'
            with self.assertRaisesRegex(RuntimeError, 'source failed'):
                run('unused', 'unused', destination, [14])
            result = json.loads((destination / 'receipt.json').read_text())
            self.assertFalse(result['passed'])
            self.assertFalse(result['executionCompleted'])
            self.assertEqual(result['completedIds'], 0)
            self.assertIsNone(result['casesSha256'])
            self.assertFalse(result['installationAllowed'])


if __name__ == '__main__':
    unittest.main()
