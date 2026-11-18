'use strict';
// Photo-based reservations. They are not a complete, verified F40 factory ownership map.
const box={x:1400,y:340,w:230,h:90};
// F40 1920×720 native pixel proof: left [752,17,811,74], right [1110,17,1169,74].
// The boundaries include margins around the rendered pixels.
const turnIndicators=[{x:744,y:12,w:76,h:68},{x:1102,y:12,w:76,h:68}];
const holes=[box,{x:0,y:660,w:1920,h:60},{x:650,y:510,w:650,h:150}].concat(turnIndicators);
// Keep the complete round faces above the factory warning opening at y=510.
const mainDialSize=472;
const dials=[{side:'left',x:240,y:271,max:330,signal:'speed',w:688,h:688,sweep:234,displaySize:mainDialSize},
 {side:'right',x:960,y:271,max:8000,signal:'rpm',w:688,h:688,sweep:234,displaySize:mainDialSize}];
const minis=['oil','boost','water'].map((side,i)=>({side,x:[1440,1630,1820][i],y:140,radius:65,w:190,h:216,max:side==='boost'?25:180,signal:side,sweep:260,optional:true}));
function intersect(a,b){return a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h;}
function split(rect,reservations){let rs=[rect];reservations.forEach(h=>{const next=[];rs.forEach(r=>{const x=Math.max(r.x,h.x),y=Math.max(r.y,h.y),right=Math.min(r.x+r.w,h.x+h.w),bottom=Math.min(r.y+r.h,h.y+h.h);if(right<=x||bottom<=y){next.push(r);return;}[{x:r.x,y:r.y,w:r.w,h:y-r.y},{x:r.x,y:bottom,w:r.w,h:r.y+r.h-bottom},{x:r.x,y,w:x-r.x,h:bottom-y},{x:right,y,w:r.x+r.w-right,h:bottom-y}].forEach(q=>{if(q.w>0&&q.h>0)next.push(q);});});rs=next;});return rs;}
function bounds(d){
 const w=d.displaySize||d.w;
 const h=d.displaySize||d.h;
 return {x:d.x-w/2,y:d.y-h/2,w,h};
}
function pieces(d){return split(bounds(d),holes);}
module.exports={box,holes,turnIndicators,dials,minis,bounds,intersect,pieces,split};
