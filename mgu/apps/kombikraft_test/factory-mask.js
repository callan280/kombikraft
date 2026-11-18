'use strict';

const { holes, split } = require('./geometry');
const { trace, additionalReservations } = require('./mask-profile.json');

// Geometry is cut out ahead of time because transparent coverage over native
// fields can still cause a visual obstruction. Never claim the whole panel.
const reserves = holes.concat(additionalReservations);
const x = Math.min(...trace.map(point => point[0]));
const y = Math.min(...trace.map(point => point[1]));
const width = Math.max(...trace.map(point => point[0])) - x;
const height = Math.max(...trace.map(point => point[1])) - y;
const pieces = split({ x, y, w: width, h: height }, reserves);

const edgeCalls = trace.map((a, index) => {
    const b = trace[(index + 1) % trace.length];
    return `inside = edge(p, vec2(${a[0]}.0,${a[1]}.0), vec2(${b[0]}.0,${b[1]}.0)) != inside;`;
}).join('\n    ');

const shader = `
precision highp float;
varying vec2 v_uv;
uniform vec4 u_bounds;

bool edge(vec2 p, vec2 a, vec2 b) {
    if ((a.y > p.y) == (b.y > p.y)) return false;
    return p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x;
}

void main() {
    vec2 p = u_bounds.xy + v_uv * u_bounds.zw;
    bool inside = false;
    ${edgeCalls}
    if (!inside) discard;
    gl_FragColor = vec4(0.012,0.024,0.035,1.0);
}`;

module.exports = { pieces, reserves, shader };
