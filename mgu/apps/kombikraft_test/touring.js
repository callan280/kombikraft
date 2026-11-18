'use strict';

const speedShader = `
precision highp float;
varying vec2 v_uv;
uniform sampler2D u_art;
uniform float u_speed;

void main() {
    vec2 pixel = v_uv * vec2(325.0, 108.0);
    float speed = floor(clamp(u_speed, 0.0, 330.0) + .5);
    float digits = speed >= 100.0 ? 3.0 : speed >= 10.0 ? 2.0 : 1.0;
    if (pixel.x >= 240.0) {
        gl_FragColor = texture2D(u_art, vec2((960.0 + pixel.x - 240.0) / 1056.0, v_uv.y));
        return;
    }
    float left = 234.0 - digits * 78.0;
    float column = floor((pixel.x - left) / 78.0);
    if (column < 0.0 || column >= digits) {
        gl_FragColor = vec4(0.0);
        return;
    }
    float divisor = pow(10.0, digits - column - 1.0);
    float digit = mod(floor(speed / divisor), 10.0);
    float offset = mod(pixel.x - left, 78.0) + 9.0;
    gl_FragColor = texture2D(u_art, vec2((digit * 96.0 + offset) / 1056.0, v_uv.y));
}`;

const rpmShader = `
precision highp float;
varying vec2 v_uv;
uniform sampler2D u_art;
uniform highp float u_time;
uniform vec4 u_times;
uniform vec4 u_angles;

float progress() {
    float t = u_time - u_times.x;
    t -= 3600.0 * floor((t + 1800.0) / 3600.0);
    if (t < -.25) return u_angles.x;
    if (t < u_times.y) return mix(u_angles.x, u_angles.y, t / max(u_times.y, .0001));
    if (t < u_times.z) return mix(u_angles.y, u_angles.z, (t-u_times.y) / max(u_times.z-u_times.y, .0001));
    return mix(u_angles.z, u_angles.w, min(1.0, (t-u_times.z) / max(u_times.w-u_times.z, .0001)));
}

vec4 frame(float index) {
    vec2 offset = vec2(mod(index, 4.0), floor(index / 4.0));
    vec2 pixel = clamp(v_uv * vec2(470.0, 100.0), vec2(.5), vec2(469.5, 99.5));
    return texture2D(u_art, (offset * vec2(470.0,100.0) + pixel) / vec2(1880.0,300.0));
}

void main() {
    float index = clamp(progress(), 0.0, 10.0);
    vec4 a = frame(floor(index));
    vec4 b = frame(min(10.0, ceil(index)));
    float mixBy = fract(index);
    float alpha = mix(a.a, b.a, mixBy);
    gl_FragColor = vec4(mix(a.rgb*a.a, b.rgb*b.a, mixBy) / max(alpha, .0001), alpha);
}`;

const instruments = [
    { x: 58, y: 535, w: 325, h: 108, image: 'touring-speed.rgba',
        textureW: 1056, textureH: 108, signal: 'speed', max: 330, shader: speedShader },
    { x: 1310, y: 545, w: 470, h: 100, image: 'touring-rpm.rgba',
        textureW: 1880, textureH: 300, signal: 'rpm', max: 8000, sweep: 10, shader: rpmShader }
];

module.exports = { instruments };
