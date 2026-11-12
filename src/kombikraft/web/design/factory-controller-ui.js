/* Authored internal fixtures and actual original-controller output stay distinct. */
(function(root,factory){
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else if(root.document){root.KombiKraftOriginalController=api.create({document:root.document,fetch:root.fetch.bind(root)});root.KombiKraftOriginalController.refresh();}
})(globalThis,function(){'use strict';
function create({document,fetch}){
 const element=id=>document.getElementById(id);
 const state={available:false,ccAvailable:false,enabled:false,busy:false,requestedInput:null,result:null,previewPlan:null,previewResult:null,error:null};
 let previewHandler=null;
 function snapshot(){return JSON.parse(JSON.stringify(state));}
 function render(){
  element('controller-enable').disabled=!state.available||state.busy;
  element('controller-enable').checked=state.enabled;
  for(const button of document.querySelectorAll('[data-controller-signal]'))button.disabled=!state.enabled||!state.available||state.busy;
  for(const id of ['controller-run','controller-use-pair','controller-clear','controller-ccid','controller-quality','controller-mode'])element(id).disabled=!state.enabled||!state.ccAvailable||state.busy;
  element('controller-refresh').disabled=state.busy;
  element('controller-capability').textContent=state.ccAvailable?'Original CC, BC and lamp controller ready. Internal fixtures only; no car connected.':state.available?'Original BC/lamp controller ready. Start the viewer with --check-control and matching14-bank inputs to enable CC.':'Original controller unavailable. Supply matching local firmware inputs when starting the viewer.';
  element('controller-request').textContent=state.requestedInput?JSON.stringify(state.requestedInput,null,2):'No authored input submitted.';
  const selected=state.result?.selected;
  element('controller-output').textContent=selected?JSON.stringify({selectedCcid:selected.selectedCcid,textLines:selected.textLines,primaryIcon:selected.primaryIcon,iconSelector:selected.iconSelector,textSelector:selected.textSelector,iconRGBA:selected.iconSelectorHelperRGBA,textRGBA:selected.textSelectorHelperRGBA,sourceVariantIndex:selected.sourceVariantIndex,sourceCollectionBankOrdinal:selected.sourceCollectionBankOrdinal,explicitLanguageFixture:selected.sourceLanguageOrdinal,payloadConsumerCalls:state.result.payloadConsumerCalls},null,2):state.result?JSON.stringify({events:state.result.events,callbackCount:state.result.callbackCount},null,2):'No original computed output yet.';
  element('controller-result').textContent=state.result?JSON.stringify(state.result,null,2):'No original result.';
  const graphics=state.result&&state.result.signal!=='checkControl'?'Original BC/lamp event computation returned. Existing CC preview is unchanged.':state.previewResult?.error?'Original controller computed. Preview unavailable: '+state.previewResult.error:state.previewResult?.applied===true?'Original computation applied to the custom preview. Factory graphics and warning arbitration remain unverified.':state.previewPlan?.status==='unsupported'?'Original controller computed; preview unsupported: '+state.previewPlan.reason:state.previewPlan?'A preview plan was returned separately. Factory graphics and warning arbitration remain unverified.':'Graphics not attached. This panel shows actual original computation; placement previews remain inspection fixtures.';
  element('controller-feedback').textContent=state.busy?'Executing original controller fixture…':state.error?'Input failed: '+state.error+'. Previous computed output is retained.':graphics;
 }
 async function refresh(){
  if(state.busy)return;
  try{
   const response=await fetch('/api/factory-controller/status');
   if(!response.ok)throw Error('Original controller status unavailable');
   const status=await response.json();state.available=status.available===true;state.ccAvailable=state.available&&status.checkControl?.available===true;
   if(!state.available)state.enabled=false;
   if(status.checkControl?.sourceStateUnavailable===true){
    state.previewPlan=null;
    if(previewHandler){try{state.previewResult=await previewHandler(null,{signal:'checkControl',sourceStateUnavailable:true});}catch(error){state.previewResult={applied:false,error:error.message};}}
   }
   if(!state.result&&status.checkControl?.lastResult){state.result=status.checkControl.lastResult;state.requestedInput=status.checkControl.lastRequest;state.previewPlan=status.checkControl.previewPlan??null;}
   state.error=status.checkControl?.sourceStateUnavailable===true?'Source machine unavailable; restart the viewer':null;
  }catch(error){state.available=false;state.ccAvailable=false;state.enabled=false;state.error=error.message;}
  render();return snapshot();
 }
 async function runCommand(command){
  if(!state.enabled||!state.available||state.busy)throw Error('Enable the available original controller first');
  if(command.signal==='checkControl'&&!state.ccAvailable)throw Error('Original Check Control is unavailable');
  state.busy=true;state.error=null;state.requestedInput=JSON.parse(JSON.stringify(command));render();
  try{
   const response=await fetch('/api/factory-controller/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(command)});
   const reply=await response.json();
   if(!response.ok||!reply.result||reply.result.signal!==command.signal){
    if(reply.sourceStateUnavailable===true){
     state.available=false;state.ccAvailable=false;state.enabled=false;state.previewPlan=null;
     if(previewHandler){try{state.previewResult=await previewHandler(null,{signal:'checkControl',sourceStateUnavailable:true});}catch(error){state.previewResult={applied:false,error:error.message};}}
    }
    throw Error(reply.error||'Original fixture result unavailable');
   }
   state.result=reply.result;
   if(command.signal==='checkControl'){
    state.previewPlan=reply.previewPlan??null;state.previewResult=null;
    if(previewHandler){
     try{state.previewResult=await previewHandler(state.previewPlan,state.result);}
     catch(error){state.previewResult={applied:false,error:error.message};}
    }
   }
   return reply;
  }catch(error){state.error=error.message;return {error:error.message};}
  finally{state.busy=false;render();}
 }
 function runCc(ccid){
  if(!Number.isInteger(ccid)||ccid<0||ccid>65535){state.error='CCID must be UInt16';render();return;}
  const raw={ccid,quality:Number(element('controller-quality').value)};
  if(element('controller-mode').value!=='')raw.mode=Number(element('controller-mode').value);
  return runCommand({signal:'checkControl',raw});
 }
 element('controller-enable').onchange=()=>{state.enabled=element('controller-enable').checked&&state.available;state.error=null;render();};
 element('controller-refresh').onclick=()=>refresh();
 element('controller-run').onclick=()=>runCc(Number(element('controller-ccid').value));
 element('controller-clear').onclick=()=>{element('controller-ccid').value='0';return runCc(0);};
 element('controller-use-pair').onclick=()=>{
  const value=element('original-cc-popup').value;
  if(!/^source-cc:\d+$/.test(value)){state.error='Select an inspection source pair first';render();return;}
  const ccid=Number(value.split(':')[1]);element('controller-ccid').value=String(ccid);return runCc(ccid);
 };
 for(const button of document.querySelectorAll('[data-controller-signal]'))button.onclick=()=>runCommand({signal:button.dataset.controllerSignal,raw:Number(button.dataset.controllerRaw)});
 render();
 return {refresh,runCommand,getState:snapshot,setPreviewHandler(handler){if(handler!==null&&typeof handler!=='function')throw Error('Preview handler must be a function or null');previewHandler=handler;}};
}
return {create};
});
