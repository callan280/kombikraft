'use strict';
// Normal OAP lifecycle routing. Only declared entry UUIDs can open their mapped app state.
function createEntryRouter(options) {
    const ui = options.ui, log = options.log, routes = {}, mapped = {}, opening = {};
    const sleep = options.sleep || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
    (options.entryPoints || []).forEach((entry) => {
        if (!entry.uuid || routes[entry.uuid]) throw new Error('Missing or duplicate app entry UUID');
        const declared = (options.routes || {})[entry.uuid];
        const name = declared ? declared.stateName : options.mainName;
        const state = ui.comp(name);
        if (!state) throw new Error('Entry route references missing state: ' + name);
        routes[entry.uuid] = { name, state };
    });
    function map(uuid) {
        if (!routes[uuid]) return Promise.reject(new Error('Unknown app entry UUID'));
        if (mapped[uuid]) return Promise.resolve();
        return Promise.resolve().then(() => ui.rhmi.mapEntryState(uuid, routes[uuid].state))
            .then(() => { mapped[uuid] = true; log.info('mapped entry ' + uuid + ' -> ' + routes[uuid].name); });
    }
    function open(uuid, tries) {
        if (!routes[uuid]) { log.error('Unknown app entry UUID: ' + uuid); return Promise.resolve(false); }
        if (opening[uuid]) return opening[uuid];
        const route = routes[uuid];
        async function attempt() {
            for (let left = Math.max(1, Math.min(6, tries || 1)); left > 0; left--) {
                try {
                    await map(uuid);
                    if (route.state.updateResources) await route.state.updateResources();
                    await ui.rhmi.openEntryState(uuid);
                    ui._setVisible(route.name, true);
                    return true;
                } catch (e) {
                    if (left > 1 && /INVALID/.test(String(e && e.message || e))) await sleep(800);
                    else { log.error('open entry state', e); return false; }
                }
            }
            return false;
        }
        opening[uuid] = attempt().then((result) => { delete opening[uuid]; return result; }, (error) => { delete opening[uuid]; throw error; });
        return opening[uuid];
    }
    return { open, mapAll: () => Promise.all(Object.keys(routes).map((uuid) => map(uuid).catch((e) => log.error('map entry state', e)))) };
}
module.exports = { createEntryRouter };
