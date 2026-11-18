'use strict';

const bounds = { x:78, y:617, w:285, h:28 };
const shader = `
precision mediump float;
varying vec2 v_uv;
uniform float u_level;

void main() {
    vec2 p = v_uv * vec2(285.0,28.0);
    vec3 ink = vec3(.80,.84,.88);
    if (p.x < 28.0) {
        bool pump = p.x > 4.0 && p.x < 17.0 && p.y > 4.0 && p.y < 24.0;
        bool glass = p.x > 7.0 && p.x < 14.0 && p.y > 7.0 && p.y < 14.0;
        bool hose = (p.x >= 17.0 && p.x < 22.0 && p.y > 14.0 && p.y < 17.0) ||
                    (p.x >= 21.0 && p.x < 24.0 && p.y > 9.0 && p.y < 19.0);
        if ((!pump || glass) && !hose) discard;
        gl_FragColor = vec4(ink,1.0);
        return;
    }
    float x = p.x - 34.0;
    if (x < 0.0 || x >= 246.0) discard;
    float cell = floor(x / 25.0);
    bool middle = p.y >= 9.0 && p.y <= 21.0 && mod(x,25.0) < 21.0;
    bool tick = p.y >= 3.0 && p.y <= 7.0 &&
      (abs(x-1.0)<1.0 || abs(x-123.0)<1.0 || abs(x-244.0)<1.0);
    if(u_level < 0.0 && p.y > 13.0 && p.y < 16.0 && abs(x-123.0)<5.0){
        gl_FragColor=vec4(ink,1.0);
        return;
    }
    if (!middle && !tick) discard;
    bool lit = u_level >= 0.0 && cell < ceil(u_level * 10.0);
    gl_FragColor = vec4(tick ? ink : lit ? (cell == 0.0 ? vec3(.94,.22,.20) : ink) : vec3(.19,.21,.24),1.0);
}`;

module.exports = { bounds, shader };
