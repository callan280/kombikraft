/* Original supplier output in a custom layout; no transport or arbitration. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClusterSourceControllerPreview=api;})(globalThis,function(){'use strict';
const profile='gss-5c58-160.002.002';
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),copy=x=>JSON.parse(JSON.stringify(x));
function create(){
 let state={active:false,status:'inactive',selectedCcid:null,popup:null,error:null};
 function snapshot(){return copy(state);}
 function release(){state={active:false,status:'inactive',selectedCcid:null,popup:null,error:null};return snapshot();}
 function accept(plan,result){
  if(result?.signal!=='checkControl')return {applied:false,ignored:true};
  state={active:true,status:'unsupported',selectedCcid:result.selected?.selectedCcid??null,popup:null,error:null};
  try{
   if(plan?.schema!=='original-cc-custom-canvas-plan-v1'||plan.sourceProfile!==profile||plan.customComposition!==true||plan.factoryGraphics!==false||plan.vehicleCompatibilityVerified!==false)throw Error('Reviewed custom-preview plan is unavailable');
   if(plan.status!=='supported')throw Error(plan.reason||'Original selected warning has no reviewed graphics');
   const selected=result.selected;
   if(!selected||selected.sourceProfile!==profile||selected.originalPayloadConsumerObserved!==true||selected.payloadReadbackMatchesConsumer!==true||plan.selectedCcid!==selected.selectedCcid)throw Error('Original selected output does not match the preview plan');
   if(plan.action==='clear'){
    if(plan.selectedCcid!==0||plan.popup!==null||!same(selected.textLines,[null,null])||selected.primaryIcon!==null||!same(selected.collectionSlots,[])||selected.iconSelector!==255||selected.textSelector!==255)throw Error('Original clear is not the reviewed null state');
    state.status='clear';return {applied:true,action:'clear',customComposition:true};
   }
   const popup=plan.popup;
   if(plan.action!=='show'||!Number.isInteger(plan.selectedCcid)||plan.selectedCcid<=0||!popup||popup.ccid!==plan.selectedCcid||popup.id!=='source-cc:'+plan.selectedCcid||popup.iconKey!=='sourceCC-'+plan.selectedCcid||popup.originalControllerComputed!==true||!same(popup.originalLines,selected.textLines)||popup.text!==popup.originalLines.filter(Boolean).join('\n'))throw Error('Original text/icon identity does not match the preview plan');
   state.status='show';state.popup=copy(popup);return {applied:true,action:'show',customComposition:true};
  }catch(error){state.error=error.message;return {applied:false,error:error.message};}
 }
 function project(base,entries){
  if(!state.active||!base)return base;
  const info={active:true,status:state.status,selectedCcid:state.selectedCcid,error:state.error};
  if(state.status!=='show')return {...base,popup:null,originalControllerPreview:info};
  const entry=entries.find(e=>e.id===state.popup.id);
  if(!entry)return {...base,popup:null,originalControllerPreview:{...info,status:'waiting-for-assets',error:'Reviewed warning image is still loading'}};
  for(const key of ['id','ccid','text','originalLines','iconKey','iconRgb','textRgb','sourceFormat','sourceColorSelectorBits','file','pngSha256','rgbaSha256','inspectionVerticalFlip','preserveDecodedRgb']){
   if(!same(entry[key],state.popup[key]))return {...base,popup:null,originalControllerPreview:{...info,status:'unsupported',error:'Loaded warning asset differs from the computed preview: '+key}};
  }
  return {...base,popup:{...copy(entry),...copy(state.popup),originalCcFixture:true,originalControllerComputed:true,placementFixture:false},originalControllerPreview:info};
 }
 return {accept,project,release,snapshot};
}
return {create};
});
