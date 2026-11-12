# Native source, visual inputs and local build

The native package now contains the actual authored compact40 renderer and its generated visual input tables. It builds a Linux x86-64 executable from relative public paths. The reviewed profile is M Round/no-map, wire version 10/layout revision 12:1920×720 logical scene, footer680..720,325 meshes and118 footer readbacks. This is an offline Ramses19 graphics application in a captured HU Linux environment, not a rebuilt KOMBI INTEGRITY firmware image or completed factory application boot.

## Source and rights split

|Path|Contents|Licence/ownership boundary|
|---|---|---|
|native/source|Authored C runtime, fixed request parsers, source-property readbacks, BC/CC reservation, typography/gear/fuel/semantic presentation logic|Project-authored code; generated graphics are included separately|
|native/data/v12|202 pinned visual inputs: mesh/UV arrays, original visual GLSL, rasters/font glyphs, composition tables and synthetic fixture stream|Original rights retained; excluded from MIT; maintainer-confirmed graphics/font redistribution permission|
|native/bridges/idemu|Modified IDEmu guest GLES/host CGL source plus protocol/generator headers|PolyForm Noncommercial 1.0.0; upstream LICENSE/NOTICE retained|
|native/bridges/qemu|Upstream QEMU integration source and patch only|GPL-2.0-or-later; complete external QEMU source is still required for a redistributed binary|
|native/bridges/astc-source-pin.json|Exact external Arm astcenc source identities|Apache 2.0 source dependency; source/binary not bundled|
|native/host|Authored local import/wrapper/no-NIC VM launcher and captured-kernel-specific RAM clock workaround|Local experiment only; no car connection or firmware write path|

The source provenance manifest records hashes and logical origins without copying private receipts or machine paths. Firmware libraries, kernel/root images, coding backups, credentials and vehicle-specific captures remain user-local. The supplied album example remains third-party artwork; see ASSET-NOTICE.

## Compile from the public inputs

Use Python 3.11+ and Zig 0.13.0. For image generation/tests, install the repository's native extra/Pillow. No download is performed by these commands.

```sh
python native/build.py --validate-only
python -m unittest discover -s native/tests -v
python native/build.py --zig /path/to/zig --output native/build/v13
python native/generate_f97.py --asset-pack assets/viewer-pack --output native/build/regenerated-f97
```

The build verifies the selected profile’s data hashes before copying them to a fresh stage, then compiles the actual authored C. It rejects overwriting an existing executable. A receipt records source/data/compiler/output hashes. The public F97 generator verifies the route/file/hash manifest, reconstructs original source mesh/UV arrays and bitmap conversions, and preserves physical-calibration-unverified scope. Other accepted generated visual tables are supplied directly as attributed data; a complete public regeneration path for every table is a separate remaining task.

## Build the graphics bridge locally

The reviewed host is Apple Silicon macOS. Supply the external Arm astc-encoder Source directory matching revision a16be552282a5fce554f9018a04c9401dd86ce11; every required source/header hash is checked.

```sh
python native/build_bridges.py --astc-source /path/to/astc-encoder/Source --zig /path/to/zig --output native/build/bridges
```

This compiles a decompression-only ASTC library, Linux guest GLES transport and macOS host GL process. The bridge adds actual ASTC handling and a narrowly scoped neutral initialization for the captured shader's otherwise-unwritten vSegelpunkt output. That emulator compatibility change limits pixel-fidelity claims. IDEmu is pinned to7c18b368e92ea3c2f0542de9bf7b8b06d5eacb5c. Build its external patched QEMU 11.1.2 from the corresponding upstream source; the idemu-shm PCI device and SDHCI fix are required. No QEMU or IDEmu executable is distributed here.

The retained IDEmu NOTICE specifies PolyForm Noncommercial for its ordinary source and GPL-2.0-or-later for QEMU-derived parts. An independently redistributed QEMU binary requires complete corresponding source including applicable modifications; this repository's patch-only folder is not that complete source.

## Import and launch the matching local native environment

Copy runtime-import.example.json into native/local/ and fill local paths and actual hashes. Native rendering requires the exact reviewed Ramses19.0.14 library, compatible guest dependencies, the reviewed kernel, matching 4GiB root filesystem, built GLES/GL bridges, patched QEMU and pinned QEMU-share files. These are not supplied by the graphics permission or MIT licence. No firmware acquisition is automated.

```sh
python native/build.py --zig /path/to/zig --runtime-import native/local/runtime.json --make-disk --mke2fs /path/to/mke2fs --output native/build/v13-runtime
python native/host/prepare_root_wrapper.py --root-filesystem /path/to/root.img --output native/local/root-wrapper.img
python native/host/run_vm.py --runtime-import native/local/runtime.json --root-wrapper-metadata native/local/root-wrapper.json --build native/build/v13-runtime --preflight-only
python native/host/run_vm.py --runtime-import native/local/runtime.json --root-wrapper-metadata native/local/root-wrapper.json --build native/build/v13-runtime --seconds 30
```

The root wrapper tool checks the matching source bytes, creates a new sparse PARTUUID disk, reads the payload back and makes the wrapper read-only. It never edits the source filesystem. The launcher uses snapshot disks, no NIC, a private shared-memory graphics channel and loopback only inside the guest. The kernel workaround is restricted to that owned VM's Unix GDB socket and an exact kernel/instruction guard; it changes disposable guest RAM only. It records actual framebuffer dimensions/counter and stops only its own positive-PID child processes. Startup explicitly selects the pinned unavailable/provider-loss fixture212 and requires its native ACK plus a later frame; it does not inherit raw example needle poses as telemetry. Runtime logs/frames stay local. A produced framebuffer is not an automatic visual-equivalence or completed factory-controller proof.

## What the native application exposes

The fixed guest request files remain the reviewed internal graphics-test ABI, not a CAN transport or public vehicle control interface. Monotonic request IDs and native setter/getter/flush acknowledgements distinguish requests from applied state. Main needle fixtures, BC pages, source-art CC previews, gear overrides, footer/status fixtures and fixed synthetic semantic replay are independent lanes. A real host adapter must check the exact ACK and later framebuffer before calling a control applied.

BC cycles stats/consumption/media/sport/G-force/blank without switching themes. CC reserves its region and hides BC/road content; clear restores selected state. Actual gear bitmap glyphs and BMWTA remain source-derived. Unknown semantic speed/gear/coolant/boost/clock/traction do not inherit sample values. Host time is explicitly a graphics fixture. The optional typed projection adapter requires an explicit reviewed source-pin mapping; hash/shape checks do not authenticate a car.

Touring sweeping-RPM graphics, original-controller owner grafts and warning-order experiments remain separate research branches rather than silently becoming this public V12 runtime. No navigation provider/frame transport, stock-owner entry, signed deployment acceptance, full warning lifecycle, physical display mapping or installation is established by this source build.

## V13 fixed mini styling

The current visual profile ports the same public miniBandProfile/miniBandMesh/miniBandTexels helper outputs into native mesh/UV arrays and two256×32RGBA textures. Blue covers0–65%, red35–100%; their radial tapers complement each other over35–65%. Thresholds are fixed. Boost pictogram geometry scales1.68 about its existing center; original pixels/UVs and all native runtime logic remain unchanged. This is authored styling, not an OEM physical temperature calibration.

`node native/generate_mini_v13.cjs --output native/build/mini-v13` recreates the data from the public source helpers and versioned V12 base. A bounded native V12/V13 comparison passed:8,539changed pixels restricted to the three mini regions; all pixels outside those regions and every row260–720 match exactly. No new212-state replay or full controller/vehicle claim is made.
