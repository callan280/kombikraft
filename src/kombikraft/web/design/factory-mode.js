let factoryRuntime=null,factoryInputState=null,factoryLastFrame=null,factoryFrameUrl=null,factoryRequestedInputs=null,factoryPollBusy=false,factoryGraphBusy=false,factoryGraphError=null;
function renderFactoryViewport(){
 if(theme!=='factory')return;
 const raw=$('factory-raw').checked;
 const initialized=factoryRuntime?.factoryControllersInitialized===true;
 const graphActive=factoryRuntime?.factoryOriginalGraphBaselineActive===true;
 const graphAvailable=factoryRuntime?.state==='rendering'&&factoryRuntime?.activeMode==='factory'&&factoryRuntime?.nativeControls?.includes('factory-original-graph');
 $('factory-controller-options').style.display='flex';
 $('factory-graph-start').disabled=!graphAvailable||graphActive||factoryGraphBusy||factoryInputState?.busy;
 $('factory-graph-restore').disabled=!graphAvailable||!graphActive||factoryGraphBusy||factoryInputState?.busy;
 if(!factoryGraphBusy)$('factory-graph-status').textContent=factoryGraphError||(graphActive?'Original Telltales baseline active · seatbelt switch drives the original general belt glyph; turn indicators use a separate fixture.':'Partial controller fixture · not full factory startup');
 const drawable=factoryRuntime?.activeMode==='factory'&&factoryRuntime?.state==='rendering'&&(initialized||raw);
 $('factory-wait').style.display=drawable?'none':'flex';$('factory-frame').style.display=drawable?'block':'none';
 if(factoryInputState){
  const results=Object.entries(factoryInputState.results||{}),events=results.flatMap(([,r])=>(r.originalEvents||[]).map(e=>e.nativeName));
  const rendered=results.filter(([,r])=>r.rendered===true).map(([lamp])=>lamp),errors=results.flatMap(([,r])=>r.renderError?[r.renderError]:[]);
  const progress=factoryInputState.busy?'Checking original code and native readback… ':events.length?'Original factory events: '+events.join(' · ')+'. ':'No original input result yet. ';
  const detail=factoryInputState.error?'Input check failed: '+factoryInputState.error:errors.length?'Native bridge: '+errors.join(' · '):rendered.length?'Native shader readback confirmed: '+rendered.join(' / ')+'. Full factory startup and CAN wire decoding remain incomplete.':'Native rendering has not been acknowledged for these inputs.';
  $('factory-command-status').textContent=progress+detail;
 }
}
async function syncFactoryCommands(){
 if(theme!=='factory'||!simulator||factoryGraphBusy)return;const state=simulator.snapshot().signals;
 const request={left:state.hazards||state.turnLeft,right:state.hazards||state.turnRight,belt:!state.seatbeltFastened},key=JSON.stringify(request);
 if(key===factoryRequestedInputs)return;factoryRequestedInputs=key;
 try{const response=await fetch('/api/factory-inputs',{method:'POST',headers:{'Content-Type':'application/json'},body:key});const result=await response.json();if(!result.accepted)throw new Error(result.error||'Factory inputs unavailable');}
 catch(error){factoryRequestedInputs=null;$('factory-command-status').textContent=error.message;}
}
async function factoryGraphAction(action){
 if(factoryGraphBusy||factoryInputState?.busy)return;
 factoryGraphBusy=true;factoryGraphError=null;renderFactoryViewport();
 $('factory-graph-status').textContent='Checking original controller outputs and native readback…';
 try{
  const before=await (await fetch('/api/status')).json();
  const result=await (await fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'factory-original-graph',action})})).json();
  if(!result.accepted||!Number.isInteger(result.transaction))throw Error(result.error||'Original graph request rejected');
  const deadline=Date.now()+50000;let acknowledged=false;
  while(Date.now()<deadline){
   await new Promise(resolve=>setTimeout(resolve,250));
   const state=await (await fetch('/api/status')).json();
   if(state.run!==before.run)throw Error('Native runtime restarted before readback');
   const receipt=state.lastTransaction;
   if(receipt?.id!==result.transaction||receipt.acknowledged!==true)continue;
   if(receipt.kind!=='factory-original-graph'||receipt.action!==action||receipt.applied!==true||receipt.nativeAcknowledgement?.readbackVerifiedEndpoints!==174||receipt.nativeAcknowledgement?.nativeFlushStatus!==0||state.factoryOriginalGraphBaselineActive!==(action==='baseline'))throw Error(receipt.error||'Original graph readback failed');
   factoryRuntime=state;acknowledged=true;break;
  }
  if(!acknowledged)throw Error('Original graph acknowledgement timed out');
  factoryRequestedInputs=null;factoryLastFrame=null;
 }catch(error){factoryGraphError=error.message;$('factory-graph-status').textContent=error.message;}
 finally{factoryGraphBusy=false;await pollFactory();syncFactoryCommands();}
}
$('factory-graph-start').onclick=()=>factoryGraphAction('baseline');
$('factory-graph-restore').onclick=()=>factoryGraphAction('restore');
async function enterFactoryMode(){
 factoryRequestedInputs=null;
 renderFactoryViewport();
 try{const response=await fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'factory-view'})});const reply=await response.json();if(!reply.accepted)$('factory-command-status').textContent=reply.error||'Native factory view is unavailable';}
 catch(error){$('factory-command-status').textContent='Native runtime is unavailable';}
 syncFactoryCommands();pollFactory();
}
async function pollFactory(){
 if(factoryPollBusy)return;factoryPollBusy=true;
 try{
  if(theme==='factory'){
   const responses=await Promise.all([fetch('/api/status'),fetch('/api/factory-inputs')]);
   const previousRun=factoryRuntime?.run;factoryRuntime=await responses[0].json();factoryInputState=await responses[1].json();renderFactoryViewport();
   if(previousRun&&factoryRuntime.run&&previousRun!==factoryRuntime.run){factoryRequestedInputs=null;syncFactoryCommands();}
   const key=factoryRuntime.run+':'+factoryRuntime.frameSequence;
   if(factoryRuntime.activeMode==='factory'&&factoryRuntime.state==='rendering'&&(factoryRuntime.factoryControllersInitialized===true||$('factory-raw').checked)&&factoryLastFrame!==key){
    const response=await fetch('/frame.png?t='+Date.now());if(response.ok){const url=URL.createObjectURL(await response.blob());$('factory-frame').src=url;if(factoryFrameUrl)URL.revokeObjectURL(factoryFrameUrl);factoryFrameUrl=url;factoryLastFrame=key;}
   }
  }
 }catch(error){if(theme==='factory')$('factory-command-status').textContent='Factory runtime connection unavailable.';}
 finally{factoryPollBusy=false;}
}
$('factory-raw').onchange=()=>{factoryLastFrame=null;renderFactoryViewport();pollFactory();};
setInterval(pollFactory,1000);
if(ready&&theme==='factory')enterFactoryMode();
