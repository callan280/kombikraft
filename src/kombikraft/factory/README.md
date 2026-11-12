# Original partial controller fixture

This optional backend runs unchanged application machine code from **locally
supplied** matching firmware banks under Unicorn. The package contains only our
loader, bounded platform adapters and research identity metadata. It does not
include BMW firmware, graphics, fonts, runtime libraries or decompiled code.

Install `unicorn==2.1.4` in the environment used for the fixture. Provide a local
JSON manifest with profile `gss-5c58-160.002.002` and a `banks` list. Each bank
has `name`, `file` (relative to your chosen bank root), `base` (hex string), and
`sha256`. The required names, addresses and pinned digests are in `profile.py`.
No input is fetched or extracted automatically. Missing files, path escapes,
profile mismatches and digest mismatches stop execution.

`kombikraft.factory.inputs.manifest_template()` returns a JSON-serializable local
manifest template containing those filenames, bases and digests. It contains no
firmware. Save it locally and place your matching source banks under your root.

```sh
python -m kombikraft.factory.replay --manifest YOUR_MANIFEST.json --root YOUR_BANK_DIRECTORY
```

The fixed replay covers 24 BC and actual left/right lamp-status transitions,
including duplicates and unmatched values. It calls original local mutex/HMI/
RTE initialization, original internal record receive, generated callbacks, typed
datastore, five original scheduler phases and original SEM event enqueueing.
Six source match constants are registered explicitly through the original API.
Readiness flags are raised by original instructions; the loader never sets them.

The reported backend is **partial**: it does not boot INTEGRITY, execute SEM
activities, render factory graphics, join physical CAN/SOME-IP traffic, establish
real blink timing, or prove live F40 coding. Full factory startup stays false.
The internal record IDs are not CAN IDs. Quality-byte meaning and loss timing
are not certified by the default quality-zero replay.

Platform adapters supply bounded allocation/TLS, unavailable graphics handles,
tracked uncontended mutex ownership, deterministic mock clock syscall results and
opaque kernel semaphore-creation handles. Original higher clock/local-mutex
arithmetic remains in the imported firmware. Unsupported platform states fail
closed. This is an offline debugging fixture, not a replacement vehicle runtime.

For the optional integration test, set `KOMBIKRAFT_FIRMWARE_MANIFEST` and
`KOMBIKRAFT_FIRMWARE_ROOT` to your local inputs. Without them, firmware-dependent
tests skip; admission and platform tests still run using ordinary test data.

## Optional Check Control command fixture

`check_control.py` adds the original registered Check Control supplier/consumer
beside the existing BC and lamp inputs. Its separate local import requires the
same exact profile plus hash-admitted bank `18-203d0000.bin`, for 14 banks total.
The existing 13-bank backend, server routes and replay remain unchanged.

```sh
python -m kombikraft.factory.check_control_cli --manifest-template > cc-inputs.json
python -m kombikraft.factory.check_control_cli --manifest cc-inputs.json --root YOUR_BANK_DIRECTORY --commands commands.ndjson
```

The local JSON-lines command envelope is:

```json
{"signal":"bc","raw":1}
{"signal":"leftLamp","raw":1}
{"signal":"rightLamp","raw":0}
{"signal":"checkControl","raw":{"ccid":2051}}
{"signal":"checkControl","raw":{"ccid":0}}
```

Check Control accepts either a UInt16 `ccid` fixture or `record66Hex` encoding
exactly 66 bytes of an internal native record. Optional `quality` is an opaque
byte; optional `mode` admits only the reviewed source datastore fixtures 0/2.
These records are internal fixtures, not physical CAN or SOME/IP frames.

The original receiver, decoder, getter, registered callback, aggregation and
producer/consumer execute through explicit source scheduler phases. Source
refreshes with unchanged first 64 bytes, including counter/CRC-only changes in
bytes 64/65, can preserve the warning with no new payload callback. The complete
66-byte getter readback remains available. Quality semantics, master warning
priority and acknowledgement lifecycle remain unverified.

`OriginalCcControllerBackend` reports actual selected nullable text lines,
descriptor references, selectors and original palette-helper values. These are
source data for a separately admitted preview bridge. This module renders no
graphics and makes no native factory-pixel claim. A genuine clear after the
source consumer callback has `[null,null]` text, null icon and selectors 255.
An unobserved initial consumer state is explicitly distinguished from clear.

Untouched source coding currently yields variant 1 and numeric collection-bank
ordinal 1 for this exact firmware profile. Language 2 is an explicit reviewed
input through original datastore 0x0D. Neither establishes current-car coding,
language or generic compatibility. No source coding fixture is forced by the
loader. Factory graphics, physical
transport, master arbitration and live installation remain outside this fixture.

The command session accepts at most 1,000 lines and 2,048 bytes per line and has
no HTTP or vehicle endpoint. To run its optional source-backed integration test,
set `KOMBIKRAFT_CC_MANIFEST` to the 14-bank manifest and
`KOMBIKRAFT_FIRMWARE_ROOT` to the local bank directory. Otherwise it skips.
