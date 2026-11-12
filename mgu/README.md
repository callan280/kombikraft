# KombiKraft for MGU Store

The app provides native iDrive menus for display preferences. It stores layout,
map, unit and HUD choices in the app's own data directory. It does not replace a
factory cluster scene, connect HUD graphics, change ambient lighting or operate
the exhaust. The unavailable controls stay off, including when a saved file asks
to enable them. The BC button and factory alerts are untouched.

## Add the app to MGU Store

Add `callan280/kombikraft` (or its GitHub URL) as a source and select
**Releases**. The release named `catalog` supplies `catalog.json` and the small
SDK-free application package. Alternatively use the direct HTTPS catalogue:

```text
https://raw.githubusercontent.com/callan280/kombikraft/main/catalog.json
```

The app appears as **KombiKraft Lab · Offline prototype**. It is a preferences
prototype with the validation limits below; it does not activate a KOMBI skin.
Use a compatible Store/deploy version with donor SDK linking.

Avoid selecting the full `main` branch for an on-unit source build: it contains
the large visual research library and exceeds Store's 200 MB source-build
workspace limit. The lightweight catalogue downloads the app artifact directly.
`mgu-repo.json` is retained for developer checkouts and source-layout tooling.

## Build from source

From the repository root:

```sh
python3 mgu/tools/build.py kombikraft
```

The result is `mgu/dist/kombikraft@0.1.0.tgz`, with a file/hash receipt beside it.
Python's standard library is sufficient. The archive is deterministic and contains
no BMW SDK, firmware, captured graphics or native libraries. MGU Store supplies its
SDK locally from an installed donor when it installs the package. A unit without
that supported donor-linking path cannot run this app.

`mgu-repo.json` is the root-catalog template: it finds `mgu/apps/*` and runs this
builder. Store builds write their one `.tgz` to `MGU_OUT`; local builds default to
`mgu/dist`. No SDK download or build network access is needed. Use a Store/deploy
version with the documented SDK-free package linking support; this project has
not validated older installers.

## Native factory-menu experiment

```sh
python3 mgu/tools/build.py kombikraft --experimental-factory-menu
```

This produces the separate prerelease `0.1.0-factorymenu.1`. It requests an extra
entry under the captured ID7 HUD menu and routes that entry to native HUD
preferences. The fixed state/anchor pair is firmware-specific. This prerelease
profile is absent from the default Store catalog. Menu insertion does not enable
factory skin replacement, and is not evidence of compatibility with another car
or firmware. Remove the app through Store to remove its registered app entries.

## Tests and experiments

```sh
python3 -m unittest discover -s mgu/tests -p 'test_*.py'
node mgu/tests/preferences.test.js
node mgu/experiments/vehicle-enhancements/tests/features.test.js
```

Host tests prove package structure, persistence, lifecycle contracts and blocked
features. They do not prove actual HMI activation or vehicle compatibility.
Any captured-head-unit validation uses separately supplied local runtime files;
those files and their logs are not public package dependencies.
See `VALIDATION.md` for the bounded real-SDK attempt and its unresolved native
activation boundary.

`experiments/vehicle-enhancements` contains the original guarded lighting/exhaust
controllers and their 16 behavior tests. It is not an installed component or a
dependency of the Store app. `experiments/hud-menu` preserves authored prototype
helpers separately from renderer assets. See their dependency and status notes.

See `THIRD_PARTY.md` for the MIT upstream pin and SDK boundary. No car connection,
flash operation or automatic install is part of this builder.
