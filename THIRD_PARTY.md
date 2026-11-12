# Third-party components

The public source contains original project tooling and browser adapters.
Locally imported firmware, resources and runtime images are excluded from the
MIT grant and from distributions.

Optional packages are installed from their normal package registries:

| Dependency | Role | Licence source |
| --- | --- | --- |
| Unicorn 2.1.4 | Bounded original instruction execution | Its installed distribution and upstream project |
| Pillow 13.0.0 | Local native-frame/image utilities | Its installed distribution and upstream project |

QEMU and native graphics build dependencies are external tools, not bundled
copies. Record their versions with each native test. Additional upstream source
must retain its own licence and attribution before it is added here.
