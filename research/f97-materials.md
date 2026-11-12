# Original older-F97 material readers

The supported donor is SWFL4CEB045.009.002. It supplies older round-dial
graphics, not an F40-compatible firmware image. The exact SHA256 profile is
available without Unicorn or firmware:

```sh
python -m kombikraft.research.f97 --profile
```

The executable checks need Python3.11+ and `unicorn==2.1.4`, supplied by the
project's optional `factory` dependency. Keep all inputs and results local:

```sh
python -m pip install -e '.[factory]'
python -m kombikraft.research.f97 \
  --bank /path/to/decoded/bank-13.bin \
  --scene /path/to/decoded/ki_3d_high.bin \
  --nor /path/to/original/nor-container.ce51 \
  --output private/f97-material-checks.json
```

This command rejects unsupported hashes before importing the emulator. It
reconstructs source names and typed records directly from the admitted bank,
scene and NOR string pool, so a private art catalogue is not required. Existing
receipt paths are not overwritten. Outputs contain analysis-fixture addresses
and hashes, not vehicle telemetry.

If you have the decoded contiguous NORboot flash image (not an arbitrary SWE),
the new bounded extractor can produce bank13:

```sh
python tools/extract_norboot_bank.py /path/to/decoded-norboot.flash \
  private/f97-bank --bank 13
```

Use `--offset` if the NORboot header is at a known nonzero byte offset, and
`--lz4-library` if system lookup cannot find your installed liblz4. Decoding
programming-data containers to that flash image is a separate source-specific
step. The [CE51 reader](../tools/extract_ce51.py) can extract the `ki_3d_high`
scene payload from the admitted NOR container. Never use the table target
field or successful decompression as proof of a runtime address or zero-fill.

## What the current214 executions establish

- 66 cases execute the original UniformSetter constructor and complete record
  reader for eleven appearances, two heap fills and three input values. Original
  list/callback management and memcpy run; the source default is `oparam0=1.0`.
  V2 also verifies the real native C-string lookup with a distinct query pointer.
- 4 uniform-name regressions exercise one genuine four-entry ECO record under
  both heap fills: the correct caller origin preserves distinct source names
  and values; the raw-origin cases are retained as rejected caller witnesses.
- 48 cases run original Bitmap identifier parsing, type/name resolution and
  release. Each source path resolves as Bitmap type7 and the exact resource name.
- 96 cases run the original Texture constructor and reader prefix, through an
  original provider path resolver, to the image-cache factory boundary. Source
  flags produce the expected `/0` or `/1` cache keys. The cache factory is not
  executed and no bitmap result is substituted.

Allocation/free wrappers use a bounded host heap. The texture experiment
declares a source-vtable provider input; it does not execute that provider's
constructor. Four-byte heap backing alignment admits the original optimized
string reader's final aligned word. Zero/A5 fills vary that padding, and freed
or out-of-backed-allocation accesses are rejected.

The original complete parameter reader validated a decoded-scene reference
origin of payload-start minus12. An earlier isolated test had supplied the
payload start and selected payload coordinates instead of typed headers. The
published tool uses the corrected origin. Original linked analysis coordinates
do not establish a physical target mapping.

The record length word also includes its 12-byte header. Adjacent Texture
records provide thirteen exact source boundaries confirming this convention.
The structural reader reports `recordBytes` separately from `payloadBytes`,
and stops each record before the following header. This metadata correction
does not alter the source headers passed to the original-code probes.

These checks do not boot firmware, initialize the real heap/kernel, load the
complete scene, execute the original GPU code, change the viewer or permit
installation. The normal viewer retains its separately tested layout renderer.

## Optional image, controller and widget suites

New source-only experiments are available through a separate command. The
original material command above has a separately versioned214-case report. Its
native uniform-name correction is documented [here](../docs/f97-uniform-names-v2.md).
The extended suites remain unchanged. Inspect the extended hashes and
suite names without Unicorn or firmware:

```sh
python -m kombikraft.research.f97.extended --profile
```

The `controller` suite needs only the exact admitted bank13:

```sh
python -m kombikraft.research.f97.extended --suite controller \
  --bank /path/to/decoded/bank-13.bin \
  --output private/f97-controller-checks.json
```

The `image-sampling` and `widgets` suites need `--bank`, `--scene` and `--nor`
as above. The `loaded-images` suite additionally needs the admitted initialized
bank14 and19 named decoded bitmap payloads. A local CE51 extraction manifest
identifies those payload files; actual bytes must match all19 published hashes.
The manifest alone is not trusted as proof of their content.

```sh
python -m kombikraft.research.f97.extended --suite all \
  --bank /path/to/decoded/bank-13.bin \
  --data-bank /path/to/decoded/bank-14.bin \
  --scene /path/to/decoded/ki_3d_high.bin \
  --nor /path/to/original/nor-container.ce51 \
  --bitmap-manifest /path/to/nand-extraction/ce51-manifest.json \
  --output private/f97-extended-checks.json
```

Use the existing CE51 extractor with an absolute output path so its manifest
contains absolute payload paths. Otherwise relative `decodedFile` entries are
resolved against the manifest directory. `--bitmap-root /path/to/base` selects
the base explicitly if an older manifest used working-directory-relative paths.
Only the19 selected bitmap files are read. The firmware/container extraction
steps, runtime images and decoded resources remain local inputs.

The extended suites establish these additional bounded results:

- **Image construction and filtering:**48 genuine texture-reference cases and
  12 declared property/field witnesses run original Texture and BitmapTextureImage
  constructors, SharedPtr attach/release and virtual filtering decisions. The
  scene-field reader and minification prefix have explicit interior caller
  states and stop before the graphics call. Witness input copies are deliberately
  mutated and then remain unchanged during execution.
- **Loaded bitmap attachment:**48 cases execute original resident bitmap
  deserialization/copy, image construction, bitmap attachment, mip setter,
  software thread-manager initialization and ownership. Selected fresh-zero
  globals and initialized bank14's analysis mapping are explicit unit inputs;
  they do not establish original boot, OS threading, TLS or concurrency. The
  source callback's deleter0 and generation flag0 are retained. Explicit
  active-count witnesses test mutation guards. Final destruction is untested.
- **Original speedometer inputs:**120 owner/payload fixtures execute600 input
  callbacks plus120 parameter calculations. The five internal IDs, source
  `>=5` threshold and division by41600 remain opaque source contracts, not CAN
  identifiers, road-speed calibration or named driving-mode bindings. Widget
  construction/lifecycle and application to shader/scene fields are unproved.
- **Structural widget inventory:**492 nodes and40 widget records contain185
  properties:177 exact node paths, one scene-root value and seven literal
  calibration values. Encoded references select a string-length record at
  reference minus12, with characters at plus2. Deserializer execution, runtime
  widget resolution, transforms and live input semantics are not claimed.

All228 new original-code results and the widget inventory matched the reviewed
local research receipts exactly before export. The observer function bodies
are preserved in the [source export manifest](f97-extended-source-manifest.json).
The command does not render the ring gallery, run the original GPU/kernel,
initialize the resource provider/cache, modify a viewer, or permit installation.
