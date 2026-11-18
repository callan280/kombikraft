# F40 M Round 0.1.15

The mini gauges follow the right-hand factory tachometer arc: oil above, boost to the right, and coolant below. Oil and coolant use uniformly scaled 130% artwork. Their complete layer bounds clear the recorded obstruction and parking-lamp reservation. Both main dials remain 700 pixels across.

The right-side trim mask is continuous around the recorded obstruction. The factory temperature area is masked only while both temperature readings are fresh; both temperature mini faces clear when either reading expires so they cannot obscure the restored factory gauge. Mask alignment remains approximate until confirmed in a vehicle photo.

M Round is selected while stationary and continues using live speed and RPM in motion. Speed does not introduce a Check Control freshness gate. The renderer remains non-exclusive and non-contending, with reserved indicator, warning and footer openings. Missing speed/RPM data, renderer errors, disconnection or suspension still release the overlay. This does not claim all factory warning scenarios have been tested.

Every five seconds during an active session, the application logs the actual speed, RPM, age of the core reading, and shown/total layer count as `KombiKraft live`. This supplies road-test evidence without changing the instrument display or requiring interaction during the drive.

Validation: eight local unittest checks pass, including packaged JavaScript runtime/lifecycle checks, driving samples, stale-data recovery, mini bounds, scaling and temperature fallback. `mgu/tools/preview_theme.cjs` renders the actual packaged shaders and uniforms using WebGL/ETC2 for fresh and stale temperature scenarios. The render verifies shader compilation and supports visual review; it is not road-test evidence.
