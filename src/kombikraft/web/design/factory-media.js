/* Captured BMW IC cover component plus a reused BMW cover-background mask.
 * Composition positions and sample metadata belong to this custom lab layout.
 * The shared mask is not claimed to be the F40 factory IC media configuration.
 */
(function(root){
 'use strict';
 const BASE='/design/factory-media/assets/';
 const proof=Object.freeze({
  scope:'instrument-cluster',layoutVerified:true,reusedComponents:true,
  sourceSha256:'dbd3f7ca836c3c749f02206d2390f756f05e4230e1cc930cd9a719c655c9fd6f',
  detail:'Captured IC cover wrapper plus BMW coverbackground mask reused in custom layout',
  provenanceUrl:BASE+'provenance.json',nativeControllerBound:false,
  f40AvailabilityVerified:false,factoryIcMaskLinkVerified:false,
  sampleArtwork:true,sampleArtworkProvenanceUrl:BASE+'sample-media-provenance.json',factoryMissingArtFallbackVerified:false,
  decorationNativePixelVerified:false,
  maskEquation:'maskValue=mix(texMask.r,1.0-texMask.a,0.0); alpha=artAlpha*maskValue*opacity*scrollFade',
  maskExport:'red-mask.png A equals the original Cover_BG_Mask RGB red channel; no generated gradient.',
  typography:'Custom 0.75 scale of captured icFontSize44 and icFontSizeLabelSecondary36; inherited BMW font helper.'
 });
 const state={registered:false,loaded:false,error:null};
 const metadata={title:'Demon Days',artist:'Gorillaz'};
 const timeline=root.ClusterMediaMarquee?.createTimeline();
 function observeVisibility(visibility,now){
  if(timeline)timeline.observe({active:visibility.active,paused:visibility.paused,key:metadata.title+'\n'+metadata.artist},now);
 }
 function image(name){return new Promise((resolve,reject)=>{
  if(typeof root.Image!=='function'){reject(new Error('Browser image surface unavailable'));return;}
  const value=new root.Image();value.onload=()=>resolve(value);
  value.onerror=()=>reject(new Error('Factory media asset unavailable: '+name));value.src=BASE+name;
 });}
 function canvas(width,height){
  if(root.document&&typeof root.document.createElement==='function'){
   const value=root.document.createElement('canvas');value.width=width;value.height=height;return value;
  }
  if(typeof root.OffscreenCanvas==='function')return new root.OffscreenCanvas(width,height);
  return null;
 }
 function backdrop(art,mask){
  const target=canvas(854,720);if(!target)return null;
  const c=target.getContext('2d');if(!c||typeof c.drawImage!=='function')return null;
  const width=art.naturalWidth||art.width,height=art.naturalHeight||art.height;
  const aspect=854/720;let sw=width,sh=height;
  if(sw/sh>aspect)sw=sh*aspect;else sh=sw/aspect;
  c.drawImage(art,(width-sw)/2,(height-sh)/2,sw,sh,0,0,854,720);
  // Exact source-mask pixels, oriented from the native bottom-origin UV space
  // into the browser's top-origin custom composition. No fade stops are chosen.
  c.globalCompositeOperation='destination-in';c.save();c.translate(0,720);c.scale(1,-1);
  c.drawImage(mask,0,0,854,720);c.restore();c.globalCompositeOperation='source-over';
  return target;
 }
 function renderer(art,frame,background){return function render(c,helpers,context,snapshot){
  if(!c||typeof c.drawImage!=='function')return false;
  c.save();
  c.drawImage(background,740,180,440,266);
  c.drawImage(frame,740,200,236,236);
  c.drawImage(art,755.3,215.3,205.4,205.4);
  if(helpers&&typeof helpers.text==='function'){
   for(const [value,y,size,color] of [[metadata.title,276,30,'#ffffff'],[metadata.artist,321,25,'#ababab']]){
    c.save();c.beginPath();c.rect(990,y-22,185,44);c.clip();
    c.font=`${size}px BMWTA,sans-serif`;
    const width=c.measureText(value).width;
    const dx=root.ClusterMediaMarquee?root.ClusterMediaMarquee.offset(timeline?.elapsed()||0,width,185):0;
    helpers.text(c,value,990+dx,y,size,color);c.restore();
   }
  }
  c.restore();
  return true;
 };}
 const api={proof,status:()=>Object.assign({},state),renderer,observeVisibility};
 api.ready=Promise.all([image('sample-gorillaz-demon-days.png'),image('cover-frame-138.png'),image('red-mask.png')])
  .then(([art,frame,mask])=>{
   if((art.naturalWidth||art.width)!==1000||(art.naturalHeight||art.height)!==1000||
      (frame.naturalWidth||frame.width)!==154||(frame.naturalHeight||frame.height)!==154||
      (mask.naturalWidth||mask.width)!==854||(mask.naturalHeight||mask.height)!==720)throw new Error('Factory media asset dimensions differ from source proof');
   const background=backdrop(art,mask);if(!background)throw new Error('Factory media canvas surface unavailable');
   state.loaded=true;
   if(!root.ClusterBcContent||typeof root.ClusterBcContent.registerFactoryWidget!=='function')throw new Error('Factory BC registration surface unavailable');
   root.ClusterBcContent.registerFactoryWidget('media',{proof,render:renderer(art,frame,background)});
   state.registered=true;return true;
  }).catch(error=>{state.error=error.message;return false;});
 root.ClusterFactoryMedia=api;
 if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
