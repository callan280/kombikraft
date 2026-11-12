#!/usr/bin/env python3
"""Build an SDK-free OAP package. MGU Store supplies its local donor SDK at install.

Only Python's standard library is required. No network, firmware or SDK is read.
RHMI/OAP interoperability follows the MIT bimmer-lab kit; see ../THIRD_PARTY.md.
"""
from pathlib import Path
import argparse, copy, gzip, hashlib, io, json, os, re, struct, tarfile, uuid, zlib
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = uuid.UUID('0c0523a8-b82c-4301-b273-699e73c3ed31')

def canonical(value):
    return (json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + '\n').encode()

def identity(app, key):
    return str(uuid.uuid5(NAMESPACE, app + ':' + key))

def sid(app, key):
    return 'SID_' + re.sub('[^A-Z0-9]', '_', (app + '_' + key).upper())

def native_ui(spec):
    """Generate native list/drop-down states; no framebuffer or custom theme hook."""
    number = 0
    def allocate():
        nonlocal number
        number += 1
        return number
    strings = {sid(spec['id'], 'TITLE'): spec['title']}
    description = {'schemaVersion': '1.3.0', 'containers': {}}
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<application>']
    states = {}
    settings = {s['key']: s for s in spec['settings']}
    def text(key, value, cell='Text'):
        name = sid(spec['id'], key)
        strings[name] = value
        return {cell: {'value': name, 'type': 'StringId'}}
    first_state = None
    for screen in spec['screens']:
        state = allocate()
        states[screen['name']] = state
        container = {'type': 'state', 'name': screen['name'], 'components': {}}
        xml.append('    <container id="%d" type="state" widget="LT_State_Wide">' % state)
        if first_state is not None and not (spec.get('_factoryEntry') and screen['name'] == 'HUD'):
            xml.append('        <property id="9" value="%d"/>' % first_state)
            container['properties'] = {'ParentState': {'value': first_state, 'type': 'UInt'}}
        elif first_state is None:
            first_state = state
        group = allocate()
        xml.extend(['        <layoutGroup id="%d" name="List">' % group, '            <property id="3" value="1"/>'])
        components = []
        for kind, name, label in screen.get('items', []):
            widget, ctype = ('LT_Button_1Row', 'button') if kind == 'button' else ('LT_Label_3Row_1TextDyn', 'label')
            components.append((allocate(), ctype, widget, name, [text(name, label)], None))
        for key in screen.get('settings', []):
            setting = settings[key]
            name = 'PREF_' + key.upper()
            if setting['type'] == 'bool':
                components.append((allocate(), 'checkBox', 'LT_CheckBox_1Row', name, [text(name, setting['label'])], None))
            else:
                labels = setting['options']
                rows = [text(name + '_' + str(i), option[1], 'ItemText') for i, option in enumerate(labels)]
                cells = text(name + '_HEADER', setting['label'], 'HeaderText')
                cells['SelectedItem'] = {'value': next(i for i, v in enumerate(labels) if v[0] == setting['default']), 'type': 'UInt'}
                components.append((allocate(), 'dropDownMenu', None, name, rows, cells))
        for cid, ctype, widget, name, rows, cells in components:
            attrs = ' widget="%s"' % widget if widget else ''
            xml.append('            <component id="%d" type="%s"%s>' % (cid, ctype, attrs))
            properties = {'Visible': {'value': 1, 'type': 'UInt'}, 'Focusable': {'value': 0 if ctype == 'label' else 2, 'type': 'UInt'}}
            xml.extend(['                <property id="2" value="1"/>', '                <property id="3" value="%d"/>' % properties['Focusable']['value'], '            </component>'])
            component = {'type': ctype, 'name': name, 'rows': rows, 'properties': properties}
            if cells:
                component['cells'] = cells
            container['components'][str(cid)] = component
        xml.append('        </layoutGroup>')
        title_group, title = allocate(), allocate()
        xml.extend(['        <layoutGroup id="%d" name="Titlebar">' % title_group, '            <component id="%d" type="title"/>' % title, '        </layoutGroup>', '    </container>'])
        container['components'][str(title)] = {'type': 'title', 'name': screen['name'] + '_TITLE', 'rows': [text(screen['name'] + '_TITLE', screen['title'])]}
        description['containers'][str(state)] = container
    xml.append('</application>')
    return ('\n'.join(xml) + '\n').encode(), description, strings, states

