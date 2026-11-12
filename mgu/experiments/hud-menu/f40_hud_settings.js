'use strict';
// F40 test build: actual vehicle values only. No map/video producer is supplied.
const MODES = ['drive-data', 'map-only', 'map-gauges', 'map-shift'];
function enabled(ctx) { return !!(ctx.spec && ctx.spec.config && ctx.spec.config.f40HudTest); }
function view(settings) {
    const value = settings.get('customViewMode');
    return MODES.indexOf(value) >= 0 ? value : 'drive-data';
}
function layoutName(settings) {
    if (settings.get('customOverlayEnabled') !== true) return 'off';
    const mode = view(settings);
    if (mode === 'map-only') return 'off';
    return mode === 'drive-data' ? 'f40-drive-data' : mode === 'map-gauges' ? 'f40-overlay' : 'f40-shift-only';
}
function themeName(settings) { return settings.get('customTheme') === 'm-style' ? 'm' : 'oem'; }
function liveContext(ctx) {
    const settings = Object.create(ctx.settings);
    settings.get = (key) => key === 'demo' ? 'off' : ctx.settings.get(key);
    return Object.assign({}, ctx, { settings });
}
function liveOnly(car) {
    // Bypass the upstream learned-gear fallback as well as any saved demo setting.
    car._wantDemo = () => false;
    car.data = () => Object.assign({}, car.live, { demo: false });
    return car;
}
function prepareLayout(raw, settings) {
    const layout = JSON.parse(JSON.stringify(raw));
    delete layout.theme; // allow the native settings choice to apply
    layout.slots = []; // fixed live oil/coolant semantics in this first build
    layout.widgets = layout.widgets.filter((w) => w.type !== 'shiftbar' || settings.get('customFullWidthShiftLights') !== false);
    layout.widgets.forEach((w) => {
        if (w.type === 'shiftbar') { w.x = 0; w.w = 500; w.segments = 50; }
    });
    return layout;
}
function theme(base, mode) {
    return Object.assign({}, base, { modeAccent: mode === 'sport' ? [255, 95, 72, 255]
        : mode === 'eco' ? [92, 215, 255, 255] : [230, 235, 245, 255] });
}
function note(settings) {
    if (settings.get('customOverlayEnabled') !== true) return 'Custom overlay disabled; factory HUD retained';
    return view(settings) === 'drive-data' ? 'Live vehicle data; factory speed/signs retained'
        : 'CarPlay navigation source required; ' + (view(settings) === 'map-only' ? 'custom overlay off' : 'live sensor overlay');
}
function rendererCompatible(targets) { return String(targets || '').split(',').indexOf('hud:500x210') >= 0; }
module.exports = { rendererCompatible, enabled, view, layoutName, themeName, liveContext, liveOnly, prepareLayout, theme, note };
