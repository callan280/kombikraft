# Source and licensing

The memory guard, architectural reset bridge, Python build/admission helpers
and synthetic tests are authored KombiKraft research code. The guard integrates
with QEMU's public device/memory APIs and is offered under GPL-2.0-or-later;
the other files in this directory use the same license. See COPYING for GPLv2
terms; the source's later-version option also applies.

QEMU is a separate upstream project: https://www.qemu.org/ and
https://gitlab.com/qemu-project/qemu . Tested local API/build version:11.1.2.
The build helper reuses an existing user-owned QEMU build; it does not download
or redistribute QEMU binaries, ROMs, dependencies or source archives.

This directory contains no BMW firmware/code slices, compiled memory-map data,
fonts/graphics, native analysis snapshots, captured device state, vehicle IDs,
network credentials or guest images. The reset bridge is authored test code,
not a recovered BMW bootloader. Its generic x86 GDT/reset constants and
generated ROM belong to this architectural fixture.

Private controlled experiments establish exact-byte access rejection and the
authored bridge behavior. They do not establish complete physical-board boot,
factory display readiness or a vehicle deployment path. In-progress MSR
admission changes and original-firmware test outcomes are outside this stable
source export.
