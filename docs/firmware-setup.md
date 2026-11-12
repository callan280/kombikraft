# Start with the firmware fitted to your car

KombiKraft is offline research. There is no vehicle-validated release of our
custom cluster layouts or a proved replacement-scene installer. Passing local
tests and displaying a preview do not prove that a layout can run in your car.

## Identify the units first

Record the vehicle platform and production date, current integration level,
and the actual MGU and KOMBI hardware/software identifiers using your existing
diagnostic tools. ISTA or E-Sys can help identify the ECU inventory: HWEL, BTLD,
SWFL and CAFD identifiers and versions matter. Keep your full VIN, coding,
configuration and diagnostic exports private.

The first project target is the F40 M135i. Older F97 round-dial resources are
visual research inputs; their presence does not make F97 firmware compatible
with an F40. Identical model badges or an iDrive 7 label do not establish the
same cluster hardware, rendering ABI, warning logic or bus configuration.

## Obtain matching programming data

Use a lawfully obtained **full PSdZData/programming-data set** containing the
specific software files identified on your units. A coding-only or “Lite”
dataset may lack the firmware payloads needed for extraction. Use the ECU
inventory to select the relevant SWFL/BTLD resources; do not flash a newer
dataset or an unrelated model merely to match a tutorial.

Extract only the packages needed for the unit and software version under
investigation. Retain original hashes, identifiers and versions with every
derived asset. Shared interface names and numeric IDs are research leads;
they do not establish a physical CAN identifier or a working vehicle command.

PSdZData is a starting point, not a complete emulator or recovery backup.
Some native-rendering experiments additionally require a compatible locally
supplied MGU runtime/library, kernel and filesystem capture. Full KOMBI board
startup and hardware emulation remain unfinished. Firmware versions outside
the explicitly supported import profiles need their own extraction and ABI
work; the current loader does not automatically support arbitrary releases.

## Inspect a supported extracted graphics container

The bounded CE51 resource reader accepts an already extracted container:

```sh
python3 tools/extract_ce51.py /path/to/container.ce51 private/ce51-resources
```

The output directory must not exist. The reader keeps input bytes unchanged,
checks table bounds, exact zlib lengths and resource hashes, and reports
unsupported bitmap packing. It has been checked against all 1,022 resources
in the selected older F97 NOR graphics container. It does not decompress an
arbitrary SWFL, decode every vendor graphics format, verify BMW signatures,
or make the extracted resources compatible with another ECU. SWFL/container
staging for additional versions remains an area for contributions.

Generated manifests can contain your local input/output paths. Use the
sanitizing export tools before contributing a catalogue; keep raw imports in
ignored `private/`.

## Work offline, then establish a vehicle test

1. Preserve original files and work from copies. Run the toolkit doctor and
   verify imports before running bounded original-code fixtures.
2. Start with the included visual library and browser layouts. Record whether
   a result is an authored fixture, decoded asset, original-code execution or
   an actual vehicle observation. A map preview is not a CarPlay map feed.
3. For your own firmware, contribute reproducible extraction tools, sanitized
   identifiers/hashes, interface observations and tests. Do not attach complete
   firmware images, VINs, keys, coding backups or private logs to GitHub issues.
4. Before deployment, establish current identity and recoverable backups,
   correlate readouts with parked live observations, and verify missing data,
   warnings, telltales, BC operation, ownership and recovery behaviour.

The MGU app catalogue is an experimental application distribution path. An
app appearing in Store, installing, or saving a skin preference does not prove
factory-menu injection or activation of a KOMBI skin. Those capabilities must
be demonstrated and documented separately on the relevant hardware/version.
