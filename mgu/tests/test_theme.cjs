'use strict';
const assert=require('assert'),{EventEmitter}=require('events'),path=require('path');
const root=process.argv[2];
const {Session,valid}=require(path.join(root,'javascript/session'));
const geometry=require(path.join(root,'javascript/geometry'));
const mask=require(path.join(root,'javascript/factory-mask'));
const inputs=require(path.join(root,'javascript/inputs'));
class Client extends EventEmitter{
 constructor(){super();this.id=0;this.layers=[];this.assets=[];this.uniforms=[];this.dropped=[];}
 asset(options){this.assets.push(options);return ++this.id;}
 pixels(){return true;}
 effect(options){this.layers.push(options);return ++this.id;}
 bind(){}
 uniform(ref,name,values){assert(values.every(Number.isFinite));this.uniforms.push({ref,name,values});}
 connect(){this.backend='id7';this.targets='map:1088x480,panel:1920x720';this.emit('ready');}
 drop(ref){this.dropped.push(ref);}
 close(){this.closed=true;}
}
let now=1000;
function make(){
 const client=new Client(),reports=[];
 const session=new Session(client,{now:()=>now,art:path.join(root,'javascript/art'),report:value=>reports.push(value)});
 return {client,session,reports};
}
const sample=(values={})=>Object.assign({speed:0,rpm:750,at:now},values);
const shown=(client,session)=>session.refs.forEach(layer=>client.emit('layer',layer.ref,'shown'));
for(const bad of [null,{},sample({speed:null}),sample({rpm:65535}),sample({speed:2}),sample({at:now-4000}),sample({at:now+1})])assert(!valid(bad,now));
{
 const {client,session}=make();
 assert.throws(()=>session.start());
 session.update(sample());session.start();
 assert.equal(client.assets.length,12);
 assert(client.uniforms.some(entry=>entry.name==='u_speed'&&entry.values[0]===0));
 assert.equal(client.layers.filter(layer=>layer.fs.startsWith('#define F40_DIGITAL_SPEED')).length,1);
 const maskLayers=client.layers.filter(layer=>layer.z===5);
 assert.equal(maskLayers.length,mask.pieces.length);
 assert(maskLayers.length>0);
 for(const layer of client.layers){
  assert(!layer.exclusive&&!layer.contend&&!layer.guide_hold);
  assert(geometry.holes.every(hole=>!geometry.intersect(layer,hole)));
 }
 assert(maskLayers.every(layer=>mask.reserves.every(hole=>!geometry.intersect(layer,hole))));
 assert(client.assets.reduce((sum,asset)=>sum+asset.w*asset.h*8,0)+1088*480*1.5*4<16*1024*1024);
 shown(client,session);
 now+=50000;session.update(sample());session.tick();assert(session.active);
 session.update(sample({speed:1.1}));assert(!session.active&&client.closed);
 assert.equal(client.dropped.length,client.assets.length+client.layers.length);
}
for(const dial of geometry.dials){
 const bounds=geometry.bounds(dial);
 assert(bounds.x>=0&&bounds.y>=0&&bounds.x+bounds.w<=1920&&bounds.y+bounds.h<=510);
 for(const box of geometry.turnIndicators){
  const dx=Math.max(box.x-dial.x,dial.x-box.x-box.w,0);
  const dy=Math.max(box.y-dial.y,dial.y-box.y-box.h,0);
  assert(Math.hypot(dx,dy)>=dial.displaySize/2,'An indicator would clip the circular face');
 }
}
assert.equal(geometry.dials[0].y,geometry.dials[1].y);
assert.equal(geometry.dials[0].displaySize,geometry.dials[1].displaySize);
for(const event of ['disconnected','refused','suspended','stale','timeout','stalled']){
 const {client,session,reports}=make();session.update(sample());session.start();
 if(event==='suspended')client.emit('layer',session.refs[0].ref,'suspended');
 else if(event==='stale'){now+=3501;session.tick();}
 else if(event==='timeout'){now+=9000;session.update(sample());session.tick();assert(/^Renderer startup timed out/.test(reports.at(-1)));}
 else if(event==='stalled'){
  client.emit('layer',session.refs[0].ref,'stalled');assert(session.active);
  shown(client,session);session.tick();client.emit('layer',session.refs[0].ref,'stalled');
 }else client.emit(event);
 assert(!session.active&&client.closed,event);
}
{
 const {client,session}=make();client.connect=function(){this.backend='id8';this.targets='panel:1920x720';this.emit('ready');};
 session.update(sample());session.start();assert(!session.active&&client.closed);assert.equal(client.layers.length,0);
}
assert.equal(inputs.temperatures({temperatureEngineOilDrive:138,temperatureEngineDrive:148},now).oil.value,90);
assert.equal(inputs.temperatures({temperatureEngineOilDrive:255,temperatureEngineDrive:148},now).oil.value,null);
assert.equal(inputs.temperatures({temperatureEngineOilDrive:138,temperatureEngineDrive:148},now).water.value,100);
assert.equal(inputs.boost({displayBoostPressure:255},now).value,null);
assert.equal(inputs.pressureBoost(null,100,now).value,null);
const engine=inputs.pressureBoost(150,100,now);
const sport=inputs.boost({displayBoostPressure:100},now);
const zero={value:0,at:now};
assert(Math.abs(engine.value-7.2518868865)<1e-9);
assert(Math.abs(sport.value-14.503773773)<1e-8);
assert.equal(inputs.selectBoost(engine,sport,now),engine);
assert.equal(inputs.selectBoost(zero,sport,now),sport);
assert.equal(inputs.selectBoost(zero,null,now),zero);
assert.equal(inputs.selectBoost(engine,sport,now+3000),null);
assert.equal(inputs.driveMode({actualValueModeDrivingExperience:'SPORT_DYNAMIC'},now).value,'sport');
assert.equal(inputs.driveMode({actualValueModeDrivingExperience:'ECO_PRO_EFFICIENT'},now).value,'eco');
assert.equal(inputs.driveMode({actualValueModeDrivingExperience:'4'},now).value,'comfort');
{
 const {client,session}=make();session.update(sample());session.start();shown(client,session);
 const rpm=session.refs.find(layer=>layer.shiftStage!==undefined);
 const boost=session.refs.find(layer=>layer.d&&layer.d.signal==='boost');
 const values=(ref,name)=>client.uniforms.filter(item=>item.ref===ref&&item.name===name).map(item=>item.values[0]);
 const tick=(value,mode,shiftLights=true,advance=33,boostValue=null)=>{
  now+=advance;
  session.update(sample({rpm:value,mode:{value:mode,at:now},shiftLights,boost:{value:boostValue,at:now}}));
  session.tick();
 };
 tick(6600,'comfort');tick(6600,'eco');tick(6600,'sport',false);
 assert.deepEqual(values(rpm.ref,'u_shiftStage'),[0]);
 assert.equal(values(boost.ref,'u_valid').at(-1),0);
 tick(5200,'sport',true,33,0);assert.equal(values(boost.ref,'u_valid').at(-1),1);
 const zeroAngle=values(boost.ref,'u_angles').at(-1);
 for(const threshold of [5350,5500,5650,5800,5950,6150,6350,6500])tick(threshold,'sport',true,33,16);
 assert(values(boost.ref,'u_angles').at(-1)>zeroAngle);
 tick(6500,'sport',true,200);tick(6500,'sport',true,200);tick(6500,'comfort');
 assert.deepEqual(values(rpm.ref,'u_shiftStage'),[0,1,2,3,4,5,6,7,8,9,0,9,0]);
 tick(6500,'sport');
 now+=3501;
 session.update(sample({rpm:6500,mode:{value:'sport',at:now-3501},shiftLights:true}));
 session.tick();
 assert.deepEqual(values(rpm.ref,'u_shiftStage').slice(-2),[9,0]);
 session.stop();
}
console.log('PASS full dial and turn indicator clearance, factory mask, Sport shift lights, boost and parked recovery.');
