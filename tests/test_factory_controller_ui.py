"""Optional Node execution of the browser module's authored DOM/fetch tests."""
from pathlib import Path
import shutil,subprocess,unittest


class ControllerUiTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node is unavailable for the isolated browser-state test')
    def test_fixture_and_original_output_remain_separate(self):
        result=subprocess.run([shutil.which('node'),str(Path(__file__).with_name('factory-controller-ui.cjs'))],
                              capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('"passed":true',result.stdout)


if __name__=='__main__':unittest.main()
