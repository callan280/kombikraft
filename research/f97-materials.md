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

## What the 210 cases establish

- 66 cases execute the original UniformSetter constructor and complete record
  reader for eleven appearances, two heap fills and three input values. Original
  list/callback management and memcpy run; the source default is `oparam0=1.0`.
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
