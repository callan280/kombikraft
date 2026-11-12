# Exact-memory QEMU research guard

This source-only component makes unknown memory/port accesses fatal instead
of accepting QEMU's default values. It is an architectural experiment harness,
not an OEM bootloader or a vehicle installer. Supply your own reviewed input
manifest and source files; none are included here.

## Build into a separate executable

Requirements: Python3.9+, an existing QEMU11.1.2 x86_64-softmmu Ninja build
with compile_commands.json and upstream generic-loader enabled, and its
original compiler/dependencies. The helper compiles one new authored device
and reuses the existing link inputs. It does not rebuild or overwrite the
existing QEMU executable, source tree or objects. Choose a fresh output folder
outside that build directory.

```sh
python3 build_guard.py --qemu-build-dir /path/to/qemu-build --output-dir /path/to/new-guard-build
python3 make_bridge.py --output-dir /path/to/new-authored-bridge
python3 -m unittest -v test_portable.py
```

The authored bridge begins at physical8000 after a reset-vector far jump,
sets a flat32-bit GDT/CR0 state and jumps to entry100000 by default. It leaves
original paging/long-mode setup to the supplied program. It supplies no
Multiboot input by default and is **not a complete firmware-loader contract**.
Changing its entry with `--entry` does not prove compatibility. Clang must
support the i386-unknown-none-elf assembler target; no linker or unresolved
relocations are used for its raw image.

## Review local byte admission

A manifest has a `regions` list. Each region contains a safe `name`, hex
`address`, integer `bytes`, boolean `readonly` and SHA256. A `file` is optional:
present means exact file bytes; absent means an explicitly reviewed zero-fill
input. Input paths are relative to the supplied source root.

```sh
python3 validate_layout.py reviewed-layout.json --source-root /path/to/local-inputs --emit-resolved /path/to/new-local-layout.json
```

The resolved file contains local absolute paths; keep it local. Structural
validation and hashes do not establish source provenance, architectural
correctness or physical memory availability. Those require a separate source
contract. Keep source zero initialization distinct from executed initializer
writes. Do not treat alignment padding as admitted RAM.

## Arm before any execution

Start the private QEMU process with `-S`, no network adapter, private stdio
QMP, and the device below. Substitute the SHA256 of the exact resolved layout.
No guest may execute before the preflight succeeds.

```text
-device kombikraft-memory-guard,id=guard,layout=/path/to/new-local-layout.json,layout-sha256=REVIEWED_SHA256,authored-test-exit=off
```

After QMP capabilities, verify query-status is paused. Then send qom-set on
`/machine/peripheral/guard`, property `armed`, value true. Read it back with
qom-get and require true with no errors **before sending cont**. The one-way
arm rejects running/unprepared machines and disarming. The process controller
must use a private pipe, stop on any preflight error and bound runtime/cleanup.

The guard overlays the CPU-private address-space root, covering APIC aliases,
and all port I/O. Exact-size aliases reference hidden aligned backing; hidden
padding is inaccessible. Unknown reads/writes/fetches and read-only writes
exit86 without returning a value. Region hashes, arming and denial records
appear as JSON lines prefixed `KOMBI_GUARD` on stderr. A CPU register dump is
an observation of the stopped fixture, not proof of a complete boot.

`authored-test-exit=on` enables a synthetic completion port for authored-only
tests. Keep it **off for firmware research**. No MSR/CPUID admission changes
are included in this export; architectural CPU/device scope must be reviewed
separately. The guard does not make a generic virtual board match real hardware.

See PROVENANCE.md and COPYING. Generated objects, executables, manifests,
inputs and runtime logs should remain outside the source repository.
