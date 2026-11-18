'use strict';
const assert=require('assert'),{EventEmitter}=require('events'),path=require('path'),fs=require('fs');
// Use the built archive's staged source tree, so paths match deployment.
const root=process.argv[2],{Session,valid}=require(path.join(root,'javascript/session')),g=require(path.join(root,'javascript/geometry'));
class Client extends EventEmitter{constructor(){super();this.n=0;this.layers=[];this.assets=[];this.uniforms=[];this.closed=false;}asset(o){this.assets.push(o);return ++this.n;}pixels(){return true;}effect(o){this.layers.push(o);return ++this.n;}bind(){}uniform(r,k,v){assert(v.every(Number.isFinite));this.uniforms.push({r,k,v});}connect(){this.connected=true;this.backend='id7';this.targets='map:1088x480,panel:1920x720,hud:800x480';this.emit('ready');}drop(r){this.dropped=(this.dropped||[]).concat(r);}close(){this.closed=true;}}
let now=1000;const make=()=>{const c=new Client(),messages=[],s=new Session(c,{now:()=>now,art:path.join(root,'javascript/art'),report:t=>messages.push(t)});return{c,s,messages};};
for(const bad of [null,{}, {speed:null,rpm:0,at:now},{speed:0,rpm:65535,at:now},{speed:2,rpm:900,at:now},{speed:0,rpm:900,at:now-4000},{speed:0,rpm:900,at:now+1}])assert(!valid(bad,now));
let a=make();assert.throws(()=>a.s.start('live'));assert.equal(a.c.layers.length,0);a.s.update({speed:0,rpm:900,at:now});a.s.start('live');assert.equal(a.c.assets.length,10);assert.equal(a.c.layers.length,8);assert(a.c.layers.every(l=>!l.exclusive&&!l.contend&&!l.guide_hold&&!l.time_fps));
for(const l of a.c.layers){for(const h of g.holes)assert(!g.intersect(l,h));assert(l.y+l.h<=660);}
a.s.refs.forEach(l=>a.c.emit('layer',l.ref,'shown'));
for(let i=0;i<40;i++){now+=33;a.s.update({speed:0,rpm:900+i*100,at:now});a.s.tick();}assert(a.s.active);a.s.update({speed:2,rpm:1000,at:now});assert(!a.s.active&&a.c.closed);assert.equal(a.c.dropped.length,18);assert.throws(()=>a.s.start('live'));
a=make();a.s.update({speed:0,rpm:800,at:now});a.s.start('sweep');now+=3501;a.s.tick();assert(!a.s.active&&a.c.closed);
a=make();a.s.update({speed:0,rpm:800,at:now});a.s.start('live');now+=20000;a.s.update({speed:0,rpm:800,at:now});a.s.tick();assert(!a.s.active&&a.c.closed);
for(const ev of ['disconnected','refused']){a=make();a.s.update({speed:0,rpm:0,at:now});a.s.start('live');a.c.emit(ev);assert(!a.s.active&&a.c.closed);}
a=make();a.s.update({speed:0,rpm:0,at:now});a.s.start('live');a.c.emit('layer',a.s.refs[0].ref,'suspended');assert(!a.s.active&&a.c.closed);
// Conservatively enclose all recovered meshes and all rotation angles.
for(const d of g.dials){assert(d.x+d.radius*1.002+24<=g.box.x);}
assert.equal(g.dials[0].y,g.dials[1].y);assert.equal(g.dials[0].radius,g.dials[1].radius);
a=make();a.c.connect=function(){this.backend='id8';this.targets='panel:1920x720';this.emit('ready');};a.s.update({speed:0,rpm:0,at:now});a.s.start('live');assert(!a.s.active&&a.c.closed);assert.equal(a.c.layers.length,0);
console.log('PASS 8 layers / 10 assets, reservations, alignment, stationary/fresh guards, timer, disconnect/refusal/suspension release.');

const input=require(path.join(root,'javascript/inputs'));
assert.equal(input.temperatures({temperatureEngineOilDrive:138,temperatureEngineDrive:148},now).oil.value,90);
assert.equal(input.temperatures({temperatureEngineOilDrive:255,temperatureEngineDrive:148},now).oil.value,null);
assert.equal(input.temperatures({temperatureEngineOilDrive:138,temperatureEngineDrive:148},now).water.value,100);
assert(Math.abs(input.boost({displayBoostPressure:100},now).value-14.503773773)<1e-8);
assert.equal(input.boost({displayBoostPressure:255},now).value,null);
assert.equal(input.miniValue({boost:{value:30,at:now}},g.minis[1],now),25);
assert.equal(input.miniValue({oil:{value:90,at:now-3000}},g.minis[0],now),null);
a=make();a.s.update({speed:0,rpm:800,at:now});a.s.start('live');
const ref=a.s.refs.find(l=>l.d.signal==='oil').ref;
assert(a.c.uniforms.some(u=>u.r===ref&&u.k==='u_valid'&&u.v[0]===0));
a.s.update({speed:0,rpm:800,at:now,oil:{value:90,at:now}});a.s.tick();
assert(a.c.uniforms.some(u=>u.r===ref&&u.k==='u_valid'&&u.v[0]===1));
a.s.stop();console.log('PASS oil/coolant raw-minus-48, boost bar-to-psi, invalid/stale hiding and overrange clamp.');

