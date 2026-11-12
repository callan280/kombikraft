/* Explicit native graphics fixture; no vehicle telemetry or fallback screenshot. */
let nativeCustomState=null,nativeCustomBusy=false,nativeCustomPolling=false,nativeCustomUrl=null,nativeCustomError=null,nativeCustomFrameKey=null;
let nativeCustomQueued=[];
const nativeCustomBcLabels={stats:'Journey data',consumption:'Consumption',media:'Media','sport-instruments':'Sport displays','g-force':'G-force',blank:'Blank centre'};
const nativeCustomDisabled=new Map();
const nativeCustomNeedles=[['speed','Speedometer',25],['rpm','Tachometer',45],['oil','Oil',35],['boost','Boost',65],['water','Water',50]];
const nativeSemanticPanel=document.createElement('section');nativeSemanticPanel.hidden=true;
nativeSemanticPanel.innerHTML='<h3>Decoded signal replay</h3><p class="sim-note">Reviewed offline decoder fixtures. No vehicle is connected. Indicated speed, coolant, boost and gear remain unavailable.</p><label>Decoded state<select id="native-semantic-state"></select></label><div class="options"><button id="native-semantic-apply">Apply decoded state</button><button id="native-semantic-release">Return to graphics fixture</button></div><p id="native-semantic-readout" class="sim-note" role="status"></p>';
$('native-custom-panel').append(nativeSemanticPanel);
const nativeStatusPanel=document.createElement('section');nativeStatusPanel.hidden=true;
nativeStatusPanel.innerHTML='<h3>Status graphics fixtures</h3><label>Traction graphic<select id="native-status-traction"><option value="dsc-on">Traction on</option><option value="dtc">Sport traction</option><option value="dsc-off">Traction off</option></select></label><label><input id="native-status-clock" type="checkbox"> Show Mac clock (preview fixture only)</label><button id="native-status-apply">Apply status graphics</button><p class="sim-note">These change the preview graphics only. They do not control vehicle traction. Decoded replay suppresses these fixtures.</p>';
$('native-custom-panel').append(nativeStatusPanel);
for(const [value,label]of [[19,'Known decoded readings'],[51,'Valid zero readings'],[212,'Provider lost / unavailable']]){const option=document.createElement('option');option.value=value;option.textContent=label;$('native-semantic-state').append(option);}
const nativeSemanticOther=document.createElement('optgroup');nativeSemanticOther.label='All reviewed decoded states';
for(let value=1;value<=212;value++){if([19,51,212].includes(value))continue;const option=document.createElement('option');option.value=value;option.textContent='State '+String(value).padStart(3,'0');nativeSemanticOther.append(option);}$('native-semantic-state').append(nativeSemanticOther);
for(const [key,label,value] of nativeCustomNeedles){
 const box=document.createElement('label');box.textContent=label+' position';
 const input=document.createElement('input');input.id='native-custom-'+key;input.type='range';input.min=0;input.max=100;input.value=value;box.append(input);$('native-custom-sliders').append(box);
}
function nativeCustomActive(){return $('native-custom-mode').checked&&theme==='m-round'&&!mapVisible;}
function renderNativeCustomViewport(){
 const active=nativeCustomActive(),good=nativeCustomState?.frameAvailable===true&&!nativeCustomError;
 const semanticSupported=nativeCustomState?.controls?.includes('semantic')===true,semantic=nativeCustomState?.semanticState,semanticActive=semanticSupported&&semantic?.index>0&&semantic?.released!==true;
 nativeSemanticPanel.hidden=!semanticSupported;
 nativeStatusPanel.hidden=!nativeCustomState?.controls?.includes('status');
 for(const id of ['native-status-traction','native-status-clock','native-status-apply'])$(id).disabled=!active||nativeCustomBusy||!good||semanticActive;
 for(const id of ['native-semantic-state','native-semantic-apply','native-semantic-release'])$(id).disabled=!active||nativeCustomBusy||!good;
 if(semanticActive){
  const fields=[['Engine speed','rpm'],['Oil','°C'],['Range','km'],['Odometer','km']];
  $('native-semantic-readout').textContent='State '+String(semantic.index).padStart(3,'0')+' · '+fields.map(([name,unit],i)=>name+': '+((semantic.availableMask&(1<<i))?semantic.values[i]+' '+unit:'unavailable')).join(' · ')+'. Physical source identity remains unverified.';
 }else $('native-semantic-readout').textContent='Graphics fixture active. Decoded states keep missing data unavailable; zero is shown only when valid.';
 $('native-custom-mode').disabled=!$('native-custom-mode').checked&&!nativeCustomState?.frameAvailable;
 for(const el of document.querySelectorAll('#native-custom-sliders input,#native-custom-examples,#native-custom-fuel,#native-custom-apply,#native-custom-bc,#native-custom-gear,#native-custom-marquee'))el.disabled=!active||nativeCustomBusy||!good;
 const unsupported=document.querySelectorAll('#speed,#rpm,#animate,#reset,#dial-profile,#map-fade,#gauge-fade,.simulation input,.simulation select,.simulation button');
 for(const el of unsupported){
  if(['original-cc-popup','placement-stop'].includes(el.id))continue;
  if(active){if(!nativeCustomDisabled.has(el))nativeCustomDisabled.set(el,el.disabled);el.disabled=true;}
  else if(nativeCustomDisabled.has(el)){el.disabled=theme==='factory'&&['dial-profile','map-fade','gauge-fade'].includes(el.id)?true:nativeCustomDisabled.get(el);nativeCustomDisabled.delete(el);}
 }
 for(const id of ['mode','branding','original-cc-popup','placement-stop']){const el=$(id);if(active){if(!nativeCustomDisabled.has(el))nativeCustomDisabled.set(el,el.disabled);el.disabled=nativeCustomBusy||(id==='original-cc-popup'?el.options.length<2:nativeCustomDisabled.get(el));}else if(nativeCustomDisabled.has(el)){el.disabled=theme==='factory'&&id==='branding'?true:nativeCustomDisabled.get(el);nativeCustomDisabled.delete(el);}}
 if(!active){$('native-custom-frame').style.display='none';$('native-custom-wait').style.display='none';if(theme!=='factory')$('cluster').style.display='block';return false;}
 $('cluster').style.display='none';$('factory-frame').style.display='none';$('factory-wait').style.display='none';
 $('native-custom-frame').style.display=good&&nativeCustomUrl?'block':'none';$('native-custom-wait').style.display=good&&nativeCustomUrl?'none':'flex';
 $('theme-caption').textContent='M Round / native graphics fixture';
 $('description').textContent='Live framebuffer from the captured BMW HU graphics runtime. Explicit graphics-test inputs; no car connected. Six centre pages run in the native renderer. Physical BC, map and vehicle signal binding remain unverified.';
 const bcAvailable=good&&nativeCustomState?.controls?.includes('bc'),popup=Boolean($('original-cc-popup').value);
 $('native-custom-bc').disabled=nativeCustomBusy||!bcAvailable||popup;
 $('bc-preview').disabled=nativeCustomBusy||!bcAvailable||popup;
 $('native-custom-gear').disabled=nativeCustomBusy||!good||!nativeCustomState?.controls?.includes('gear');
 $('native-custom-marquee').disabled=nativeCustomBusy||!bcAvailable||popup||$('native-custom-bc').value!=='media'||!nativeCustomState?.mediaMarqueeAvailable;
 if(active&&semanticActive)for(const el of document.querySelectorAll('#native-custom-sliders input,#native-custom-examples,#native-custom-fuel,#native-custom-apply,#native-custom-gear,#mode,#branding'))el.disabled=true;
 $('bc-preview-status').textContent=popup?'Original CC preview has priority; centre page retained.':(nativeCustomBcLabels[$('native-custom-bc').value]+' · Native graphics fixture; physical BC is not connected.');
 return true;
}
async function nativeCustomPoll(){
 if(nativeCustomPolling)return;nativeCustomPolling=true;
 try{
  const response=await fetch('/api/native-custom/status');if(!response.ok)throw Error('Native preview status unavailable');
  const state=await response.json();
  if(nativeCustomState?.run&&state.run&&state.run!==nativeCustomState.run){nativeCustomFrameKey=null;if(nativeCustomActive())nativeCustomError='Native renderer restarted. Turn native preview off and on to reset the fixture.';}
  nativeCustomState=state;
  if(!nativeCustomBusy)$('native-custom-status').textContent=nativeCustomError||state.error||(state.frameAvailable?'Native render loop is live. Controls require confirmed native readback.':'Waiting for a live native render loop.');
  const key=state.run+':'+state.frameSequence;
  if(nativeCustomActive()&&state.frameAvailable&&!nativeCustomError&&nativeCustomFrameKey!==key){
   const image=await fetch('/api/native-custom/frame.png?t='+Date.now());
   if(image.ok){const url=URL.createObjectURL(await image.blob());$('native-custom-frame').src=url;if(nativeCustomUrl)URL.revokeObjectURL(nativeCustomUrl);nativeCustomUrl=url;nativeCustomFrameKey=key;}
  }
 }catch(error){nativeCustomState={frameAvailable:false};$('native-custom-status').textContent=error.message;}
 finally{nativeCustomPolling=false;renderNativeCustomViewport();}
}
async function nativeCustomSend(payload){
 const response=await fetch('/api/native-custom/control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
 const queued=await response.json();if(!response.ok||!queued.accepted)throw Error(queued.error||'Native request rejected');
 const deadline=Date.now()+50000;
 while(Date.now()<deadline){
  await new Promise(resolve=>setTimeout(resolve,300));
  const state=await(await fetch('/api/native-custom/status')).json();nativeCustomState=state;
  if(state.run!==queued.run)throw Error(state.error||'Native runtime changed');
  const ack=state.lastTransaction;
  if(ack?.id!==queued.transaction)continue;
  if(ack.applied!==true)throw Error(ack.error||'Native readback failed');
  $('native-custom-status').dataset.lastTransaction=JSON.stringify(ack);
  return ack;
 }
 throw Error('Native acknowledgement timed out');
}
function nativeCustomGaugeRequest(){return{type:'gauges',positions:nativeCustomNeedles.map(([key])=>Number($('native-custom-'+key).value)/100),mode:{COMFORT:0,SPORT:1,'ECO PRO':2}[$('mode').value]};}
function nativeCustomBcRequest(){return{type:'bc',page:$('native-custom-bc').value,fixture:$('native-custom-bc').value==='media'&&$('native-custom-marquee').checked&&nativeCustomState?.mediaMarqueeAvailable?2:$('native-custom-examples').checked?1:0};}
function nativeCustomGearRequest(){return{type:'gear',gear:$('native-custom-gear').value};}
function nativeCustomOptionalGear(){return nativeCustomState?.controls?.includes('gear')?[nativeCustomGearRequest()]:[];}
function nativeCustomBcNext(){const pages=nativeCustomState?.bcPages||[];if(!pages.length||$('bc-preview').disabled)return;$('native-custom-bc').value=pages[(pages.indexOf($('native-custom-bc').value)+1)%pages.length];nativeCustomAction([nativeCustomBcRequest()]);}
function nativeCustomFooterRequest(){return{type:'footer',brand:$('branding').value==='m'?1:0,fixture:$('native-custom-examples').checked?1:0,fuel:Number($('native-custom-fuel').value),cc:0,checker:0};}
function nativeCustomStatusRequest(){return{type:'status',traction:$('native-status-traction').value,clock:$('native-status-clock').checked?'host-preview':'unavailable'};}
async function nativeCustomAction(requests){
 if(!nativeCustomActive())return;
 if(nativeCustomBusy){if(nativeCustomQueued.length<16)nativeCustomQueued.push(requests);return;}
 nativeCustomBusy=true;nativeCustomError=null;renderNativeCustomViewport();$('native-custom-status').textContent='Waiting for native readback and a subsequent frame…';
 try{for(const request of requests)await nativeCustomSend(request);$('native-custom-status').textContent='Native graphics confirmed by readback and native render-loop progress.';}
 catch(error){nativeCustomQueued=[];nativeCustomError=error.message;$('native-custom-status').textContent=error.message;}
 finally{nativeCustomBusy=false;nativeCustomFrameKey=null;await nativeCustomPoll();if(nativeCustomQueued.length&&nativeCustomActive())nativeCustomAction(nativeCustomQueued.shift());}
}
$('native-custom-mode').onchange=async()=>{
 nativeCustomQueued=[];nativeCustomError=null;nativeCustomFrameKey=null;
 if($('native-custom-mode').checked){
  mapVisible=false;setTheme('m-round');$('original-cc-popup').value='';
  await nativeCustomAction([...(nativeCustomState?.controls?.includes('semantic')?[{type:'semantic',index:0}]:[]),{type:'cc',ccid:0},nativeCustomFooterRequest(),...(nativeCustomState?.controls?.includes('status')?[nativeCustomStatusRequest()]:[]),nativeCustomGaugeRequest(),nativeCustomBcRequest(),...nativeCustomOptionalGear()]);
 }else{nativeCustomQueued=[];renderNativeCustomViewport();draw();}
};
$('native-custom-apply').onclick=()=>nativeCustomAction([nativeCustomGaugeRequest(),nativeCustomFooterRequest(),nativeCustomBcRequest(),...nativeCustomOptionalGear()]);
$('native-custom-gear').onchange=()=>nativeCustomAction([nativeCustomGearRequest()]);
$('native-custom-marquee').onchange=()=>nativeCustomAction([nativeCustomBcRequest()]);
$('native-custom-bc').onchange=()=>nativeCustomAction([nativeCustomBcRequest()]);
$('native-semantic-apply').onclick=()=>nativeCustomAction([{type:'semantic',index:Number($('native-semantic-state').value)}]);
$('native-semantic-release').onclick=()=>nativeCustomAction([{type:'semantic',index:0}]);
$('native-status-apply').onclick=()=>nativeCustomAction([nativeCustomStatusRequest()]);
for(const id of ['mode','branding'])$(id).addEventListener('change',()=>nativeCustomAction([id==='mode'?nativeCustomGaugeRequest():nativeCustomFooterRequest()]));
for(const id of ['touring','round','factory','map-toggle'])$(id).addEventListener('click',()=>{if(theme!=='m-round'||mapVisible){$('native-custom-mode').checked=false;nativeCustomQueued=[];renderNativeCustomViewport();draw();}});
setInterval(nativeCustomPoll,1000);nativeCustomPoll();
