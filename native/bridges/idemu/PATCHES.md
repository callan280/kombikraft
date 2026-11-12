# IDEmu-derived graphics bridge changes

Required Notice: Copyright 2026 IDEmu contributors. PolyForm Noncommercial 1.0.0 applies to this directory, except where upstream files state otherwise. The full upstream LICENSE and NOTICE are retained. These are not relicensed under the repository MIT licence.

KombiKraft's glhost-cluster.c/gles-cluster.c derive from the pinned IDEmu mgu transport. The host bridge adds actual ASTC LDR/sRGB decompression through the separately supplied Arm astcenc implementation. It also initializes only the exact otherwise-unwritten vSegelpunkt vertex output to0.0 where Apple GLSL would reject the captured shader. That initialization is an explicit offline compatibility limitation, not proof of bit-identical target GPU behavior. The guest/host shared-memory protocol, generated GL IDs/stubs and original comments are preserved.

No IDEmu executable, QEMU executable, BMW runtime, kernel or filesystem image is bundled. The sibling qemu directory preserves upstream GPL-derived integration source/patches. A distributed QEMU binary requires its complete corresponding source, including applicable patches; this patch directory alone is not the complete source for such a binary. Build the external QEMU dependency from the pinned IDEmu project and retain its notices and corresponding-source obligations.
