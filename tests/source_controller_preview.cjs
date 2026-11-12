/* Authored protocol/state checks; original-code execution is tested separately. */
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const root=path.resolve(__dirname,'..'),modelApi=require(path.join(root,'src/kombikraft/web/design/source-controller-preview.js'));
const metadata=JSON.parse(fs.readFileSync(path.join(root,'src/kombikraft/factory/cc_preview_contract.json'),'utf8'));
const copy=x=>JSON.parse(JSON.stringify(x));
function selected(row){return {sourceProfile:metadata.sourceProfile,selectedCcid:row?.ccid??0,originalPayloadConsumerObserved:true,payloadReadbackMatchesConsumer:true,textLines:row?row.textLines:[null,null],primaryIcon:row?row.primaryIcon:null,collectionSlots:[],iconSelector:row?row.iconSelector:255,textSelector:row?row.textSelector:255};}
function plan(row){return {schema:'original-cc-custom-canvas-plan-v1',status:'supported',action:row?'show':'clear',selectedCcid:row?.ccid??0,popup:row?{...copy(row.popup),originalControllerComputed:true}:null,sourceProfile:metadata.sourceProfile,customComposition:true,factoryGraphics:false,vehicleCompatibilityVerified:false};}
const base={signals:{gear:'D'},popup:{id:'authored-fault',text:'Authored example'},bc:{page:'media'},indicators:[]},entries=metadata.records.map(r=>copy(r.popup));
let checks=0;
for(const row of metadata.records){
 const model=modelApi.create(),result={signal:'checkControl',selected:selected(row)};
 assert.equal(model.accept(plan(row),result).applied,true);
 const projected=model.project(base,entries);
 assert.equal(projected.popup.ccid,row.ccid);assert.equal(projected.popup.originalControllerComputed,true);
 assert.deepEqual(projected.popup.originalLines,row.textLines);assert.equal(projected.bc,base.bc);
 assert.equal(model.accept(plan(row),result).applied,true);assert.deepEqual(model.project(base,entries),projected);
 assert.equal(model.accept(plan(null),{signal:'checkControl',selected:selected(null)}).applied,true);
 assert.equal(model.project(base,entries).popup,null);assert.equal(model.project(base,entries).bc,base.bc);
 assert.equal(base.popup.id,'authored-fault');model.release();assert.equal(model.project(base,entries),base);checks++;
}
{
 const model=modelApi.create(),row=metadata.records[0];model.accept(plan(row),{signal:'checkControl',selected:selected(row)});
 const before=model.snapshot();assert.equal(model.accept(null,{signal:'bc',events:[0x98]}).ignored,true);assert.deepEqual(model.snapshot(),before);
 const unsupported={...plan(row),status:'unsupported',action:null,popup:null,reason:'Unreviewed collection'};
 assert.equal(model.accept(unsupported,{signal:'checkControl',selected:{...selected(row),selectedCcid:34}}).applied,false);
 assert.equal(model.project(base,entries).popup,null);assert.equal(model.snapshot().status,'unsupported');assert.equal(model.snapshot().selectedCcid,34);checks++;
}
{
 const model=modelApi.create(),row=metadata.records[0];model.accept(plan(row),{signal:'checkControl',selected:selected(row)});
 assert.equal(model.project(base,[]).originalControllerPreview.status,'waiting-for-assets');
 const changed=copy(entries);changed[0].iconRgb=[255,0,0];
 assert.equal(model.project(base,changed).popup,null);assert.equal(model.project(base,changed).originalControllerPreview.status,'unsupported');checks++;
}
for(const mutate of [p=>p.sourceProfile='other',p=>p.factoryGraphics=true,p=>p.popup.originalLines=['Wrong',''],p=>p.popup.iconKey='another',p=>p.selectedCcid=true]){
 const model=modelApi.create(),row=metadata.records[0],p=plan(row);mutate(p);
 assert.equal(model.accept(p,{signal:'checkControl',selected:selected(row)}).applied,false);assert.equal(model.project(base,entries).popup,null);checks++;
}
{
 const model=modelApi.create(),bad=selected(null);bad.textLines=['',''];assert.equal(model.accept(plan(null),{signal:'checkControl',selected:bad}).applied,false);
 assert.equal(model.project(base,entries).originalControllerPreview.status,'unsupported');checks++;
}
console.log(JSON.stringify({passed:true,protocolStateChecks:checks,originalFirmwareExecuted:false}));
