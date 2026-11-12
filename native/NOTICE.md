# Native package ownership and dependencies

KombiKraft-authored source/build/host logic is covered by the project licence, except where a file or directory states another licence. The generated BMW-derived graphics/font/visual-shader inputs in data/ are excluded from MIT and retain original rights; see data/v12/NOTICE.md and ../ASSET-NOTICE.md.

Required Notice: Copyright 2026 IDEmu contributors. The IDEmu-derived source in bridges/idemu/ retains its PolyForm Noncommercial 1.0.0 LICENSE and NOTICE. It is not MIT-relicensed. The separate bridges/qemu/ integration source/patches retain GPL-2.0-or-later terms and their original headers; COPYING is the upstream QEMU licence text. No QEMU binary or full source tree is bundled. Distributing an independently built QEMU binary requires its complete corresponding source, not merely this patch subset.

Arm astcenc is an external Apache 2.0 source dependency. Its exact source identities are pinned, but neither its source nor compiled library is bundled. Matching BMW native libraries, kernel, root filesystem and guest executables remain user-local dependencies. The permissions for extracted graphics/fonts do not supply those runtime files or relicense third-party code.
