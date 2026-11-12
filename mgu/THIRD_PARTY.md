# MGU source and runtime dependencies

The two platform configuration files in `vendor/` are adapted from the MIT
bimmer-lab App Kit at commit `c01878a4efc90e5c8b3888d32d7e5c187fe81f09`:
[bimmer-lab/apps](https://github.com/bimmer-lab/apps/tree/c01878a4efc90e5c8b3888d32d7e5c187fe81f09).
Their notice is retained in `vendor/LICENSE.bimmer-lab`. Packaging and RHMI
interoperability follow that kit's documented package format. The new app,
preference model and deterministic builder are KombiKraft source under MIT.

BMW's `oap-sdk` is a runtime prerequisite, **not included** in this source tree or
its generated packages. MGU Store's donor-linking installation path supplies it
locally on the owner's head unit. Local emulator validation must use a separately
provided local SDK/donor; that does not grant redistribution permission.

The experimental vehicle controllers retain their own MIT notice and community
attribution. They are outside the Store catalog and do not start from the new
KombiKraft app. Their SDK/App Kit adapters are separate prerequisites. No firmware,
captured SDK, private evidence, calibration record, account identifier or live
vehicle identity is included here.
