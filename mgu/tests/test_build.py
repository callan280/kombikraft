from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, tarfile, tempfile, unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location('mgu_build', ROOT / 'tools/build.py')
build = importlib.util.module_from_spec(loader)
loader.loader.exec_module(build)

class BuildTests(unittest.TestCase):
    def test_deterministic_sdk_free_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            one, receipt = build.build('kombikraft', out / 'one')
            two, _ = build.build('kombikraft', out / 'two')
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertFalse(receipt['sdkIncluded'])
            self.assertFalse(receipt['factorySkinInjectionProved'])
            with tarfile.open(one) as archive:
                names = archive.getnames()
                self.assertFalse(any('node_modules/' in n for n in names))
                self.assertFalse(any('experiments/' in n for n in names))
                for item in archive:
                    self.assertTrue(item.isfile())
                    self.assertEqual((item.uid, item.gid, item.mtime), (0, 0, 0))
                    self.assertNotIn('..', Path(item.name).parts)
                javascript = archive.extractfile('package/javascript/app.js').read()
                self.assertIn(b"require('oap-sdk')", javascript)
                self.assertNotIn(b'/Users/', javascript)
                self.assertEqual(json.load(archive.extractfile('package/package.json'))['version'], '0.1.0')

    def test_native_states_components_and_strings_are_consistent(self):
        spec, files = build.package_files('kombikraft')
        xml = ET.fromstring(files['rhmiData/uiDescriptions/ID7/application.xml'])
        ui = json.loads(files['rhmiData/uiDescriptions/ID7/uiDescription.json'])
        runtime = json.loads(files['javascript/app-spec.json'])
        self.assertEqual(len(xml.findall('container')), len(spec['screens']))
        self.assertEqual(set(runtime['stateIds']), {s['name'] for s in spec['screens']})
        names = [c['name'] for state in ui['containers'].values() for c in state['components'].values()]
        for setting in spec['settings']:
            self.assertIn('PREF_' + setting['key'].upper(), names)
            if setting.get('blocked'):
                self.assertIs(setting['default'], False)

    def test_experimental_entry_has_distinct_prerelease_and_no_false_status(self):
        normal, files = build.package_files('kombikraft')
        lab, lab_files = build.package_files('kombikraft', True)
        self.assertNotEqual(normal['version'], lab['version'])
        app = json.loads(lab_files['rhmiData/application.json'])['application']
        self.assertEqual(len(app['entryPoints']), 2)
        entry = app['entryPoints'][1]
        self.assertEqual((entry['insertionStateId'], entry['insertionFocusId'], entry['insertionOrder']), (20800, 24327, 65533))
        runtime = json.loads(lab_files['javascript/app-spec.json'])
        self.assertFalse(runtime['factoryEntryVehicleValidated'])
        self.assertEqual(runtime['entryRoutes'][entry['uuid']], 'HUD')
        hud = next(c for c in json.loads(lab_files['rhmiData/uiDescriptions/ID7/uiDescription.json'])['containers'].values() if c['name'] == 'HUD')
        self.assertNotIn('ParentState', hud.get('properties', {}))
        containers = json.loads(lab_files['rhmiData/uiDescriptions/ID7/uiDescription.json'])['containers']
        for container in containers.values():
            if container['name'] not in ('MAIN', 'HUD'):
                self.assertEqual(container['properties']['ParentState']['value'], runtime['stateIds']['MAIN'])
        self.assertEqual(len(json.loads(files['rhmiData/application.json'])['application']['entryPoints']), 1)

    def test_store_catalog_and_mgu_out_protocol(self):
        catalog = json.loads((ROOT / 'mgu-repo.json').read_text())
        self.assertEqual(catalog['apps']['path'], 'mgu/apps/*')
        self.assertNotIn('sdk', catalog['apps']['build'])
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ, MGU_OUT=temporary)
            result = subprocess.run(['python3', str(ROOT / 'tools/build.py'), 'kombikraft'], cwd=temporary, env=env, check=True, capture_output=True, text=True)
            self.assertFalse(json.loads(result.stdout)['sdkIncluded'])
            self.assertEqual(len(list(Path(temporary).glob('*.tgz'))), 1)

    def test_identity_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            build.package_files('../kombikraft')

    def test_actual_app_source_mocked_lifecycle(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            artifact, _ = build.build('kombikraft', out)
            with tarfile.open(artifact) as archive:
                for member in archive:
                    relative = Path(member.name)
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn('..', relative.parts)
                    self.assertTrue(member.isfile())
                    target = out / 'tree' / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
            subprocess.run(['node', str(ROOT / 'tests/lifecycle_mock.js'), str(out / 'tree/package')], check=True, capture_output=True, text=True)

if __name__ == '__main__':
    unittest.main()
