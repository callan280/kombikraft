"""Bake aligned faces and compact mini gauges from the original M Round artwork."""
import argparse
import hashlib
import json
import math
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from export_f97_dial_trim import smooth

ART = Path(__file__).resolve().parents[1] / 'apps/kombikraft_test/art'
BACKGROUND = (3, 6, 9)
SIZE = 688
MINI_SIZE = (190, 216)
MINI_CENTER = (95, 108)
SUPERSAMPLE = 4
MINI_START = 140
MINI_SWEEP = 260

# Centres measured from the original, upright numeral strips, ordered by value.
SCALES = {
    'left': (126, 234, 160, [(190, 554), (137, 483), (100, 394), (99, 303),
                            (142, 213), (198, 145), (275, 100), (373, 84),
                            (456, 120), (520, 176), (560, 251), (581, 340)]),
    'right': (158, 224, 180, [(114, 434), (89, 325), (132, 203), (224, 119),
                              (342, 93), (463, 119), (556, 201), (603, 316),
                              (581, 440)]),
}
SWEEP = 200


def sha(data):
    return hashlib.sha256(data).hexdigest()


def coords(center, radius, degrees):
    angle = math.radians(degrees)
    return center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius


def main_face(image, side):
    old_start, old_sweep, new_start, positions = SCALES[side]
    center = (SIZE / 2, SIZE / 2)
    glyphs = []
    for index, (x, y) in enumerate(positions):
        half_width = 45 if side == 'left' and index >= 4 else 31 if side == 'left' else 25
        box = (x-half_width, y-19, x+half_width, y+19)
        tile = image.crop(box)
        ink = Image.new('L', tile.size)
        ink.putdata([min(rgb) if max(rgb)-min(rgb) < 28 and min(rgb) > 15 else 0
                     for rgb in tile.convert('RGB').getdata()])
        visible = ink.getbbox()
        if visible is None:
            raise ValueError(f'Missing numeral {side} {index}')
        glyph = tile.crop(visible)
        glyph.putalpha(ink.crop(visible))
        image.paste((*BACKGROUND, 255), box, ink.point(lambda a: 255 if a else 0))
        glyphs.append(glyph)

    def source(x, y):
        dx, dy = x-center[0], y-center[1]
        radius = math.hypot(dx, dy)
        if radius < 110 or radius > 336:
            return x, y
        angle = math.degrees(math.atan2(dy, dx))
        position = (angle-new_start) % 360
        if position <= SWEEP:
            original = old_start + position*old_sweep/SWEEP
        else:
            original = old_start + old_sweep + (position-SWEEP)*(360-old_sweep)/(360-SWEEP)
        delta = (original-angle+180) % 360 - 180
        weight = smooth((radius-110)/45) * (1-smooth((radius-325)/11))
        return coords(center, radius, angle + weight*delta)

    mesh = []
    for y in range(0, SIZE, 4):
        for x in range(0, SIZE, 4):
            right, bottom = x+4, y+4
            mesh.append(((x, y, right, bottom),
                         source(x, y)+source(x, bottom)+source(right, bottom)+source(right, y)))
    face = image.transform(image.size, Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)
    for index, glyph in enumerate(glyphs):
        angle = new_start + SWEEP*index/(len(glyphs)-1)
        radius = 245 if side == 'left' else 258
        # Open up the scale endpoints without moving the actual index marks.
        x, y = coords(center, radius, angle + (5 if side == 'left' and index == 0 else 0))
        if side == 'left':
            glyph = glyph.resize((round(glyph.width*.91), round(glyph.height*.91)), Image.Resampling.LANCZOS)
        face.alpha_composite(glyph, (round(x-glyph.width/2), round(y-glyph.height/2)))
    # Keep the bezel with a soft dark edge. Remove the square backing corners.
    fade = Image.new('L', face.size)
    fade.putdata([round(255*(1-smooth((math.hypot(x+.5-center[0], y+.5-center[1])-340)/11)))
                  for y in range(SIZE) for x in range(SIZE)])
    face.putalpha(fade)
    return face


