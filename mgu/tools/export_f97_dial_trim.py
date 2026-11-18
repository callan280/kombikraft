"""Composite recovered F97 bezels and RPM warning art onto fresh M Round faces."""
import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageChops

from export_f97_shift_art import bitmap, sha


def raster_mesh(mesh, size, material):
    center = size / 2
    scale = 343 / 340
    vertices = [(center + x * scale, center - z * scale, u, v)
                for (x, _, z), (u, v) in zip(mesh['positions'], mesh['attributes']['4:0'])]
    output = Image.new('RGBA', (size, size))
    pixels = output.load()
    for i in range(0, len(vertices), 3):
        (ax, ay, au, av), (bx, by, bu, bv), (cx, cy, cu, cv) = vertices[i:i + 3]
        area = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if not area:
            continue
        for y in range(max(0, math.floor(min(ay, by, cy))), min(size, math.ceil(max(ay, by, cy)))):
            for x in range(max(0, math.floor(min(ax, bx, cx))), min(size, math.ceil(max(ax, bx, cx)))):
                wa = ((by - cy) * (x + .5 - cx) + (cx - bx) * (y + .5 - cy)) / area
                wb = ((cy - ay) * (x + .5 - cx) + (ax - cx) * (y + .5 - cy)) / area
                wc = 1 - wa - wb
                if min(wa, wb, wc) >= -1e-7:
                    pixels[x, y] = material(wa * au + wb * bu + wc * cu,
                                            wa * av + wb * bv + wc * cv, y / size)
    return output


def smooth(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)


def sample_row(texture, u):
    width, _, data, _ = texture
    position = max(0, min(width - 1, u * width - .5))
    x = int(position)
    neighbour = min(width - 1, x + 1)
    fraction = position - x
    return tuple(round(a + (b - a) * fraction)
                 for a, b in zip(data[x * 4:x * 4 + 4], data[neighbour * 4:neighbour * 4 + 4]))


def main(donor, branding, art):
    manifest_file = art / 'manifest.json'
    manifest = json.loads(manifest_file.read_text())
    if 'dialTrimSource' in manifest:
        raise ValueError('Export fresh dial faces before applying trim again')
    mesh_dir = donor / 'older-donor-art/meshes'
    bitmap_dir = donor / 'older-donor-nor-complete/payloads/0007'
    corona_path, = bitmap_dir.glob('*tex_corona_sport_bitmapBmp.bin')
    warning_path, = bitmap_dir.glob('*dzm_vorwarn_rotBmp.bin')
    corona = bitmap(corona_path, 4)
    warning = bitmap(warning_path, 4)
    warning_mesh_path, = mesh_dir.glob('*ki_3d_msport_vorwarn_rot.ctm.json')
    warning_mesh = json.loads(warning_mesh_path.read_text())
    badge_manifest = json.loads((branding / 'manifest.json').read_text())
    badge_source = next(row for row in badge_manifest['textures'] if 'M135i_MSPORT' in row['name'])
    badge_data = (branding / 'm135i.png').read_bytes()
    if sha(badge_data) != badge_source['pngSha256']:
        raise ValueError('F40 M135i badge hash mismatch')
    badge = Image.open(branding / 'm135i.png').convert('RGBA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    badge = badge.crop(badge.getbbox())
    badge_width = 150
    badge = badge.resize((badge_width, round(badge.height * badge_width / badge.width)), Image.Resampling.LANCZOS)

    def metallic(u, _v, y):
        primary, secondary, _, alpha = sample_row(corona, u)
        light = .65 + .35 * (1 - y)
        rgb = [min(255, round((primary * white + secondary * steel) * light))
               for white, steel in ((.82, .96), (.90, 1.03), (1, 1.14))]
        return (*rgb, alpha)

    def redline(u, v, _y):
        # The donor mesh's angular V goes from .5 at zero to 0 at 8,000.
        # Place the preview transition beside the 7 mark as in the reference.
        rpm_mark = (1 - 2 * v) * 8000
        opacity = smooth((rpm_mark - 6800) / 250)
        red, green, blue, alpha = sample_row(warning, u)
        return (red, green, blue, round(alpha * opacity))

    source = dict(firmware='F97 SWFL 4CEB/4CED/4CEE 045.009.002',
                  coronaBitmapSha256=corona[3], warningBitmapSha256=warning[3],
                  warningMeshSha256=warning_mesh['decodedSha256'], coronaMeshSha256={},
                  badgeName=badge_source['name'], badgePngSha256=sha(badge_data),
                  badgePlacement='Centered below the tachometer hub, under the moving needle',
                  redlineAppearance='Reference transition at 6800–7050 on the 8000 RPM dial; preview styling')
    for side, mesh_name in (('left', 'speedo'), ('right', 'dzm')):
        entry = next(row for row in manifest['images'] if row['name'] == f'{side}-face.rgba')
        path = art / entry['name']
        raw = path.read_bytes()
        size = entry['width']
        if size != 688 or entry['height'] != size or sha(raw) != entry['sha256']:
            raise ValueError(f'Unexpected base face: {path}')
        face = Image.frombytes('RGBA', (size, size), raw)
        mesh_path, = mesh_dir.glob(f'*ki_3d_corona_{mesh_name}_sportShape.ctm.json')
        mesh = json.loads(mesh_path.read_text())
        source['coronaMeshSha256'][side] = mesh['decodedSha256']
        trim = raster_mesh(mesh, size, metallic)
        # Keep the opaque index marks and numerals in front of the bezel.
        highlight_mask = face.convert('L').point(lambda value: 255 - round(255 * smooth((value - 48) / 118)))
        trim.putalpha(ImageChops.multiply(trim.getchannel('A'), highlight_mask))
        face.alpha_composite(trim)
        if side == 'right':
            face.alpha_composite(raster_mesh(warning_mesh, size, redline))
            face.alpha_composite(badge, ((size - badge.width) // 2, size // 2 + 68))
        raw = face.tobytes()
        path.write_bytes(raw)
        entry['sha256'] = sha(raw)
    manifest['dialTrimSource'] = source
    manifest_file.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('donor', type=Path)
    parser.add_argument('branding', type=Path)
    parser.add_argument('--art', type=Path, default=Path(__file__).resolve().parents[1] / 'apps/kombikraft_test/art')
    args = parser.parse_args()
    main(args.donor, args.branding, args.art)
