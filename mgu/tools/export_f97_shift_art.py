"""Pack the recovered F97 shift mesh, frame colours and glow for the parked demo."""
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bitmap(path, channels):
    data = path.read_bytes()
    _, width, height, _, _, _, _, _, byte_count = struct.unpack_from('<9I', data)
    pixels = data[36:]
    if len(pixels) != byte_count:
        raise ValueError(f'Unexpected declared bitmap size: {path}')
    if len(pixels) != width * height * channels:
        raise ValueError(f'Unexpected source bitmap size: {path}')
    return width, height, pixels, sha(data)


def main(donor, output):
    mesh_path, = (donor / 'older-donor-art/meshes').glob('*ki_3d_shift_planes.ctm.json')
    mesh = json.loads(mesh_path.read_text())
    research = donor / 'original-material-research/node-transform-research'
    scene = (research / 'full-scene-candidate-next/inputs.js').read_text()
    models = json.JSONDecoder().raw_decode(scene[scene.index('{'):])[0]['cameras'][0]['models']
    scale_model, shift_model = (models[key] for key in ('199376', '201420'))
    if any(scale_model[i] != shift_model[i] or not scale_model[i] for i in (0, 9)):
        raise ValueError('Tachometer and shift mesh projection differ')
    dx = (shift_model[12] - scale_model[12]) / scale_model[0]
    dz = (shift_model[13] - scale_model[13]) / scale_model[9]
    face_scale = 343 / 340
    vertices = [((x + dx) * face_scale, -(z + dz) * face_scale, u, v)
                for (x, _, z), (u, v) in zip(mesh['positions'], mesh['attributes']['4:0'])]
    left = math.floor(min(x for x, _, _, _ in vertices))
    top = math.floor(min(y for _, y, _, _ in vertices))
    width = math.ceil(max(x for x, _, _, _ in vertices)) - left
    map_height = math.ceil(max(y for _, y, _, _ in vertices)) - top
    pixels = bytearray(width * (map_height + 9) * 4)
    assets = donor / 'older-donor-assets/payloads/0007'
    glow_path, = assets.glob('*ki_dzm_shiftlights_glowbandBmp.bin')
    gw, gh, glow, glow_hash = bitmap(glow_path, 3)
    if (gw, gh) != (2, 32):
        raise ValueError('Unexpected glow profile')
    glow_profile = [sum(glow[row * 6:row * 6 + 6]) / 6 for row in range(gh)]
    for i in range(0, len(vertices), 3):
        (ax, ay, au, av), (bx, by, bu, bv), (cx, cy, cu, cv) = vertices[i:i + 3]
        area = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if not area:
            continue
        for y in range(math.floor(min(ay, by, cy)), math.ceil(max(ay, by, cy))):
            for x in range(math.floor(min(ax, bx, cx)), math.ceil(max(ax, bx, cx))):
                wa = ((by - cy) * (x + .5 - cx) + (cx - bx) * (y + .5 - cy)) / area
                wb = ((cy - ay) * (x + .5 - cx) + (ax - cx) * (y + .5 - cy)) / area
                wc = 1 - wa - wb
                if min(wa, wb, wc) < -1e-7:
                    continue
                u = wa * au + wb * bu + wc * cu
                v = wa * av + wb * bv + wc * cv
                # The source's long bitmap axis follows the curved UV axis.
                arc = round((1 - v) * 65535)
                spread = u * (gh - 1)
                row = min(gh - 2, int(spread))
                halo = round(glow_profile[row] + (spread - row) * (glow_profile[row + 1] - glow_profile[row]))
                offset = ((y - top) * width + x - left) * 4
                # Keep the light attached to the ring with a short inward fade.
                rim_alpha = round(255 * max(0, 1 - u / .42) ** 2)
                pixels[offset:offset + 4] = bytes((arc >> 8, arc & 255, halo, rim_alpha))
    hashes = []
    for frame in range(1, 10):
        source, = assets.glob(f'*ki_dzm_shiftlights{frame}Bmp.bin')
        pw, ph, strip, source_hash = bitmap(source, 4)
        if (pw, ph) != (130, 2):
            raise ValueError(f'Unexpected stage strip: {source}')
        offset = (map_height + frame - 1) * width * 4
        half = pw * 4
        pixels[offset:offset + half] = bytes((a + b + 1) // 2 for a, b in zip(strip[:half], strip[half:]))
        hashes.append(source_hash)
    name = 'right-shift.rgba'
    (output / name).write_bytes(pixels)
    manifest_path = output / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    entry = dict(name=name, width=width, height=map_height + 9, sha256=sha(pixels),
                 offsetX=left, offsetY=top, mapHeight=map_height, paletteWidth=130)
    manifest['images'] = [row for row in manifest['images'] if row['name'] != name] + [entry]
    manifest['shiftRingSource'] = dict(firmware='F97 SWFL 4CEB/4CED/4CEE 045.009.002',
        meshSha256=mesh['decodedSha256'], frameSha256=hashes, glowSha256=glow_hash,
        mapping='Tach-relative source mesh with adapted strip sampling, inward fade and parked-demo timing')
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(entry))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('donor', type=Path)
    main(parser.parse_args().donor, Path(__file__).resolve().parents[1] / 'apps/kombikraft_test/art')
