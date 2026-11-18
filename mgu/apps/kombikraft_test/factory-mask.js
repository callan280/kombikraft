'use strict';

const { holes, split } = require('./geometry');
const { trace, speedometerTrace, temperatureTrace, additionalReservations } = require('./mask-profile.json');

// Geometry is cut out ahead of time because transparent coverage over native
// fields can still cause a visual obstruction. Never claim the whole panel.
const reserves = holes.concat(additionalReservations);
const traces = [speedometerTrace, trace];
const pieces = traces.reduce((regions, polygon) => {
    const xs = polygon.map(point => point[0]), ys = polygon.map(point => point[1]);
    const x = Math.min(...xs), y = Math.min(...ys);
    return regions.concat(split({ x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y }, reserves));
}, []);

function edgeCalls(polygon) {
    return polygon.map((a, index) => {
        const b = polygon[(index + 1) % polygon.length];
        return `inside = edge(p, vec2(${a[0]}.0,${a[1]}.0), vec2(${b[0]}.0,${b[1]}.0)) != inside;`;
    }).join('\n        ');
}

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
    if (p.x < 960.0) {
        ${edgeCalls(speedometerTrace)}
    } else {
        ${edgeCalls(trace)}
    }
    if (!inside) discard;
    gl_FragColor = vec4(0.012,0.024,0.035,1.0);
}`;

const temperatureBounds=additionalReservations.find(r=>r.id==='temperature-gauge');
const temperatureShader=`
precision highp float;
varying vec2 v_uv;
uniform vec4 u_bounds;
uniform float u_show;
bool edge(vec2 p,vec2 a,vec2 b){
    if((a.y>p.y)==(b.y>p.y))return false;
    return p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x;
}
void main(){
    if(u_show<.5)discard;
    vec2 p=u_bounds.xy+v_uv*u_bounds.zw;
    bool inside=false;
    ${edgeCalls(temperatureTrace)}
    if(!inside)discard;
    gl_FragColor=vec4(.012,.024,.035,1.0);
}`;
module.exports = { pieces, reserves, shader, temperatureBounds, temperatureShader };
