'use strict';
// Photo-based reservations. They are not a complete, verified F40 factory ownership map.
const box={x:1400,y:340,w:230,h:90};
const holes=[box,{x:0,y:660,w:1920,h:60},{x:650,y:510,w:650,h:150}];
const dials=[{side:'left',x:344,y:344,radius:343,max:330,signal:'speed',w:688,h:688,sweep:234},
 {side:'right',x:1032,y:344,radius:343,max:8000,signal:'rpm',w:688,h:688,sweep:234}];
const minis=['oil','boost','water'].map((side,i)=>({side,x:[1440,1630,1820][i],y:140,radius:65,w:190,h:216,max:side==='boost'?25:180,signal:side,sweep:260,optional:true}));
function intersect(a,b){return a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h;}
function split(rect,reservations){let rs=[rect];reservations.forEach(h=>{const next=[];rs.forEach(r=>{const x=Math.max(r.x,h.x),y=Math.max(r.y,h.y),right=Math.min(r.x+r.w,h.x+h.w),bottom=Math.min(r.y+r.h,h.y+h.h);if(right<=x||bottom<=y){next.push(r);return;}[{x:r.x,y:r.y,w:r.w,h:y-r.y},{x:r.x,y:bottom,w:r.w,h:r.y+r.h-bottom},{x:r.x,y,w:x-r.x,h:bottom-y},{x:right,y,w:r.x+r.w-right,h:bottom-y}].forEach(q=>{if(q.w>0&&q.h>0)next.push(q);});});rs=next;});return rs;}
function pieces(d){const r={x:d.x-d.w/2,y:Math.max(0,d.y-d.h/2),w:d.w,h:d.optional?d.h:660};return split(r,holes);}
module.exports={box,holes,dials,minis,intersect,pieces,split};
