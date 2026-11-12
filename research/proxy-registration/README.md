# Original proxy-registration research

These authored Python tools inspect and execute a narrow loader-registration path from a user-supplied, exact-profile head-unit library. They contain no firmware image, library, generated carrier, extracted source data, VIN, network configuration, or installation operation. No BMW library code is distributed here. The generated carrier contains original library bytes and stays local.

The supported SHA-256 profile is `ce831cee2bd80a2f574f0f609314764164a219372344409ab9ff976e543cd669` (ELF64 x86-64). Other profiles fail admission. File names are not evidence of compatibility.

## Run

Python 3 is required. Only the execution probe needs `unicorn==2.1.4` (tested version); carrier generation and synthetic tests use the standard library. Install dependencies in your own virtual environment.

```sh
python3 test_admission.py
python3 make_carrier.py --firmware /your/local/library --output ./local-generated
python3 probe_registration.py --firmware /your/local/library \
  --carrier-map ./local-generated/mgu-proxy-registration-complete-analysis-map.json \
  --output ./local-results
```

Use the virtual environment's Python for the last command. Do not add `local-generated`, `local-results`, or the supplied library to a source-only export.

The carrier preserves selected source bytes and original virtual addresses. ELF analysis scaffolding and analyst seed labels are authored. It does not apply original dynamic relocations, patch firmware, create a runnable target image, or sign a binary. PLT import labels are derived from and checked against the source relocation/jump-slot table. The probe regenerates those ranges/labels before admitting the supplied map.

## Validated scope

The original `.init_array` callback body at `0xC3340` calls `SomeIP::Factory::get` and `registerInterface(0x28FD80)`. The original registration callback at `0x28FD80` constructs these exact arguments:

- Address `local:de.bmw.infotainment.KombiIF:v1_0:1`.
- Service `46363` (`0xB51B`), instance `1`, major `1`, minor `0`.
- Interface `de.bmw.infotainment.KombiIF:v1_0`, creator `0x299CD0`.

The probe runs each original body twice, with zero and `0xA5` allocation fills: four cases pass, returning after 21/21/99/99 observed instruction/import stops. This count includes adapter-entry stops; it is not a firmware performance benchmark. Twelve synthetic tests cover profile/output admission and forged-map rejection without any firmware.

Imported singleton/registry operations are explicitly inert capture adapters. Bounded string allocation and free are host adapters. The factory callback queue, address map, real backend dispatch, network connection and resulting proxy are **not** executed by this probe. It therefore does not prove actual runtime backend selection, a remote setter-51 to KOMBI transport-399 join, native layout activation, safety-warning preservation, or vehicle compatibility. No car or network is accessed.

The separate source inspection that identifies creator `0x299CD0` calling typed constructor `0x294D30` is not an execution claim for this probe. All unsupported imports and mismatched source/map evidence fail closed. Firmware-profile constants and addresses are research observations, not a public installation API.
