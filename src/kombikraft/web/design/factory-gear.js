/* Captured BMW M gear artwork. Layout/readout selection is custom preview logic. */
(function(root,factory){const api=factory(root);if(typeof module==='object'&&module.exports)module.exports=api;else root.FactoryGear=api;})(typeof globalThis!=='undefined'?globalThis:this,function(root){
 'use strict';
 const BASE='/design/factory-gear/assets/',supported=Object.freeze(['P','R','N','D','S',...Array.from({length:8},(_,i)=>'M'+(i+1))]);
 const state={available:false,error:null,sourceBitmapGlyphs:true,vehicleBindingVerified:false};let manifest=null,pending=null;const images={};
 function layout(value,config,glyphs){
  if(!supported.includes(value))return null;
  const {x,y,height}=config;if(![x,y,height].every(Number.isFinite)||height<=0)throw Error('Finite gear readout geometry required');
  const chars=Array.from(value),gap=height*.1,parts=chars.map(ch=>{const g=glyphs[ch];if(!g||g.width<=0||g.height<=0)throw Error('Captured gear glyph missing');return{glyph:ch,width:height*g.width/g.height,height};});
  const width=parts.reduce((n,p)=>n+p.width,0)+gap*(parts.length-1);let left=x-width/2;
  return{value,width,centerX:x,centerY:y,height,parts:parts.map(p=>{const out={...p,x:left,y:y-height/2};left+=p.width+gap;return out;})};
 }
 async function load(){
  if(pending)return pending;
  pending=(async()=>{try{
   const response=await root.fetch(BASE+'manifest.json');if(!response.ok)throw Error('Gear provenance unavailable');manifest=await response.json();
   if(manifest.schema!=='f40-source-gear-glyphs-v1'||manifest.extraction!=='Exact RGB red channel, vertical flip, tight ink crop; whiteRGB/Ralpha, no substitute font')throw Error('Unknown gear asset contract');
   await Promise.all(Object.entries(manifest.glyphs).map(([key,g])=>new Promise((resolve,reject)=>{const im=new root.Image();im.onload=()=>{if(im.naturalWidth!==g.width||im.naturalHeight!==g.height){reject(Error('Gear glyph dimensions differ'));return;}images[key]=im;resolve();};im.onerror=()=>reject(Error('Gear glyph unavailable: '+key));im.src=BASE+g.file;})));
   state.available=true;
  }catch(e){state.error=e.message;}return Object.assign({},state);})();return pending;
 }
 function render(c,value,config){
  if(!state.available)return false;const result=layout(value,config,manifest.glyphs);if(!result)return false;
  for(const p of result.parts)c.drawImage(images[p.glyph],p.x,p.y,p.width,p.height);return true;
 }
 return{load,render,layout,supported,status:()=>Object.assign({},state)};
});
