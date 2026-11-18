# KombiKraft Themes for F40

In MGU Store, add **callan280/kombikraft**, select **Releases**, and install
**KombiKraft Themes**. An existing source can be refreshed. The catalogue
declares cluster-render 0.6.9 and mgu-deploy 0.4.0.

With the car parked, open the app in iDrive and choose a 20-second test.

- **M Round** uses large aligned BMW dial artwork and oil, coolant and boost
  mini gauges. Missing or stale mini readings hide their needles.
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
FES boost as fallback. The request set is fixed and read-only.

It requires fresh speed below 1 km/h and valid RPM to activate.
The M Round sweep option is an explicit visual demo. It moves the artwork
without sending vehicle signals.

The layouts preserve space for the footer and modelled warning regions.
The M Round warning reservation cuts into the lower tachometer artwork.
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
