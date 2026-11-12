/* Central content design fixtures. Source-backed families, not decoded factory pages. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClusterBcContent=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const bounds=Object.freeze({x:700,y:160,width:520,height:345});
 const baselineOffset=185;
 const displayBounds=Object.freeze({x:740,y:365,width:440,height:255});
 const pages=Object.freeze([
  Object.freeze({id:'journey',label:'Journey data',sourceCandidate:'stats'}),
  Object.freeze({id:'consumption',label:'Consumption',sourceCandidate:'consumption'}),
  Object.freeze({id:'media',label:'Media',sourceCandidate:'media',albumArtIsOwnPage:false}),
  Object.freeze({id:'power-torque',label:'Sport displays',sourceCandidate:'sport-instruments'}),
  Object.freeze({id:'g-force',label:'G-force',sourceCandidate:'g-force'}),
  Object.freeze({id:'blank',label:'Blank centre',sourceCandidate:null,blank:true})
 ]);
 const evidence=Object.freeze({candidateFile:'cluster-theme-research-20261111/menu-bc/content-pages/page-candidates.json',inputContract:'cluster-theme-research-20261111/menu-bc/bc-input-contract.json',nativePhysicalBcBindingVerified:false,f40AvailabilityVerified:false,nativePageOrderVerified:false,nativeControllerBound:false,vehicleValues:'Explicit mock values and normalized graphics inputs; never derived from RPM.',albumArtSeparateNativePageVerified:false});
 const renderers=new Map();
 function registerFactoryWidget(id,entry){
  if(!pages.some(p=>p.id===id)||!entry||typeof entry.render!=='function'||entry.proof?.scope!=='instrument-cluster'||entry.proof?.layoutVerified!==true||!/^([a-f0-9]{64})$/.test(entry.proof?.sourceSha256||''))throw new Error('A source-pinned factory instrument-cluster layout is required');
  renderers.set(id,entry);
 }
 function initial(){return {index:0,seen:[]};}
 function eligible(context){
  context=context||{};
  if(context.theme!=='m-round')return 'round-theme-required';
  if(context.mapVisible!==false)return 'map-visible';
  if(context.popup)return 'popup-has-input-priority';
  if(context.resetActive)return 'reset-has-input-priority';
  return null;
 }
 function reduce(state,event,context){
  const unchanged=reason=>({state,changed:false,reason,page:pages[state.index]});
  if(!event||event.source!=='emulator')return unchanged('normalized-emulator-input-required');
  if(event.factoryHandled!==false)return unchanged('factory-ownership');
  if(event.gesture!=='short')return unchanged('short-press-required');
  if(event.reset===true||event.resetRequested===true)return unchanged('reset-has-input-priority');
  if(event.context!=='normal-display'||event.safeToCycle!==true)return unchanged('context-not-admitted');
  if(typeof event.id!=='string'||!event.id.trim()||event.id.length>160)return unchanged('event-id-required');
  const blocked=eligible(context);if(blocked)return unchanged(blocked);
  if(state.seen.includes(event.id))return unchanged('duplicate-event');
  const next={index:(state.index+1)%pages.length,seen:state.seen.concat(event.id).slice(-64)};
  return {state:next,changed:true,reason:'preview-content-cycled',page:pages[next.index]};
 }
 function create(){
  let state=initial();
  function handle(event,context){const result=reduce(state,event,context);state=result.state;return Object.assign({},result,{state:{index:state.index,seen:state.seen.slice()}});}
  function status(context){return {page:pages[state.index],index:state.index,count:pages.length,available:!eligible(context),blockedReason:eligible(context),previewFixture:true,availabilityAndOrderVerified:false,nativeControllerBound:false,factoryGraphicsReady:pages[state.index].blank===true||renderers.has(pages[state.index].id),blank:pages[state.index].blank===true,description:pages[state.index].blank?'Centre BC content hidden.':renderers.has(pages[state.index].id)?(renderers.get(pages[state.index].id).proof.reusedComponents?'BMW factory components in a custom composition.':'Captured factory widget layout; F40 availability and BC order unverified.'):'Factory widget graphics pending; no invented replacement.'};}
  function render(c,helpers,context,snapshot,accent){
   if(!context||context.theme!=='m-round'||context.mapVisible!==false)return false;
   if(context.popup)return false;
   if(pages[state.index].blank)return true;
   const {text}=helpers;
   c.save();c.beginPath();c.rect(displayBounds.x,displayBounds.y,displayBounds.width,displayBounds.height);c.clip();c.translate(0,baselineOffset);
   const page=pages[state.index],factory=renderers.get(page.id);
   const rendered=factory&&factory.render(c,helpers,context,snapshot,accent)!==false;
   if(!rendered){
    text(c,page.label,960,263,27,'#e3e7ec','center');
    text(c,'Factory widget reconstruction pending',960,321,21,'#94a0ad','center');
    text(c,'No substitute graphic is displayed',960,357,18,'#77838f','center');
   }
   c.restore();return true;
  }
  return {handle,render,status};
 }
 const preview=create();return {pages,bounds,displayBounds,baselineOffset,evidence,initial,reduce,create,registerFactoryWidget,handle:preview.handle,render:preview.render,status:preview.status};
});
