'use strict';
const { driveMode } = require('./lighting');
const PROFILE = 'bmw-mg1-el-agk-v1';
function validationMatches(record, live) {
    return !!(record && record.schemaVersion === 1 && record.profile === PROFILE && record.parkedTestPassed === true &&
        typeof record.vin === 'string' && /^[A-HJ-NPR-Z0-9]{17}$/.test(record.vin) &&
        typeof record.sgbdIndex === 'string' && /^[0-9A-F]{6}$/.test(record.sgbdIndex) &&
        live && live.available && live.electricFlap && live.vin === record.vin && live.sgbdIndex === record.sgbdIndex);
}
function request(mode) {
    if (mode === 'OEM') return [0x60, 0xFD, 0x00];
    if (mode === 'OPEN') return [0x60, 0xFD, 0x03, 0x03, 0xE8];
    if (mode === 'CLOSED') return [0x60, 0xFD, 0x03, 0x23, 0x28];
    throw new Error('Unknown exhaust mode');
}
class Exhaust {
    constructor(o) {
        this.get = o.get; this.send = o.send; this.validation = o.validation || null; this.now = o.now || Date.now;
        this.delay = o.delay || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
        this.capabilities = null; this.drive = null; this.driveAt = -Infinity; this.rpm = null; this.rpmAt = -Infinity;
        this.last = 'OEM'; this.owns = false; this.lastSend = -Infinity; this.revision = 0; this.lastKey = null;
        this.message = 'Off'; this.accepted = null; this.confirmed = 'UNKNOWN'; this.flight = null; this.stopping = false;
        this.closeLatched = false; this.highRpmPaused = false;
    }
    changed(key) { if (/^exhaust/.test(key)) { this.revision++; this.closeLatched = false; this.faulted = false; } }
    observeRPM(value) {
        if (typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 8500) {
            this.rpm = value; this.rpmAt = this.now();
        } else { this.rpm = null; this.rpmAt = -Infinity; }
    }
    observeDrive(raw) { this.drive = driveMode(raw); this.driveAt = this.now(); }
    ready() { return validationMatches(this.validation, this.capabilities); }
    step() {
        if (this.flight) return this.flight;
        this.flight = this._step().then(() => { this.flight = null; }, (e) => {
            this.accepted = false; this.message = 'Not applied: ' + e.message; this.flight = null;
        });
        return this.flight;
    }
    async _step() {
        const enabled = !this.stopping && this.get('exhaustEnabled') === true;
        let desired = enabled ? this.get('exhaustBehaviour') : 'OEM';
        const automatic = desired === 'DRIVE';
        if (automatic) desired = this.drive && this.now() - this.driveAt <= 10000 ? this.get('exhaust_' + this.drive) : 'OEM';
        if (this.faulted) desired = 'OEM';
        if (['OEM', 'OPEN', 'CLOSED'].indexOf(desired) < 0) { this.message = 'Invalid exhaust preference'; return; }
        if (!enabled && !this.owns) { this.message = 'Off'; return; }
        // No probe response alone enables actuation: an exact VIN + DME validation record is required.
        // Returning a previously owned override is still attempted if identity discovery drops out.
        if (!this.ready() && !(desired === 'OEM' && this.owns)) { this.message = 'Parked VIN/DME validation required'; return; }
        let guard = '';
        if (desired === 'CLOSED') {
            const fresh = this.rpm !== null && this.now() - this.rpmAt <= 5000;
            if (!fresh && !automatic) this.closeLatched = true;
            if (fresh && this.rpm > 4000) this.highRpmPaused = true;
            if (fresh && this.rpm < 3500) this.highRpmPaused = false;
            if (!fresh || this.closeLatched || this.highRpmPaused) {
                guard = !fresh ? 'Live RPM unavailable' : this.closeLatched ? 'Reselect Close after RPM loss' : 'RPM guard active';
                desired = 'OEM';
            }
        }
        const key = this.revision + ':' + (automatic ? this.drive : 'manual') + ':' + desired;
        const hold = enabled && this.get('exhaustHold') === true && desired !== 'OEM';
        const repeat = hold && this.now() - this.lastSend >= 15000;
        if (desired === 'OEM' && !this.owns) { this.message = guard || (enabled ? 'BMW control' : 'Off'); this.lastKey = key; return; }
        if (this.lastKey === key && !repeat) { if (guard) this.message = guard; return; }
        if (this.now() - this.lastSend < 1000) return;
        this.lastSend = this.now();
        // A lost reply can follow a real actuation. Remember possible ownership before sending.
        if (desired !== 'OEM') this.owns = true;
        let reply;
        try { reply = await this.send(request(desired)); }
        catch (e) { this.faulted = true; throw e; }
        // Only an exact positive echo of this DID is treated as accepted, never physical position confirmation.
        const accepted = Array.isArray(reply) && reply[0] === 0x6F && reply[1] === 0x60 && reply[2] === 0xFD;
        if (!accepted) { this.faulted = true; throw new Error('DME did not accept the flap request'); }
        this.accepted = true; this.last = desired; this.lastKey = key; this.owns = desired !== 'OEM';
        this.message = guard || (desired === 'OEM' ? 'BMW control requested' : desired + ' accepted; physical position unconfirmed');
    }
    async stop() {
        this.stopping = true; if (this.flight) await this.flight;
        if (this.owns) await this.delay(Math.max(0, 1000 - (this.now() - this.lastSend)));
        await this.step();
    }
}
module.exports = { Exhaust, validationMatches, request, PROFILE };
