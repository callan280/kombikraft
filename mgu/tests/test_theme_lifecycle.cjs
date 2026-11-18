'use strict';
const assert=require('assert'),fs=require('fs'),Module=require('module'),os=require('os'),path=require('path'),{EventEmitter}=require('events');
const root=process.argv[2],rows={},children=[],watches=[];
const dataDir=fs.mkdtempSync(path.join(os.tmpdir(),'kombikraft-rhmi-'));
class Item extends EventEmitter{
 setValue(...args){this.value=args[2];return Promise.resolve();}
 updateResources(){return Promise.resolve();}
}
class App extends EventEmitter{
 constructor(){super();this.rhmiApplication={getByName:n=>rows[n]||(rows[n]=new Item()),mapEntryState:()=>Promise.resolve(),openEntryState:()=>Promise.resolve()};}
 start(){return Promise.resolve();} registerActive(){return Promise.resolve();} initialized(){return Promise.resolve();}
 getLastExecutedEntryPointUuid(){return null;}
}
const load=Module._load;
Module._load=function(name){
 if(name==='oap-sdk')return{OnlineApp:App,logging:{getSDKLogger:()=>({warn(){},error(){},info(){}})}};
 if(name==='child_process')return{fork(){
  const child=new EventEmitter();child.connected=true;child.exitCode=null;child.sent=[];
  child.send=message=>{child.sent.push(message);if(message.op==='stop'){child.exitCode=0;child.emit('exit',0);}};
  children.push(child);return child;
 }};
 if(name==='./kit/signals')return{watch:async(iface,instance,handlers,log,opts)=>{
  watches.push({iface,instance,handlers,opts});return{error:null,shutdown:()=>Promise.resolve()};
 }};
 return load.apply(this,arguments);
};
(async()=>{
 const app=await require(path.join(root,'javascript/app')).start({dataDir});
 assert.equal(children.length,0);
 rows.LIVE.emit('action');assert.equal(children.length,0);
 const check=rows.PREF_SPORTSHIFTLIGHTS;
 assert.equal(check.value,true);check.emit('action');assert.equal(check.value,false);
 assert.equal(JSON.parse(fs.readFileSync(path.join(dataDir,'kombikraft-preferences.json'))).preferences.sportShiftLights,false);
 for(const {handlers} of watches){
  if(handlers.statusCarSpeed2)handlers.statusCarSpeed2({speedVehicleCentreOfGravity:0});
  if(handlers.statusEngineSpeed2)handlers.statusEngineSpeed2({actualValueRPMEngineCrankshaft:3200});
  if(handlers.statusEngineTemperature)handlers.statusEngineTemperature({temperatureEngineOilDrive:138,temperatureEngineDrive:148});
  if(handlers.statusSwitchDriveDynamicSport2)handlers.statusSwitchDriveDynamicSport2({displayBoostPressure:100});
  if(handlers.DataPowerTrain2)handlers.DataPowerTrain2({statusGearSelectionDrive:'P'});
 }
 rows.LIVE.emit('action');assert.equal(children.length,1);
 const child=children[0],start=child.sent[0];
 assert.equal(start.op,'start');assert.equal(start.sample.rpm,800);assert.equal(start.sample.oil.value,90);
 assert.equal(start.sample.water.value,100);assert(Math.abs(start.sample.boost.value-14.503773773)<1e-8);
 assert.equal(start.sample.shiftLights,false);
 check.emit('action');assert.equal(check.value,true);
 await new Promise(resolve=>setTimeout(resolve,150));
 assert.equal(child.sent.at(-1).sample.shiftLights,true);
 rows.STOP.emit('action');assert.equal(child.sent.at(-1).op,'stop');
 assert.equal(watches.length,5);
 assert.equal(start.sample.gear.value,'P');
 assert.deepEqual(Object.keys(rows).filter(name=>rows[name].listenerCount('action')),['PREF_SPORTSHIFTLIGHTS','LIVE','STOP']);
 console.log('PASS one M Round mode, persistent Sport light toggle, live source inputs and factory release.');
 app.emit('shutdown');
})().catch(error=>{console.error(error);process.exitCode=1;process.exit();}).finally(()=>fs.rmSync(dataDir,{recursive:true,force:true}));