def icon():
    """Original project K monogram, not BMW artwork or a captured font."""
    size = 128
    pattern = ['10001', '10010', '10100', '11000', '10100', '10010', '10001']
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            gx, gy = (x - 34) // 12, (y - 22) // 12
            on = 0 <= gx < 5 and 0 <= gy < 7 and pattern[gy][gx] == '1'
            row.extend((238, 242, 247, 255) if on else (20, 25, 32, 255))
        rows.append(b'\0' + row)
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) + chunk(b'IEND', b'')

def package_files(app_id, experimental=False):
    if not re.fullmatch(r'[a-z][a-z0-9_]{1,39}', app_id):
        raise ValueError('Invalid app ID')
    folder = ROOT / 'apps' / app_id
    if folder.is_symlink():
        raise ValueError('App folder must not be a symlink')
    spec = json.loads((folder / 'app.json').read_text())
    if spec['id'] != app_id or not re.fullmatch(r'\d+\.\d+\.\d+', spec['version']):
        raise ValueError('App identity/version mismatch')
    spec = copy.deepcopy(spec)
    if experimental:
        spec['version'] += '-factorymenu.1'
        spec['_factoryEntry'] = True
    xml, ui, strings, states = native_ui(spec)
    app = spec['id']
    routes = {identity(app, 'apps-entry'): 'MAIN'}
    entry = {'name': 'KOMBIKRAFT_ENTRY', 'uuid': identity(app, 'apps-entry'), 'textId': sid(app, 'TITLE'), 'icon': 'kombikraft_icon.png', 'insertionStateId': 20974, 'insertionFocusId': 2, 'insertionMode': 'INSERT_BELOW', 'insertionOrder': 0, 'insertionPriority': 0, 'previewType': 'NONE', 'bookmarkable': True, 'private': False, 'appearance': 'DEFAULT', 'isGroupHeader': False, 'insertionGroup': 0}
    entries = [entry]
    if experimental:
        key = sid(app, 'FACTORY_ENTRY')
        strings[key] = 'KombiKraft preferences'
        entries.append({'name': 'KOMBIKRAFT_FACTORY_SETTINGS', 'uuid': identity(app, 'factory-settings-entry'), 'textId': key, 'insertionStateId': 20800, 'insertionFocusId': 24327, 'insertionMode': 'INSERT_BELOW', 'insertionOrder': 65533, 'insertionPriority': 0, 'insertionGroup': 0, 'isGroupHeader': False, 'appearance': 'BUTTON', 'previewType': 'NONE', 'private': False, 'bookmarkable': False})
        routes[identity(app, 'factory-settings-entry')] = 'HUD'
    application = {'schemaVersion': '1.3.0', 'application': {'uuid': identity(app, 'application'), 'type': 'OnlineApp', 'name': app, 'vendor': spec['vendor'], 'version': spec['version'], 'defaultLanguage': 'en_GB', 'stringBundleUuid': identity(app, 'strings'), 'resourceBundleUuid': identity(app, 'resources'), 'entryPoints': entries, 'uiDescriptions': [{'applicationFilePath': './uiDescriptions/ID7/application.xml', 'uiDescriptionFilePath': './uiDescriptions/ID7/uiDescription.json', 'hmi': ['ID7']}], 'variantGroups': [{'stringsPath': './variantGroups/Common/texts', 'resourcesPath': './variantGroups/Common/images', 'hmi': ['ID7'], 'brands': ['BMW']}]}}
    pkg = {'name': app, 'version': spec['version'], 'description': spec['description'], 'main': 'javascript/app.js', 'private': False, 'author': 'KombiKraft contributors', 'license': 'MIT', 'engines': {'node': '>=8.7.0'}, 'oapAppSettings': {'maxDiskUsage': 20971520, 'cpuLimit': 60, 'memoryThresholdKB': 196608, 'priority': 'PRIO_LOW', 'visibility': 'FOREGROUND', 'latencyClass': 'FOREGROUND', 'loggingId': spec['loggingId'], 'userLoginRequired': False, 'backgroundPriority': 200, 'someipManifest': 'manifest.json'}}
    files = {'package.json': canonical(pkg), 'manifest.json': (ROOT / 'vendor/platform-manifest.json').read_bytes(), 'permissions.json': (ROOT / 'vendor/permissions.json').read_bytes(), 'config/base.json': canonical({'rhmiLoadingEnabled': True, 'entryPointLoadingEnabled': True}), 'npm-shrinkwrap.json': canonical({'name': app, 'version': spec['version'], 'lockfileVersion': 1}), 'rhmiData/application.json': canonical(application), 'rhmiData/uiDescriptions/ID7/application.xml': xml, 'rhmiData/uiDescriptions/ID7/uiDescription.json': canonical(ui), 'rhmiData/variantGroups/Common/images/kombikraft_icon.png': icon()}
    for language in ['en_GB', 'en_US']:
        files['rhmiData/variantGroups/Common/texts/' + language + '.json'] = canonical(strings)
    runtime_spec = {'id': app, 'version': spec['version'], 'screens': spec['screens'], 'settings': spec['settings'], 'stateIds': states, 'entryRoutes': routes, 'experimentalFactoryEntryRequested': experimental, 'factoryEntryVehicleValidated': False}
    files['javascript/app-spec.json'] = canonical(runtime_spec)
    for name in ['main.js', 'preferences.js', 'controller.js']:
        source = folder / name
        if source.is_symlink():
            raise ValueError('Source files must not be symlinks')
        files['javascript/' + ('app.js' if name == 'main.js' else name)] = source.read_bytes()
    files['LICENSE'] = (ROOT.parent / 'LICENSE').read_bytes()
    files['THIRD_PARTY.md'] = (ROOT / 'THIRD_PARTY.md').read_bytes()
    files['LICENSE.bimmer-lab'] = (ROOT / 'vendor/LICENSE.bimmer-lab').read_bytes()
    return spec, files

