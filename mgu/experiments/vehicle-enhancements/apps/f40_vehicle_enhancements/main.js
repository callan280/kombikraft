'use strict';
const mgu = require('./kit/mgu');
const { FeatureService } = require('./service');
let service = null;
mgu.run({
    background(ctx) { service = new FeatureService(ctx).start(); return service; },
    start(ctx) {
        const current = ctx.background || service;
        if (!current) { ctx.ui.text('LIGHT_STATUS', 'Enhancements unavailable'); return; }
        current.onChange((status) => {
            ctx.ui.text('LIGHT_STATUS', 'Lighting: ' + status.lighting);
            ctx.ui.text('EXHAUST_STATUS', 'Exhaust: ' + status.exhaust);
            ['BTN_OPEN','BTN_CLOSE','BTN_OEM'].forEach((id) => ctx.ui.enabled(id, status.exhaustReady && status.exhaustEnabled));
        });
        ctx.ui.onClick('BTN_ALL_OFF', () => {
            ctx.settings.set('lightingEnabled', false); ctx.settings.set('exhaustEnabled', false);
        });
        [['BTN_OPEN','OPEN'],['BTN_CLOSE','CLOSED'],['BTN_OEM','OEM']].forEach((pair) => {
            ctx.ui.onClick(pair[0], () => {
                if (current.exhaust.ready() && ctx.settings.get('exhaustEnabled') === true) ctx.settings.set('exhaustBehaviour', pair[1]);
            });
        });
    },
    stop() { return service ? service.stop() : Promise.resolve(); }
});
