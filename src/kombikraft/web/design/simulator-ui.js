/* Visual fixtures only. This adapter neither decodes a BMW bus nor calls a car. */
const simulatedIcons={},simulatedIconSpecs={},missingFactoryIcons=new Set(),signalInputs=new Map();
const simulationColours={green:'#00d700',blue:'#549dff',amber:'#ffb500',red:'#ff0000',white:'#ffffff'};
const signalLabels={turnLeft:'Left indicator',turnRight:'Right indicator',hazards:'Hazards',lowBeam:'Dipped headlights',highBeam:'High beam',sideLights:'Side lights',frontFog:'Front fog lamps',rearFog:'Rear fog lamp',parkingLightLeft:'Left parking light',parkingLightRight:'Right parking light',ambientDark:'Dark surroundings',autoHighBeamEnabled:'High-beam assistant',parkingBrake:'Parking brake',seatbeltFastened:'Seat belt fastened',doorOpen:'Door open',engineRunning:'Engine running',navActive:'Navigation active',tyrePressureLow:'Low tyre pressure',engineFault:'Engine fault',oilPressureLow:'Low oil pressure',oilLevelLow:'Low oil level',chargingFault:'Charging fault',coolantOverheat:'Engine overheating',brakeFault:'Brake system fault',absFault:'ABS fault',dscFault:'DSC fault',dscActive:'DSC intervening',serviceDue:'Service due',batteryLow:'Battery low',collisionWarning:'Collision warning'};
const mainSignalKeys=new Set(['turnLeft','turnRight','hazards','lowBeam','highBeam','sideLights','frontFog','rearFog','parkingLightLeft','parkingLightRight','autoHighBeamEnabled','parkingBrake']);
let lastWalkthroughScenario=null,placementCycling=false,placementNextAt=0,placementEntries=[],originalCcEntries=[];
const authoredLamps=[],expandedFamilyBindings={};let telltaleRowState=null;
function placementProjection(state){const original=originalCcEntries.find(m=>m.id===$('original-cc-popup')?.value);if(original)return ClusterOriginalCc.project(state,original);const selected=$('placement-popup')?.value;return ClusterPlacement.project(state,placementEntries.find(m=>m.id===selected));}
function simulationAction(action){try{action();simSnapshot=simulator.snapshot();updateSimulationInputs();draw();updateSimulationReadout();$('sim-feedback').textContent='Local fixture updated.';if(typeof syncFactoryCommands==='function')syncFactoryCommands();}catch(error){$('sim-feedback').textContent=error.message;updateSimulationInputs();}}
function updateSimulationInputs(){
 if(!simulator)return;const s=simulator.snapshot().signals;
 for(const [key,input] of signalInputs)input.checked=s[key];
 $('sim-gear').value=s.gear;$('sim-traction').value=s.tractionMode;$('sim-cruise').value=s.cruiseMode;$('sim-assistance').value=s.assistanceMode;
 const selectedFuel=Array.from($('sim-fuel').options).some(o=>Number(o.value)===s.fuelPercent);if(!selectedFuel){const option=document.createElement('option');option.value=s.fuelPercent;option.textContent=s.fuelPercent+'%';$('sim-fuel').append(option);}$('sim-fuel').value=s.fuelPercent;
}
function updateSimulationReadout(){
 if(!simSnapshot)return;const state=simSnapshot;
 if(state.walkthrough.running&&state.walkthrough.id!==lastWalkthroughScenario){lastWalkthroughScenario=state.walkthrough.id;$('scenario').value=state.walkthrough.id;adoptScenarioReadings();updateSimulationInputs();}
 $('sim-coverage').textContent=(telltaleRowState?.lampTest?'Lamp test icons lit: '+telltaleRowState.litIcons:'Active telltales: '+(telltaleRowState?.activeFamilies??0)+' · Icons lit now: '+(telltaleRowState?.litIcons??0))+' · Fixtures exercised: '+state.coverage.exercised+'/'+state.coverage.total+(state.walkthrough.running?' · Scenario '+(state.walkthrough.index+1)+'/'+state.walkthrough.total:'');
 $('sim-active').textContent='Active: '+(state.indicators.filter(x=>x.id!=='gear').map(x=>x.label).join(' · ')||'No telltales')+(state.popup?' | Popup: '+state.popup.text:'')+(state.queue.length?' | Queued: '+state.queue.map(x=>x.label).join(', '):'')+(missingFactoryIcons.size?' | Factory glyph pending: '+Array.from(missingFactoryIcons).join(', '):'');
}
function syncPreviewSignals(){
 if(!simulator)return;const speed=Number($('speed').value),rpm=Number($('rpm').value),current=simulator.snapshot().signals;
 const patch={speedKmh:speed,rpm,driveMode:{SPORT:'sport',COMFORT:'comfort','ECO PRO':'eco'}[$('mode').value]};
 if(speed>0&&current.gear==='P')patch.gear='D';if(rpm>0&&!current.engineRunning)patch.engineRunning=true;
 simulationAction(()=>simulator.setSignals(patch));
}
function adoptScenarioReadings(){
 const s=simulator.snapshot().signals;$('speed').value=s.speedKmh;$('rpm').value=s.rpm;$('speed-value').textContent=s.speedKmh+' km/h';$('rpm-value').textContent=s.rpm.toLocaleString()+' rpm';
 // Keep the user's style selection; scenarios primarily exercise signals.
 savePreview();
}
function initialiseSimulation(){
 if(!ready||simulator||typeof ClusterSimulation==='undefined')return;
 // Reuse the normal matching-cluster pump for reserve status as well; a
 // powertrain-degradation pictogram is a different source graphic.
 simulatedIcons.footerFuelPump=assets.fuel;simulatedIconSpecs.footerFuelPump={flipY:true,preserveDecodedRgb:false};
 simulator=ClusterSimulation.create();
 simulator.setSignals({gear:Number($('speed').value)>0?'D':'P',speedKmh:Number($('speed').value),rpm:Number($('rpm').value),engineRunning:Number($('rpm').value)>0,fuelPercent:62,speedLimitKmh:80,driveMode:{SPORT:'sport',COMFORT:'comfort','ECO PRO':'eco'}[$('mode').value],navActive:true});
 simSnapshot=simulator.snapshot();
 placementEntries=ClusterSimulation.inventory.filter(m=>m.kind==='fault'||m.kind==='popup');
 for(const m of placementEntries){const o=document.createElement('option');o.value=m.id;o.textContent=m.label;$('placement-popup').append(o);}
 const nextPopup=()=>{$('original-cc-popup').value='';const options=$('placement-popup').options;$('placement-popup').selectedIndex=($('placement-popup').selectedIndex%(options.length-1))+1;draw();};
 $('lamp-test').onchange=()=>draw();$('placement-popup').onchange=()=>{placementCycling=false;$('original-cc-popup').value='';draw();};
 $('original-cc-popup').onchange=()=>{placementCycling=false;$('placement-popup').value='';draw();};
 $('placement-next').onclick=()=>{placementCycling=false;nextPopup();};
 $('placement-run').onclick=()=>{placementCycling=true;placementNextAt=performance.now()+3500;nextPopup();};
 $('placement-stop').onclick=()=>{placementCycling=false;$('placement-popup').value='';$('original-cc-popup').value='';$('lamp-test').checked=false;draw();};
 for(const scenario of ClusterSimulation.scenarios){const option=document.createElement('option');option.value=scenario.id;option.textContent=scenario.label;$('scenario').append(option);}
 for(const [key,value] of Object.entries(ClusterSimulation.defaults)){
  if(typeof value!=='boolean')continue;
  const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.id='signal-'+key;input.checked=simSnapshot.signals[key];label.append(input,document.createTextNode(signalLabels[key]||key.replace(/([A-Z])/g,' $1')));signalInputs.set(key,input);
  input.onchange=()=>simulationAction(()=>{const patch={[key]:input.checked},s=simulator.snapshot().signals;
   if(key==='turnLeft'&&input.checked&&!s.hazards)patch.turnRight=false;
   if(key==='turnRight'&&input.checked&&!s.hazards)patch.turnLeft=false;
   if(key==='hazards'&&!input.checked&&s.turnLeft&&s.turnRight)patch.turnRight=false;
   if(key==='engineRunning'&&!input.checked){patch.rpm=0;patch.cruiseMode='off';$('rpm').value=0;$('rpm-value').textContent='0 rpm';}
   simulator.setSignals(patch);
  });
  $(mainSignalKeys.has(key)?'signals-main':'signals-faults').append(label);
 }
 $('scenario-apply').onclick=()=>simulationAction(()=>{simulator.stopWalkthrough();simulator.applyScenario($('scenario').value);adoptScenarioReadings();});
 $('scenario-run').onclick=()=>simulationAction(()=>{simulator.startWalkthrough({intervalMs:5000});adoptScenarioReadings();});
 $('scenario-stop').onclick=()=>simulationAction(()=>simulator.stopWalkthrough());
 $('popup-ack').onclick=()=>{const critical=simulator.snapshot().popup?.critical;simulationAction(()=>simulator.acknowledge());if(critical)$('sim-feedback').textContent='Critical condition remains active; acknowledgement does not clear it.';};
 $('fault-clear').onclick=()=>simulationAction(()=>{for(const message of simulator.snapshot().activeMessages)if(message.retained&&!message.conditionActive)simulator.clearFault(message.id);});
 $('sim-reset').onclick=()=>simulationAction(()=>{simulator.stopWalkthrough();simulator.reset();simulator.setSignals({gear:'D',speedKmh:72,rpm:2500,fuelPercent:62,speedLimitKmh:80});adoptScenarioReadings();});
 $('sim-gear').onchange=()=>simulationAction(()=>{const patch={gear:$('sim-gear').value};if(patch.gear==='P'){patch.speedKmh=0;patch.cruiseMode='off';$('speed').value=0;$('speed-value').textContent='0 km/h';}if(patch.gear==='R')patch.cruiseMode='off';simulator.setSignals(patch);});
 $('sim-traction').onchange=()=>simulationAction(()=>simulator.setSignals({tractionMode:$('sim-traction').value}));
 $('sim-cruise').onchange=()=>simulationAction(()=>simulator.setSignals({cruiseMode:$('sim-cruise').value,cruiseSetKmh:simulator.snapshot().signals.speedKmh}));
 $('sim-assistance').onchange=()=>simulationAction(()=>simulator.setSignals({assistanceMode:$('sim-assistance').value}));
 $('sim-fuel').onchange=()=>simulationAction(()=>simulator.setSignals({fuelPercent:Number($('sim-fuel').value)}));
 updateSimulationInputs();updateSimulationReadout();draw();
 fetch('/design/original-cc/manifest.json').then(r=>{if(!r.ok)throw Error('Original CC manifest unavailable');return r.json();}).then(async manifest=>{
  const entries=ClusterOriginalCc.entries(manifest);
  await Promise.all(entries.map(entry=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{simulatedIcons[entry.iconKey]=im;simulatedIconSpecs[entry.iconKey]={flipY:entry.inspectionVerticalFlip,preserveDecodedRgb:entry.preserveDecodedRgb,factoryRgb:entry.iconRgb.map(v=>v/255)};resolve();};im.onerror=()=>reject(Error('Original CC graphic unavailable: '+entry.ccid+' / '+entry.file));im.src='/design/original-cc/'+entry.file;})));
  originalCcEntries=entries;for(const entry of entries){const o=document.createElement('option');o.value=entry.id;o.textContent=entry.label;$('original-cc-popup').append(o);}
  $('original-cc-popup').disabled=false;$('original-cc-status').textContent=entries.length+' original BMW text/icon pairs ready. Source bank 0 with recovered BMW colours; vehicle selection and warning activation remain unverified.';draw();
 }).catch(error=>{$('original-cc-status').textContent=error.message;$('original-cc-popup').disabled=true;});
 fetch('/design/simulation/icon-manifest.json').then(r=>r.json()).then(manifest=>{
  for(const [key,entry] of Object.entries(manifest.icons||{})){if(entry.exactResourceDecoded!==true)continue;simulatedIconSpecs[key]=entry;const im=new Image();im.onload=()=>{simulatedIcons[key]=im;draw();};im.src='/design/simulation/'+entry.png;}
 }).catch(()=>{$('sim-feedback').textContent='Factory icon resources unavailable; no substitute glyphs will be drawn.';});
 fetch('/traction-research/glyph-manifest.json').then(r=>r.json()).then(manifest=>{const selected={'f97-fes-traction-text':'tractionDtc','f97-fes-dsc-off-text':'tractionOff','mgu-dsc-off-icon':'dscOffLamp'};for(const entry of manifest.assets||[]){const key=selected[entry.key];if(!key||!entry.exactResourceDecoded)continue;simulatedIconSpecs[key]={...entry,flipY:false};const im=new Image();im.onload=()=>{simulatedIcons[key]=im;draw();};im.src='/traction-research/assets/'+entry.png.split('/').pop();}}).catch(()=>{});
 fetch('/design/simulation/expanded-icons/manifest.json').then(r=>{if(!r.ok)throw Error('Additional source glyphs pending');return r.json();}).then(manifest=>{Object.assign(expandedFamilyBindings,manifest.familyBindings||{});for(const[key,entry]of Object.entries(manifest.icons||{})){if(entry.exactResourceDecoded!==true)continue;simulatedIconSpecs[key]=entry;const im=new Image();im.onload=()=>{simulatedIcons[key]=im;draw();};im.src='/design/simulation/expanded-icons/'+entry.file;}}).catch(()=>{});
 fetch('/design/warning-pictos/manifest.json').then(r=>{if(!r.ok)throw Error('Recovered warning graphics unavailable');return r.json();}).then(async manifest=>{
  if(manifest.schema!=='f40-warning-pictos-source-v1'||manifest.factoryWarningLifecycleVerified!==false)throw Error('Unknown warning artwork contract');
  await Promise.all(manifest.entries.map(entry=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{simulatedIcons[entry.key]=im;simulatedIconSpecs[entry.key]={flipY:entry.inspectionVerticalFlip,preserveDecodedRgb:entry.preserveDecodedRgb,factoryRgb:entry.iconRgb.map(v=>v/255)};resolve();};im.onerror=()=>reject(Error('Recovered warning graphic unavailable: '+entry.key));im.src='/design/warning-pictos/'+entry.file;})));
  Object.assign(expandedFamilyBindings,manifest.familyBindings);$('placement-status').dataset.warningPictos='ready';draw();
 }).catch(error=>{$('placement-status').dataset.warningPictos='failed';$('sim-feedback').textContent=error.message;});
 fetch('/design/factory-graphics/telltales-v2.json').then(r=>{if(!r.ok)throw new Error('Factory atlas unavailable');return r.json();}).then(manifest=>{
  for(const entry of ClusterPlacement.selectLamps(manifest.entries||[])){
   const image=new Image();image.onload=()=>{const surface=document.createElement('canvas');surface.width=image.width;surface.height=image.height;const c=surface.getContext('2d');c.translate(0,image.height);c.scale(1,-1);c.drawImage(image,0,0);c.globalCompositeOperation='source-in';c.fillStyle='rgb('+entry.factoryRgb.map(v=>Math.round(v*255)).join(',')+')';c.fillRect(0,0,image.width,image.height);authoredLamps.push({entry,surface});draw();};image.src='/design/factory-graphics/'+entry.file;
  }
  for(const key of new Set([...Object.keys(manifest.previewAliases||{}),...Object.keys(manifest.previewAliasEntries||{})])){
   const name=manifest.previewAliases?.[key],entryId=manifest.previewAliasEntries?.[key];
   const entry=entryId?manifest.entries.find(e=>e.sourceEntryId===entryId):manifest.entries.find(e=>e.name===name);
   if(!entry||entry.exactGlyphPixels!==true||entry.colorVerified!==true||!/^telltales(?:-v2)?\/[A-Za-z0-9_.-]+\.png$/.test(entry.file))continue;
   simulatedIconSpecs[key]=entry;const im=new Image();im.onload=()=>{simulatedIcons[key]=im;draw();};im.src='/design/factory-graphics/'+entry.file;
  }
 }).catch(()=>{$('sim-feedback').textContent='Factory telltale atlas unavailable; no substitute glyphs will be drawn.';});
}
function previewIcon(c,id,x,y,size,color,iconKey){
 const image=iconKey&&simulatedIcons[iconKey],spec=iconKey&&simulatedIconSpecs[iconKey];
 if(spec?.factoryRgb)color='rgb('+spec.factoryRgb.map(v=>Math.round(v*255)).join(',')+')';
 c.save();c.translate(x,y);
 if(image){
  const surface=document.createElement('canvas');surface.width=image.width;surface.height=image.height;const s=surface.getContext('2d');s.translate(0,image.height);s.scale(1,-1);s.drawImage(image,0,0);s.globalCompositeOperation='source-in';s.fillStyle=color;s.fillRect(0,0,image.width,image.height);
  let width=size*image.width/Math.max(image.width,image.height),height=size*image.height/Math.max(image.width,image.height);
  if(spec?.originalQuad&&spec.alphaBounds){const q=spec.originalQuad,b=spec.alphaBounds,scale=size/Math.max((b[2]-b[0])*q.widthX/image.width,(b[3]-b[1])*q.heightZ/image.height);width=q.widthX*scale;height=q.heightZ*scale;}
  c.drawImage(surface,0,0,surface.width,surface.height,-width/2,-height/2,width,height);c.restore();return true;
 }
 c.restore();missingFactoryIcons.add(id);return false;
}

