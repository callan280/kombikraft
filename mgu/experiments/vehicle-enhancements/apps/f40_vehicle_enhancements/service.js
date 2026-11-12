'use strict';
const fs = require('fs');
const path = require('path');
const { Lighting } = require('./lighting');
const { Exhaust } = require('./exhaust');
const { Diag, replyTo } = require('./kit/diag');
const LIGHT = 'de.bmw.infotainment.misc.ComfortFunctionIuK';
const FES = 'de.bmw.infotainment.drivingexcitement.FES';
function rpmFromWire(raw) {
    // Captured BMW M Laptimer conversion / kit SCALE.rpm. No demo fallback.
    return Number.isInteger(raw) && raw >= 0 && raw < 65535 ? raw * 0.25 : null;
}
class FeatureService {
    constructor(ctx) {
        this.ctx = ctx; this.subs = []; this.pending = []; this.listeners = []; this.closed = false;
        this.diag = null; this.diagStart = null; this.diagWork = Promise.resolve(); this.lastProbe = -Infinity;
        this.lightSub = null; this.capabilities = null;
        let validation = null;
        try { validation = JSON.parse(fs.readFileSync(path.join(ctx.dataDir, 'exhaust-validation.json'), 'utf8')); }
        catch (e) { if (e.code !== 'ENOENT') ctx.log.warn('Exhaust validation unavailable: ' + e.message); }
        const get = (key) => ctx.settings.get(key);
        this.lighting = new Lighting({ get, send: (value) => {
            if (!this.lightSub || !this.lightSub.available) throw new Error('Lighting service unavailable');
            return ctx.signals.set(this.lightSub.proxy, 'ambientLightInteriorColour', value);
        }});
        this.exhaust = new Exhaust({ get, validation, send: (bytes) => this.uds(0x2F, bytes) });
        ctx.settings.onChange((key) => {
            if (/^(lighting|manualColour|colour_)/.test(key)) this.lighting.changed();
            this.exhaust.changed(key); this.tick();
        });
    }
    start() {
        const watch = (iface, handlers, options) => {
            const promise = this.ctx.signals.watch(iface, '1', handlers, this.ctx.log, options).then((sub) => {
                this.subs.push(sub); if (this.closed) return sub.shutdown().then(() => sub); return sub;
            });
            this.pending.push(promise); return promise;
        };
        watch(LIGHT, {statusAmbientLightInteriorColour: (value) => this.lighting.observeColour(value)}, {pollMs: 3000})
            .then((sub) => { this.lightSub = sub; }).catch((e) => this.ctx.log.warn('Lighting: ' + e.message));
        watch(FES, {statusFESVehicleDynamicSwitchHMI: (value) => {
            const mode = value && value.actualValueModeDrivingExperience;
            this.lighting.observeDrive(mode); this.exhaust.observeDrive(mode);
        }}, {pollMs: 3000}).catch((e) => this.ctx.log.warn('Drive mode: ' + e.message));
        watch('de.bmw.infotainment.vehicle.CDS', {statusEngineSpeed2: (value) => {
            this.exhaust.observeRPM(rpmFromWire(value && value.actualValueRPMEngineCrankshaft));
        }}, {pollMs: 2000}).catch((e) => this.ctx.log.warn('Engine speed: ' + e.message));
        this.timer = setInterval(() => this.tick(), 250); this.tick(); return this;
    }
    async initDiag() {
        if (this.diagStart) return this.diagStart;
        this.diagStart = new Diag(this.ctx.signals, this.ctx.log).init().then((diag) => {
            this.diag = diag;
            diag.on('available', () => { this.capabilities = null; this.lastProbe = -Infinity; });
            return diag;
        });
        return this.diagStart;
    }
    uds(sid, data) {
        const run = async () => {
            if (this.closed && !(sid === 0x2F && data.length === 3 && data[0] === 0x60 && data[1] === 0xFD && data[2] === 0)) {
                throw new Error('Enhancements are stopping');
            }
            const diag = await this.initDiag();
            if (!diag.available) throw new Error('DME diagnostic link unavailable');
            const answer = await diag.physical(0x12, sid, data, 2500, replyTo(sid, data), {maxRetries: 0, callTimeoutMs: 3000});
            if (!answer || answer[0] === 0x7F) throw new Error('DME response unavailable or rejected');
            return answer;
        };
        const next = this.diagWork.then(run, run); this.diagWork = next.catch(() => {}); return next;
    }
    async probeExhaust() {
        if (this.probing || this.closed) return;
        this.probing = true; this.lastProbe = Date.now();
        try {
            const vinReply = await this.uds(0x22, [0xF1, 0x90]);
            const indexReply = await this.uds(0x22, [0xF1, 0x50]);
            let electricFlap = false;
            for (const did of [[0x62,0xFD], [0x64,0xFD]]) {
                try { const value = await this.uds(0x22, did); if (value.length > 3) electricFlap = true; } catch (_) {}
            }
            const vin = Buffer.from(vinReply.slice(3)).toString('ascii').replace(/\0+$/, '');
            const sgbdIndex = indexReply.slice(3).map((n) => n.toString(16).toUpperCase().padStart(2, '0')).join('');
            this.capabilities = {vin, sgbdIndex, electricFlap, available: true};
        } catch (e) { this.capabilities = null; this.ctx.log.warn('Exhaust identification: ' + e.message); }
        finally { this.probing = false; }
    }
    tick() {
        if (this.closed) return;
        this.lighting.available = !!(this.lightSub && this.lightSub.available);
        this.exhaust.capabilities = this.capabilities && Object.assign({}, this.capabilities, {available: !!(this.diag && this.diag.available)});
        if (this.ctx.settings.get('exhaustEnabled') === true && !this.probing && !this.exhaust.ready() && Date.now() - this.lastProbe >= 30000) {
            this.probeExhaust().catch((e) => this.ctx.log.warn(e.message));
        }
        this.lighting.step(); this.exhaust.step();
        const view = this.view(); const digest = JSON.stringify(view);
        if (digest !== this.digest) { this.digest = digest; this.listeners.forEach((fn) => fn(view)); }
    }
    view() {
        return {lighting: this.lighting.message, exhaust: this.exhaust.message, exhaustReady: this.exhaust.ready(),
            exhaustEnabled: this.ctx.settings.get('exhaustEnabled') === true, confirmedExhaustPosition: this.exhaust.confirmed};
    }
    onChange(fn) { this.listeners.push(fn); fn(this.view()); }
    stop() {
        if (this.stopWork) return this.stopWork;
        this.closed = true; clearInterval(this.timer);
        this.stopWork = Promise.all([this.lighting.stop(), this.exhaust.stop()]).then(async () => {
            await Promise.all(this.pending.map((p) => p.catch(() => null)));
            await Promise.all(this.subs.map((sub) => sub.shutdown()));
            await this.diagWork;
            if (this.diag && this.diag.p) await this.diag.p.shutdown();
        });
        return this.stopWork;
    }
}
module.exports = { FeatureService, rpmFromWire };
