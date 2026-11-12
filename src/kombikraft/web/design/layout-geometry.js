(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ClusterLayoutGeometry=factory();})(typeof globalThis==='object'?globalThis:this,function(){
 'use strict';
 const round={left:{x:330,y:350,radius:264},right:{x:1590,y:350,radius:264},status:{x:0,y:624,width:1920,height:96},fuel:{x:150,y:651,width:360,height:44},gear:{x:1550,y:444,width:80,height:44},speedLimit:{x:41,y:637,width:78,height:78},branding:{x:1460,y:231,width:260,height:74}};
 const popup={x:650,y:520,width:650,height:200};
 const profiles={'round':round,'flat-base':{left:{x:330,y:375,radius:330},right:{x:1590,y:375,radius:330},clipY:624,reservedFooter:popup}};
 const touring={speed:{x:60,y:576,width:310,height:125},fuel:{x:150,y:651,width:360,height:44},tacho:{x:1340,y:567,width:420,height:90},gear:{x:375,y:609,width:60,height:32},mode:{x:354,y:663,width:102,height:24},speedLimit:{x:41,y:637,width:78,height:78}};
 const intersects=(a,b)=>a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;
 const dialBounds=d=>({x:d.x-d.radius,y:d.y-d.radius,width:d.radius*2,height:d.radius*2});
 function circleHitsBox(d,box,clipY=720){
  const bottom=Math.min(box.y+box.height,clipY);if(box.y>=bottom)return false;
  const x=Math.max(box.x,Math.min(d.x,box.x+box.width)),y=Math.max(box.y,Math.min(d.y,bottom));
  return (x-d.x)**2+(y-d.y)**2<d.radius**2;
 }
 function validate(profile='round'){
  const selected=profiles[profile];if(!selected)return {valid:false,errors:['Unknown dial profile']};
  const circles=[selected.left,selected.right],clipY=selected.clipY||720;
  const errors=[],dials=circles.map(d=>{const box=dialBounds(d);box.height=Math.min(box.height,clipY-box.y);return box;}),statusItems=[round.fuel,round.speedLimit];
  for(const dial of circles){if(circleHitsBox(dial,round.status,clipY))errors.push('Dial enters reserved status band');if(selected.reservedFooter!==popup&&circleHitsBox(dial,popup,clipY))errors.push('Popup covers dial');}
  for(const item of statusItems){if(item.y<round.status.y||item.y+item.height>720)errors.push('Status item outside reserved band');if(intersects(item,popup))errors.push('Popup covers status item');}
  for(let a=0;a<statusItems.length;a++)for(let b=a+1;b<statusItems.length;b++)if(intersects(statusItems[a],statusItems[b]))errors.push('Status items overlap');
  if(intersects(round.gear,popup))errors.push('Popup covers round gear');
  if(intersects(round.branding,popup))errors.push('Popup covers model badge');
  for(const item of Object.values(touring))if(intersects(item,popup))errors.push('Popup covers Map Touring instrument');
  for(const box of [...dials,...statusItems,round.branding,popup,...Object.values(touring)])if(box.x<0||box.y<0||box.x+box.width>1920||box.y+box.height>720)errors.push('Layout exceeds configured framebuffer');
  return {valid:!errors.length,errors,physicalF40MaskVerified:false,scope:'Preview geometry; rendered text/asset extents require visual checks'};
 }
 const visibleDialPoint=(profile,side,x,y)=>{const p=profiles[profile],d=p[side],hole=p.reservedFooter;return y<(p.clipY||720)&&(x-d.x)**2+(y-d.y)**2<d.radius**2&&!(hole&&x>=hole.x&&x<hole.x+hole.width&&y>=hole.y&&y<hole.y+hole.height);};
 return {round,profiles,touring,popup,intersects,dialBounds,circleHitsBox,visibleDialPoint,validate};
});
