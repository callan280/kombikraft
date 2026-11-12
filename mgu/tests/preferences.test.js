'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');
const {Preferences} = require('../apps/kombikraft/preferences');
const {createController} = require('../apps/kombikraft/controller');
const spec = require('../apps/kombikraft/app.json');
const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'kombikraft-preferences-'));
let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log('PASS ' + name); }
async function rejects(fn) { let caught = false; try { await fn(); } catch (_) { caught = true; } assert(caught); }
async function main() {
    const p = new Preferences(spec.settings, directory);
    await test('all unavailable vehicle features default off', () => {
        spec.settings.filter((s) => s.blocked).forEach((s) => assert.strictEqual(p.get(s.key), false));
    });
    await test('preferences survive a native-app restart', () => {
        assert.strictEqual(p.set('clusterTheme', 'm-round').vehicleApplied, false);
        assert.strictEqual(new Preferences(spec.settings, directory).get('clusterTheme'), 'm-round');
    });
    await test('unavailable controls cannot be enabled by UI or saved state', () => {
        assert.strictEqual(p.set('exhaustControl', true).stored, false);
        const record = JSON.parse(fs.readFileSync(p.file)); record.preferences.exhaustControl = true;
        fs.writeFileSync(p.file, JSON.stringify(record));
        assert.strictEqual(new Preferences(spec.settings, directory).get('exhaustControl'), false);
    });
    await test('invalid choices, values and unknown keys are rejected', () => {
        assert.throws(() => p.set('clusterTheme', 'not-a-layout'));
        assert.throws(() => p.set('hudShiftStrip', 'true'));
        assert.throws(() => p.set('__proto__', true));
    });
    await test('failed persistence retains old memory/disk and removes owned temporary file', () => {
        p.set('clusterTheme', 'factory'); const before = fs.readFileSync(p.file);
        const rename = fs.renameSync; fs.renameSync = () => { throw new Error('fixture disk failure'); };
        try { assert.throws(() => p.set('clusterTheme', 'touring')); } finally { fs.renameSync = rename; }
        assert.strictEqual(p.get('clusterTheme'), 'factory'); assert(before.equals(fs.readFileSync(p.file)));
        assert.deepStrictEqual(fs.readdirSync(directory), ['kombikraft-preferences.json']);
    });
    await test('corrupt and oversized saved files do not enable anything', () => {
        fs.writeFileSync(p.file, '{'); assert(new Preferences(spec.settings, directory).loadError);
        fs.writeFileSync(p.file, ' '.repeat(17000)); const bad = new Preferences(spec.settings, directory);
        assert(bad.loadError); assert.strictEqual(bad.get('exhaustControl'), false); p.reset();
    });
    const handlers = {}, calls = [], messages = [];
    const ui = {onClick(name, fn) { handlers[name] = fn; }, checked(name, value) { calls.push([name, value]); return Promise.resolve(); }, selected(name, row) { calls.push([name, row]); return Promise.resolve(); }, open(name) { calls.push(['open', name]); return Promise.resolve(); }};
    const controller = createController({spec, ui, preferences: p, status: (s) => messages.push(s)});
    await test('native dropdown changes persist only their admitted value', async () => {
        await handlers.PREF_CLUSTERTHEME({row: 1}); assert.strictEqual(p.get('clusterTheme'), 'touring');
        await handlers.PREF_CLUSTERTHEME({row: -1}); await handlers.PREF_CLUSTERTHEME({row: '2'});
        assert.strictEqual(p.get('clusterTheme'), 'touring');
    });
    await test('blocked checkbox stays off and reports its actual limitation', async () => {
        await handlers.PREF_EXHAUSTCONTROL({}); assert.strictEqual(p.get('exhaustControl'), false);
        assert(messages[messages.length - 1].indexOf('not enabled') >= 0);
        assert(calls.some((c) => c[0] === 'PREF_EXHAUSTCONTROL' && c[1] === false));
    });
    await test('native UI selection rolls back when storage fails', async () => {
        const rename = fs.renameSync; fs.renameSync = () => { throw new Error('fixture save failure'); };
        try { await rejects(() => handlers.PREF_CLUSTERTHEME({row: 2})); } finally { fs.renameSync = rename; }
        assert.strictEqual(p.get('clusterTheme'), 'touring');
        assert.deepStrictEqual(calls.filter((c) => c[0] === 'PREF_CLUSTERTHEME').slice(-1)[0], ['PREF_CLUSTERTHEME', 1]);
    });
    await test('navigation targets are native app states', async () => {
        await handlers.OPEN_HUD({}); assert.deepStrictEqual(calls.slice(-1)[0], ['open', 'HUD']);
    });
    await test('capabilities do not advertise a factory skin or actuator', () => {
        Object.keys(controller.capabilities).filter((k) => k !== 'preferenceStorage').forEach((k) => assert.strictEqual(controller.capabilities[k], false));
    });
    await test('reset restores defaults and blocked flags', async () => {
        await handlers.RESET({}); assert.strictEqual(p.get('clusterTheme'), 'factory'); assert.strictEqual(p.get('hudOverlayEnabled'), false);
    });
    console.log(passed + ' preference/controller tests passed; no vehicle or network access.');
}
main().then(() => { fs.readdirSync(directory).forEach((f) => fs.unlinkSync(path.join(directory, f))); fs.rmdirSync(directory); }, (error) => { console.error(error); process.exitCode = 1; });
