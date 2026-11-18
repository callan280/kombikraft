'use strict';
// Original texture composition; path interpolation follows aidac/apps MIT e36 maths.
module.exports=`
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
varying vec2 v_uv;
uniform vec2 u_size;
uniform vec2 u_origin;
uniform vec2 u_center;
uniform vec2 u_textureSize;
uniform float u_valid;
uniform sampler2D u_face;
uniform sampler2D u_needle;
uniform vec4 u_times;
uniform vec4 u_angles;
uniform highp float u_time;
float angle(){float s=u_time-u_times.x;s-=3600.0*floor((s+1800.0)/3600.0);
 if(s<-.25)return u_angles.x;
 if(s<u_times.y)return mix(u_angles.x,u_angles.y,s/max(u_times.y,.0001));
 if(s<u_times.z)return mix(u_angles.y,u_angles.z,(s-u_times.y)/max(u_times.z-u_times.y,.0001));
 return mix(u_angles.z,u_angles.w,min(1.0,(s-u_times.z)/max(u_times.w-u_times.z,.0001)));}
void main(){vec2 p=v_uv*u_size+u_origin-u_center;
 vec2 uv=(p+u_textureSize*.5)/u_textureSize;
 vec4 face=texture2D(u_face,uv);
 float a=radians(angle());float c=cos(a),s=sin(a);
 vec2 n=vec2(c*p.x+s*p.y,-s*p.x+c*p.y);
 vec2 nuv=(n+u_textureSize*.5)/u_textureSize;
 vec4 nd=texture2D(u_needle,nuv);nd.a*=u_valid;
 if(any(lessThan(nuv,vec2(0.0)))||any(greaterThan(nuv,vec2(1.0))))nd=vec4(0.0);
 float alpha=nd.a+face.a*(1.-nd.a);vec3 color=(nd.rgb*nd.a+face.rgb*face.a*(1.-nd.a))/max(alpha,.0001);if(u_valid<.5&&abs(p.x)<8.&&abs(p.y)<1.){color=vec3(.7);alpha=1.;}gl_FragColor=vec4(color,alpha);
}`;
