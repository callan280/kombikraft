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
