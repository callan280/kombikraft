'use strict';
const fs=require('fs'),path=require('path'),{fork}=require('child_process');
const {OnlineApp,logging}=require('oap-sdk');
const signals=require('./kit/signals');
const {temperatures,boost,fresh,selectBoost,driveMode,currentMode,stageGear,selectionGear,currentGear}=require('./inputs');
const {enginePressure}=require('./engine-pressure');
const {Preferences}=require('./preferences');
const {valid}=require('./session'),spec=require('./app-spec.json');
const clock=()=>{const t=process.hrtime();return t[0]*1000+t[1]/1e6;};

async function start(options={}){
 const app=new OnlineApp(),logger=logging.getSDKLogger();
 const data=path.resolve(__dirname,'..','..','data');
 const preferences=new Preferences(spec.settings,options.dataDir||(fs.existsSync(data)?data:process.cwd()));
 const subscriptions=[];
 let worker=null,heartbeat=null,monitor=null,ui=null;
 let speed=null,rpm=null,speedAt=-Infinity,rpmAt=-Infinity,fesBoost=null,dmeBoost=null,stage=null,selection=null;
 const mini={};
 const sample=()=>Object.assign({speed,rpm,at:Math.min(speedAt,rpmAt),
  boost:selectBoost(dmeBoost,fesBoost,clock()),shiftLights:preferences.get('sportShiftLights'),
  gear:currentGear(stage,clock())?stage:selection},mini);
 const warn=error=>logger.warn('KombiKraft: '+String(error&&error.message||error));
 const text=(name,value)=>Promise.resolve(ui.getByName(name).setValue(0,'Text',value,'Text')).catch(warn);
 const status=value=>{logger.info(value);if(ui)text('MAIN_STATUS',value);};
 const pressure=enginePressure(signals,logger,clock,
  ()=>!!worker&&valid(sample(),clock())&&rpm>0,value=>{dmeBoost=value;});

 function stop(){
  if(worker){
   const old=worker;worker=null;
   if(old.connected)old.send({op:'stop'});
   setTimeout(()=>{if(old.exitCode===null)old.kill('SIGKILL');},1000);
  }
  clearInterval(heartbeat);heartbeat=null;
  status('Factory display released.');
 }
 function run(){
  if(worker){status('M Round is already on.');return;}
  if(!valid(sample(),clock())){status('Waiting for a fresh stationary speed and RPM reading.');return;}
  const child=fork(path.join(__dirname,'worker.js'),[],{stdio:['ignore','ignore','ignore','ipc']});
  worker=child;
  child.on('message',message=>{if(message.status&&worker===child)status(message.status);});
  child.on('error',error=>{warn(error);if(worker===child)stop();});
  child.on('exit',(code,signal)=>{
   if(worker!==child)return;
   worker=null;clearInterval(heartbeat);heartbeat=null;
   if(code!==0)status('Theme worker exited: '+(signal||code));
  });
  child.send({op:'start',sample:sample()});
  heartbeat=setInterval(()=>{if(worker===child&&child.connected)child.send({op:'sample',sample:sample()});},100);
 }

 app.on('appStatusProxyReady',()=>Promise.resolve(app.registerActive()).catch(warn));
 app.on('shutdown',()=>{stop();clearInterval(monitor);subscriptions.forEach(sub=>sub.shutdown());setTimeout(()=>process.exit(0),100);});
 process.on('SIGTERM',()=>{stop();setTimeout(()=>process.exit(0),100);});
 await app.start();await app.registerActive();
 ui=app.rhmiApplication;
 if(!ui){status('Native menu unavailable.');return app;}
 const checkbox=ui.getByName('PREF_SPORTSHIFTLIGHTS');
 const refreshCheckbox=()=>Promise.resolve(checkbox.setValue(0,'eParam_RowSelected',preferences.get('sportShiftLights'),'Bool')).catch(warn);
 checkbox.on('action',()=>{
  try{preferences.set('sportShiftLights',!preferences.get('sportShiftLights'));}
  catch(error){warn(error);status('Could not save the shift-light setting.');}
  refreshCheckbox();
 });
 ui.getByName('LIVE').on('action',()=>{try{run();}catch(error){stop();warn(error);}});
 ui.getByName('STOP').on('action',stop);
 for(const uuid of Object.keys(spec.entryRoutes))await ui.mapEntryState(uuid,ui.getByName('MAIN'));
 const open=uuid=>{if(Object.prototype.hasOwnProperty.call(spec.entryRoutes,uuid))Promise.resolve(ui.openEntryState(uuid)).catch(warn);};
 app.on('entryPointExecute',open);
 await ui.getByName('MAIN').updateResources();await refreshCheckbox();await app.initialized();
 const entry=app.getLastExecutedEntryPointUuid&&app.getLastExecutedEntryPointUuid();if(entry)open(entry);
 status('Factory display active. M Round is available while parked.');

 subscriptions.push(await signals.watch('de.bmw.infotainment.vehicle.Vehicle2','1',{
  statusCarSpeed2:value=>{const n=value&&value.speedVehicleCentreOfGravity;speed=Number.isInteger(n)&&n>=0&&n<65535?n*.015625:null;speedAt=clock();}
 },logger,{pollMs:1000}));
 subscriptions.push(await signals.watch('de.bmw.infotainment.vehicle.CDS','1',{
  statusEngineSpeed2:value=>{const n=value&&value.actualValueRPMEngineCrankshaft;rpm=Number.isInteger(n)&&n>=0&&n<65535?n*.25:null;rpmAt=clock();},
  statusEngineTemperature:value=>Object.assign(mini,temperatures(value,clock()))
 },logger,{pollMs:1000}));
 subscriptions.push(await signals.watch('de.bmw.infotainment.drivingexcitement.FES','1',{
  statusSwitchDriveDynamicSport2:value=>{fesBoost=boost(value,clock());},
  statusFESVehicleDynamicSwitchHMI:value=>{mini.mode=driveMode(value,clock());}
 },logger,{pollMs:1000}));
 subscriptions.push(await signals.watch('de.bmw.infrastructure.VehicleInformation','1',{
  statusGearboxDrive:value=>{stage=stageGear(value,clock());},
  DataPowerTrain2:value=>{selection=selectionGear(value,clock());}
 },logger,{pollMs:1000}));
 monitor=setInterval(()=>{
  pressure.poll();
  const current=sample(),now=clock();
  const temperature=key=>{const n=fresh(current[key],now,3000);return n===null?'—':n.toFixed(1)+'°C';};
  const mode={sport:'Sport',comfort:'Comfort',eco:'Eco Pro'}[currentMode(current.mode,now)]||'—';
  const boostReading=current.boost?current.boost.value.toFixed(1)+' psi ('+(current.boost===dmeBoost?'DME':'Sport display')+')':'unavailable';
  text('SENSORS','Oil '+temperature('oil')+' · Water '+temperature('water')+' · Boost '+boostReading+' · '+mode);
 },1000);
 if(subscriptions.slice(0,2).some(sub=>sub.error))status('Core vehicle signals unavailable.');
 return app;
}
module.exports={start};
if(require.main===module)start().catch(error=>logging.getSDKLogger().error(String(error.stack||error)));
