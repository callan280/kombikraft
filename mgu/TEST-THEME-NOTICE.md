# Parked test sources and scope

This package contains original KombiKraft glue plus:

- `cluster_render_client.js`: unmodified MPL-2.0 source by Robert Nisipeanu,
  from aidac/apps commit `27a6a7662d7243f2d5562829b5fe9628cac668f2`,
  `shared/cluster_render_client.js`. Source is bundled. See LICENSE.MPL-2.0.
- `kit/runtime/signals.js`: unmodified bimmer-lab MIT source from the same
  commit, `kit/runtime/signals.js`. See LICENSE.bimmer-lab.
- `needle-math.js`: adapted bimmer-lab MIT needle/path functions, same pin,
  `shared/e36.js`. See THIRD-PARTY-NEEDLES.txt.
- `art/*.rgba`: exported from the existing recovered BMW F97 mesh/texture
  package using the viewer's custom material. These assets retain their
  original ownership; see the repository ASSET-NOTICE.md. They are not MIT
  merely because the application code is MIT. The shift demo packs the shared
  225-vertex `ki_3d_shift_planes` mesh, nine `ki_dzm_shiftlights` frame strips
  and their glow profile from F97 SWFL 4CEB/4CED/4CEE 045.009.002. The atlas
  records source hashes. Placement uses the source tach-relative transforms.
  Texture sampling, the inward fade and timing are adapted for the demo.
  The M Round faces also use the F97 corona meshes and red warning-ring
  material, plus the original F40 M135i designation. Trim shading and the
  position of the redline transition are preview choices.
  No captured firmware or SDK is in this archive.

Upstream: https://github.com/aidac/apps/tree/27a6a7662d7243f2d5562829b5fe9628cac668f2
Renderer: https://github.com/robertnisipeanu/idrive-apps/tree/main/native/cluster-render

The app uses fixed read-only pressure queries and vehicle signal subscriptions.
The factory retains ownership of warning lights. Geometry reservations avoid
known or estimated regions. Full F40 warning preservation remains unverified.
