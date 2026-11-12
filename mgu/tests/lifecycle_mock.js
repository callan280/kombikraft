'use strict';
// Contract test only: the mock is not evidence that the real HMI accepts a package.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const EventEmitter = require('events');
const Module = require('module');
const source = path.resolve(process.argv[2]);
const spec = require(path.join(source, 'javascript/app-spec.json'));
const uiDescription = require(path.join(source, 'rhmiData/uiDescriptions/ID7/uiDescription.json'));
const calls = [], warnings = [];
const components = {};
function component(name) {
    const item = new EventEmitter();
    item.setValue = function () { calls.push(['value', name].concat(Array.prototype.slice.call(arguments))); return Promise.resolve(); };
    item.updateResources = () => { calls.push(['resources', name]); return Promise.resolve(); };
    components[name] = item; return item;
}
Object.keys(uiDescription.containers).forEach((id) => {
    const state = uiDescription.containers[id]; component(state.name);
    Object.keys(state.components).forEach((key) => component(state.components[key].name));
});
class OnlineApp extends EventEmitter {
    constructor() {
        super(); this.startReason = 'ENTRY_POINT';
        this.rhmiApplication = {getByName: (name) => components[name], mapEntryState: (uuid, state) => { calls.push(['map', uuid, state]); return Promise.resolve(); }, openEntryState: (uuid) => { calls.push(['entry', uuid]); return Promise.resolve(); }, openState: (name) => { calls.push(['open', name]); return Promise.resolve(); }};
    }
    start() { this.emit('appStatusProxyReady'); calls.push(['start']); return Promise.resolve(); }
    registerActive() { calls.push(['active']); return Promise.resolve(); }
    initialized() { calls.push(['initialized']); return Promise.resolve(); }
    getLastExecutedEntryPointUuid() { return Object.keys(spec.entryRoutes)[0]; }
}
const oldLoad = Module._load;
Module._load = function (name, parent, main) {
    if (name === 'oap-sdk') return {OnlineApp, logging: {getSDKLogger: () => ({warn: (s) => warnings.push(s), error: (s) => warnings.push(s)})}};
    return oldLoad.call(this, name, parent, main);
};
const root = path.resolve(source, '..');
if (!fs.existsSync(path.join(root, 'data'))) fs.mkdirSync(path.join(root, 'data'));
async function run() {
    const app = await require(path.join(source, 'javascript/app.js')).start();
    assert.strictEqual(calls.filter((c) => c[0] === 'initialized').length, 1);
    assert.strictEqual(calls.filter((c) => c[0] === 'map').length, Object.keys(spec.entryRoutes).length);
    assert.strictEqual(app.listenerCount('shutdown'), 1);
    assert(calls.some((c) => c[0] === 'entry'));
    const before = calls.filter((c) => c[0] === 'entry').length;
    app.emit('entryPointExecute', 'undeclared-entry'); await new Promise((r) => setTimeout(r, 5));
    assert.strictEqual(calls.filter((c) => c[0] === 'entry').length, before);
    components.OPEN_CLUSTER.emit('action', {}); await new Promise((r) => setTimeout(r, 5));
    assert(calls.some((c) => c[0] === 'open' && c[1] === 'CLUSTER'));
    components.PREF_CLUSTERTHEME.emit('action', {row: 1}); await new Promise((r) => setTimeout(r, 10));
    const saved = JSON.parse(fs.readFileSync(path.join(root, 'data/kombikraft-preferences.json')));
    assert.strictEqual(saved.preferences.clusterTheme, 'touring');
    components.PREF_EXHAUSTCONTROL.emit('action', {}); await new Promise((r) => setTimeout(r, 10));
    assert(calls.some((c) => c[0] === 'value' && c[1] === 'PREF_EXHAUSTCONTROL' && c[4] === false));
    console.log('PASS mocked OAP lifecycle, entry routing, resource refresh, native events and persistence. Real HMI activation unproved by this test.');
}
run().then(() => { Module._load = oldLoad; }, (error) => { Module._load = oldLoad; console.error(error); process.exitCode = 1; });
