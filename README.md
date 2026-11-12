# KombiKraft

An offline workshop for BMW instrument clusters: source-graphics layout previews,
simulated signals, and bounded execution of original cluster controller code.

The first target is the F40 M135i with iDrive 7. M Round and Map Touring are two
separate layout experiments. Selected graphics from an older F97 donor are
used locally to study BMW's round instruments; this does not establish that an
F97 firmware package can be installed on an F40.

**Pre-alpha research.** Full KOMBI startup, complete warning arbitration,
physical CAN compatibility and a reversible replacement-scene deployment route
are unfinished. This repository contains no vehicle installer or flasher.

## Start

Use Python 3.11 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[factory,native]'
.venv/bin/kombikraft doctor
.venv/bin/kombikraft serve
```

Open the loopback address printed by the server. With no local graphics import,
the viewer explains which inputs are missing. It never substitutes invented
graphics for an unavailable BMW scene or reports a simulated input as a live
vehicle signal.

Firmware, extracted graphics/fonts, vehicle coding, virtual-machine disks and
album-cover images are **not distributed**. The current graphics pipeline
imports a separately prepared local asset directory; extraction directly from
arbitrary PSdZ versions is not yet a one-command public workflow. See
[local assets](docs/local-assets.md), [status](docs/status.md) and
[contributing](CONTRIBUTING.md).

```sh
kombikraft assets verify /path/to/local/asset-pack
kombikraft serve --assets /path/to/local/asset-pack
python -m unittest discover -s tests
```

To run the bounded original-controller fixture, generate its metadata-only
manifest and point it at matching, locally extracted banks:

```sh
mkdir -p private
kombikraft factory-manifest > private/source-banks.json
python -m kombikraft.factory.replay --manifest private/source-banks.json --root /path/to/banks
kombikraft serve --assets /path/to/local/asset-pack --firmware-manifest private/source-banks.json --firmware-root /path/to/banks
```

The toolkit page exposes BC and left/right indicator fixture controls when this
backend is initialized. It reports original event results; those events are not
yet joined to a completed factory graphics startup. See
[native runtime requirements](docs/native-runtime.md) for the separate emulator
work. The `native` Python extra supplies image utilities, **not a bundled QEMU,
BMW runtime image or complete native emulator**.

The browser layout viewer and original-controller backend are distinct. The
browser can render locally supplied source graphics without a whole-system
KOMBI boot. The original-controller backend needs matching local source banks
and explicit platform adapters; its coverage is reported separately.
The preview clock uses the host computer's time; a vehicle clock input is not
yet bound.

## Contribute

Useful work includes original startup/lifecycle research, validated signal
routes, native rendering, local extraction adapters, warning priority tests and
layout refinement. Include evidence and negative cases with compatibility
claims. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before adding files.

MIT applies to our original code. Upstream dependencies retain their own
licences. BMW firmware, graphics, fonts and trademarks are not covered by this
repository's licence. This is an independent community project.
