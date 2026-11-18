#!/usr/bin/env python3
"""Generate the Store catalogue from built SDK-free packages."""

import hashlib
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
MGU = ROOT / 'mgu'
RELEASE = 'https://github.com/callan280/kombikraft/releases/download/catalog/'


def component(app_id, requires, title=None, description=None):
    spec = json.loads((MGU / 'apps' / app_id / 'app.json').read_text())
    name = f"{app_id}@{spec['version']}.tgz"
    artifact = (MGU / 'dist' / name).read_bytes()
    return {
        'id': app_id,
        'kind': 'app',
        'title': title or spec['title'],
        'description': description or spec['description'],
        'version': spec['version'],
        'artifact': {
            'name': name,
            'size': len(artifact),
            'sha256': hashlib.sha256(artifact).hexdigest(),
            'url': RELEASE + quote(name, safe=''),
        },
        'requires': requires,
        'uninstallable': True,
        'mguHmi': ['ID7'],
    }


def main():
    catalog = {'schema': 2, 'components': [
        component(
            'kombikraft', {'mgu-deploy': '0.2.0'},
            'KombiKraft Lab · Offline prototype',
            'Experimental native preferences app. No vehicle-validated release; factory menu injection, HUD rendering and KOMBI skin activation remain unavailable.',
        ),
        component('kombikraft_test', {'mgu-deploy': '0.4.0', 'cluster-render': '0.6.9'}),
    ]}
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')


if __name__ == '__main__':
    main()
