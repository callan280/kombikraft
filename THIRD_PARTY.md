# Third-party components

The public source contains original project tooling and browser adapters.
Reviewed visual resources are separately attributed; see ASSET-NOTICE.md.
Full firmware and runtime images remain user-local inputs and are excluded
from the MIT grant and distributions.

Optional packages are installed from their normal package registries:

| Dependency | Role | Licence source |
| --- | --- | --- |
| Unicorn 2.1.4 | Bounded original instruction execution | Its installed distribution and upstream project |
| Pillow 13.0.0 | Local native-frame/image utilities | Its installed distribution and upstream project |

QEMU and native graphics build dependencies are external tools, not bundled
copies. Record their versions with each native test. Additional upstream source
must retain its own licence and attribution before it is added here.

IDEmu-derived graphics transport is PolyForm Noncommercial 1.0.0, including its
required contributor notice. QEMU-derived parts are GPL-2.0-or-later. Arm
astcenc is Apache 2.0. Community MGU app-kit derivatives retain their MIT
notices. Consult each subtree's notices; the root MIT licence does not replace
the upstream terms.
# QEMU research guard

`research/gss-guard/` contains authored GPL-2.0-or-later code intended to integrate
with QEMU. Its local COPYING and PROVENANCE.md apply instead of the root MIT
licence. QEMU itself and its build dependencies are user-supplied and are not
distributed as binaries by this project.
