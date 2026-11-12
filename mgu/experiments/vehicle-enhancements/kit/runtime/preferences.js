'use strict';
const fs = require('fs');
function valid(item, value) {
    if (item.type === 'bool') return typeof value === 'boolean';
    if (item.type === 'choice') return item.options.some((option) => option[0] === value);
    if (item.type === 'number') return (item.steps || []).indexOf(value) >= 0;
    return false;
}
function sanitize(schema, saved) {
    const values = {};
    schema.forEach((item) => { values[item.key] = saved && valid(item, saved[item.key]) ? saved[item.key] : item.default; });
    return values;
}
function commit(file, schema, current, key, value) {
    const item = schema.find((candidate) => candidate.key === key);
    if (!item || !valid(item, value)) throw new Error('Invalid preference: ' + key);
    const next = Object.assign({}, current, {[key]: value});
    const tmp = file + '.tmp-' + process.pid;
    try { fs.writeFileSync(tmp, JSON.stringify(next, null, 1), {mode: 0o600}); fs.renameSync(tmp, file); }
    catch (error) { try { fs.unlinkSync(tmp); } catch (_) {} throw error; }
    return next;
}
module.exports = { valid, sanitize, commit };
