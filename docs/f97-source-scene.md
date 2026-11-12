# Original F97 node tree, source defaults and Camera units

The optional `kombikraft.research.f97.scene` command reproduces the completed original-code graph/defaults/Camera experiments from four locally supplied, hash-admitted files. It depends on the authored Python package and pinned Unicorn2.1.4; no private research directory, QEMU image, extracted runtime library, bitmap/font files or manually prepared node catalogue is required.

Install the optional execution dependency and inspect the exact profile without firmware execution:

```sh
python -m pip install -e '.[factory]'
python -m kombikraft.research.f97.scene --profile
```

Supply the supported older-F97 iDrive6 045.009.002 source inputs:

- Unmodified decoded NORboot code bank13.
- Its decoded initialized-data bank14.
- The original matching NOR CE51 container, providing the genuine class/string tables.
- Its decoded `ki_3d_high` scene payload.

The existing source extraction guidance and NORboot extraction tool apply; `--profile` prints exactSHA256 identities. Input files remain local, and every identity is checked before optional emulation code is imported. Unsupported images and incomplete graphs fail closed.

```sh
python -m kombikraft.research.f97.scene \
  --bank /path/to/13-code.bin \
  --data-bank /path/to/14-data.bin \
  --nor /path/to/original-nor.ce51 \
  --scene /path/to/ki_3d_high.bin \
  --output /path/to/NEW-scene-receipt.json
```

The output must not already exist. It is created only after the checks complete. The receipt contains input and implementation hashes, source entry/stop coordinates and adapters, actual executed-source range hashes, source traces, original native objects/matrix outputs, per-node gate/factor results and explicit limits. Machine paths or vehicle captures are not included in the report. No firmware/code banks are bundled by this module.

## What actually executes

The original selected static initializer, full original constructors for116Group/362Mesh/14Billboard nodes, common Node readers, Billboard-specific factory/readers and491 genuine AddChild edges run in each of two heap-fill cases. All492 native world matrices are obtained through original virtual methods. Serialized source9C/B0 property fields are applied by an **explicit interior Group-reader suffix**, not by host writes to native flags.

The suffix is source bank3FA794 through the stop before3FA808, with a declared descriptor inR6, actual Node inR7 and writable stack offsets30/34. The earlier child/material factory work in the full Group reader is neither executed nor given a fabricated success return. This is a source-shaped unit, not a complete factory loader.

After attachments, original getters calculate ancestor B8 AND and cached C8 product. The actual render-bin consumer executes only its genuine local zero-gate/factor short-circuit branches; no enabled visitor or outer traversal is fabricated. The two fills execute984 constructors,982 AddChild edges,984 suffixes,984 inherited gate queries,984 inherited factor queries and346 actual local render-bin exclusions. Graph/resource names come from the source; there is no authored node-hide list.

Separate original Camera units construct five actual Camera/projection candidates per fill, use the exact property API bindings selected by the original record reader, and obtain original view/combined matrices.376 original drawable-world outputs are explicit handoffs into the Camera units. The original matrix routine produces3760 model/view/projection products over both fills. Projection mutation/restore witnesses use the original setters and callback invalidation path. Cameras are not silently selected as the factory's active view.

Source bounds, observed analysis aliases, selected fresh unit statics and the two bounded allocation adapters are declared in `_scene_profile.py` and each case. The selected initializer and real static registration methods execute; whole CRT/kernel/board startup does not. Only the original heap-allocation function boundaries are adapted; no kernel, provider, scene-factory or graphics result is fabricated. Analysis coordinates are not presented as a physical memory map.

## Scope and tests

This command reports source objects/defaults and matrices. It does not render a factory frame, load all material resources, establish normal vehicle/coding/controller state, apply nonzero C8 as blanket shader alpha, join the outer traversal, boot the operating system, contact a car or permit installation. A matching source package can contain alternative model/scale variants; these results are not current-F40 compatibility evidence.

Firmware-free tests cover input admission, refusal to overwrite receipts, graph coverage, source export identities and JSON tuple/array metadata normalization without dropping numeric bits. Optional genuine-source tests use `KOMBIKRAFT_F97_BANK`, `KOMBIKRAFT_F97_SCENE`, `KOMBIKRAFT_F97_NOR` and `KOMBIKRAFT_F97_DATA_BANK`, then:

```sh
python -m unittest discover -s tests -p test_research_f97_scene.py
```

A green publicCI run without these local inputs does not imply the original-code cases were executed. The historical material V1, corrected material V2 and extended command contracts are unchanged by this separate research command.
