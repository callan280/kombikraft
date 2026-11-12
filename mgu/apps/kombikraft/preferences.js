'use strict';
// SPDX-License-Identifier: MIT
const fs = require('fs');
const path = require('path');
class Preferences {
    constructor(schema, directory) {
        this.schema = schema;
        this.file = path.join(directory, 'kombikraft-preferences.json');
        this.serial = 0;
        this.values = {};
        schema.forEach((item) => { this.values[item.key] = item.default; });
        try {
            const stat = fs.statSync(this.file);
            if (stat.size > 16384) throw new Error('Preferences exceed size limit');
            const record = JSON.parse(fs.readFileSync(this.file, 'utf8'));
            if (record.schema !== 1 || !record.preferences || Array.isArray(record.preferences)) throw new Error('Unsupported preferences schema');
            const saved = record.preferences;
            schema.forEach((item) => {
                if (!item.blocked && this.valid(item, saved[item.key])) this.values[item.key] = saved[item.key];
            });
        } catch (error) { this.loadError = error.code === 'ENOENT' ? null : error.message; }
    }
    valid(item, value) {
        return item.type === 'bool' ? typeof value === 'boolean'
            : item.options.some((option) => option[0] === value);
    }
    get(key) { return this.values[key]; }
    set(key, value) {
        const item = this.schema.find((candidate) => candidate.key === key);
        if (!item || !this.valid(item, value)) throw new Error('Invalid preference');
        if (item.blocked && value !== false) return {stored: false, vehicleApplied: false, reason: item.blocked};
        const previous = this.values[key];
        this.values[key] = value;
        try { this.save(); } catch (error) { this.values[key] = previous; throw error; }
        return {stored: true, vehicleApplied: false};
    }
    save() {
        const temporary = this.file + '.tmp-' + process.pid + '-' + (++this.serial);
        let created = false;
        try {
            fs.writeFileSync(temporary, JSON.stringify({schema: 1, preferences: this.values}, null, 2), {mode: 384, flag: 'wx'});
            created = true;
            fs.renameSync(temporary, this.file);
        } catch (error) {
            if (created) { try { fs.unlinkSync(temporary); } catch (_) {} }
            throw error;
        }
    }
    reset() {
        const previous = Object.assign({}, this.values);
        this.schema.forEach((item) => { this.values[item.key] = item.default; });
        try { this.save(); } catch (error) { this.values = previous; throw error; }
    }
    snapshot() { return Object.assign({}, this.values); }
}
module.exports = {Preferences};
