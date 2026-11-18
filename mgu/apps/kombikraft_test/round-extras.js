'use strict';

const badgeBounds={x:538,y:80,w:322,h:91};
const badgeShader=`
precision mediump float;
varying vec2 v_uv;
uniform sampler2D u_roundExtras;
void main(){gl_FragColor=texture2D(u_roundExtras,(vec2(0.0,64.0)+v_uv*vec2(184.0,52.0))/vec2(896.0,116.0));}
`;

// Only the measured gear window is eligible for footer coverage. It returns
// to the factory immediately if the replacement gear signal is unavailable.
const factoryGearBounds={x:1367,y:655,w:63,h:47};
const factoryGearShader=`
precision mediump float;
uniform float u_show;
void main(){if(u_show<.5)discard;gl_FragColor=vec4(.012,.024,.035,1.0);}
`;
module.exports={badgeBounds,badgeShader,factoryGearBounds,factoryGearShader};
