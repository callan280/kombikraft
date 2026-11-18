'use strict';
// Photo-based reservations. They are not a complete, verified F40 factory ownership map.
const box={x:1400,y:340,w:230,h:90};
// F40 1920×720 native pixel proof: left [752,17,811,74], right [1110,17,1169,74].
// The boundaries include margins around the rendered pixels.
const turnIndicators=[{x:744,y:12,w:76,h:68},{x:1102,y:12,w:76,h:68}];
// The DSC warning photo places the banner near y=600. Keep clearance above it.
const centreWarning={x:650,y:574,w:650,h:86};
const holes=[box,{x:0,y:660,w:1920,h:60},centreWarning].concat(turnIndicators);
const dials=[{side:'left',x:344,y:430,displaySize:700,max:330,signal:'speed',w:688,h:688,sweep:200,arcRotation:34},
 {side:'right',x:1054,y:430,displaySize:700,max:8000,signal:'rpm',w:688,h:688,sweep:200,arcRotation:0}];
// Place boost halfway between the temperature dials, in the strip between
// the photo-based black box and parking lamp reservations.
const [speedometer,tachometer]=dials;
const speedRimCutout=[
 speedometer.x+tachometer.x-centreWarning.x-centreWarning.w,centreWarning.y,
 speedometer.x+tachometer.x-centreWarning.x,centreWarning.y+centreWarning.h
];
const minis=[{side:'oil',x:1535,y:144},{side:'boost',x:1725,y:345,displayWidth:216},{side:'water',x:1535,y:545}]
 .map(d=>({displayWidth:247,...d,radius:65*(d.displayWidth||247)/190,w:190,h:216,max:d.side==='boost'?25:180,
  signal:d.side,sweep:260,optional:true,
  artBounds:{left:d.side==='boost'?13:23,top:20,right:d.side==='boost'?188:190,bottom:196}}));
function scale(d){return (d.displayWidth||d.displaySize||d.w)/d.w;}
function intersect(a,b){return a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h;}
function split(rect,reservations){let rs=[rect];reservations.forEach(h=>{const next=[];rs.forEach(r=>{const x=Math.max(r.x,h.x),y=Math.max(r.y,h.y),right=Math.min(r.x+r.w,h.x+h.w),bottom=Math.min(r.y+r.h,h.y+h.h);if(right<=x||bottom<=y){next.push(r);return;}[{x:r.x,y:r.y,w:r.w,h:y-r.y},{x:r.x,y:bottom,w:r.w,h:r.y+r.h-bottom},{x:r.x,y,w:x-r.x,h:bottom-y},{x:right,y,w:r.x+r.w-right,h:bottom-y}].forEach(q=>{if(q.w>0&&q.h>0)next.push(q);});});rs=next;});return rs;}
function bounds(d){
 const art=d.artBounds||{left:0,top:0,right:d.w,bottom:d.h};
 const factor=scale(d);
 const x=Math.max(0,Math.floor(d.x+(art.left-d.w/2)*factor));
 const y=Math.max(0,Math.floor(d.y+(art.top-d.h/2)*factor));
 const right=Math.min(1920,Math.ceil(d.x+(art.right-d.w/2)*factor));
 const bottom=Math.min(660,Math.ceil(d.y+(art.bottom-d.h/2)*factor));
 return {x,y,w:right-x,h:bottom-y};
}
function pieces(d){return split(bounds(d),holes);}
module.exports={box,holes,centreWarning,turnIndicators,speedRimCutout,dials,minis,scale,bounds,intersect,pieces,split};
