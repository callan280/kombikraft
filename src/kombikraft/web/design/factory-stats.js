/* Original BMW IC text fields/raster components in the custom centre space.
 * Values are explicit samples. No value is calculated from RPM or vehicle speed.
 * The dynamic consumption chart remains unregistered until its renderer is proved.
 */
(function(root){
 'use strict';
 const BASE='/design/factory-stats/assets/';
 const SOURCE='dbd3f7ca836c3c749f02206d2390f756f05e4230e1cc930cd9a719c655c9fd6f';
 const common=Object.freeze({scope:'instrument-cluster',layoutVerified:true,sourceSha256:SOURCE,reusedComponents:true,
  provenanceUrl:BASE+'provenance.json',customComposition:true,nativeControllerBound:false,
  f40AvailabilityVerified:false,nativePhysicalBcBound:false,nativeLayoutEngineExecuted:false,
  sampleTelemetry:true,valuesDerivedFromRpm:false,nativePixelVerified:false});
 const proofs={
  journey:Object.freeze(Object.assign({},common,{detail:'Captured LT_Table_IC_DriveInfoWidget47415 fields, source font/baseline/gap values, original masterline raster; sample icons explicitly invisible.',widgetType:47415,iconsVisible:false})),
  gforce:Object.freeze(Object.assign({},common,{detail:'Captured LT_Label_IC_Gforce46590 plus original scale_Kombi424px texture and original dot/shadow channel shader; neutral sample in a custom composition.',widgetType:47426,neutralOnly:true})),
  consumption:Object.freeze({registered:false,reason:'Original dynamic Figure_Graphic/consumption_history renderer unresolved; no invented chart or bars.'})
 };
 const state={loaded:false,registered:[],error:null};
 function load(name){return new Promise((resolve,reject)=>{
  if(typeof root.Image!=='function'){reject(new Error('Browser image surface unavailable'));return;}
  const image=new root.Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('Factory stats asset unavailable: '+name));image.src=BASE+name;
 });}
 function safeText(c,helpers,value,x,y,size,color,align){
  if(typeof c.fillText==='function'&&typeof c.save==='function'){
   c.save();c.font=`${size}px BMWTA,sans-serif`;c.fillStyle=color;c.textAlign=align||'left';
   c.textBaseline='alphabetic';c.fillText(String(value),x,y);c.restore();
  }else if(helpers&&typeof helpers.text==='function')helpers.text(c,String(value),x,y,size,color,align||'left');
 }
 function journeyRenderer(images){return function(c,helpers,context,snapshot){
  if(!c||typeof c.drawImage!=='function')return false;
  const t=(value,x,y,size,color,align)=>safeText(c,helpers,value,x,y,size,color,align);
  // Captured350×304 content group is reused at its original scale. Only its
  // placement in the custom centre changes; footer/road-name space is outside.
  const left=785,top=175;
  c.drawImage(images['journey-background.png'],781,160,358,345);
  t('Total',left,top+41,22,'#ababab');
  t('12,345',left+119+9,top+41,25,'#ffffff');
  t('km',left+119+9+94+9,top+41,22,'#ababab');
  c.drawImage(images['journey-masterline.png'],left,top+46+12,329,4);
  const body=top+46+12+5,x=left+82;
  t('Data since',x,body+43,26,'#ababab');
  t('Individual',x,body+43+42,32,'#ffffff');
  // Exact native Distance and AVGSpeed number/unit fields; source icon flags
  // are explicitly false in this sample. No substitute icon is painted.
  function valueUnit(value,unit,y){
   t(value,x,y,38,'#ffffff');
   // Native Preferred width comes from the actual shaped text, followed by
   // the captured unitGapW_ID7=9. Do not assume an invented digit width.
   if(typeof c.measureText==='function'){
    c.save();c.font='38px BMWTA,sans-serif';const width=c.measureText(value).width;c.restore();
    t(unit,x+width+9,y,29,'#ababab');
   }
  }
  valueUnit('42.6','km',body+43+50+42);
  valueUnit('52.4','km/h',body+43+50+50+42);

  return true;
 };}
 function gforceRenderer(images){return function(c,helpers){
  if(!c||typeof c.drawImage!=='function')return false;
  const cx=960,cy=314,size=240,scale=size/424;
  c.drawImage(images['gforce-kombi-ring.png'],cx-size/2,cy-size/2,size,size);
  c.drawImage(images['gforce-dot-shadow.png'],cx-50*scale,cy-50*scale,100*scale,100*scale);
  c.drawImage(images['gforce-dot.png'],cx-16*scale,cy-16*scale,32*scale,32*scale);
  safeText(c,helpers,'0.0',936,250,24,'#ababab','right');safeText(c,helpers,'g',945,250,24,'#ababab');
  safeText(c,helpers,'0.0',936,385,24,'#ababab','right');safeText(c,helpers,'g',945,385,24,'#ababab');
  return true;
 };}
 const names=['journey-background.png','journey-masterline.png','gforce-background.png','gforce-kombi-ring.png','gforce-dot.png','gforce-dot-shadow.png'];
 const api={proofs,status:()=>Object.assign({},state,{registered:state.registered.slice(),consumption:proofs.consumption}),journeyRenderer,gforceRenderer};
 api.ready=Promise.all(names.map(name=>load(name).then(image=>[name,image])))
  .then(pairs=>{
   const images=Object.fromEntries(pairs);
   if((images['gforce-kombi-ring.png'].naturalWidth||images['gforce-kombi-ring.png'].width)!==424)throw new Error('Original Kombi scale dimensions differ from proof');
   if(!root.ClusterBcContent||typeof root.ClusterBcContent.registerFactoryWidget!=='function')throw new Error('Factory BC registration surface unavailable');
   state.loaded=true;
   root.ClusterBcContent.registerFactoryWidget('journey',{proof:proofs.journey,render:journeyRenderer(images)});state.registered.push('journey');
   root.ClusterBcContent.registerFactoryWidget('g-force',{proof:proofs.gforce,render:gforceRenderer(images)});state.registered.push('g-force');return true;
  }).catch(error=>{state.error=error.message;return false;});
 root.ClusterFactoryStats=api;if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
