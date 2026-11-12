(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.ClusterSimulationCatalog=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 // Preview policy and sample wording, not recovered BMW control logic or CC text.
 const inventory=[];
 function item(id,label,kind,source,color,priority,extra){inventory.push(Object.assign({id,label,kind,source,color,priority,iconKey:null,simulated:true,factoryTextVerified:false},extra));}
 item('turn-left','Left indicator','indicator','turnLeft','green',0,{blink:true,iconKey:'turnLeft'});
 item('turn-right','Right indicator','indicator','turnRight','green',0,{blink:true,iconKey:'turnRight'});
 item('hazards','Hazard indicators','indicator','hazards','green',0,{blink:true});
 item('high-beam','High beam','indicator','highBeam','blue',0);
 item('low-beam','Dipped headlights','indicator','lowBeamEffective','green',0,{iconKey:'lowBeam'});
 item('side-lights','Side lights','indicator','sideLightsEffective','green',0,{iconKey:'sideLights'});
 item('parking-light-left','Left parking light','indicator','parkingLightLeft','green',0,{iconKey:'parkingLeft'});
 item('parking-light-right','Right parking light','indicator','parkingLightRight','green',0,{iconKey:'parkingRight'});
 item('high-beam-assist','High-beam assistant enabled','indicator','autoHighBeamEnabled','white',0);
 item('front-fog','Front fog lamps','indicator','frontFog','green',0,{iconKey:'frontFog'});
 item('rear-fog','Rear fog lamp','indicator','rearFog','amber',0,{iconKey:'rearFog'});
 item('seatbelt','Fasten seat belt','fault','seatbelt','red',70,{iconLimitation:'Front-seat warning glyph unverified; rear-seat-belt art is not substituted'});
 item('door-open','Door open','fault','doorOpen','amber',55);
 item('fuel-reserve','Fuel reserve','fault','fuelReserve','amber',50);
 item('tyre-pressure','Tyre pressure warning','fault','tyrePressureLow','amber',60,{latched:true,iconKey:'tyrePressure'});
 item('engine','Engine warning','fault','engineFault','amber',60,{latched:true});
 item('oil-pressure','Oil pressure warning','fault','oilPressureLow','red',100,{latched:true,critical:true});
 item('coolant','Engine temperature warning','fault','coolantOverheat','red',100,{latched:true,critical:true});
 item('brake','Brake system warning','fault','brakeFault','red',100,{latched:true,critical:true,iconKey:'brake'});
 item('parking-brake','Parking brake','indicator','parkingBrake','red',0,{iconKey:'parkingBrake'});
 item('parking-brake-moving','Release parking brake','fault','parkingBrakeMoving','red',90,{critical:true,iconKey:'parkingBrake'});
 item('abs','ABS warning','fault','absFault','amber',65,{latched:true,iconKey:'abs'});
 item('dsc','Stability control warning','fault','dscFault','amber',65,{latched:true,iconKey:'dsc'});
 item('dsc-active','Stability control intervening','indicator','dscActive','amber',0,{blink:true,iconKey:'dsc'});
 item('cruise-standby','Cruise control ready','indicator','cruiseStandby','white',0,{iconKey:'cruise'});
 item('cruise-active','Cruise control active','indicator','cruiseActive','green',0,{iconKey:'cruise'});
 item('assistance-active','Driving assistance active','indicator','assistanceActive','green',0,{iconKey:'assistance'});
 item('assistance-warning','Driving assistance requires attention','fault','assistanceWarning','amber',75,{iconKey:'warning'});
 item('navigation-active','Navigation active','indicator','navActive','white',0);
 item('phone-active','Call in progress','popup',null,'white',35,{timeoutMs:5000});
 item('phone-incoming','Incoming call','popup',null,'white',40,{timeoutMs:0});
 item('media-track','Now playing','popup',null,'white',15,{timeoutMs:4000});
 item('nav-turn','Navigation instruction','popup',null,'white',30,{timeoutMs:6000});
 item('nav-reroute','Recalculating route','popup',null,'white',25,{timeoutMs:4000});
 item('check-info','Vehicle information','popup',null,'white',20,{timeoutMs:5000,iconKey:'service'});
 item('check-warning','Check Control warning','popup',null,'amber',60,{timeoutMs:0,iconKey:'warning'});
 item('service','Service reminder','fault','serviceDue','amber',45,{iconKey:'service'});
 item('battery','Battery charge warning','fault','batteryLow','amber',60,{latched:true});
 item('charging-system','Charging system warning','fault','chargingFault','red',80,{latched:true});
 item('oil-level','Engine oil level warning','fault','oilLevelLow','amber',60);
 item('speed-limit','Speed limit exceeded','fault','speedLimitExceeded','amber',50);
 item('collision','Collision warning','fault','collisionWarning','red',110,{critical:true,iconKey:'collision'});
 item('gear','Gear selection','indicator','gear','white',0);
 const scenarios=[
  {id:'normal',label:'Normal drive',signals:{gear:'D',speedKmh:62,rpm:1900,navActive:true,cruiseMode:'active',cruiseSetKmh:65},popups:[['nav-turn',{text:'Turn left · 300 m · Example Road'}]]},
  {id:'left',label:'Left turn signal',signals:{turnLeft:true}},
  {id:'right',label:'Right turn signal',signals:{turnRight:true}},
  {id:'hazards',label:'Hazards + lighting',signals:{hazards:true,highBeam:true,frontFog:true,rearFog:true}},
  {id:'headlights',label:'Dipped headlights + side lights',signals:{lowBeam:true,sideLights:true,autoHighBeamEnabled:true}},
  {id:'automatic-lights',label:'Automatic headlights in darkness',signals:{headlightAutoMode:'auto',ambientDark:true}},
  {id:'parking-lights',label:'Parking lights',signals:{parkingLightLeft:true,parkingLightRight:true}},
  {id:'door-belt',label:'Door and seat belt',signals:{doorOpen:true,seatbeltFastened:false,gear:'D',speedKmh:5,rpm:1100}},
  {id:'fuel-tyres',label:'Fuel reserve + tyre pressure',signals:{fuelPercent:5,tyrePressureLow:true}},
  {id:'engine',label:'Engine + ABS + DSC',signals:{engineFault:true,absFault:true,dscFault:true}},
  {id:'oil',label:'Critical oil pressure preempts media',signals:{oilPressureLow:true,mediaTitle:'Simulated track'},popups:[['media-track',{text:'A critical warning must stay on top'}]]},
  {id:'coolant',label:'Critical engine temperature',signals:{coolantOverheat:true}},
  {id:'brake',label:'Brake fault + moving parking brake',signals:{brakeFault:true,parkingBrake:true,gear:'D',speedKmh:15,rpm:1200}},
  {id:'critical-multiple',label:'Multiple critical warnings + call',signals:{brakeFault:true,coolantOverheat:true,oilPressureLow:true,phoneState:'incoming'}},
  {id:'assistance',label:'Cruise standby + assistance',signals:{cruiseMode:'standby',assistanceMode:'active',dscActive:true}},
  {id:'assistance-warning',label:'Assistance takeover + collision',signals:{assistanceMode:'warning',collisionWarning:true}},
  {id:'navigation',label:'Navigation turn + reroute',signals:{navActive:true},popups:[['nav-turn',{text:'Take the next exit · 1.2 km'}],['nav-reroute',{text:'Recalculating the simulated route'}]]},
  {id:'phone',label:'Incoming call',signals:{phoneState:'incoming'}},
  {id:'call-active',label:'Call in progress',signals:{phoneState:'active'}},
  {id:'media',label:'Media track change',signals:{mediaTitle:'Preview track · Example artist'}},
  {id:'check-control',label:'Check Control messages',popups:[['check-info',{text:'Simulated vehicle information'}],['check-warning',{text:'Simulated retained Check Control warning'}]]},
  {id:'service-battery',label:'Service and battery',signals:{serviceDue:true,batteryLow:true}},
  {id:'charging-oil',label:'Charging and oil level',signals:{chargingFault:true,oilLevelLow:true,batteryVoltage:11.2,oilTempC:110,coolantTempC:98}},
  {id:'speed-limit',label:'Speed-limit warning',signals:{gear:'D',speedKmh:85,rpm:2400,speedLimitKmh:80}},
  {id:'reverse',label:'Reverse selection',signals:{gear:'R',speedKmh:3,rpm:1000}},
  {id:'parked',label:'Parked, engine off',signals:{engineRunning:false,rpm:0,gear:'P',parkingBrake:true}}
 ];
 return {inventory,scenarios,scope:'Known preview signal families and matching asset candidates, not every BMW warning'};
});
