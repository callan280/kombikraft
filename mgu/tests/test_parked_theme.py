from pathlib import Path
import hashlib, importlib.util, json, subprocess, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
loader=importlib.util.spec_from_file_location('mgu_build',ROOT/'tools/build.py')
build=importlib.util.module_from_spec(loader);loader.loader.exec_module(build)
class ParkedThemeTests(unittest.TestCase):
 def test_package_and_runtime(self):
  spec, files=build.package_files('kombikraft_test')
  manifest=json.loads(files['manifest.json'])
  for iface in spec['readSignals']:
   self.assertEqual(set(manifest['proxies'][iface]['attributes'].values()),{'rs'})
   self.assertNotIn('methods',manifest['proxies'][iface])
  self.assertNotIn(b'InternalTasu',files['javascript/app.js'])
  self.assertIn('LICENSE.MPL-2.0',files)
  self.assertEqual(len(json.loads(files['rhmiData/application.json'])['application']['entryPoints']),1)
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for name,data in files.items():
    out=root/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
   result=subprocess.run(['node',str(ROOT/'tests/test_theme.cjs'),str(root)],capture_output=True,text=True,timeout=20)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   lifecycle=subprocess.run(['node',str(ROOT/'tests/test_theme_lifecycle.cjs'),str(root)],capture_output=True,text=True,timeout=20)
   self.assertEqual(lifecycle.returncode,0,lifecycle.stdout+lifecycle.stderr)
   a,_=build.build('kombikraft_test',root/'a');b,_=build.build('kombikraft_test',root/'b')
   self.assertEqual(hashlib.sha256(a.read_bytes()).digest(),hashlib.sha256(b.read_bytes()).digest())
 def test_no_factory_injection_variant(self):
  with self.assertRaises(ValueError):build.package_files('kombikraft_test',True)
if __name__=='__main__':unittest.main()