a=make();
a.s.update({speed:0,rpm:2400,at:now});
a.s.start('live','touring');
assert.equal(a.c.assets.length,2);
assert.equal(a.c.layers.length,2);
for(const layer of a.c.layers)for(const hole of g.holes)assert(!g.intersect(layer,hole));
assert(a.c.uniforms.some(u=>u.k==='u_speed'&&u.v[0]===0));
assert(a.c.uniforms.some(u=>u.k==='u_angles'&&u.v[0]===3));
a.s.refs.forEach(l=>a.c.emit('layer',l.ref,'shown'));
now+=33;
a.s.update({speed:0,rpm:4000,at:now});
a.s.tick();
assert(a.c.uniforms.some(u=>u.k==='u_angles'&&u.v[3]>3));
a.s.stop();
assert.equal(a.c.dropped.length,4);
assert(a.c.closed);
console.log('PASS Map Touring live speed/RPM, reserved region clearance and release.');

for(const theme of ['round','touring']){
 a=make();a.s.update({speed:0,rpm:900,at:now});a.s.start('live',theme);
 const total=a.c.assets.reduce((sum,asset)=>sum+asset.w*asset.h*8,0);
 const map=1088*480*1.5*4;
 assert(total+map<16*1024*1024,theme+' leaves room for the observed map stream');
 const layer=a.s.refs[0];
 a.c.emit('layer',layer.ref,'stalled','asset pixels pending');
 assert(a.s.active,'initial stalled state can be normal');
 a.c.emit('layer',layer.ref,'waiting','target acquiring');
 assert(a.s.active,'normal panel acquisition can finish');
 a.s.refs.forEach(ref=>a.c.emit('layer',ref.ref,'shown'));
 a.s.tick();
 a.c.emit('layer',layer.ref,'stalled','asset pixels lost');
 assert(!a.s.active);
 assert.equal(a.messages[a.messages.length-1],'Renderer stalled: asset pixels lost');
}

a=make();a.s.update({speed:0,rpm:900,at:now});a.s.start('live','touring');
const waiting=a.s.refs[0];
a.c.emit('layer',waiting.ref,'waiting','target acquiring');
now+=9000;
a.s.update({speed:0,rpm:900,at:now});a.s.tick();
assert(!a.s.active);
assert.equal(a.messages[a.messages.length-1],'Renderer startup timed out: target acquiring');
console.log('PASS shared pixel budget, startup stall and attach, runtime loss, and startup timeout.');

const mask=require(path.join(root,'javascript/factory-mask'));
a=make();
a.s.update({speed:0,rpm:750,at:now,fuel:input.fuel({fluidLevelFuelTank:17},now)});
a.s.start('live','round-mask');
const masked=a.c.layers.filter(layer=>layer.z===5);
assert.equal(masked.length,mask.pieces.length);
assert(masked.length>0&&a.c.layers.length<64);
assert(masked.every(layer=>mask.reserves.every(box=>!g.intersect(layer,box))));
assert(a.c.uniforms.some(u=>u.k==='u_level'&&u.v[0]===.34));
a.s.refs.forEach(layer=>a.c.emit('layer',layer.ref,'shown'));
a.s.tick();
a.s.stop();
assert(a.c.dropped.length===a.c.layers.length+a.c.assets.length);
a=make();
a.s.update({speed:0,rpm:750,at:now});
a.s.start('live','round-stay');
a.s.refs.forEach(layer=>a.c.emit('layer',layer.ref,'shown'));
now+=50000;
a.s.update({speed:0,rpm:750,at:now});
a.s.tick();
assert(a.s.active);
a.s.update({speed:1.1,rpm:750,at:now});
assert(!a.s.active&&a.c.closed);
assert.equal(input.fuel({fluidLevelFuelTank:255},now).value,null);
assert.equal(input.fuel({fluidLevelFuelTank:50},now).value,1);
assert.equal(input.pressureBoost(null,100,now).value,null);
const measured=input.pressureBoost(150,100,now);
assert(Math.abs(measured.value-7.2518868865)<1e-9);
assert.equal(input.selectBoost(measured,{value:0,at:now},now),measured);
console.log('PASS fuel/boost decoders, mask reservations, continuous mode and restore on movement.');