def mini_art(role, numeral_font_path, unit_font_path, pictogram):
    def scale(values):
        return tuple(round(value*SUPERSAMPLE) for value in values)

    def canvas():
        return Image.new('RGBA', scale(MINI_SIZE))

    def ellipse(radius):
        x, y = MINI_CENTER
        return scale((x-radius, y-radius, x+radius, y+radius))

    art = canvas()
    draw = ImageDraw.Draw(art)

    def arc(radius, start, end, color, width):
        draw.arc(ellipse(radius), start, end, fill=color, width=max(1, round(width*SUPERSAMPLE)))

    def line(points, color, width):
        draw.line([scale(point) for point in points], fill=color, width=round(width*SUPERSAMPLE), joint='curve')

    numeral_font = ImageFont.truetype(str(numeral_font_path), 24*SUPERSAMPLE)
    unit_font = ImageFont.truetype(str(unit_font_path), 19*SUPERSAMPLE)

    def text(value, x, y, font, color):
        draw.text(scale((x, y)), value, fill=color, font=font, anchor='mm')

    start, end = MINI_START, MINI_START+MINI_SWEEP
    degrees = lambda fraction: start + MINI_SWEEP*fraction
    labels = (0, 5, 10, 15, 20, 25) if role == 'boost' else (0, 90, 180)
    major_angles = [degrees(i/(len(labels)-1)) for i in range(len(labels))]
    draw.ellipse(ellipse(68), fill=(*BACKGROUND, 255))

    # The steel corona is a separate circle outside the indented scale rim.
    arc(68, 0, 360, (38, 44, 52), 2.3)
    arc(67.5, 0, 360, (85, 95, 108), 1.1)
    arc(67.5, 197, 343, (143, 156, 170), 1.1)
    # Every segment uses the same radial profile for its shadow, body and bevel.
    segment_profile = ((54.5, 7.8), (53.5, 5.9), (52.7, 3.5), (52.7, .95), (48.9, 1.1))
    silver = ((20, 25, 32), (65, 75, 89), (133, 146, 165), (210, 223, 236), (56, 67, 82))
    blue = ((5, 11, 32), (9, 28, 84), (13, 69, 186), (39, 121, 247), (7, 25, 78))
    red = ((34, 4, 10), (83, 8, 17), (178, 13, 31), (243, 53, 66), (73, 7, 16))
    bands = (
        (start+4, degrees(.35), silver if role == 'boost' else blue),
        (degrees(.35), degrees(.65), silver),
        (degrees(.65), end-4, silver if role == 'boost' else red),
    )
    for first, last, palette in bands:
        span = (last-first)/3
        for segment in range(3):
            begin = first+span*segment+1.3
            finish = first+span*(segment+1)-1.3
            for (radius, width), color in zip(segment_profile, palette):
                arc(radius, begin, finish, color, width)

    # Follow the main dial's open scale: the line dips into each major mark
    # and returns to the rim. Minor marks sit just inside the rim.
    rim_radius = 62.5
    rim = [(start, 55), (start+1.3, 55), (start+2.6, rim_radius)]
    previous_angle = start+2.6
    for angle in major_angles[1:-1]:
        arc_end = angle-1.7
        steps = math.ceil((arc_end-previous_angle)/2)
        rim.extend((previous_angle+(arc_end-previous_angle)*i/steps, rim_radius)
                   for i in range(1, steps+1))
        rim.extend(((angle-.9, 55), (angle+.9, 55), (angle+1.7, rim_radius)))
        previous_angle = angle+1.7
    steps = math.ceil((end-2.6-previous_angle)/2)
    rim.extend((previous_angle+(end-2.6-previous_angle)*i/steps, rim_radius)
               for i in range(1, steps+1))
    rim.extend(((end-1.3, 55), (end, 55)))
    rim_points = [coords(MINI_CENTER, radius, angle) for angle, radius in rim]
    line(rim_points, (58, 65, 75), 2.3)
    line(rim_points, (194, 202, 212), 1.15)
    minor_per_gap = 1 if role == 'boost' else 3
    for first, last in zip(major_angles, major_angles[1:]):
        for i in range(1, minor_per_gap+1):
            angle = first+(last-first)*i/(minor_per_gap+1)
            line([coords(MINI_CENTER, radius, angle) for radius in (58, 60)],
                 (103, 114, 127), 1.05)
    # The wider BMW numerals need staggered endpoints and side labels to
    # remain clear of the steel corona and the vehicle's reserved areas.
    positions = {
        'boost': [(34, 169), (24, 80), (62, 35), (128, 35), (168, 63), (165, 169)],
        'oil': [(33, 170), (95, 32), (163, 170)],
        'water': [(33, 170), (95, 32), (163, 170)],
    }
    for label, (x, y) in zip(labels, positions[role]):
        text(str(label), x, y, numeral_font, (244, 246, 250))

    # Keep the BMW symbols subordinate to the scale. Pin them to the lower
    # opening, with the same quiet grey used for the units.
    width = 28*SUPERSAMPLE
    height = round(pictogram.height*width/pictogram.width)
    rendered_icon = pictogram.resize((width, height), Image.Resampling.LANCZOS)
    icon = Image.new('RGBA', rendered_icon.size, (186, 196, 209))
    icon.putalpha(rendered_icon.getchannel('A'))
    x, y = scale((95, 158))
    art.alpha_composite(icon, (x-icon.width//2, y-icon.height//2))
    text('psi' if role == 'boost' else '°C', 95, 184, unit_font, (214, 222, 234))

    return art.resize(MINI_SIZE, Image.Resampling.LANCZOS)


def load_pictogram(role, package_path, package):
    binding = package['miniPictograms'][role]
    texture = package['textures'][binding['texture']]
    data = Path(texture['png']).read_bytes()
    if sha(data) != texture['pngSha256']:
        raise ValueError(f'BMW {role} pictogram hash mismatch in {package_path}')
    icon = Image.open(BytesIO(data)).convert('RGBA')
    if role in ('oil', 'water'):
        # These source exports store the thermometer upside down.
        icon = ImageOps.flip(icon)
    return icon.crop(icon.getbbox())


def main(source, art, numeral_font, unit_font, pictograms):
    source_manifest = json.loads((source/'manifest.json').read_text())
    manifest = json.loads((art/'manifest.json').read_text())
    images = {entry['name']: entry for entry in manifest['images']}
    sources = {entry['name']: entry for entry in source_manifest['images']}
    def save(name, image):
        data = image.tobytes()
        (art/name).write_bytes(data)
        images[name].update(width=image.width, height=image.height, sha256=sha(data))

    faces = {}
    for side in SCALES:
        name = f'{side}-face.rgba'
        data = (source/name).read_bytes()
        if sha(data) != sources[name]['sha256'] or 'alignedMainFaces' in source_manifest:
            raise ValueError('Use the original M Round faces and matching manifest')
        faces[side] = main_face(Image.frombytes('RGBA', (SIZE, SIZE), data), side)

    # Copy only the bezel annulus. The speed scale and artwork inside it stay upright.
    center = SIZE/2
    bezel_mask = Image.new('L', (SIZE, SIZE))
    bezel_mask.putdata([round(255*smooth((math.hypot(x+.5-center, y+.5-center)-328)/3))
                        for y in range(SIZE) for x in range(SIZE)])
    faces['left'] = Image.composite(ImageOps.mirror(faces['right']), faces['left'], bezel_mask)
    for side, face in faces.items():
        name = f'{side}-face.rgba'
        save(name, face)
        images[name].pop('compressed', None)
    package = json.loads(pictograms.read_text())
    for role in ('oil', 'boost', 'water'):
        icon = load_pictogram(role, pictograms, package)
        save(f'{role}-face.rgba', mini_art(role, numeral_font, unit_font, icon))
        name = f'{role}-needle.rgba'
        needle = (source/name).read_bytes()
        if sha(needle) != sources[name]['sha256']:
            raise ValueError(f'Original needle hash mismatch: {name}')
        (art/name).write_bytes(needle)
        images[name].update(sources[name])
    manifest['alignedMainFaces'] = {
        'speedBezel': 'Horizontal reflection of tachometer outer bezel',
        'leftStartDegrees': SCALES['left'][2], 'rightStartDegrees': SCALES['right'][2], 'sweepDegrees': SWEEP,
        'sourceSha256': {side: sources[f'{side}-face.rgba']['sha256'] for side in SCALES},
    }
    manifest['mguMiniPictograms'] = {
        role: package['textures'][binding['texture']]['pngSha256']
        for role, binding in package['miniPictograms'].items()
    }
    manifest['mguMiniFonts'] = {
        'numerals': {'name': numeral_font.name, 'sha256': sha(numeral_font.read_bytes())},
        'units': {'name': unit_font.name, 'sha256': sha(unit_font.read_bytes())},
    }
    (art/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Original 0.1.17 uncompressed main faces, mini needles and manifest')
    parser.add_argument('--art', type=Path, default=ART)
    parser.add_argument('--numeral-font', type=Path, required=True, help='Recovered BMW M Type Condensed font')
    parser.add_argument('--unit-font', type=Path, required=True, help='Recovered BMW TA unit label font')
    parser.add_argument('--pictograms', type=Path, required=True, help='F97 gauges render package manifest')
    args = parser.parse_args()
    main(args.source, args.art, args.numeral_font, args.unit_font, args.pictograms)