function wrapSimulationText(c,value,x,y,maxWidth,size,color){
 c.save();c.font=`${size}px BMWTA`;const words=value.split(/\s+/);let lineText='',row=0;
 for(const word of words){const next=lineText?lineText+' '+word:word;if(c.measureText(next).width>maxWidth&&lineText){text(c,lineText,x,y+row*36,size,color);row++;lineText=word;if(row>=2)break;}else lineText=next;}
 if(row<3&&lineText)text(c,lineText,x,y+row*36,size,color);c.restore();
}
const popupIconProfiles=new Map();
function popupIconProfile(key){
 const image=simulatedIcons[key];if(!image)return null;const cached=popupIconProfiles.get(key);if(cached?.image===image)return cached;
 const surface=document.createElement('canvas');surface.width=image.width;surface.height=image.height;const s=surface.getContext('2d');if(simulatedIconSpecs[key]?.flipY!==false){s.translate(0,image.height);s.scale(1,-1);}s.drawImage(image,0,0);
 const pixels=s.getImageData(0,0,image.width,image.height).data;let x0=image.width,y0=image.height,x1=-1,y1=-1;
 for(let y=0;y<image.height;y++)for(let x=0;x<image.width;x++)if(pixels[(y*image.width+x)*4+3]>16){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
 if(x1<x0||y1<y0)return null;const w=x1-x0+1,h=y1-y0+1,scale=48/Math.max(w,h),profile={image,surface,x:x0,y:y0,w,h,fitWidth:w*scale,fitHeight:h*scale};popupIconProfiles.set(key,profile);return profile;
}
function drawPopupPictogram(c,message,position,color,profile){
 if(!profile||!position){missingFactoryIcons.add(message.id);return false;}
 const spec=simulatedIconSpecs[message.iconKey],tile=document.createElement('canvas');tile.width=profile.w;tile.height=profile.h;const s=tile.getContext('2d');s.drawImage(profile.surface,profile.x,profile.y,profile.w,profile.h,0,0,profile.w,profile.h);if(!spec?.preserveDecodedRgb){s.globalCompositeOperation='source-in';s.fillStyle=spec?.factoryRgb?'rgb('+spec.factoryRgb.map(v=>Math.round(v*255)).join(',')+')':color;s.fillRect(0,0,tile.width,tile.height);}
 c.drawImage(tile,position.centerX-profile.fitWidth*(position.maxInkSize/48)/2,position.centerY-profile.fitHeight*(position.maxInkSize/48)/2,profile.fitWidth*(position.maxInkSize/48),profile.fitHeight*(position.maxInkSize/48));return true;
}
function renderSimulatedStatus(c,state){
 missingFactoryIcons.clear();
 const rearRaw=["left","centre","right"].map(seat=>Number($("rear-belt-"+seat).value)),rearShow=$("rear-belt-show").checked;
 FactorySeatbelt.render(c,rearRaw,rearShow);$("rear-belt-status").dataset.fixture=JSON.stringify({raw:rearRaw,show:rearShow,status:FactorySeatbelt.status()});
 if(placementCycling&&performance.now()>=placementNextAt){placementNextAt=performance.now()+3500;const options=$('placement-popup').options;$('placement-popup').selectedIndex=($('placement-popup').selectedIndex%(options.length-1))+1;}
 const visualBindings={...expandedFamilyBindings,'fuel-reserve':{iconKey:'footerFuelPump'}};
 telltaleRowState=ClusterTelltaleRow.project(state,ClusterSimulation.inventory,visualBindings,{theme,lampTest:$('lamp-test').checked,availableKeys:new Set(Object.keys(simulatedIcons).filter(key=>popupIconProfile(key)))});
 for(const id of telltaleRowState.missing)missingFactoryIcons.add(id);
 for(const slot of telltaleRowState.displays){const profile=popupIconProfile(slot.key);if(!profile){missingFactoryIcons.add(slot.item.id);continue;}const paired=slot.item.pairedIconKey&&popupIconProfile(slot.item.pairedIconKey),dx=paired?22:0;drawPopupPictogram(c,{...slot.item,iconKey:slot.key},{centerX:slot.x+dx,centerY:slot.y,maxInkSize:slot.size},simulationColours[slot.item.color]||'#ffffff',profile);if(paired)drawPopupPictogram(c,{...slot.item,iconKey:slot.item.pairedIconKey},{centerX:slot.x-71,centerY:slot.y,maxInkSize:32},simulationColours.amber,paired);}
 $('placement-status').dataset.telltaleRow=JSON.stringify(telltaleRowState);
 $('placement-status').dataset.loadedFactoryIconKeys=JSON.stringify(Object.keys(simulatedIcons).filter(key=>popupIconProfile(key)).sort());
 $('placement-status').textContent='Grouped cluster placement · '+telltaleRowState.litIcons+' mapped icons lit · popup '+$('placement-popup').selectedIndex+'/'+placementEntries.length+'. This is an offline fixture, not verified factory warning control.';
 const message=state.popup;delete $('placement-status').dataset.popupLayout;if(!message)return;
 if(message.originalCcFixture)$('placement-status').textContent='Original BMW CC '+message.ccid+' · source text and icon pairing · custom placement; no live warning input binding.';
 const {x,y,width,height}=ClusterLayoutGeometry.popup;const color=simulationColours[message.color]||'#dce6f2';
 // Recovered original CC anchors; exact factory mesh bounds remain under study.
 c.save();FactoryCc.render(c,'popup');
 c.font='29px BMWTA';const popupIconKey=visualBindings[message.id]?.iconKey||message.iconKey,iconProfile=popupIconProfile(popupIconKey),layout=ClusterPopupLayout.layout(message.text,value=>c.measureText(value),{iconPresent:!!iconProfile,iconWidth:iconProfile?.fitWidth,originalLines:message.originalCcFixture?message.originalLines:undefined});
 drawPopupPictogram(c,{...message,iconKey:popupIconKey},layout.icon,color,iconProfile);
 c.fillStyle=message.originalCcFixture?'rgb('+message.textRgb.join(',')+')':'#f1f4f8';c.textAlign='left';c.textBaseline='alphabetic';
 for(const row of layout.lines)c.fillText(row.text,row.x,row.baseline);
 $('placement-status').dataset.popupLayout=JSON.stringify({id:message.id,originalCcFixture:message.originalCcFixture===true,sourceTextLines:message.originalCcFixture?message.originalLines:undefined,iconAvailable:!!iconProfile,...layout});

 c.restore();
}
initialiseSimulation();

FactorySeatbelt.load().then(status=>{$("rear-belt-status").textContent=status.available?"Original rear-seat graphics and raw-state outputs ready; live binding unverified.":status.error;$("rear-belt-status").dataset.proof=JSON.stringify(status);draw();});
for(const id of ["rear-belt-show","rear-belt-left","rear-belt-centre","rear-belt-right"])$(id).onchange=()=>draw();
