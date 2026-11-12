# Portable visual library

Open `assets/library/index.html` directly for offline image browsing and
search, or serve the repository locally for browsers that restrict local font
loads. There are no external scripts, remote calls or account requirements.
Filter by source family, image/font/mesh/shader type, or explicitly labelled
name-based pictogram groups. Select a card for full sanitized provenance,
orientation/format interpretation, hashes and direct resource downloads.

The catalogue uses lossless decoded PNGs instead of multi-gigabyte uncompressed
texture buffers. Original font/known-font-container, visual mesh and compiled
shader/resource bytes are included separately. Content-addressed object names
support deduplication and independent SHA-256 verification. Full firmware,
executables, scenes with unresolved embedded behavior, unknown generic payloads,
archives, backups, the private ledger and machine/vehicle data are excluded.

To reproduce from a local private extraction inventory:

```sh
python3 tools/export_graphics_library.py --source /path/to/private/library
python3 tools/export_graphics_library.py --verify
```

The source folder must contain `assets.jsonl` and its existing `objects/` tree.
The script never extracts or executes firmware. It follows an explicit visual
kind allowlist, checks input hashes and PNG dimensions, sanitizes metadata,
copies selected resources and rehashes every output. It rejects executable or
archive magic even if upstream classification changes. Its export receipt
records exact selected/excluded counts, sizes and hashes without source paths.
The compact `catalog.js` loads directly as static data; the private 65 MB JSONL
inventory and SQLite ledger are not copied.

Asset rights and third-party attribution are in
`assets/library/NOTICE.md`. These assets are separate from the source-code
license. A decoded graphics resource or familiar symbol does not prove a
controller binding, live diagnostic integration or model compatibility.

## Current export

The checked inventory contains19,467 records. This export includes16,490
visual records and16,193 unique content-addressed files (479,098,404 bytes):

- All9,509 previewable records, represented by9,212 unique decoded PNG files.
- Seven decoded TTF fonts and22 known font containers/wrappers (29 records),
  including BMWMType_Condensed, BMWTA variants and two Bitstream Vera fonts.
  Their original embedded notices are retained in `FONT-LICENSES.md`.
- 209 CE51 meshes and116 compiled shader resources.
- 4,594 Ramses vertex,604 index and1,429 effect records; their internal
  undecoded schemas remain explicitly labelled.

The5,040,872-byte initial search catalogue keeps complete sanitized provenance
in256 small on-demand shards (20,591,304 bytes total). The export receipt lists
exact source inventory hash, per-object hashes, type/family counts and every
excluded type. Shared M_GmbH family assets are not relabelled exact F97 ID7 art.

Four textures lack decoded PNGs. Unknown generic resource/interface records,
whole scenes and unresolved scene-layout records are not admitted as visual
objects by this export; the viewer's separately reviewed pack is independent.
Compressed CC source records are represented by their decoded PNGs. Nothing
is silently promoted as decoded, upright or natively bound when that remains
unverified.

Validation includes every copied object's SHA-256 readback, catalogue/shard
checks, PNG dimensions, executable/archive magic rejection, source-path
metadata sanitization, and local-machine/private-key marker scanning of the
exported binary bytes. The PNGs contain no EXIF or text chunks;618 retain
standard ICC colour profiles. This is not image OCR or proof against arbitrary
unknown secrets. `verify_gallery.cjs` runs seven UI actions in a Node DOM
fixture; it is clearly separate from a graphical-browser review.
