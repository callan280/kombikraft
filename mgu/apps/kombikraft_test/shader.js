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
uniform vec4 u_needleRect;
uniform float u_valid;
uniform float u_shiftStage;
uniform vec3 u_modeTint;
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
vec4 shiftLights(vec4 face, vec2 p){
    if(u_shiftStage<0.0 || p.y>=0.0)return face;
    float radius=length(p);
    float angleFromTop=abs(degrees(atan(p.x,-p.y)));
    if(radius<111.0 || radius>130.0 || angleFromTop>=72.0)return face;
    float segment=floor(angleFromTop/18.0);
    float radial=smoothstep(111.0,113.0,radius)*(1.0-smoothstep(128.0,130.0,radius));
    float along=mod(angleFromTop,18.0);
    float edge=smoothstep(1.0,2.0,along)*(1.0-smoothstep(16.0,17.0,along));
    float order=4.0-segment;
    vec3 tint=order<=2.0?vec3(1.,.57,.10):vec3(1.,.12,.08);
    bool lit=u_shiftStage>=order;
    vec3 ink=lit?tint:vec3(.17,.18,.20);
    face.rgb=mix(face.rgb,ink,radial*edge);
    return face;
}
void main(){vec2 p=v_uv*u_size+u_origin-u_center;
 vec2 uv=(p+u_textureSize*.5)/u_textureSize;
 vec4 face=texture2D(u_face,uv);
 // Only recolour the saturated centre-ring material. Keep the scale,
 // original needle and the mini temperature bands in their source colours.
 float redInk=smoothstep(.02,.14,face.r-max(face.g,face.b));
 float ring=smoothstep(.12,.21,length(p)/u_textureSize.x)*(1.-smoothstep(.425,.454,length(p)/u_textureSize.x));
 if (dot(u_modeTint,u_modeTint)>0.0) {
     face.rgb=mix(face.rgb, vec3(min(face.g,face.b)) + face.r*u_modeTint, redInk*ring);
 }
 face=shiftLights(face,p);
 float a=radians(angle());float c=cos(a),s=sin(a);
 vec2 n=vec2(c*p.x+s*p.y,-s*p.x+c*p.y);
 vec2 nuv=(n+u_textureSize*.5-u_needleRect.xy)/u_needleRect.zw;
 vec4 nd=texture2D(u_needle,nuv);nd.a*=u_valid;
 if(any(lessThan(nuv,vec2(0.0)))||any(greaterThan(nuv,vec2(1.0))))nd=vec4(0.0);
 float alpha=nd.a+face.a*(1.-nd.a);vec3 color=(nd.rgb*nd.a+face.rgb*face.a*(1.-nd.a))/max(alpha,.0001);if(u_valid<.5&&abs(p.x)<8.&&abs(p.y)<1.){color=vec3(.7);alpha=1.;}gl_FragColor=vec4(color,alpha);
}`;
