'use strict';
/**
 * signals.js - read live vehicle signals over SOME/IP.
 *
 * Interface configs come from the app's own oap_<uid>/someipInterfaces/,
 * which the installer generates from the app's manifest.json with BMW's own
 * generator (kit/tools/oapgen) against the unit's master catalog
 * /etc/oap/someip/someip-interfaces.json - exactly what MainApp does when it
 * installs an app. So any interface/field listed in app.json "signals" is
 * reachable, not just the trimmed MainApp subset.
 *
 *   const sub = await signals.watch('de.bmw.infotainment.vehicle.CDS', '1', {
 *       statusEngineSpeed2: (v) => rpm = v.actualValueRPMEngineCrankshaft,
 *   });
 *   sub.available  // true once the provider (the car) answers
 */
const fs = require('fs');
const path = require('path');

let someip = null;
try { someip = require('someip'); } catch (e) { /* host preview / not installed */ }

const APP_ROOT = path.resolve(__dirname, '..', '..', '..');
const DIRS = [path.join(APP_ROOT, 'someipInterfaces'), path.join(__dirname, '..', '..', 'someipdefs')];

// The native binding deadlocks (main thread stuck on a futex) when buildProxy/
// init run inline inside the app's promise chains next to the SDK's own SOME/IP
// traffic. The SDK always calls them from a fresh setImmediate tick, one at a
// time - do the same.
let chain = Promise.resolve();
function nativeTick(fn) {
    const run = () => new Promise((resolve, reject) => setImmediate(() => { try { Promise.resolve(fn()).then(resolve, reject); } catch (e) { reject(e); } }));
    const p = chain.then(run, run);
    chain = p.catch(() => {});
    return p;
}

function loadConfig(iface) {
    const f = iface.replace(/\./g, '_') + '.json';
    for (const d of DIRS) {
        try { return JSON.parse(fs.readFileSync(path.join(d, f), 'utf8')); } catch (e) { /* next */ }
    }
    throw new Error('no SOME/IP config for ' + iface + ' (add it to app.json "signals")');
}

/**
 * Build a proxy and subscribe to fields. handlers = { fieldName: fn(value) }.
 * Also does an initial getValue() for fields that have a getter, so values
 * show up without waiting for the next change.
 * opts.pollMs: also re-read those fields that often while the provider is available - for
 * fields a car may not notify (BMW's x_call only ever reads TPMS, it never subscribes).
 */
async function watch(iface, instance, handlers, log, opts) {
    const res = { iface, available: false, proxy: null, error: null, shutdown: () => Promise.resolve() };
    if (!someip) { res.error = 'someip native module not available'; return res; }
    try {
        const cfg = loadConfig(iface);
        const p = await nativeTick(() => someip.buildProxy(cfg, String(instance)).then((px) => px.init().then(() => px)));
        res.proxy = p;
        const fields = Object.keys(handlers || {});
        let epoch = 0, sequence = 0, timer = null, fastTimer = null;
        const fast = opts && opts.fastPoll;
        let fastReadPending = false, lastFastEvent = -Infinity;
        const latest = Object.create(null);
        res.shutdown = () => {
            clearInterval(timer);
            clearInterval(fastTimer);
            res.available = false;
            epoch++;
            return Promise.resolve().then(() => p.shutdown && p.shutdown()).catch(() => {});
        };
        const deliver = (field, value, generation, order) => {
            if (opts && opts.ordered && (!res.available || epoch !== generation || order <= (latest[field] || 0))) return;
            latest[field] = order;
            handlers[field](value);
        };
        const fetchField = f => {
            if (!cfg.fields || !cfg.fields[f] || !cfg.fields[f].getter) return;
            const isFastField = fast && fast.field === f;
            if (isFastField && fastReadPending) return;
            if (isFastField) fastReadPending = true;
            const generation = epoch, order = ++sequence;
            p.getValue(f, 3000).then(v => deliver(f, v, generation, order)).catch(() => {}).then(() => {
                if (isFastField) fastReadPending = false;
            });
        };
        const fetchAll = () => fields.forEach(fetchField);
        await nativeTick(() => {
            try { return p.subscribeToAvailability((a) => { if (res.available !== !!a) epoch++; res.available = !!a; if (!a && opts && opts.onUnavailable) opts.onUnavailable(); if (a) setImmediate(fetchAll); }); } catch (e) { return null; /* older binding */ }
        });
        for (const f of fields) {
            try {
                await nativeTick(() => p.subscribe({ name: f, onReceive: (v) => { try {
                    if (fast && f === fast.field) lastFastEvent = Date.now();
                    deliver(f,v,epoch,++sequence);
                } catch (e) { if (log) log.warn(iface + '.' + f + ': ' + e); } } }));
            } catch (e) {
                if (log) log.warn('subscribe ' + iface + '.' + f + ': ' + e);
            }
        }
        if (p.isAvailable && p.isAvailable()) { res.available = true; fetchAll(); }
        if (fast) fastTimer = setInterval(() => {
            if (res.available && fast.active() && Date.now() - lastFastEvent >= fast.ms) fetchField(fast.field);
        }, fast.ms);
        if (opts && opts.pollMs) timer = setInterval(() => { if (res.available) setImmediate(fetchAll); }, opts.pollMs);
    } catch (e) {
        res.error = String(e);
        if (log) log.warn('signals ' + iface + ': ' + e);
    }
    return res;
}

/** Call a method on an interface instance (e.g. UDS over InternalTasu). */
async function proxy(iface, instance) {
    if (!someip) throw new Error('someip native module not available');
    const cfg = loadConfig(iface);
    return nativeTick(() => someip.buildProxy(cfg, String(instance)).then((p) => p.init().then(() => p)));
}

/** Call a method on a proxy from proxy(); params = the method's argument struct. */
function call(p, method, params, timeoutMs) {
    return nativeTick(() => p.callMethod(method, params || {}, timeoutMs || 5000));
}

/**
 * Write a field that has a setter (e.g. ConditionBasedServicesLegacy.cBSReset) on a proxy from
 * proxy() or watch().proxy, as BMW's SDK does (_someIpProxy.setValue). value = the field's struct;
 * resolves when the provider took it. Needs "w" in the field's app.json flags, or the installer
 * leaves the setter out of the app's interface config.
 */
function set(p, field, value, timeoutMs) {
    return nativeTick(() => p.setValue(field, value, timeoutMs || 5000));
}

/** Subscribe to a broadcast/event or field on a proxy from proxy(). */
function on(p, name, fn, log) {
    return nativeTick(() => p.subscribe({ name, onReceive: (v) => { try { fn(v); } catch (e) { if (log) log.warn(name + ': ' + e); } } }));
}

/** Availability of a proxy's provider; fn(bool) on every change. */
function onAvailable(p, fn) {
    return nativeTick(() => { try { return p.subscribeToAvailability((a) => fn(!!a)); } catch (e) { return null; } })
        .then(() => { if (p.isAvailable && p.isAvailable()) fn(true); });
}

module.exports = { watch, proxy, call, set, on, onAvailable, loadConfig, hasNative: () => !!someip };
