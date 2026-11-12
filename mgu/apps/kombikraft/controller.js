'use strict';
// SPDX-License-Identifier: MIT
function createController(options) {
    const spec = options.spec, ui = options.ui, preferences = options.preferences;
    const status = options.status || function () {};
    const component = (key) => 'PREF_' + key.toUpperCase();
    function refresh() {
        return Promise.all(spec.settings.map((item) => {
            if (item.type === 'bool') return ui.checked(component(item.key), preferences.get(item.key));
            return ui.selected(component(item.key), item.options.findIndex((o) => o[0] === preferences.get(item.key)));
        }));
    }
    spec.settings.forEach((item) => {
        ui.onClick(component(item.key), (event) => {
            let value;
            if (item.type === 'bool') value = !preferences.get(item.key);
            else {
                const row = event && event.row;
                if (!Number.isInteger(row) || row < 0 || row >= item.options.length) return;
                value = item.options[row][0];
            }
            let result;
            try { result = preferences.set(item.key, value); }
            catch (error) {
                status('Preference could not be saved. Vehicle output is inactive.');
                return refresh().then(() => { throw error; });
            }
            status(result.stored ? 'Preference saved. Vehicle output is inactive.' : result.reason);
            return refresh();
        });
    });
    ['CLUSTER', 'HUD', 'FEATURES', 'ABOUT'].forEach((name) => ui.onClick('OPEN_' + name, () => ui.open(name)));
    ui.onClick('RESET', () => {
        try { preferences.reset(); }
        catch (error) { return refresh().then(() => { throw error; }); }
        status('Preferences reset. Vehicle output is inactive.'); return refresh();
    });
    return {refresh, capabilities: {
        nativeClusterReplacement: false, factoryWarningOwnership: false,
        hudOutput: false, vehicleActuation: false, preferenceStorage: true
    }};
}
module.exports = {createController};
