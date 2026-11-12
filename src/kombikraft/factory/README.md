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
The existing 13-bank backend and replay remain available. The viewer's existing
command route adds Check Control only when explicitly enabled at startup.

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

To use the original controller in the same browser simulator, explicitly enable
it when starting the viewer:

```sh
kombikraft serve --check-control --firmware-manifest cc-inputs.json --firmware-root YOUR_BANK_DIRECTORY --assets assets/viewer-pack
```

The simulator's **Original controller** section submits the same bounded
`signal`/`raw` envelope used by the local CLI. It keeps the requested authored
fixture separate from the actual selected source output. BC press/release and
left/right lamp buttons compute original input events; they do not automatically
cycle an authored centre page. Existing source-pair placement controls remain
inspection fixtures until explicitly submitted to the original controller.

The HTTP route requires the exact loopback Host and same Origin, limits requests
to 256 bytes, validates all fixture fields before execution and serializes
inputs/status through one backend lock. It exposes no upload, filesystem-import,
vehicle or native-process-control route. Source banks are loaded only through
the startup arguments.

The separately admitted preview contract connects the reviewed 16 original
source outputs and actual clear to the same simulator's canvas. Enable the
**Original controller** panel, submit a selected source pair or enter a CCID,
and inspect the actual computed selection. **Return to visual fixtures** releases
the computed preview; changing a visual placement fixture also releases it.
Source warnings hide BC content while displayed; original clear returns to the
retained custom centre page. This composition uses the original selected
graphics/font/colours with authored text placement and is not a factory renderer.
Missing or changed
visual assets, unreviewed selections and collection warnings remain unsupported;
original computation is still available. A preview plan does not establish
factory graphics startup, physical bus mapping or warning-master arbitration.
An original execution failure makes that source machine unavailable until the
viewer restarts; the browser invalidates its previous computed popup. Invalid
authored input is rejected before execution and does not fault the source machine.
The viewer owns a separate emulator process: source construction, initialization,
execution and readback all stay on that process's main thread. HTTP threads
exchange local messages with it. A native-emulator exit therefore invalidates
the source worker while the viewer can still report the failure. Directly
sharing `OriginalControllerBackend` between HTTP request threads is rejected.
This is crash containment, not a security sandbox or complete firmware boot.
Standalone low-level replay remains available for single-thread experiments.
Set `KOMBIKRAFT_ASSET_PACK` along with the source-test environment variables to
exercise the actual source-to-HTTP-to-preview-plan integration test.
