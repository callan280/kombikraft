# Native runtime and local dependencies

The browser viewer, original-controller loader and native renderer are different
runtimes. The viewer composes imported resources in a browser. The loader runs
selected original controller code against explicit platform adapters. A native
Ramses renderer additionally needs a compatible native runtime and graphics
transport. Neither is a complete KOMBI cold boot.

## Verified native rendering path

The existing private research implementation builds a Linux x86-64 C scene
probe and loads `libramses-shared-lib-wayland-ivi-egl-es-3-0.so.19.0` through its
actual exported C++ ABI. The matched captured version is Ramses 19.0.14. It loads
both the matching Main scene/resources and Init resources; Main resources alone
are insufficient for the shared effects. OEM scenes, resource packs, shaders,
fonts and the native library must be imported from the user's own matching
firmware. They are not part of this repository.

For original F97 round-dial source material, the earlier CE51/iDrive6 donor and
the later Ramses/iDrive7 scene family remain separately identified. An imported
round-dial texture is not proof that the original F97 controller or shader is
running. Native custom scenes mix authored composition with imported graphics;
their simulation is not live vehicle data.

## Build requirements observed in the research implementation

| Layer | Verified requirement |
|---|---|
|Host build|Apple Silicon macOS with Xcode command-line Clang and the OpenGL/CGL frameworks|
|Cross compiler|Zig 0.13.0, `zig cc -target x86_64-linux-gnu.2.27 -std=c11`, linking `-ldl -lm` and `/lib/ld-linux-x86-64.so.2`|
|Guest GLES transport|Separate x86-64 `libGLESv2.so.2` shim built as PIC/shared; IDEmu protocol headers and generated GL stubs|
|Host graphics transport|IDEmu-derived offscreen GL host plus Arm astcenc decompression; original ASTC uploads must not be dropped|
|ASTC decoder|Arm astcenc revision `a16be552282a5fce554f9018a04c9401dd86ce11`, decompression-only build; current source requires C++20|
|Virtual machine|IDEmu's patched QEMU x86-64 build based on 11.1.2, including `idemu-shm` and the SDHCI PCI fix|
|Disk assembly|e2fsprogs `mke2fs`, creating a separate asset disk from a local stage directory|
|Guest OS|User-supplied matching captured Linux kernel and HU root filesystem with native dependencies; not the KOMBI INTEGRITY OS|
|Controller execution|The separate Python >=3.9 factory loader, standard library and optional `unicorn==2.1.4`; it does not replace the native graphics requirements above|

The current private scene prototype is built from authored C plus generated
resource arrays. The arrays include firmware-derived content. A public build
must generate those locally from verified imported assets; generated C/INC,
shared libraries, kernels, images and source-derived resource packages stay
outside version control.

## Minimal reproducible local package boundary

A native package needs a versioned user-local import manifest that pins the
native library, Main/Init scene and resource hashes, kernel/root identity and
required ABI symbols. It should then:

1. Build authored source and separately licensed dependencies from pinned source.
2. Generate source-derived geometry/shader/texture inputs locally from verified
   imported resources. Reject a different renderer ABI or missing resource.
3. Assemble a separate asset disk. Preserve the imported filesystem bytes; any
   boot partition wrapper is a generated local artifact, never a firmware image
   to install in a car.
4. Launch an owned disposable VM with `-nic none` and snapshot disks, a private
   graphics channel and bounded local command interface.
5. Require native scene-load/SceneShown acknowledgement and actual framebuffer
   evidence. A running process or HTTP response does not prove rendering.
6. Restore initial scene state, stop only owned processes and unlink their
   private sockets/shared memory. Keep hashes and cleanup receipts locally.

This is the required packaging boundary derived from the working research
implementation. It is **not yet a portable native build/launch command supplied
by this repository**. The private captured root image and machine-specific
scripts cannot simply be bundled as dependencies. There is no automatic
firmware acquisition, vehicle connection, flashing or live installation here.

## Licence and fidelity boundaries

IDEmu's inspected source licence is PolyForm Noncommercial 1.0.0; its QEMU-derived
parts are GPL-2.0-or-later. Arm astcenc is Apache 2.0. Keep each project's notices
and conditions separately from KombiKraft-authored code. A dependency's source
licence does not grant redistribution rights to captured BMW software/assets.

The tested host transport adds ASTC decode support and a narrowly scoped neutral
initialization for one captured shader's otherwise unwritten varying. These
compatibility changes apply only to the emulator and limit any pixel-fidelity
claim. Browser WebGL composition and native renderer readbacks should continue
to report their evidence separately. Actual factory initialization, vehicle
coding, warning arbitration, board devices and full KOMBI cold boot remain
independent requirements.
