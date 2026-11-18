'use strict';
const assert=require('assert'),{EventEmitter}=require('events'),path=require('path');
const root=process.argv[2];
const {Session,valid}=require(path.join(root,'javascript/session'));
const {pathAt}=require(path.join(root,'javascript/needle-math'));
const geometry=require(path.join(root,'javascript/geometry'));
const mask=require(path.join(root,'javascript/factory-mask'));
const inputs=require(path.join(root,'javascript/inputs'));
const extras=require(path.join(root,'javascript/round-extras'));
const {ClusterRender}=require(path.join(root,'javascript/cluster_render_client'));
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
{
 const {client,session}=make();
 session.update(sample());session.start();shown(client,session);session.tick();
 const tach=session.refs.find(layer=>layer.d&&layer.d.signal==='rpm');
 const pathMessages=()=>client.uniforms.filter(u=>u.ref===tach.ref&&u.name==='u_angles').length;
 const idleCount=pathMessages();
 for(let i=0;i<10;i++){now+=33;session.update(sample());session.tick();}
 assert.equal(pathMessages(),idleCount);
 const frames=[];
 for(let i=0;i<25;i++){
  now+=33;session.update(sample({rpm:3000}));session.tick();
  for(const offset of [0,1000/60])frames.push(pathAt(tach.path,(now+offset-tach.t0)/1000));
 }
 const target=3000/tach.d.max*tach.d.sweep;
 assert(frames.every((frame,index)=>index===0||frame>=frames[index-1]-0.02));
 assert(new Set(frames.map(frame=>frame.toFixed(1))).size>12);
 assert(Math.abs(frames.at(-1)-target)<0.02);
 assert.equal(tach.path.a[3],target);
 const movingCount=pathMessages();
 assert(movingCount>idleCount);
 for(let i=0;i<10;i++){now+=33;session.update(sample({rpm:3000}));session.tick();}
 assert.equal(pathMessages(),movingCount);
 session.stop();
}
for(const bad of [null,{},sample({speed:null}),sample({rpm:65535}),sample({speed:331}),sample({at:now-4000}),sample({at:now+1})])assert(!valid(bad,now));
{
 const {client,session}=make();
 assert.throws(()=>session.start());
 session.update(sample());session.start();
 assert.equal(client.assets.length,13);
 const compressedFaces=client.assets.filter(asset=>asset.format==='etc2rgba');
 assert.equal(compressedFaces.length,2);
 assert(compressedFaces.every(asset=>asset.w===688&&asset.h===688));
 assert(client.uniforms.some(entry=>entry.name==='u_speed'&&entry.values[0]===0));
 assert(client.layers.some(layer=>layer.fs.startsWith('#define F40_DIGITAL_SPEED')));
 const maskLayers=client.layers.filter(layer=>layer.z===5&&layer.fs===mask.shader);
 assert.equal(maskLayers.length,mask.pieces.length);
 assert(maskLayers.length>0);
 for(const layer of client.layers){
  assert(!layer.exclusive&&!layer.contend&&!layer.guide_hold);
  if(layer.fs!==extras.factoryGearShader)assert(geometry.holes.every(hole=>!geometry.intersect(layer,hole)));
  else assert.deepEqual({x:layer.x,y:layer.y,w:layer.w,h:layer.h},extras.factoryGearBounds);
 }
 assert(maskLayers.every(layer=>mask.reserves.every(hole=>!geometry.intersect(layer,hole))));
 const pixelBytes=client.assets.reduce((sum,asset)=>sum+asset.w*asset.h*(asset.format==='etc2rgba'?1:8),0);
 assert(pixelBytes<6*1024*1024);
 assert(pixelBytes+1088*480*1.5*4<16*1024*1024);
 shown(client,session);
 now+=50000;session.update(sample());session.tick();assert(session.active);
 for(const speed of [2,30,80]){
  session.update(sample({speed,checkControl:{clear:true,at:now}}));session.tick();
  assert(session.active);
  assert(client.uniforms.some(entry=>entry.name==='u_speed'&&entry.values[0]===speed));
 }
 // Speed and an optional Check Control snapshot never change theme lifetime.
 for(const checkControl of [null,{clear:false,at:now},{clear:true,at:now-60000}]){
  now+=10000;session.update(sample({speed:80,checkControl}));session.tick();assert(session.active);
 }
 now+=3501;session.tick();assert(!session.active&&client.closed);
 assert.equal(client.dropped.length,client.assets.length+client.layers.length);
}
{
 const client=new ClusterRender('asset-format-check');
 const opts={target:'panel',format:'etc2rgba',w:8,h:4};
 assert.equal(client.asset({...opts,w:7}),0);
 const ref=client.asset(opts), frame=Buffer.alloc(32);
 assert(ref);
 assert(!client.pixels(ref,null,Buffer.alloc(128)));
 assert(!client.pixels(ref,[{x:0,y:0,w:8,h:4}],frame));
 assert(client.pixels(ref,null,frame));
 assert(!client.pixels(ref,null,frame));
 client.close();
}
for(const checkControl of [null,{clear:true,at:now-1501},{clear:true,at:now+1}]){
 const {session}=make();
 session.update(sample({speed:50,checkControl:{clear:true,at:now}}));assert.throws(()=>session.start());
 session.update(sample());session.start();session.update(sample({speed:50,checkControl}));
 assert(session.active);session.stop();
}
for(const dial of geometry.dials){
 const bounds=geometry.bounds(dial);
 assert(bounds.y===80&&bounds.y+bounds.h===660);
 assert(bounds.x>=0&&bounds.x+bounds.w<=1920);
}
const parking=mask.reserves.find(r=>r.id==='parking-lamp');
for(const mini of geometry.minis){
 const bounds=geometry.bounds(mini);
 assert(!geometry.intersect(bounds,geometry.box),'Mini overlaps black box');
 assert(!geometry.intersect(bounds,parking),'Mini overlaps parking lamp');
 assert(bounds.y>=0&&bounds.y+bounds.h<=660,'Mini clips footer');
 assert.equal(bounds.h,Math.ceil(mini.y+mini.h*geometry.scale(mini)/2)-Math.floor(mini.y-mini.h*geometry.scale(mini)/2));
 assert.equal(geometry.pieces(mini).length,1,'Mini gets split by reservation');
 assert.equal(geometry.scale(mini),mini.side==='boost'?1:1.3);
}
for(let i=0;i<geometry.minis.length;i++)for(let j=i+1;j<geometry.minis.length;j++){
 const a=geometry.minis[i],b=geometry.minis[j];
 assert(Math.hypot(a.x-b.x,a.y-b.y)>a.radius+b.radius+30,'Mini dial faces collide');
}
const [speedDial,tachDial]=geometry.dials;
assert.equal(speedDial.y,tachDial.y);
assert.equal(speedDial.displaySize,700);
assert.equal(tachDial.displaySize,700);
assert(tachDial.x-speedDial.x>tachDial.displaySize);
const radius=tachDial.displaySize/2;
for(const endpoint of [180+tachDial.arcRotation,180+tachDial.sweep+tachDial.arcRotation])
 assert(tachDial.y+radius*Math.sin(endpoint*Math.PI/180)<geometry.centreWarning.y,'A tach endpoint crosses the warning opening');
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
assert.equal(inputs.selectionGear({statusGearSelectionDrive:'NP'},now).value,null);
assert.equal(inputs.selectionGear({statusGearSelectionDrive:'_3'},now).value,'D3');
assert.equal(inputs.stageGear({statusActualStageDrive:'M',statusActualGearDrive:'G2'},now).value,'M2');
assert.equal(inputs.currentGear({value:'P',at:now-3000},now),null);
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
 const temp=session.refs.find(layer=>layer.isTemperatureMask);
 const tempReading={value:90,at:now};
 session.update(sample({oil:tempReading,water:tempReading}));session.tick();
 session.update(sample({oil:tempReading,water:{value:90,at:now-3000}}));session.tick();
 assert.deepEqual(values(temp.ref,'u_show'),[0,1,0]);
 for(const role of ['oil','water']){
  const mini=session.refs.find(layer=>layer.d&&layer.d.signal===role);
  assert.deepEqual(values(mini.ref,'u_visible'),[0,1,0]);
  const scale=client.uniforms.find(u=>u.ref===mini.ref&&u.name==='u_artPerPixel');
  assert.equal(scale.values[0],1/1.3);
 }
 assert.equal(values(boost.ref,'u_visible').at(-1),1);
 const gearMask=session.refs.find(layer=>layer.isGearMask);
 session.update(sample({gear:inputs.selectionGear({statusGearSelectionDrive:3},now)}));session.tick();
 assert.deepEqual(values(rpm.ref,'u_gearGlyphs').slice(-2),[-1,0]);
 assert.deepEqual(values(gearMask.ref,'u_show'),[0,1]);
 session.update(sample({gear:inputs.selectionGear({statusGearSelectionDrive:4},now)}));session.tick();
 assert.deepEqual(values(gearMask.ref,'u_show'),[0,1,0]);
 tick(5200,'sport',true,33,0);assert.equal(values(boost.ref,'u_valid').at(-1),1);
 const zeroAngle=values(boost.ref,'u_angles').at(-1);
 for(const threshold of [5350,5500,5650,5800,5950,6150,6350,6500])tick(threshold,'sport',true,33,16);
 assert(values(boost.ref,'u_angles').at(-1)>zeroAngle);
 tick(6500,'sport',true,200);tick(6500,'sport',true,200);tick(6500,'comfort');
 assert.deepEqual(values(rpm.ref,'u_shiftStage'),[0,1,2,3,4,5,6,7,8,9,0,9,0]);
 const selected=inputs.driveMode({actualValueModeDrivingExperience:'SPORT_DYNAMIC'},now);
 now+=60000;
 session.update(sample({rpm:6150,mode:selected,shiftLights:true}));session.tick();
 assert.equal(values(rpm.ref,'u_shiftStage').at(-1),7);
 session.update(sample({rpm:6150,mode:null,shiftLights:true}));session.tick();
 assert.equal(values(rpm.ref,'u_shiftStage').at(-1),0);
 session.stop();
}
console.log('PASS curved mini clearance/scaling, temperature fallback, driving without Check Control heartbeat, full dial/indicator clearance, shift lights, boost and stale-data recovery.');
