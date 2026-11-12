# Validation status

This is an experimental preferences app. No vehicle installation or activation is
claimed for this release.

## Reproducible host checks

The six Python build tests pass, including deterministic archives, SDK exclusion,
the Store `MGU_OUT` contract, native resource consistency, entry routing and a
mocked lifecycle using the actual app source. Twelve preference tests and sixteen
vehicle-controller experiment tests also pass. Run the commands in `README.md`.
The mocked lifecycle does not substitute for a running head-unit service stack.

## Bounded captured-head-unit attempt

The default 0.1.0 package was staged in an isolated, network-disabled emulator
using separately supplied local head-unit files. The original runtime reported
Node 8.16.2. The locally supplied OAP SDK 24.10.2 loaded, and the actual
`OnlineApp.start()` entered and completed its folder initializer.

The attempt reached the SDK's joynr loading step. It reported a missing app
keychain and its own insecure-connection fallback. No `rhmiReady`, successful
start completion or visible native app activation was observed before the
bounded attempt ended. No synthetic service replies were used to make it pass.
The exact missing service or configuration responsible remains unresolved.

This check was manual staging in a disposable guest, not an MGU Store install.
It does not verify Store donor linking, app launch from the vehicle's Apps menu,
the experimental factory-menu insertion, HUD output or factory cluster skin
activation. These require further validation with the appropriate runtime and
matching vehicle firmware. Captured SDK files, emulator images and private logs
are excluded from this public MGU package.

## Output boundary

Both package profiles save app preferences only. Factory skin injection, HUD
rendering, exhaust control and ambient-lighting changes remain unavailable.
The separate controller experiments are source and host tests; the Store app
does not load or install them.
