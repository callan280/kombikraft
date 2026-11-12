# KombiKraft

An offline BMW cluster and MGU workshop: OEM graphics, M Round and Map Touring
layouts, a viewer, bounded original-controller experiments, native renderer
sources and an experimental MGU companion app.

**Pre-alpha research — no vehicle-validated release.** Custom cluster layouts,
factory-menu/skin activation and recovery remain in development. Offline tests
exist, but do not establish live CAN compatibility, complete factory warnings
or safe deployment. This is not custom KOMBI firmware or a ready-to-flash upgrade.

The first target is the F40 M135i with iDrive 7. Older F97 resources provide
round-dial graphics and rendering research; they are not a compatible F40
firmware image. Contributions for other cars need their actual firmware
identifiers and reproducible evidence.

## Start with the included viewer

Use Python 3.11 or newer and a browser with WebGL:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[factory,native]'
.venv/bin/kombikraft doctor
.venv/bin/kombikraft assets verify assets/viewer-pack
.venv/bin/kombikraft serve --assets assets/viewer-pack --library assets/library
```

Open the printed loopback address, then the layout preview. The pack includes
BMW graphics/fonts with separate attribution; see [asset notices](ASSET-NOTICE.md).
The larger collection has [its own searchable library](docs/asset-library.md).
Readouts, maps and signals are offline examples, never live vehicle data.

## Project contents

| Area | Starting point | Scope |
| --- | --- | --- |
| Viewer and layouts | `src/kombikraft/web/`, `assets/viewer-pack/` | M Round, Map Touring, BC content and simulated conditions |
| Graphics library | `assets/library/` | Decoded visuals with provenance and interpretation limits |
| Native renderer | [Source guide](docs/native-source.md), [requirements](docs/native-runtime.md) | Renderer/build sources and separate visual data; local runtime dependencies required |
| Controller fixtures | `src/kombikraft/factory/` | Bounded original-code execution with specifically matched local banks |
| MGU companion | `mgu/`, [MGU guide](mgu/README.md) | Experimental preferences and integration research |
| Your car's firmware | [Firmware setup](docs/firmware-setup.md) | Identification, PSdZData selection, extraction and contribution |
| Firmware research tools | [Research guide](research/README.md) | Original F97 material readers, MGU registration probes, bounded DMA geometry and an authored QEMU memory guard |

Add `callan280/kombikraft` to MGU Store and select **Releases** for the lightweight
application catalogue. See the [MGU guide](mgu/README.md) for its direct HTTPS
URL and requirements. The root `mgu-repo.json` also describes the source layout,
but the full research tree exceeds the head unit's source-build workspace limit.
Installing an app or saving a preference does not itself inject a factory menu
or activate a KOMBI skin. These paths remain experimental and need hardware
validation.

The [F40 factory theme entry-method findings](docs/f40-factory-theme-entry-method.md)
describe why the parked visual preview, MGU access and existing signed BMW
themes have not yet become a factory-bound custom layout.

## Work with your own firmware

Read [firmware setup](docs/firmware-setup.md) first. Record actual MGU/KOMBI
hardware, SWFL/BTLD/CAFD versions and integration level. Use lawfully obtained
matching full PSdZData where needed; some emulator paths additionally require
your own compatible runtime capture. Model name alone does not select a
firmware or bus profile.

Full firmware images, operating-system/runtime captures, coding backups,
vehicle identifiers, credentials and private logs are not distributed here.
The visuals do not replace the matching firmware needed to execute original
code. Arbitrary PSdZData versions are not automatically supported.

For the bounded original-controller fixture against supported local banks:

```sh
mkdir -p private
kombikraft factory-manifest > private/source-banks.json
python -m kombikraft.factory.replay --manifest private/source-banks.json --root /path/to/banks
kombikraft serve --assets assets/viewer-pack --firmware-manifest private/source-banks.json --firmware-root /path/to/banks
python -m unittest discover -s tests
```

The native renderer and controller loader are separate runtimes; neither
demonstrates a whole-system KOMBI boot. The optional Python `native` extra
supplies image utilities, not QEMU or a BMW operating system.

An [optional Check Control command session](src/kombikraft/factory/README.md#optional-check-control-command-fixture)
executes the original warning supplier/consumer alongside BC and lamp fixtures.
It needs a separate 14-bank local import and reports source text, icon references
and colours. The optional `serve --check-control` path also brings this output
into the existing simulator. Reviewed warnings use the original selected assets
in our custom canvas composition. See the [command and simulator guide](src/kombikraft/factory/README.md#optional-check-control-command-fixture).

## Contribute

Help with matching-firmware extraction, original startup, warning/signal routes,
native composition, MGU integration, layouts and reproducible tests. See
[status](docs/status.md), [roadmap](ROADMAP.md) and [contributing](CONTRIBUTING.md).
Keep unknown signals unavailable and document failure cases alongside success.

Current source includes reproducible research commands and opt-in original
Check Control computation inside the simulator. The MGU Store app's activation capabilities remain
experimental. See [status](docs/status.md) and the
[November research update](docs/research-update-2026-11-12.md) for tested scope
and remaining gaps.

MIT covers our original code only. Upstream components keep their licences,
and visual resources have separate permission/attribution. See
[third-party components](THIRD_PARTY.md) and [asset notices](ASSET-NOTICE.md).
KombiKraft is an independent community project.
