# Guarded vehicle-control research source

These archived controllers model ambient presets by driving mode and an exhaust
valve request lifecycle. They are outside the Store catalog and are not loaded by
the KombiKraft app. Both feature defaults are off. No validation record is supplied.

The 16 tests use synthetic vehicle strings and fake send functions; they perform
no network, diagnostic or vehicle access. They exercise stale-input handling,
restoration and failed acknowledgements. A positive diagnostic response is never
reported as proof of physical exhaust position.

```sh
node mgu/experiments/vehicle-enhancements/tests/features.test.js
```

To build this historical app requires the separate MIT App Kit adapters for
`kit/mgu`, `kit/diag` and signal handling, plus a locally supplied platform SDK.
The upstream reference is bimmer-lab/apps commit
`c01878a4efc90e5c8b3888d32d7e5c187fe81f09`; its notice is retained in
`mgu/vendor/LICENSE.bimmer-lab`. The authored preferences helper needed by the
tests is included. No SDK, native diagnostic library, original private evidence,
vehicle identity or per-vehicle validation file is distributed here.

This source does not establish compatibility or authorize enabling vehicle
actuation on a particular car. The public Store app deliberately contains no
vehicle actuator service or diagnostic client.
