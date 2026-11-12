'use strict';
// SPDX-License-Identifier: MIT
// The MGU Store links the installed platform's SDK. It is not distributed here.
const fs = require('fs');
const path = require('path');
const {OnlineApp, logging} = require('oap-sdk');
const {Preferences} = require('./preferences');
const {createController} = require('./controller');
const spec = require('./app-spec.json');
const logger = logging.getSDKLogger();
function timeout(promise, milliseconds) {
    let timer;
    return Promise.race([promise, new Promise((resolve) => { timer = setTimeout(resolve, milliseconds); })])
        .then((result) => { clearTimeout(timer); return result; }, (error) => { clearTimeout(timer); throw error; });
}
async function start() {
    const app = new OnlineApp();
    const warn = (error) => logger.warn('KombiKraft: ' + String(error && error.message || error));
    const active = () => Promise.resolve().then(() => app.registerActive()).catch(warn);
    app.on('appStatusProxyReady', active);
    app.on('shutdown', () => setTimeout(() => process.exit(0), 100));
    await app.start();
    await active();
    if (!app.rhmiApplication) { warn('RHMI unavailable; preferences were not opened.'); return app; }
    const rhmi = app.rhmiApplication;
    const get = (name) => { const item = rhmi.getByName(name); if (!item) throw new Error('Missing component: ' + name); return item; };
    const protect = (promise) => timeout(Promise.resolve(promise), 4000).catch(warn);
    const ui = {
        onClick(name, fn) { get(name).on('action', (event) => Promise.resolve().then(() => fn(event || {})).catch(warn)); },
        checked(name, value) { return protect(get(name).setValue(0, 'eParam_RowSelected', value, 'Bool')); },
        selected(name, row) { return protect(get(name).setValue('SelectedItem', row, 'UInt')); },
        open(name) { return protect(rhmi.openState(name)); },
        text(name, value) { return protect(get(name).setValue(0, 'Text', value, 'Text')); }
    };
    const appRoot = path.resolve(__dirname, '..', '..');
    const data = path.join(appRoot, 'data');
    const preferences = new Preferences(spec.settings, fs.existsSync(data) ? data : process.cwd());
    const controller = createController({spec, ui, preferences, status: (value) => {
        ['MAIN_STATUS', 'CLUSTER_STATUS', 'HUD_STATUS', 'FEATURE_STATUS'].forEach((name) => ui.text(name, value));
    }});
    const routes = spec.entryRoutes;
    for (const uuid of Object.keys(routes)) await protect(rhmi.mapEntryState(uuid, get(routes[uuid])));
    const open = (uuid) => {
        if (!Object.prototype.hasOwnProperty.call(routes, uuid)) { warn('Unknown entry point'); return; }
        return protect(rhmi.openEntryState(uuid));
    };
    app.on('entryPointExecute', open);
    await Promise.all(spec.screens.map((screen) => protect(get(screen.name).updateResources())));
    await controller.refresh();
    if (preferences.loadError) warn('Saved preferences ignored: ' + preferences.loadError);
    await app.initialized();
    const entry = app.getLastExecutedEntryPointUuid && app.getLastExecutedEntryPointUuid();
    if (entry && ['ENTRY_POINT', 'BOOKMARK', 'LUM'].indexOf(String(app.startReason)) >= 0) await open(entry);
    return app;
}
module.exports = {start, timeout};
if (require.main === module) start().catch((error) => logger.error('KombiKraft start: ' + String(error && error.stack || error)));
