'use strict';

// The upstream diagnostic wrapper serializes requests and permits read services only.
// These profiles are fixed to the engine ECU and current pressure reads.
const { ReadOnlyDiag } = require('./kit/readonly-diag');
const { DidReader } = require('./kit/dids');
const { pressureBoost } = require('./inputs');
const BARO = [
    { did:'F433', bytes:1, factor:1, min:55, max:115, timeoutMs:750 },
    { obd:'33', bytes:1, factor:1, min:55, max:115, timeoutMs:750 }
];
const ACTUAL = [
    { did:'580B', bytes:2, factor:1/256, min:20, max:400, timeoutMs:750 },
    { did:'F470', bytes:2, at:3, factor:1/32, min:20, max:600, timeoutMs:750 }
];

function enginePressure(signals, log, clock, enabled, onSample) {
    let link, reader, busy = false, lastAsk = -Infinity, nextBaro = 0, ambient = null;
    async function poll() {
        if (busy || !enabled() || clock() - lastAsk < 1000) return;
        busy = true;
        lastAsk = clock();
        try {
            if (!reader) {
                if (!link) link = new ReadOnlyDiag(signals, log, { gapMs:50, silentAfter:5 });
                await link.init();
                if (!link.ready) return;
                reader = new DidReader(link, { ecu:0x12 });
            }
            if (!enabled()) return;
            if (clock() >= nextBaro) {
                const baro = await reader.value('baro',BARO);
                if (!enabled()) return;
                ambient = Number.isFinite(baro) ? baro : null;
                nextBaro = clock() + (ambient === null ? 10000 : 60000);
            }
            if (!enabled() || ambient === null) return;
            const actual = await reader.value('actual',ACTUAL);
            if (enabled()) onSample(pressureBoost(actual, ambient, clock()));
        } catch (error) {
            log.warn('Engine pressure read unavailable: ' + String(error.message || error));
        } finally {
            busy = false;
        }
    }
    return { poll };
}

module.exports = { enginePressure };
