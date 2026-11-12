/* Grouped source-art fixtures. Locations adapt to this preview, not a verified F40 hardware map. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClusterTelltaleRow=api;})(globalThis,function(){'use strict';
// The recovered door silhouette is CC popup content, not a separate lamp over BC media.
const excluded=new Set(['gear','navigation-active','hazards','door-open']);
const placement={
 'turn-left':[618,155,40,'turn-left'], 'turn-right':[1302,155,40,'turn-right'],
 'high-beam':[45,65,36,'high-beam'],'high-beam-assist':[105,65,36,'high-beam-assist'],
 'low-beam':[45,110,36,'low-beam'],'side-lights':[90,105,36,'side-lights'],
 'front-fog':[40,150,36,'front-fog'],'rear-fog':[22,190,36,'rear-fog'],
 'parking-light-left':[150,50,36,'parking-left'],'parking-light-right':[1770,50,36,'parking-right'],
 'collision':[960,50,36,'collision'],'tyre-pressure':[700,285,36,'tyres'],
 'abs':[700,330,36,'abs'],'dsc':[700,375,36,'dsc'],'dsc-active':[700,375,36,'dsc'],
 'engine':[700,420,36,'engine'],'service':[700,465,36,'service'],
 'brake':[1220,285,36,'brake'],'parking-brake':[1220,330,36,'parking-brake'],'parking-brake-moving':[1220,330,36,'parking-brake'],
 'battery':[1220,375,36,'charging'],'charging-system':[1220,375,36,'charging'],
 'coolant':[1220,420,36,'coolant'],'oil-level':[1220,465,36,'oil-level'],'oil-pressure':[1220,510,36,'oil-pressure'],
 'cruise-standby':[630,575,40,'cruise'],'cruise-active':[630,575,40,'cruise'],
 'assistance-active':[1290,575,40,'assistance'],'assistance-warning':[1290,575,40,'assistance'],
 'fuel-reserve':[168,705,30,'fuel'],'seatbelt':[610,702,36,'front-belt'],
 'traction-dtc':[1590,587,130,'traction'],'traction-off':[1590,587,130,'traction']
};
const tractionVariants=[{id:'traction-dtc',familyId:'dsc',label:'Sport traction',kind:'indicator',source:'tractionMode',color:'white',priority:0,iconKey:'tractionDtc',pairedIconKey:'dscOffLamp'},{id:'traction-off',familyId:'dsc',label:'Traction off',kind:'indicator',source:'tractionMode',color:'white',priority:0,iconKey:'tractionOff',pairedIconKey:'dscOffLamp'}];
const keyFor=(item,bindings)=>bindings[item.id]?.iconKey||item.iconKey;
function slots(inventory,bindings={},options={}){
 const result=[];
 for(const item of [...inventory,...tractionVariants]){if(!item.source||excluded.has(item.id))continue;const key=keyFor(item,bindings),p=options.theme==='map-touring'&&item.id.startsWith('traction-')?[1610,500,130,'traction']:placement[item.id];if(!key||!p)continue;let slot=result.find(s=>s.group===p[3]);if(!slot){slot={key,group:p[3],x:p[0],y:p[1],size:p[2],items:[],placementScope:'Custom adaptation of functional lamp areas; factory physical route unverified'};result.push(slot);}slot.items.push(item);}
 return result;
}
function project(state,inventory,bindings={},options={}){
 const list=slots(inventory,bindings,options),available=options.availableKeys||new Set(),active=state.indicators.filter(i=>!excluded.has(i.id)).concat(state.signals?.tractionMode==='dtc'?[{...tractionVariants[0],on:true}]:state.signals?.tractionMode==='dsc-off'?[{...tractionVariants[1],on:true}]:[]),requested=options.lampTest?[...inventory,...tractionVariants].filter(i=>i.source&&!excluded.has(i.id)):active,missing=requested.filter(i=>!keyFor(i,bindings)||!available.has(keyFor(i,bindings))).map(i=>i.id),displays=[];
 for(const item of requested){if(item.pairedIconKey&&!available.has(item.pairedIconKey))missing.push(item.id+':'+item.pairedIconKey);}
 for(const slot of list){const candidates=options.lampTest?slot.items:active.filter(i=>slot.items.some(s=>s.id===i.id));if(!candidates.length)continue;const item=[...candidates].sort((a,b)=>b.priority-a.priority)[0],key=keyFor(item,bindings);if(!available.has(key))continue;if(options.lampTest||item.on)displays.push({...slot,key,item,fixtureOnly:true});}
 return{slots:list,displays,activeFamilies:active.length,litIcons:displays.length,missing:[...new Set(missing)],lampTest:options.lampTest===true,customPlacement:true,nativeControllerBindingVerified:false};
}
return{slots,project,placement};
});
