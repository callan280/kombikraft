'use strict';
// BMW field decoding reused from aidac/apps kit/runtime/car.js and shared/hud.js.
// Source validation is not proof that this particular F40 supplies valid samples.
const PSI_PER_BAR=14.503773773;
function raw(n,max){return Number.isInteger(n)&&n>=0&&n<max;}
function temperatures(v,at){return{ oil:{value:v&&raw(v.temperatureEngineOilDrive,255)?v.temperatureEngineOilDrive-48:null,at},water:{value:v&&raw(v.temperatureEngineDrive,255)?v.temperatureEngineDrive-48:null,at}};}
function boost(v,at){const n=v&&v.displayBoostPressure;return{value:raw(n,255)?n*.01*PSI_PER_BAR:null,at};}
function miniValue(sample,d,now){const item=sample&&sample[d.signal];return item&&Number.isFinite(item.value)&&Number.isFinite(item.at)&&now>=item.at&&now-item.at<3000?Math.max(0,Math.min(d.max,item.value)):null;}
const F40_TANK_LITRES=50;
function fuel(v,at){
 const n=v&&v.fluidLevelFuelTank;
 return {value:raw(n,255)&&n<=F40_TANK_LITRES+2?Math.min(1,n/F40_TANK_LITRES):null,at};
}
function fresh(item,now,ms){
 return item&&Number.isFinite(item.value)&&Number.isFinite(item.at)&&now>=item.at&&now-item.at<ms?item.value:null;
}
function pressureBoost(absoluteKpa,ambientKpa,at){
 const delta=(absoluteKpa-ambientKpa)*PSI_PER_BAR/100;
 return {value:Number.isFinite(absoluteKpa)&&Number.isFinite(ambientKpa)&&delta<=50?Math.max(0,delta):null,at};
}
function selectBoost(dme,fes,now){
 if(fresh(dme,now,3500)!==null)return dme;
 return fresh(fes,now,3000)!==null?fes:null;
}
module.exports={temperatures,boost,miniValue,fuel,fresh,pressureBoost,selectBoost,PSI_PER_BAR};
