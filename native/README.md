# Native renderer source and attributed visual inputs

This directory supplies the authored compact40 native renderer with current V13 mini visual inputs, a usable portable source build, its separately attributed generated visual inputs, and source graphics bridges. It keeps wire composition version 10/layout revision 12, visual revision13. The current build is M Round/no-map; navigation feed, physical BC, full original-controller initialization and vehicle installation are unavailable.

Run from the repository root:

```sh
python native/build.py --validate-only
python -m unittest discover -s native/tests -v
python native/build.py --zig /path/to/zig-0.13.0 --output native/build/v13
python native/generate_f97.py --asset-pack assets/viewer-pack --output native/build/regenerated-f97
```

The source build was checked with Zig 0.13.0 targeting Linux x86-64/glibc2.27. It needs no BMW runtime to **compile**. The generated executable cannot render until the matching native runtime and guest environment are supplied locally. The F97 generator resolves the public route manifest and verifies actual geometry/bitmap hashes; it does not depend on the former research machine paths.

`source/` contains authored C/runtime logic and opaque exported-ABI declarations. `data/v12/` preserves202 baseline inputs and `data/v13/` contains204 current inputs: BMW-derived mesh/UV/visual GLSL/bitmap/font data, authored composition tables and synthetic offline signal fixtures. Those data are excluded from MIT; see their NOTICE and the repository ASSET-NOTICE. No firmware executable bank, library, kernel, VM image, vehicle capture or private test receipt is shipped. Compilation receipts and all locally imported dependencies remain under ignored build/local directories.

For actual native rendering, see [the source/build guide](../docs/native-source.md). It covers separately licensed IDEmu/ASTC/QEMU dependencies, local import, snapshot-only/no-NIC launch and remaining limitations. Build success is distinct from native framebuffer evidence and from original KOMBI application startup.

Current V13 mini data use the same exported public viewer helpers: fixed35–65% complementary blue/red taper, baked bevel/glint and boost pictogram scale1.68. No GLSL or native request ABI changes. Regenerate with `node native/generate_mini_v13.cjs --output native/build/mini-v13`. V12 stays available using `--data native/data/v12`.
