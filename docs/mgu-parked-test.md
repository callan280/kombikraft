# KombiKraft Themes for F40

In MGU Store, add **callan280/kombikraft**, select **Releases**, and install
**KombiKraft Themes**. An existing source can be refreshed. The catalogue
declares cluster-render 0.6.9 and mgu-deploy 0.4.0.

With the car parked, open the app in iDrive and choose a 20-second test.

- **M Round** uses large aligned BMW dial artwork and oil, coolant and boost
  mini gauges. The F97 bezels and outer tachometer redline are drawn into
  the faces. The F40 M135i badge sits below the tachometer hub, behind the
  needle. Missing or stale mini readings hide their needles.
- **M Round · stay on while parked** holds the display until stopped, while
  stationary and receiving fresh core signals. Moving or losing data releases it.
- **M Round · mask comparison** is a short comparison using the photo-based
  right tachometer mask. It leaves the measured parking-brake, temperature,
  centre warning and footer regions open.
- **Map Touring** puts compact live speed and RPM at the lower edges and leaves
  the centre open for the factory view. Live navigation visibility depends on
  the factory display and needs a vehicle check.
- **Show factory / stop test** releases the app's layers early. Output also
  releases on timeout, motion, stale core readings or renderer disconnect.

The app uses existing BMW speed, RPM, CDS temperature and FES sport display
boost readers. M Round adds a visual fuel level strip using BMW's KombiIF tank
litres, scaled to the M135i's 50 L specification. Boost prefers the engine
pressure minus measured ambient pressure when both are available, with fresh
FES boost as fallback. The request set is fixed and read-only. The main dial
centre rings follow Comfort orange, Sport red and Eco Pro blue from BMW FES.

It requires fresh speed below 1 km/h and valid RPM to activate.
**M Round · shift-light demo** uses the nine light frames and shared curved
mesh recovered from the older round-gauge F97. The lights build on the inside
edge of the tachometer ring, with amber followed by red and a flashing final
frame. The demo builds from 5,200 RPM, flashes at 6,250 RPM and simulates a
6,300-to-4,800 RPM upshift. The RPM drop is based on the saved partial-load F40
log. Thresholds and 2.5 Hz flash timing are preview settings. The display
returns to the factory view after 10 seconds. The speed reading stays live.

The layouts preserve space for the footer and modelled warning regions.
The M Round warning reservation cuts into the lower tachometer, including
part of the redline sector. The redline artwork follows the donor dial
reference. F40 engine or tune limits are unverified.
Factory lamp visibility and recovery still need checking on the actual F40.
Compare the displays before, during and after activation while parked. If the
display does not return as expected, stop testing and remove the Themes app
through Store. Retain Store's installation backup.

Host tests cover the two renderer layouts, read-only signal declarations,
package reproducibility and display release. The installed renderer and factory
scene have yet to be validated with this package.

From the repo root, build with `python3 mgu/tools/build.py kombikraft_test`.
Source artwork provenance and third-party licences are listed in the
[app notice](../mgu/TEST-THEME-NOTICE.md).
