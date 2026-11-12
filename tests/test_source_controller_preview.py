from pathlib import Path
import json
import shutil
import subprocess
import unittest


class SourceControllerPreviewTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is required for browser model checks')
    def test_source_output_projection_and_unsupported_state(self):
        script = Path(__file__).with_name('source_controller_preview.cjs')
        result = subprocess.run([shutil.which('node'), str(script)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['passed'])
        self.assertEqual(report['protocolStateChecks'], 24)
        self.assertFalse(report['originalFirmwareExecuted'])


if __name__ == '__main__':
    unittest.main()
