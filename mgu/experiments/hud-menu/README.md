# Native HUD-menu prototype helpers

These authored helpers preserve the prototype's entry-point routing and live-only
HUD preference handling. They contain no BMW SDK, fonts or extracted graphics.
The numerical entry contract is tied to a captured ID7 menu and is not a universal
BMW setting ID. It is not enabled in the default Store app.

`entry_routes.js` maps only declared app UUIDs to their native RHMI states.
`f40_hud_settings.js` handles the historical 500x210 HUD overlay preferences;
it does not replace the original HUD speed/sign scene. Its historical visual
constants do not define the current cluster themes.

A complete historical HUD renderer also needs the separate authored `hud.js`
engine, data/layout/shader modules and locally authorized graphics/font resources.
Those dependencies are not silently replaced with placeholder artwork here.
The new Store app's optional factory-menu prerelease uses its own preference
runtime and does not load these historical helpers or start a HUD overlay.
