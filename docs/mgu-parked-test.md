# KombiKraft M Round for F40

In MGU Store, add **callan280/kombikraft**, select **Releases**, and install
**KombiKraft Themes**. The catalogue declares cluster-render and mgu-deploy.

Select **M Round** while parked. It stays active while speed and RPM are
fresh and stationary. **Show factory** releases both the dial and mask
layers immediately. Movement, stale speed/RPM, or renderer loss also releases
them. The display does not start on its own.

Both round faces fit above the centre warning opening and clear the two
turn-indicator boxes measured in the native F40 renderer. The original F40 M135i badge is enlarged
below the tachometer hub. The speedometer shows the measured speed and BMW
km/h label below its needle hub. The outer red sector starts at 6,500 RPM on the
display. This is a visual marking, independent of the engine or tune limit.
The factory fuel display remains visible where the layout leaves it open.

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
reading and the fuel and speed-limit regions have separate reservations. The map and warning
opening, footer, turn arrows, parking-brake lamp, warning triangle, and
factory temperature gauge have reserved areas. The grey centre strip can
remain visible through its opening. Full lamp and mask coverage still needs
an in-car comparison with the factory view.

Build from the repo root with `python3 mgu/tools/build.py kombikraft_test`.
Source-art provenance and upstream licences are listed in the
[app notice](../mgu/TEST-THEME-NOTICE.md).
