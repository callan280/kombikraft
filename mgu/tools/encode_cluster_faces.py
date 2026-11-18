#!/usr/bin/env python3
"""Re-encode the main M Round faces with etcpak 0.9.15."""

import hashlib
import json
from pathlib import Path

import etcpak


ART = Path(__file__).resolve().parents[1] / 'apps/kombikraft_test/art'


def main():
    manifest_path = ART / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for entry in manifest['images']:
        name = entry['name']
        if name not in ('left-face.rgba', 'right-face.rgba'):
            continue
        size = entry['width'], entry['height']
        raw = (ART / name).read_bytes()
        if any(side % 4 for side in size) or hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Invalid source face: ' + name)
        encoded = etcpak.compress_etc2_rgba(raw, *size)
        (ART / name.replace('.rgba', '.etc2rgba')).write_bytes(encoded)
        entry['compressed'] = {
            'sourceSha256': entry['sha256'],
            'sha256': hashlib.sha256(encoded).hexdigest(),
        }
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
