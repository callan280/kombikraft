import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from kombikraft.factory.inputs import FactoryInputError, load_banks, validate_bank_file, manifest_template
from kombikraft.factory.profile import PROFILE

class FactoryInputTests(unittest.TestCase):
    def test_local_hash_validation_and_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "bank.bin").write_bytes(b"test fixture only")
            digest = hashlib.sha256(b"test fixture only").hexdigest()
            self.assertEqual(validate_bank_file(directory, "bank.bin", digest), b"test fixture only")
            with self.assertRaisesRegex(FactoryInputError, "hash mismatch"):
                validate_bank_file(directory, "bank.bin", "0" * 64)

    def test_escape_absolute_and_missing_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in ("../bank.bin", str(Path(directory, "bank.bin"))):
                with self.assertRaises(FactoryInputError):
                    validate_bank_file(directory, value, "0" * 64)
            with self.assertRaisesRegex(FactoryInputError, "Missing local"):
                validate_bank_file(directory, "absent.bin", "0" * 64)

    def test_profile_missing_and_duplicate_banks(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory, "input.json")
            for value, message in (({"profile": "unknown", "banks": []}, "Unsupported"),
                                   ([], "JSON object"),
                                   ({"profile": PROFILE, "banks": []}, "missing required"),
                                   ({"profile": PROFILE, "banks": [{"name": []}]}, "Invalid"),
                                   ({"profile": PROFILE, "banks": [{"name": None}]}, "Invalid"),
                                   ({"profile": PROFILE, "banks": [{"name": "same"}, {"name": "same"}]}, "duplicate")):
                manifest.write_text(json.dumps(value))
                with self.assertRaisesRegex(FactoryInputError, message):
                    load_banks(manifest, directory)

    def test_manifest_template_is_metadata_only(self):
        value = manifest_template()
        self.assertEqual(value["profile"], PROFILE)
        self.assertEqual(len(value["banks"]), 13)
        self.assertTrue(all(set(row) == {"name", "file", "base", "sha256"} for row in value["banks"]))

if __name__ == "__main__":
    unittest.main()