def build(app_id, out, experimental=False):
    spec, files = package_files(app_id, experimental)
    out.mkdir(parents=True, exist_ok=True)
    artifact = out / (app_id + '@' + spec['version'] + '.tgz')
    with artifact.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode='w', format=tarfile.USTAR_FORMAT) as archive:
                for name, data in sorted(files.items()):
                    member = tarfile.TarInfo('package/' + name)
                    member.mode, member.mtime, member.uid, member.gid = 0o644, 0, 0, 0
                    member.uname = member.gname = ''
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
    receipt = {'app': app_id, 'version': spec['version'], 'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(), 'bytes': artifact.stat().st_size, 'sdkIncluded': False, 'sdkResolution': 'MGU Store links a local platform donor at installation', 'experimentalFactoryMenuRequested': experimental, 'factorySkinInjectionProved': False, 'vehicleValidated': False, 'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}
    artifact.with_suffix('.receipt.json').write_bytes(canonical(receipt))
    return artifact, receipt

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', nargs='?', default='kombikraft')
    parser.add_argument('--out', type=Path, default=Path(os.environ.get('MGU_OUT', str(ROOT / 'dist'))))
    parser.add_argument('--experimental-factory-menu', action='store_true', help='Build a separate prerelease profile; not listed in the default catalog')
    args = parser.parse_args()
    artifact, receipt = build(args.app, args.out, args.experimental_factory_menu)
    print(json.dumps({'artifact': str(artifact), 'sha256': receipt['sha256'], 'sdkIncluded': False, 'vehicleValidated': False}))

if __name__ == '__main__':
    main()
