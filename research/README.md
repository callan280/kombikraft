# Offline firmware research tools

These are contributor tools for source inspection and bounded experiments.
They do not connect to a car, install a scene or flash an ECU. Supply lawfully
obtained exact-profile inputs locally; generated carriers, source banks,
receipts and runtime images stay outside Git.

| Tool | Input and tested scope | Important boundary |
| --- | --- | --- |
| [F97 material readers](f97-materials.md) | Exact older-F97 source bank, scene and NOR; 66 parameter-reader, 48 identifier-parser and 96 image-cache-boundary cases | Declared heap/provider inputs; complete image fetch, scene loading and original GPU execution remain false |
| [MGU proxy registration](proxy-registration/README.md) | Exact x86-64 library; original loader callbacks with import capture adapters | Actual registries, backend/network dispatch and custom layout activation remain unproved |
| [DMA address geometry](kss-dma/README.md) | Explicit register/address values; authored synthetic tests | No payload access, transfer, interrupt or device emulation |
| [QEMU exact-memory guard](gss-guard/README.md) | User-owned QEMU build and reviewed input layout; authored reset bridge | Explicit architectural fixture; no OEM loader, complete board model or MSR admission in this stable export |
| [NORboot bank extractor](../tools/extract_norboot_bank.py) | Decoded NORboot flash/table plus local liblz4 | Does not unpack arbitrary SWFL or prove target addresses/zero initialization |

The QEMU directory uses GPL-2.0-or-later with its own COPYING. Other authored
tools use the root MIT licence. Firmware hashes, method IDs and offsets are
source observations, not a public installation interface.

Synthetic checks need no BMW firmware:

```sh
python -m unittest discover -s tests
python -m unittest discover -s research/kss-dma
python -m unittest discover -s research/proxy-registration
python -m unittest discover -s research/gss-guard
```

Original-code checks require the separate inputs and optional dependencies
documented for each tool. Passing synthetic tests does not reproduce those
firmware runs. See [current status](../docs/status.md) and
[firmware setup](../docs/firmware-setup.md).
