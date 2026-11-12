'use strict';
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const app = '../apps/f40_vehicle_enhancements/';
const {Lighting, colourRequest, driveMode} = require(app + 'lighting');
const {Exhaust, request, validationMatches, PROFILE} = require(app + 'exhaust');
const prefs = require('../kit/runtime/preferences');
const spec = require(app + 'app.json');
let passed = 0;
async function test(name, fn) { await fn(); console.log('PASS ' + name); passed++; }
const validation = {schemaVersion: 1, profile: PROFILE, parkedTestPassed: true, vin: 'TEST0000000000001', sgbdIndex: '123ABC'};
const live = {available: true, electricFlap: true, vin: validation.vin, sgbdIndex: validation.sgbdIndex};
function harness(Class, changes) {
    let time = 100000;
    const settings = Object.assign(prefs.sanitize(spec.settings, null), changes || {});
    const sends = [];
    const controller = new Class({get: (k) => settings[k], now: () => time,
        delay: async (ms) => { time += ms; }, validation,
        send: async (value) => { sends.push(value); return [0x6F,0x60,0xFD]; }});
    return {controller, settings, sends, advance: (ms) => {time += ms;}};
}
const sample = (light, n) => light.observeColour({statusMenuAmbientePanoramicRoofInteriorLighting: 'FARBAUSWAHL_' + n});
async function run() {
    await test('fresh install sends no commands even with live supported services', async () => {
        const a = harness(Lighting); a.controller.available = true; sample(a.controller, 3); a.controller.observeDrive(1);
        const b = harness(Exhaust); b.controller.capabilities = live; b.controller.observeRPM(1000);
        await a.controller.step(); await b.controller.step(); assert.deepStrictEqual(a.sends, []); assert.deepStrictEqual(b.sends, []);
    });
    await test('lighting mode selects only the requested preset and keeps other fields unfilled', async () => {
        const h = harness(Lighting, {lightingEnabled: true, colour_sport: 2}); const c = h.controller;
        c.available = true; sample(c, 3); c.observeDrive('SPORT_DYNAMIC'); await c.step();
        assert.deepStrictEqual(h.sends, [colourRequest(2)]); assert.strictEqual(h.sends[0].controlHueInteriorLighting, 4095);
        assert.strictEqual(h.sends[0].controlBrightnessValueBrightnessOffsetAmbientePanoramicRoofInteriorLighting, 255);
    });
    await test('disable before status acknowledgement queues previous-colour restoration', async () => {
        const h = harness(Lighting, {lightingEnabled:true, colour_sport:2}); const c=h.controller;
        c.available=true; sample(c,3); c.observeDrive(1); await c.step(); sample(c,3);
        h.settings.lightingEnabled=false; c.changed(); h.advance(1500); await c.step();
        assert.deepStrictEqual(h.sends.map((x)=>x.controlMenuAmbientePanoramicRoofInteriorLighting),['FARBAUSWAHL_2','FARBAUSWAHL_3']);
    });
    await test('driver colour choice is retained until the next driving-mode change', async () => {
        const h=harness(Lighting,{lightingEnabled:true,colour_sport:2,colour_eco:4});const c=h.controller;
        c.available=true;sample(c,3);c.observeDrive(1);await c.step();sample(c,2);sample(c,9);h.advance(2000);await c.step();
        assert.strictEqual(h.sends.length,1);c.observeDrive(7);await c.step();assert.strictEqual(h.sends.length,2);
    });
    await test('unknown colour modes and stale drive signals cause no speculative lighting write', async () => {
        const h=harness(Lighting,{lightingEnabled:true,colour_sport:2});const c=h.controller;
        c.available=true;c.observeColour({statusMenuAmbientePanoramicRoofInteriorLighting:'INDIVIDUALMODUS'});c.observeDrive(1);await c.step();
        sample(c,3);h.advance(11000);sample(c,3);await c.step();assert.deepStrictEqual(h.sends,[]);
        assert.strictEqual(driveMode('not-a-mode'),null);assert.throws(()=>colourRequest(14));
    });
    await test('lost lighting setter reply still permits restoration', async () => {
        const h=harness(Lighting,{lightingEnabled:true,colour_sport:2});const c=h.controller;
        c.available=true;sample(c,3);c.observeDrive(1);const original=c.send;c.send=async(v)=>{h.sends.push(v);throw new Error('timeout');};
        await c.step();c.send=original;h.settings.lightingEnabled=false;c.changed();h.advance(1500);await c.step();
        assert.strictEqual(h.sends[1].controlMenuAmbientePanoramicRoofInteriorLighting,'FARBAUSWAHL_3');
    });
    await test('lighting stop waits for an in-flight write then restores the prior preset', async () => {
        const h=harness(Lighting,{lightingEnabled:true,colour_sport:2});const c=h.controller;
        c.available=true;sample(c,3);c.observeDrive(1);let finish;let count=0;
        c.send=(v)=>{h.sends.push(v);return ++count===1?new Promise((r)=>{finish=r;}):Promise.resolve();};
        const first=c.step();const stop=c.stop();finish();await first;await stop;assert.strictEqual(h.sends.length,2);
        assert.strictEqual(h.sends[1].controlMenuAmbientePanoramicRoofInteriorLighting,'FARBAUSWAHL_3');
    });
    await test('DME capability does not substitute for exact parked VIN/DME validation', async () => {
        for (const record of [null,Object.assign({},validation,{parkedTestPassed:false}),Object.assign({},validation,{sgbdIndex:'FFFFFF'}),Object.assign({},validation,{vin:'TEST0000000000002'})]) {
            assert.strictEqual(validationMatches(record,live),false);
            const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'OPEN'});h.controller.validation=record;h.controller.capabilities=live;
            await h.controller.step();assert.deepStrictEqual(h.sends,[]);
        }
    });
    await test('accepted exhaust command is never reported as physical position confirmation', async () => {
        const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'OPEN'});const c=h.controller;c.capabilities=live;await c.step();
        assert.deepStrictEqual(h.sends,[request('OPEN')]);assert.strictEqual(c.accepted,true);assert.strictEqual(c.confirmed,'UNKNOWN');
        h.advance(16000);await c.step();assert.strictEqual(h.sends.length,1);
        h.settings.exhaustEnabled=false;c.changed('exhaustEnabled');await c.step();assert.deepStrictEqual(h.sends[1],request('OEM'));
    });
    await test('Close without RPM stays under BMW control until a new manual choice', async () => {
        const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'CLOSED'});const c=h.controller;c.capabilities=live;await c.step();
        c.observeRPM(1200);await c.step();assert.deepStrictEqual(h.sends,[]);
        c.changed('exhaustBehaviour');await c.step();assert.deepStrictEqual(h.sends,[request('CLOSED')]);
    });
    await test('stale RPM releases Close and prevents automatic manual-Close resumption', async () => {
        const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'CLOSED'});const c=h.controller;c.capabilities=live;c.observeRPM(1200);await c.step();
        h.advance(5001);await c.step();assert.deepStrictEqual(h.sends[1],request('OEM'));
        c.observeRPM(1200);h.advance(1500);await c.step();assert.strictEqual(h.sends.length,2);
    });
    await test('RPM guard releases Close and uses hysteresis before resumption', async () => {
        const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'CLOSED'});const c=h.controller;c.capabilities=live;c.observeRPM(1200);await c.step();
        h.advance(1500);c.observeRPM(4100);await c.step();assert.deepStrictEqual(h.sends[1],request('OEM'));
        h.advance(1500);c.observeRPM(3800);await c.step();assert.strictEqual(h.sends.length,2);
        h.advance(1500);c.observeRPM(3400);await c.step();assert.deepStrictEqual(h.sends[2],request('CLOSED'));
    });
    await test('lost exhaust reply attempts OEM recovery instead of replaying Open', async () => {
        const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'OPEN'});const c=h.controller;c.capabilities=live;const send=c.send;
        c.send=async(v)=>{h.sends.push(v);throw new Error('reply lost');};await c.step();c.send=send;h.advance(1500);await c.step();
        assert.deepStrictEqual(h.sends,[request('OPEN'),request('OEM')]);h.advance(16000);await c.step();assert.strictEqual(h.sends.length,2);
    });
    await test('disable during an in-flight exhaust command serializes OEM recovery', async () => {
        const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'OPEN'});const c=h.controller;c.capabilities=live;let finish;
        c.send=async(v)=>{h.sends.push(v);if(h.sends.length===1)await new Promise((r)=>{finish=r;});return [0x6F,0x60,0xFD];};
        const first=c.step();h.settings.exhaustEnabled=false;c.changed('exhaustEnabled');const stop=c.stop();finish();await first;await stop;
        assert.deepStrictEqual(h.sends,[request('OPEN'),request('OEM')]);
    });
    await test('Hold repeats only while enabled, validated and under RPM limits', async () => {
        const h=harness(Exhaust,{exhaustEnabled:true,exhaustBehaviour:'OPEN',exhaustHold:true});const c=h.controller;c.capabilities=live;await c.step();
        h.advance(15000);await c.step();assert.strictEqual(h.sends.length,2);c.capabilities.available=false;h.advance(15000);await c.step();assert.strictEqual(h.sends.length,2);
    });
    await test('preferences reject invalid values and failed saves preserve the prior disk and memory state', async () => {
        const dir=fs.mkdtempSync(path.join(os.tmpdir(),'f40-enhancements-'));const file=path.join(dir,'settings.json');
        try {
            const defaults=prefs.sanitize(spec.settings,{lightingEnabled:'yes',exhaustEnabled:'true',colour_sport:99});
            assert.strictEqual(defaults.lightingEnabled,false);assert.strictEqual(defaults.exhaustEnabled,false);assert.strictEqual(defaults.colour_sport,0);
            const saved=prefs.commit(file,spec.settings,defaults,'colour_sport',2);const original=fs.readFileSync(file,'utf8');
            assert.throws(()=>prefs.commit(file,spec.settings,saved,'lightingEnabled','true'));assert.throws(()=>prefs.commit(file,spec.settings,saved,'unknown',true));
            fs.mkdirSync(file+'.tmp-'+process.pid);assert.throws(()=>prefs.commit(file,spec.settings,saved,'exhaustEnabled',true));
            assert.strictEqual(fs.readFileSync(file,'utf8'),original);assert.strictEqual(saved.exhaustEnabled,false);
        } finally { fs.readdirSync(dir).forEach((n)=>{const p=path.join(dir,n);if(fs.statSync(p).isDirectory())fs.rmdirSync(p);else fs.unlinkSync(p);});fs.rmdirSync(dir); }
    });
    console.log(passed + ' feature behaviour tests passed; no network or vehicle access.');
}
run().catch((e)=>{console.error(e.stack);process.exitCode=1;});
