'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {Needle,nextPath}=require('./needle-math');
const geometry=require('./geometry'),shader=require('./shader');
const mask=require('./factory-mask');
const {miniValue,currentMode,currentGear,gearGlyphs}=require('./inputs');
const decorations=require('./round-extras');
const modeTints={
 sport:[0,0,0],
 comfort:[1,.45,.08],
 eco:[.15,.54,1]
};
const STALE_MS=3500,ACQUIRE_MS=9000;
const SHIFT_STEPS=[5200,5350,5500,5650,5800,5950,6150,6350,6500];
const FINAL_SHIFT_FRAME=SHIFT_STEPS.length;
const FLASH_HALF_PERIOD_MS=200;
function valid(sample,now){return sample&&Number.isFinite(sample.speed)&&sample.speed>=0&&sample.speed<1&&Number.isFinite(sample.rpm)&&sample.rpm>=0&&sample.rpm<=8000&&Number.isFinite(sample.at)&&now>=sample.at&&now-sample.at<=STALE_MS;}
class Session{
 constructor(client,opts){this.c=client;this.opts=opts||{};this.now=this.opts.now||(()=>{const t=process.hrtime();return t[0]*1000+t[1]/1e6;});this.report=this.opts.report||(()=>{});this.started=null;this.active=false;this.refs=[];this.sample=null;this.faceAssets=[];
  client.on('ready',()=>{if(!this.active)return;if(client.backend!=='id7'||!/(^|,)panel:1920x720(,|$)/.test(client.targets||'')){this.stop('Unexpected renderer backend or panel geometry.');return;}try{this.attach();}catch(e){this.stop(e.message);}});
  client.on('disconnected',()=>this.stop('Renderer disconnected; explicit restart required.'));
  client.on('refused',(op,ref,reason)=>this.stop('Renderer refused '+op+': '+reason));
  client.on('layer',(ref,state,reason)=>{
   const layer=this.refs.find(entry=>entry.ref===ref);
   if(!this.active||!layer)return;
   layer.state=state;
   layer.reason=reason;
   if(state==='shown'){
    if(!layer.shown){layer.t0=this.now();layer.path=null;layer.shown=true;}
    return;
   }
   if(state==='error'||state==='suspended'||(this.showReported&&['waiting','stalled','hidden'].includes(state))){
    this.stop('Renderer '+state+(reason?': '+reason:'.'));
   }
  });
 }
 update(sample){this.sample=sample;if(this.active&&!valid(sample,this.now()))this.stop('Speed, RPM or freshness check failed.');}
 start(){
  if(this.active)throw Error('M Round is already on');
  if(!valid(this.sample,this.now()))throw Error('Fresh stationary speed and RPM are required.');
  this.started=this.now();this.active=true;this.refs=[];this.showReported=false;this.c.connect();
 }
 loadTexture(dir, manifest, name, width, height, sampling='bilinear') {
  const entry=manifest.images.find(row=>row.name===name);
  const bytes=fs.readFileSync(path.join(dir,name));
  const compressed=name.endsWith('.etc2rgba');
  const format=compressed?'etc2rgba':'rgba8';
  if(!entry||entry.width!==width||entry.height!==height||bytes.length!==width*height*(compressed?1:4)||
     crypto.createHash('sha256').update(bytes).digest('hex')!==entry.sha256)throw Error('Art hash or size mismatch: '+name);
  const ref=this.c.asset({target:'panel',format,w:width,h:height,sampling});
  if(!ref)throw Error('Asset refused');
  this.faceAssets.push(ref);
  if(!this.c.pixels(ref,null,bytes))throw Error('Asset pixels refused');
  return ref;
 }
 makeLayer(rect, fragment, timed, z=10) {
  const {x,y,w,h}=rect;
  const ref=this.c.effect({target:'panel',klass:'overlay',x,y,w,h,z,
    exclusive:false,contend:false,guide_hold:false,time:timed,fs:fragment});
  if(!ref)throw Error('Layer refused');
  return ref;
 }
 attach(){if(this.refs.length||!this.active)return;
  try{
   const dir=this.opts.art||path.join(__dirname,'art');
   const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
   const speedArt=this.loadTexture(dir,manifest,'touring-speed.rgba',1056,108);
   const extras=this.loadTexture(dir,manifest,'round-extras.rgba',896,116);
   for(const d of geometry.dials.concat(geometry.minis)){
    const face=this.loadTexture(dir,manifest,d.side+(d.optional?'-face.rgba':'-face.etc2rgba'),d.w,d.h);
    const name=d.side+'-needle.rgba';
    const crop=manifest.images.find(entry=>entry.name===name);
    if(!crop||crop.sourceWidth!==d.w||crop.sourceHeight!==d.h||
       ![crop.offsetX,crop.offsetY,crop.width,crop.height].every(Number.isInteger)||
       crop.offsetX<0||crop.offsetY<0||crop.width<1||crop.height<1||
       crop.offsetX+crop.width>d.w||crop.offsetY+crop.height>d.h){
     throw Error('Invalid needle crop: '+name);
    }
    const needle=this.loadTexture(dir,manifest,name,crop.width,crop.height);
    const tach=d.signal==='rpm';
    const shift=tach&&manifest.images.find(entry=>entry.name==='right-shift.rgba');
    if(tach&&!shift)throw Error('F97 shift-ring artwork missing');
    const shiftArt=shift&&this.loadTexture(dir,manifest,shift.name,shift.width,shift.height,'nearest');
    const panelScale=(d.displaySize||d.w)/d.w;
    const tachBand={x:d.x-200*panelScale,y:d.y-200*panelScale,w:400*panelScale,h:400*panelScale};
    for(const r of geometry.pieces(d)){
     const showShift=shift&&geometry.intersect(r,tachBand);
     const defines=showShift?'#define F97_SHIFT_LIGHTS\n':d.signal==='speed'?'#define F40_DIGITAL_SPEED\n':'';
     const ref=this.makeLayer(r,defines+shader,true);
     const layer={ref,d,needle:new Needle(28),path:null,t0:this.now()};
     this.refs.push(layer);
     this.c.bind(ref,'u_face',face);
     this.c.bind(ref,'u_needle',needle);
     if(d.signal==='speed'){
      this.c.bind(ref,'u_speedArt',speedArt);
      this.c.uniform(ref,'u_speed',[this.sample.speed]);
      layer.speed=this.sample.speed;
     }
     this.c.uniform(ref,'u_size',[r.w,r.h]);
     this.c.uniform(ref,'u_origin',[r.x,r.y]);
     this.c.uniform(ref,'u_center',[d.x,d.y]);
     this.c.uniform(ref,'u_arcRotation',[d.arcRotation||0]);
     this.c.uniform(ref,'u_artPerPixel',[d.w/(d.displaySize||d.w)]);
     this.c.uniform(ref,'u_textureSize',[d.w,d.h]);
     this.setModeAccent(layer,this.now());
     this.c.uniform(ref,'u_needleRect',[crop.offsetX,crop.offsetY,crop.width,crop.height]);
     this.c.uniform(ref,'u_times',[0,.06,.13,.13]);
     if(showShift){
      this.c.bind(ref,'u_shiftArt',shiftArt);
      this.c.bind(ref,'u_roundExtras',extras);
      this.c.uniform(ref,'u_gearGlyphs',[-1,-1]);
      layer.gear=null;
      this.c.uniform(ref,'u_shiftMap',[shift.offsetX,shift.offsetY,shift.width,shift.mapHeight]);
      this.c.uniform(ref,'u_shiftAtlasSize',[shift.width,shift.height]);
      this.c.uniform(ref,'u_shiftStage',[0]);
      this.c.uniform(ref,'u_arcSweep',[d.sweep]);
      layer.shiftStage=0;
     }
     const value=d.optional?miniValue(this.sample,d,this.now()):this.sample[d.signal];
     const angle=(value===null?0:value)/d.max*d.sweep;
     layer.needleVisible=value!==null;
     this.c.uniform(ref,'u_valid',[layer.needleVisible?1:0]);
     this.c.uniform(ref,'u_angles',[angle,angle,angle,angle]);
    }
   }
   for(const rect of mask.pieces){
    const ref=this.makeLayer(rect,mask.shader,false,5);
    this.refs.push({ref,isMask:true});
    this.c.uniform(ref,'u_bounds',[rect.x,rect.y,rect.w,rect.h]);
   }
   const badge=this.makeLayer(decorations.badgeBounds,decorations.badgeShader,false,11);
   this.refs.push({ref:badge,isMask:true});
   this.c.bind(badge,'u_roundExtras',extras);
   const gearMask=this.makeLayer(decorations.factoryGearBounds,decorations.factoryGearShader,false,5);
   this.refs.push({ref:gearMask,isGearMask:true,gearVisible:false});
   this.c.uniform(gearMask,'u_show',[0]);
   this.report('M Round · waiting for cluster graphics.');
  }catch(e){this.stop(e.message);throw e;}
 }
 setModeAccent(layer,now){
  const mode=layer.d.optional?'sport':currentMode(this.sample.mode,now)||'comfort';
  if(layer.accentMode===mode)return;
  layer.accentMode=mode;
  this.c.uniform(layer.ref,'u_modeTint',modeTints[mode]);
 }
 updateShiftLights(layer,rpm,now){
  const mode=this.sample.mode;
  const enabled=this.sample.shiftLights===true&&currentMode(mode,now)==='sport'&&now-mode.at<=STALE_MS;
  let frame=enabled?SHIFT_STEPS.filter(threshold=>rpm>=threshold).length:0;
  if(frame===FINAL_SHIFT_FRAME){
   if(layer.flashAt===undefined)layer.flashAt=now;
   if(Math.floor((now-layer.flashAt)/FLASH_HALF_PERIOD_MS)%2===1)frame=0;
  }else{
   layer.flashAt=undefined;
  }
  if(layer.shiftStage!==frame){
   layer.shiftStage=frame;
   this.c.uniform(layer.ref,'u_shiftStage',[frame]);
  }
 }
 tick(){
  if(!this.active)return;
  const now=this.now();
  if(!valid(this.sample,now)){this.stop('Stale data or vehicle moving.');return;}
  const allShown=this.refs.length>0&&this.refs.every(layer=>layer.state==='shown');
  if(!allShown&&now-this.started>=ACQUIRE_MS){
   const pending=this.refs.find(layer=>layer.state!=='shown');
   const detail=pending&&(pending.reason||pending.state);
   this.stop('Renderer startup timed out'+(detail?': '+detail:'.'));return;
  }
  if(allShown&&!this.showReported){this.showReported=true;this.report('M Round is on.');}
  const gear=currentGear(this.sample.gear,now);
  for(const layer of this.refs){
   if(layer.isGearMask){
    const visible=this.showReported&&gear!==null;
    if(visible!==layer.gearVisible){layer.gearVisible=visible;this.c.uniform(layer.ref,'u_show',[visible?1:0]);}
    continue;
   }
   if(layer.isMask)continue;
   this.setModeAccent(layer,now);
   const {d,ref}=layer;
   const value=d.optional?miniValue(this.sample,d,now):this.sample[d.signal];
   if(layer.shiftStage!==undefined){
    this.updateShiftLights(layer,value,now);
    if(layer.gear!==gear){layer.gear=gear;this.c.uniform(ref,'u_gearGlyphs',gearGlyphs(gear));}
   }
   if(d.signal==='speed'&&value!==layer.speed){layer.speed=value;this.c.uniform(ref,'u_speed',[value]);}
   const needleVisible=value!==null;
   if(layer.needleVisible!==needleVisible){
    layer.needleVisible=needleVisible;this.c.uniform(ref,'u_valid',[needleVisible?1:0]);
   }
   if(value===null){layer.needle=new Needle(28);layer.path=null;continue;}
   const angle=value/d.max*d.sweep;
   layer.needle.step(angle,now);
   layer.path=nextPath(layer.path,(now-layer.t0)/1000,.06,.07,layer.needle.ahead(angle,130));
   this.c.uniform(ref,'u_times',layer.path.t);
   this.c.uniform(ref,'u_angles',layer.path.a);
  }
 }
 stop(reason){const was=this.active;this.active=false;this.refs.forEach(l=>{try{this.c.drop(l.ref);}catch(e){}});this.faceAssets.forEach(ref=>{try{this.c.drop(ref);}catch(e){}});this.refs=[];this.faceAssets=[];this.c.close();if(was)this.report(reason||'Factory display released.');}
}
module.exports={Session,valid,STALE_MS};
