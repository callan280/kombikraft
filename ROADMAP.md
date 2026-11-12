# Roadmap

The target is OEM-looking F40 cluster layouts that preserve factory behaviour
and can be tested through a validated, reversible vehicle route.

- [x] Package original authored layout adapters, loopback viewer and local-asset admission.
- [x] Provide a reusable matching-bank loader and 24 original BC/indicator event fixtures.
- [x] Keep firmware, extracted source/art/fonts, vehicle data and runtime images out of public history.
- [ ] Complete original factory graphics startup, vehicle-variant selection and scene lifecycle.
- [ ] Join original input processing to native graphics, including warning priority, persistence, acknowledgement and failure states.
- [ ] Package the native renderer/emulator build with pinned separately licensed dependencies and user-local runtime imports.
- [ ] Make supported firmware extraction and asset generation reproducible without the private research workspace.
- [ ] Connect typed decoder output to native readouts, with invalid/provider-loss clearing and source-scale pixel checks.
- [ ] Validate current-car indicated speed, RPM, temperatures, gear, lighting, traction and warning routes; internal IDs alone are insufficient.
- [ ] Establish real BC page availability/order and navigation ownership/feed.
- [ ] Confirm the physical F40 display mask, source fonts, warning positions and both custom layouts on a parked test.
- [ ] Prove an accepted replacement-scene route, warning ownership, fresh independent backups, rollback and recovery before enabling installation.

Offline fixtures and private experiments contribute evidence to these tasks;
they do not automatically complete the vehicle requirements.
