'use strict';
const path=require('path'),{fork}=require('child_process');
const {OnlineApp,logging}=require('oap-sdk');
const signals=require('./kit/signals');
const {temperatures,boost}=require('./inputs');
const {valid}=require('./session'),spec=require('./app-spec.json');
const clock=()=>{const t=process.hrtime();return t[0]*1000+t[1]/1e6;};
async function start(){const app=new OnlineApp(),logger=logging.getSDKLogger();let worker=null,lease=null,heartbeat=null,subscriptions=[],speed=null,rpm=null,speedAt=-Infinity,rpmAt=-Infinity,mini={},monitor=null;
 const sample=()=>Object.assign({speed,rpm,at:Math.min(speedAt,rpmAt)},mini);
 const warn=e=>logger.warn('KombiKraft test: '+String(e&&e.message||e));
 let ui=null;const status=s=>{logger.info(s);if(ui)Promise.resolve(ui.getByName('MAIN_STATUS').setValue(0,'Text',s,'Text')).catch(warn);};
 function stop(){if(worker){const old=worker;worker=null;if(old.connected)old.send({op:'stop'});setTimeout(()=>{if(old.exitCode===null)old.kill('SIGKILL');},1000);}if(lease)clearTimeout(lease);if(heartbeat)clearInterval(heartbeat);lease=heartbeat=null;status('Factory display released.');}
 function run(mode,theme){if(worker){status('A test is already running. Use Show factory first.');return;}if(!valid(sample(),clock())){status('Waiting for fresh speed below 1 km/h and valid RPM. No output enabled.');return;}
  const child=fork(path.join(__dirname,'worker.js'),[],{stdio:['ignore','ignore','ignore','ipc']});worker=child;child.on('message',m=>m.status&&status(m.status));child.on('error',e=>{warn(e);stop();});child.on('exit',()=>{if(worker===child){worker=null;if(lease)clearTimeout(lease);if(heartbeat)clearInterval(heartbeat);lease=heartbeat=null;status('Factory display released.');}});child.send({op:'start',mode,theme,sample:sample()});heartbeat=setInterval(()=>{if(worker===child&&child.connected)child.send({op:'sample',sample:sample()});},100);lease=setTimeout(stop,23000);
 }
 app.on('appStatusProxyReady',()=>Promise.resolve(app.registerActive()).catch(warn));app.on('shutdown',()=>{stop();if(monitor)clearInterval(monitor);subscriptions.forEach(s=>s.shutdown());setTimeout(()=>process.exit(0),100);});process.on('SIGTERM',()=>{stop();setTimeout(()=>process.exit(0),100);});
 await app.start();await app.registerActive();ui=app.rhmiApplication;if(!ui){status('Native menu unavailable. Output remains off.');return app;}
 for(const [button,fn] of [['LIVE',()=>run('live','round')],['TOURING',()=>run('live','touring')],['SWEEP',()=>run('sweep','round')],['STOP',stop]])ui.getByName(button).on('action',()=>{try{fn();}catch(e){stop();warn(e);}});
 for(const uuid of Object.keys(spec.entryRoutes))await ui.mapEntryState(uuid,ui.getByName('MAIN'));
 const open=uuid=>{if(Object.prototype.hasOwnProperty.call(spec.entryRoutes,uuid))Promise.resolve(ui.openEntryState(uuid)).catch(warn);};app.on('entryPointExecute',open);await ui.getByName('MAIN').updateResources();await app.initialized();const entry=app.getLastExecutedEntryPointUuid&&app.getLastExecutedEntryPointUuid();if(entry)open(entry);
 status('Output off. Read-only signals starting. Parked tests expire after 20 seconds.');
 // Both readers only get/subscribe. No setters, diagnostic commands or inferred/demo fallback.
 subscriptions.push(await signals.watch('de.bmw.infotainment.vehicle.Vehicle2','1',{statusCarSpeed2:v=>{const n=v&&v.speedVehicleCentreOfGravity;speed=Number.isInteger(n)&&n>=0&&n<65535?n*.015625:null;speedAt=clock();}},logger,{pollMs:1000}));
 subscriptions.push(await signals.watch('de.bmw.infotainment.vehicle.CDS','1',{statusEngineSpeed2:v=>{const n=v&&v.actualValueRPMEngineCrankshaft;rpm=Number.isInteger(n)&&n>=0&&n<65535?n*.25:null;rpmAt=clock();},statusEngineTemperature:v=>Object.assign(mini,temperatures(v,clock()))},logger,{pollMs:1000}));
 subscriptions.push(await signals.watch('de.bmw.infotainment.drivingexcitement.FES','1',{statusSwitchDriveDynamicSport2:v=>{mini.boost=boost(v,clock());}},logger,{pollMs:1000}));
 monitor=setInterval(()=>{const describe=(key,unit)=>{const v=mini[key];return v&&Number.isFinite(v.value)&&clock()-v.at<3000?v.value.toFixed(1)+unit:'—';};Promise.resolve(ui.getByName('SENSORS').setValue(0,'Text','Oil '+describe('oil','°C')+' · Water '+describe('water','°C')+' · Boost '+describe('boost',' psi'),'Text')).catch(warn);},1000);
 if(subscriptions.slice(0,2).some(s=>s.error))status('Signal subscription unavailable. Tests remain disabled.');return app;
}
module.exports={start};if(require.main===module)start().catch(e=>logging.getSDKLogger().error(String(e&&e.stack||e)));
