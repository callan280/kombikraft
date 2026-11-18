# KombiKraft M Round for F40

In MGU Store, add **callan280/kombikraft**, select **Releases**, and install
**KombiKraft Themes**. The catalogue declares cluster-render and mgu-deploy.

Select **M Round** while parked. It stays active while speed and RPM are
fresh and stationary. **Show factory** releases both the dial and mask
layers immediately. Movement, stale speed/RPM, or renderer loss also releases
them. The display does not start on its own.

The 700-pixel dials start beneath the factory indicator row and extend
behind the footer.
The factory turn indicators and centre warning opening remain reserved. The centre opening starts at y=574 on the 720-pixel panel,
with clearance above the DSC banner observed during the parked test.
The tachometer scale is re-spaced to fit all RPM marks above the opening.
The red sector starts at 6,500 RPM on the display. This is a visual marking.
The original M135i badge sits between the dials, and the BMW digital speed and
gear glyphs sit below their needle hubs. The original lower gear letter is
masked only while a current replacement gear reading is available.

The **Shift lights in Sport** checkbox is saved by the app and defaults to
on. The lights use the nine curved F97 frames and run only with current Sport
mode data. They progress from 5,200 RPM to a flashing final frame at 6,500 RPM.
These are display thresholds for the parked theme. The checkbox takes effect
while the overlay is active.

The app selects a current BMW DME or Sport display boost reading. A positive
Sport display reading takes precedence when the DME source reports zero.
The sensor row identifies the source and distinguishes no data from 0 psi.
The FES and temperature values are read through existing vehicle interfaces.
No boost or RPM is simulated by the head-unit app.

The mask follows the captured factory dial scales. The factory digital speed
reading and fuel regions have separate reservations. The map and warning
opening, footer, turn arrows, parking-brake lamp, warning triangle, and
factory temperature gauge have reserved areas. The grey centre strip can
remain visible through its opening. Full lamp and mask coverage still needs
an in-car comparison with the factory view.

Build from the repo root with `python3 mgu/tools/build.py kombikraft_test`.
After changing the main dial artwork, regenerate its ETC2 assets with
`python3 mgu/tools/encode_cluster_faces.py` using `etcpak==0.9.15`.
Source-art provenance and upstream licences are listed in the
[app notice](../mgu/TEST-THEME-NOTICE.md).
