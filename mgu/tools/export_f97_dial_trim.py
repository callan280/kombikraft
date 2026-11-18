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


def glyph_component(opacity, width, height):
    remaining = {index for index, alpha in enumerate(opacity) if alpha}
    largest = []
    while remaining:
        group = [remaining.pop()]
        for index in group:
            x, y = index % width, index // width
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    adjacent = ny * width + nx
                    if adjacent in remaining:
                        remaining.remove(adjacent)
                        group.append(adjacent)
        if len(group) > len(largest):
            largest = group
    keep = set(largest)
    return bytes(value if index in keep else 0 for index, value in enumerate(opacity))


def angle_map(x, y, start, sweep, new_start, new_sweep):
    source_angle = (math.degrees(math.atan2(y, x)) - start) % 360
    if source_angle <= sweep:
        dest_angle = new_start + source_angle * new_sweep / sweep
    else:
        dest_angle = new_start + new_sweep + (source_angle - sweep) * (360 - new_sweep) / (360 - sweep)
    angle = math.radians(dest_angle)
    radius = math.hypot(x, y)
    return math.cos(angle) * radius, math.sin(angle) * radius


def reshape_tach(face, numbers, new_start, new_sweep):
    center = face.width / 2
    scale = 343 / 340
    digit_tiles = []
    for start in range(0, len(numbers['positions']), 6):
        positions = numbers['positions'][start:start + 6]
        xs = [x * scale + center for x, _, _ in positions]
        ys = [center - z * scale for _, _, z in positions]
        margin = 16
        x, y = math.floor(min(xs)) - margin, math.floor(min(ys)) - margin
        box = (x, y, math.ceil(max(xs)) + margin, math.ceil(max(ys)) + margin)
        tile = face.crop(box)
        # The numeral mesh uses neutral ink over a red-and-black face.
        # Extract only the numeral from its authored quad.
        pixels = tile.tobytes()
        opacity = bytearray(tile.width * tile.height)
        for index in range(len(opacity)):
            r, g, b, _ = pixels[index * 4:index * 4 + 4]
            dx = x + index % tile.width - center
            dy = y + index // tile.width - center
            minimum, maximum = min(r, g, b), max(r, g, b)
            if dx * dx + dy * dy < 300 * 300 and minimum > 12 and maximum - minimum < 18:
                opacity[index] = min(255, round((minimum - 9) * 255 / 246))
        alpha = Image.frombytes('L', tile.size, glyph_component(opacity, tile.width, tile.height))
        ink = Image.new('RGBA', tile.size, (255, 255, 255, 0))
        ink.putalpha(alpha)
        remove = alpha.point(lambda value: 255 if value > 0 else 0)
        face.paste((3, 6, 9, 255), (x, y, box[2], box[3]), remove)
        digit_tiles.append((ink, x, y))
    def original(x, y):
        dx, dy = angle_map(x - center, y - center, new_start, new_sweep, 180, 234)
        return center + dx, center + dy

    quads = []
    for y in range(0, face.height, 8):
        for x in range(0, face.width, 8):
            right, bottom = min(x + 8, face.width), min(y + 8, face.height)
            corners = original(x, y) + original(x, bottom) + original(right, bottom) + original(right, y)
            quads.append(((x, y, right, bottom), corners))
    face = face.transform(face.size, Image.Transform.MESH, quads, Image.Resampling.BICUBIC,
                          fillcolor=(3, 6, 9, 255))
    for tile, x, y in digit_tiles:
        dx, dy = angle_map(x + tile.width / 2 - center, y + tile.height / 2 - center,
                           180, 234, new_start, new_sweep)
        dest = (round(center + dx - tile.width / 2), round(center + dy - tile.height / 2))
        face.alpha_composite(tile, dest)
    return face


