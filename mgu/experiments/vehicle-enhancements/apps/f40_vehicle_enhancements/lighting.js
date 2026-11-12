'use strict';
// Our feature policy. The wire contract is retained in evidence/factory-feature-interfaces.json.
const UNFILLED = 'SIGNAL_UNBEFUELLT';
const MODE = { SPORT_DYNAMIC: 'sport', SPORT_EXPERT: 'sport', SPORT_INDIVIDUAL: 'sport',
    COMFORT: 'comfort', COMFORT_PLUS: 'comfort', COMFORT_INDIVIDUAL: 'comfort',
    ECO_PRO_EFFICIENT: 'eco', ECO_PRO_PLUS: 'eco', ECO_PRO_INDIVIDUAL: 'eco', ADAPTIVE: 'comfort' };
function driveMode(raw) {
    if (MODE[raw]) return MODE[raw];
    const n = Number(raw);
    return n >= 1 && n <= 3 ? 'sport' : n >= 4 && n <= 6 || n === 10 ? 'comfort' : n >= 7 && n <= 9 ? 'eco' : null;
}
function slotOf(raw) {
    const match = /^FARBAUSWAHL_(\d+)$/.exec(String(raw));
    const n = match ? Number(match[1]) : typeof raw === 'number' ? raw : NaN;
    return Number.isInteger(n) && n >= 1 && n <= 12 ? n : null;
}
function colourRequest(slot) {
    if (!Number.isInteger(slot) || slot < 1 || slot > 12) throw new Error('Unsupported preset');
    return { controlMenuAmbientePanoramicRoofInteriorLighting: 'FARBAUSWAHL_' + slot,
        controlHueInteriorLighting: 4095, controlHueValueLayer1IndividualGroup: 255,
        controlHueValueLayer2IndividualGroup: 255, controlHueValueLayer3IndividualGroup: 255,
        controlBrightnessValueBrightnessOffsetAmbientePanoramicRoofInteriorLighting: 255,
        controlModeAmbientePanoramicRoofInteriorLighting: UNFILLED,
        controlDynamicInteriorLighting: UNFILLED, controlDynamicAmbienteInteriorLighting: UNFILLED };
}
class Lighting {
    constructor(o) {
        this.get = o.get; this.send = o.send; this.now = o.now || Date.now;
        this.delay = o.delay || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
        this.current = null; this.received = -Infinity; this.drive = null; this.driveAt = -Infinity;
        this.own = null; this.applied = null; this.owns = false; this.revision = 0;
        this.lastKey = null; this.lastSend = -Infinity; this.available = false;
        this.message = 'Off'; this.flight = null; this.stopping = false;
    }
    observeColour(value) {
        const slot = slotOf(value && value.statusMenuAmbientePanoramicRoofInteriorLighting);
        // Unknown/individual modes cannot be restored faithfully by the preset-only adapter.
        this.current = slot; this.received = this.now();
        if (this.owns && slot === this.applied) this.awaiting = false;
        if (this.owns && this.awaiting && slot === this.own) return;
        if (slot !== null && (!this.owns || slot !== this.applied)) {
            this.own = slot;
            if (this.owns && this.applied !== slot) this.owns = false;
        }
    }
    observeDrive(raw) {
        this.drive = driveMode(raw); this.driveAt = this.now();
    }
    changed() { this.revision++; }
    step() {
        if (this.flight) return this.flight;
        this.flight = this._step().then(() => { this.flight = null; }, (e) => {
            this.message = 'Not applied: ' + e.message; this.flight = null;
        });
        return this.flight;
    }
    async _step() {
        const enabled = !this.stopping && this.get('lightingEnabled') === true;
        const fresh = this.available && this.now() - this.received <= 10000 && this.current !== null;
        let target, key;
        if (!enabled) {
            this.message = 'Off';
            if (!this.owns) return;
            if (!fresh) { this.message = 'Off; previous colour restoration pending'; return; }
            if (this.current !== this.applied && !this.awaiting) { this.owns = false; return; }
            target = this.own; key = 'restore:' + this.revision;
        } else {
            if (!fresh) { this.message = 'Waiting for a supported live colour preset'; return; }
            const manual = this.get('lightingBehaviour') === 'manual';
            if (!manual && (!this.drive || this.now() - this.driveAt > 10000)) {
                this.message = 'Waiting for driving mode'; return;
            }
            target = this.get(manual ? 'manualColour' : 'colour_' + this.drive);
            key = this.revision + ':' + (manual ? 'manual' : this.drive);
            if (target === 0) { this.message = 'Leave current colour unchanged'; return; }
            if (!Number.isInteger(target) || target < 1 || target > 12) { this.message = 'Invalid colour preference'; return; }
            if (this.lastKey === key) return; // Driver's later factory-menu choice wins until next mode/settings change.
        }
        if (target === this.current && (enabled || !this.awaiting)) { this.lastKey = key; if (!enabled) this.owns = false; this.message = enabled ? 'Colour ' + target + ' reported by car' : 'Off; previous colour restored'; return; }
        if (this.now() - this.lastSend < 1500) return;
        const previous = this.current;
        this.lastSend = this.now();
        // If the setter acts but its reply is lost, disabling still attempts restoration.
        if (enabled) { if (!this.owns) this.own = previous; this.applied = target; this.owns = true; this.awaiting = true; }
        await this.send(colourRequest(target));
        if (!enabled) this.owns = false;
        this.lastKey = key;
        this.message = enabled ? 'Colour ' + target + ' requested; awaiting car status' : 'Off; previous colour requested';
    }
    async stop() {
        this.stopping = true; if (this.flight) await this.flight;
        if (this.owns) await this.delay(Math.max(0, 1500 - (this.now() - this.lastSend)));
        await this.step();
    }
}
module.exports = { Lighting, driveMode, slotOf, colourRequest };
