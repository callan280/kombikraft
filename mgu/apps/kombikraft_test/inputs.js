'use strict';
// BMW field decoding reused from aidac/apps kit/runtime/car.js and shared/hud.js.
// Source validation is not proof that this particular F40 supplies valid samples.
const PSI_PER_BAR=14.503773773;
function raw(n,max){return Number.isInteger(n)&&n>=0&&n<max;}
function temperatures(v,at){return{ oil:{value:v&&raw(v.temperatureEngineOilDrive,255)?v.temperatureEngineOilDrive-48:null,at},water:{value:v&&raw(v.temperatureEngineDrive,255)?v.temperatureEngineDrive-48:null,at}};}
function boost(v,at){const n=v&&v.displayBoostPressure;return{value:raw(n,255)?n*.01*PSI_PER_BAR:null,at};}
function miniValue(sample,d,now){const item=sample&&sample[d.signal];return item&&Number.isFinite(item.value)&&Number.isFinite(item.at)&&now>=item.at&&now-item.at<3000?Math.max(0,Math.min(d.max,item.value)):null;}
function fresh(item,now,ms){
 return item&&Number.isFinite(item.value)&&Number.isFinite(item.at)&&now>=item.at&&now-item.at<ms?item.value:null;
}
function pressureBoost(absoluteKpa,ambientKpa,at){
 const delta=(absoluteKpa-ambientKpa)*PSI_PER_BAR/100;
 return {value:Number.isFinite(absoluteKpa)&&Number.isFinite(ambientKpa)&&delta<=50?Math.max(0,delta):null,at};
}
function selectBoost(dme,fes,now){
 const engine=fresh(dme,now,3000),sport=fresh(fes,now,3000);
 // A zero from the engine source can reflect manifold vacuum while FES
 // still provides a current positive charge-pressure reading.
 if(engine>0||engine===0&&(sport===null||sport===0))return dme;
 return sport!==null?fes:null;
}
const GEAR_GLYPHS='PRNDSM12345678';
const GEAR_STAGES={P:'P',R:'R',N:'N',D:'D',S:'S',M:'M',1:'P',2:'R',3:'N',4:'D'};
function stageGear(raw,at){
 const stage=raw&&GEAR_STAGES[raw.statusActualStageDrive];
 const gear=raw&&raw.statusActualGearDrive;
 const numeric=typeof gear==='string'&&/^G[1-8]$/.test(gear)?Number(gear.slice(1)):Number(gear)-2;
 return {value:stage?stage+(/^[DSM]$/.test(stage)&&numeric>=1&&numeric<=8?numeric:''):null,at};
}
// DataPowerTrain2 separates Park and Neutral. NP is deliberately ambiguous.
function selectionGear(raw,at){
 const value=raw&&raw.statusGearSelectionDrive;
 const n=typeof value==='string'&&/^_[1-8]$/.test(value)?Number(value.slice(1))+4:Number(value);
 const label={N:'N',R:'R',P:'P',1:'N',2:'R',3:'P'}[value]||(n>=5&&n<=12?'D'+(n-4):null);
 return {value:label,at};
}
function currentGear(gear,now){
 return gear&&/^(?:[PRN]|[DSM][1-8]?)$/.test(gear.value)&&Number.isFinite(gear.at)&&gear.at<=now&&now-gear.at<3000?gear.value:null;
}
function gearGlyphs(label){
 return label?[GEAR_GLYPHS.indexOf(label[0]),label.length>1?GEAR_GLYPHS.indexOf(label[1]):-1]:[-1,-1];
}
// BMW's FES variants share the same visual group for this theme.
function driveMode(v,at){
 const raw=v&&v.actualValueModeDrivingExperience;
 let value=null;
 if(typeof raw==='number'||typeof raw==='string'&&/^\d+$/.test(raw.trim())){
  const n=Number(raw);
  if(Number.isInteger(n)&&n>=1&&n<=3)value='sport';
  else if((Number.isInteger(n)&&n>=4&&n<=6)||n===10)value='comfort';
  else if(Number.isInteger(n)&&n>=7&&n<=9)value='eco';
 }else if(typeof raw==='string'){
  const name=raw.trim().toUpperCase().replace(/[ +\-]+/g,'_');
  if(/^SPORT(?:_|$)/.test(name))value='sport';
  else if(/^ECO(?:_|$)/.test(name))value='eco';
  else if(/^(?:COMFORT|KOMFORT|ADAPTIVE|ADAPTIV)(?:_|$)/.test(name))value='comfort';
 }
 return {value,at};
}
function currentMode(item,now){
 // Mode is a discrete setting. Some FES variants notify only when it changes.
 return item&&item.value&&Number.isFinite(item.at)&&now>=item.at?item.value:null;
}
module.exports={driveMode,currentMode,temperatures,boost,miniValue,fresh,pressureBoost,selectBoost,stageGear,selectionGear,currentGear,gearGlyphs,PSI_PER_BAR};
