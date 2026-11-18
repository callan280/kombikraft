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
uniform float u_arcRotation;
uniform float u_artPerPixel;
uniform vec2 u_textureSize;
uniform vec4 u_needleRect;
uniform float u_valid;
#ifdef MINI_GAUGE
uniform float u_visible;
#endif
#ifdef F40_DIGITAL_SPEED
uniform sampler2D u_speedArt;
uniform float u_speed;
vec4 digitalSpeed(vec2 p){
 float speed=floor(clamp(u_speed,0.0,330.0)+.5);
 float digits=speed>=100.0?3.0:speed>=10.0?2.0:1.0;
 vec2 pixel=vec2(p.x,p.y-62.0)/.78;
 if(pixel.y>=0.0&&pixel.y<108.0){
  float x=pixel.x+42.0*digits;
  float column=floor(x/84.0);
  if(column>=0.0&&column<digits){
   float digit=mod(floor(speed/pow(10.0,digits-column-1.0)),10.0);
   return texture2D(u_speedArt,vec2(digit*96.0+6.0+mod(x,84.0),pixel.y)/vec2(1056.0,108.0));
  }
 }
 vec2 unit=vec2(p.x+30.0,p.y-143.0);
 if(all(greaterThanEqual(unit,vec2(0.0)))&&all(lessThan(unit,vec2(60.0,28.0))))
  return texture2D(u_speedArt,(vec2(963.0,68.0)+unit)/vec2(1056.0,108.0));
 return vec4(0.0);
}
#endif
#ifdef F97_SHIFT_LIGHTS
uniform float u_shiftStage;
uniform float u_arcSweep;
uniform sampler2D u_shiftArt;
uniform vec4 u_shiftMap;
uniform vec2 u_shiftAtlasSize;
uniform sampler2D u_roundExtras;
uniform vec2 u_gearGlyphs;
vec4 gearReadout(vec2 p){
 if(u_gearGlyphs.x<0.0)return vec4(0.0);
 vec2 cell=vec2(p.x/.92+(u_gearGlyphs.y<0.0?32.0:62.0),(p.y-62.0)/.92);
 float index=u_gearGlyphs.x;
 if(cell.x>=62.0&&u_gearGlyphs.y>=0.0){cell.x-=62.0;index=u_gearGlyphs.y;}
 if(any(lessThan(cell,vec2(0.0)))||any(greaterThanEqual(cell,vec2(64.0))))return vec4(0.0);
 return texture2D(u_roundExtras,(cell+vec2(index*64.0,0.0))/vec2(896.0,116.0));
}
#endif
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
#ifdef F97_SHIFT_LIGHTS
vec4 shiftLights(vec4 face,vec2 p){
 vec2 mapPixel=floor(p-u_shiftMap.xy);
 if(any(lessThan(mapPixel,vec2(0.0)))||any(greaterThanEqual(mapPixel,u_shiftMap.zw)))return face;
 vec4 surface=texture2D(u_shiftArt,(mapPixel+.5)/u_shiftAtlasSize);
 if(surface.a<=0.0)return face;
 float arc=(surface.r*65280.0+surface.g*255.0)/65535.0;
 float column=clamp(arc*130.0-.5,0.0,129.0);
 float row=u_shiftMap.w+u_shiftStage-.5;
 vec4 a=texture2D(u_shiftArt,vec2(floor(column)+.5,row)/u_shiftAtlasSize);
 vec4 b=texture2D(u_shiftArt,vec2(min(129.0,floor(column)+1.0)+.5,row)/u_shiftAtlasSize);
 vec4 segment=mix(a,b,fract(column));
 vec3 lit=min(vec3(1.0),segment.rgb+1.5*surface.b);
 face.rgb=mix(face.rgb,lit,segment.a*surface.a);
 return face;
}
#endif
void main(){
#ifdef MINI_GAUGE
 if(u_visible<.5)discard;
#endif
 vec2 p=(v_uv*u_size+u_origin-u_center)*u_artPerPixel;
 vec2 uv=(p+u_textureSize*.5)/u_textureSize;
 vec4 face=texture2D(u_face,uv);
 // Only recolour the saturated centre-ring material. Keep the scale,
 // original needle and the mini temperature bands in their source colours.
 if (dot(u_modeTint,u_modeTint)>0.0) {
     float redInk=smoothstep(.02,.14,face.r-max(face.g,face.b));
     float radial=length(p)/u_textureSize.x;
     float ring=smoothstep(.12,.21,radial)*(1.-smoothstep(.425,.454,radial));
     face.rgb=mix(face.rgb, vec3(min(face.g,face.b)) + face.r*u_modeTint, redInk*ring);
 }
#ifdef F97_SHIFT_LIGHTS
 if(u_shiftStage>=1.0){
  float arc=mod(degrees(atan(p.y,p.x))-(180.0+u_arcRotation)+720.0,360.0);
  float sourceArc=arc<=u_arcSweep?arc*234.0/u_arcSweep:234.0+(arc-u_arcSweep)*126.0/(360.0-u_arcSweep);
  float r=radians(180.0+sourceArc);
  vec2 shiftPoint=vec2(cos(r),sin(r))*length(p);
  face=shiftLights(face,shiftPoint);
 }
 vec4 gear=gearReadout(p);
 face.rgb=mix(face.rgb,gear.rgb,gear.a);
#endif
#ifdef F40_DIGITAL_SPEED
 if(u_valid>.5){
  vec4 reading=digitalSpeed(p);
  face.rgb=mix(face.rgb,reading.rgb,reading.a);
 }
#endif
 float a=radians(angle()+u_arcRotation);float c=cos(a),s=sin(a);
 vec2 n=vec2(c*p.x+s*p.y,-s*p.x+c*p.y);
 vec2 nuv=(n+u_textureSize*.5-u_needleRect.xy)/u_needleRect.zw;
 vec4 nd=texture2D(u_needle,nuv);nd.a*=u_valid;
 if(any(lessThan(nuv,vec2(0.0)))||any(greaterThan(nuv,vec2(1.0))))nd=vec4(0.0);
 float alpha=nd.a+face.a*(1.-nd.a);vec3 color=(nd.rgb*nd.a+face.rgb*face.a*(1.-nd.a))/max(alpha,.0001);if(u_valid<.5&&abs(p.x)<8.&&abs(p.y)<1.){color=vec3(.7);alpha=1.;}gl_FragColor=vec4(color,alpha);
}`;