def main(donor, branding, gear_assets, art):
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
    numbers_path, = mesh_dir.glob('*ki_3d_dzm_all_numbers.ctm.json')
    numbers = json.loads(numbers_path.read_text())
    tach_start, tach_sweep = 158, 224
    badge_manifest = json.loads((branding / 'manifest.json').read_text())
    badge_source = next(row for row in badge_manifest['textures'] if 'M135i_MSPORT' in row['name'])
    badge_data = (branding / 'm135i.png').read_bytes()
    if sha(badge_data) != badge_source['pngSha256']:
        raise ValueError('F40 M135i badge hash mismatch')
    badge = Image.open(branding / 'm135i.png').convert('RGBA').transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    badge = badge.crop(badge.getbbox())
    badge_width = 184
    badge = badge.resize((badge_width, round(badge.height * badge_width / badge.width)), Image.Resampling.LANCZOS)

    def metallic(u, _v, y):
        primary, secondary, _, alpha = sample_row(corona, u)
        light = .65 + .35 * (1 - y)
        rgb = [min(255, round((primary * white + secondary * steel) * light))
               for white, steel in ((.82, .96), (.90, 1.03), (1, 1.14))]
        return (*rgb, alpha)

    def redline(u, v, _y):
        # The donor mesh's angular V goes from .5 at zero to 0 at 8,000.
        # Colour begins at the requested 6,500 RPM display marking.
        rpm_mark = (1 - 2 * v) * 8000
        opacity = smooth((rpm_mark - 6500) / 250)
        red, green, blue, alpha = sample_row(warning, u)
        return (red, green, blue, round(alpha * opacity))

    glyphs = 'PRNDSM12345678'
    gear_manifest = json.loads((gear_assets / 'manifest.json').read_text())
    extras = Image.new('RGBA', (len(glyphs) * 64, 116))
    for index, glyph in enumerate(glyphs):
        glyph_path = gear_assets / (glyph + '.png')
        if sha(glyph_path.read_bytes()) != gear_manifest['glyphs'][glyph]['sha256']:
            raise ValueError(f'F40 gear glyph hash mismatch: {glyph}')
        image = Image.open(glyph_path).convert('RGBA')
        image = image.resize((round(image.width * 44 / image.height), 44), Image.Resampling.LANCZOS)
        extras.alpha_composite(image, (index * 64 + (64 - image.width) // 2, 10))
    extras.alpha_composite(badge, (0, 64 + (52 - badge.height) // 2))
    extras_name = 'round-extras.rgba'
    extras_pixels = extras.tobytes()
    (art / extras_name).write_bytes(extras_pixels)
    manifest['images'] = [row for row in manifest['images'] if row['name'] != extras_name]
    manifest['images'].append(dict(name=extras_name, width=extras.width, height=extras.height,
                                   sha256=sha(extras_pixels)))
    source = dict(firmware='F97 SWFL 4CEB/4CED/4CEE 045.009.002',
                  coronaBitmapSha256=corona[3], warningBitmapSha256=warning[3],
                  warningMeshSha256=warning_mesh['decodedSha256'], coronaMeshSha256={},
                  tachStartDegrees=tach_start, tachSweepDegrees=tach_sweep, numeralMeshSha256=numbers['decodedSha256'],
                  badgeName=badge_source['name'], badgePngSha256=sha(badge_data),
                  badgePlacement='Between the main dials', gearGlyphSourceSha256=gear_manifest['sourceSha256'],
                  redlineAppearance='Red starts at 6500 and blends in over 250 RPM; display styling')
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
            face = reshape_tach(face, numbers, tach_start, tach_sweep)
        raw = face.tobytes()
        path.write_bytes(raw)
        entry['sha256'] = sha(raw)
    manifest['dialTrimSource'] = source
    manifest_file.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('donor', type=Path)
    parser.add_argument('branding', type=Path)
    parser.add_argument('gear_assets', type=Path)
    parser.add_argument('--art', type=Path, default=Path(__file__).resolve().parents[1] / 'apps/kombikraft_test/art')
    args = parser.parse_args()
    main(args.donor, args.branding, args.gear_assets, args.art)
