'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {Needle,nextPath}=require('./needle-math');
const geometry=require('./geometry'),shader=require('./shader'),{miniValue}=require('./inputs');
const {instruments}=require('./touring');
const mask=require('./factory-mask');
const fuel=require('./fuel-gauge');
const {fresh}=require('./inputs');
const LIMIT_MS=20000,STALE_MS=3500,ACQUIRE_MS=9000;
function valid(sample,now){return sample&&Number.isFinite(sample.speed)&&sample.speed>=0&&sample.speed<1&&Number.isFinite(sample.rpm)&&sample.rpm>=0&&sample.rpm<=8000&&Number.isFinite(sample.at)&&now>=sample.at&&now-sample.at<=STALE_MS;}
class Session{
 constructor(client,opts){this.c=client;this.opts=opts||{};this.now=this.opts.now||(()=>{const t=process.hrtime();return t[0]*1000+t[1]/1e6;});this.report=this.opts.report||(()=>{});this.started=null;this.active=false;this.refs=[];this.sample=null;this.mode='live';this.faceAssets=[];
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
 start(mode,theme='round'){if(this.active)throw Error('Test already running');if(!valid(this.sample,this.now()))throw Error('Fresh stationary speed and RPM are required.');if(['live','sweep'].indexOf(mode)<0)throw Error('Unknown test mode');
  if(!['round','round-mask','round-stay','touring'].includes(theme)||(theme!=='round'&&mode!=='live'))throw Error('Unknown theme or mode');
  this.started=this.now();this.active=true;this.mode=mode;this.theme=theme;this.refs=[];this.showReported=false;this.c.connect();
 }
 loadTexture(dir, manifest, name, width, height) {
  const entry=manifest.images.find(row=>row.name===name);
  const bytes=fs.readFileSync(path.join(dir,name));
  if(!entry||entry.width!==width||entry.height!==height||bytes.length!==width*height*4||
     crypto.createHash('sha256').update(bytes).digest('hex')!==entry.sha256)throw Error('Art hash or size mismatch: '+name);
  const ref=this.c.asset({target:'panel',format:'rgba8',w:width,h:height,sampling:'bilinear'});
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
 attachTouring(dir,manifest) {
  for(const d of instruments){
   if(geometry.holes.some(hole=>geometry.intersect(d,hole)))throw Error('Touring obscures reserved region');
   const art=this.loadTexture(dir,manifest,d.image,d.textureW,d.textureH);
   const ref=this.makeLayer(d,d.shader,d.signal==='rpm');
   this.refs.push({ref,d,needle:new Needle(28),path:null,t0:this.now()});
   this.c.bind(ref,'u_art',art);
   if(d.signal==='speed'){
    this.c.uniform(ref,'u_speed',[this.sample.speed]);
   }else{
    const progress=this.sample.rpm/d.max*d.sweep;
    this.c.uniform(ref,'u_times',[0,.06,.13,.13]);
    this.c.uniform(ref,'u_angles',[progress,progress,progress,progress]);
   }
  }
 }
 attach(){const mode=this.mode;if(this.refs.length||!this.active)return;
  try{
   const dir=this.opts.art||path.join(__dirname,'art');
   const manifest=JSON.parse(fs.readFileSync(path.join(dir,'manifest.json')));
   if(this.theme==='touring'){
    this.attachTouring(dir,manifest);
   }else{
    for(const d of geometry.dials.concat(geometry.minis)){
     const face=this.loadTexture(dir,manifest,d.side+'-face.rgba',d.w,d.h);
     const name=d.side+'-needle.rgba';
     const crop=manifest.images.find(entry=>entry.name===name);
     if(!crop||crop.sourceWidth!==d.w||crop.sourceHeight!==d.h||
        ![crop.offsetX,crop.offsetY,crop.width,crop.height].every(Number.isInteger)||
        crop.offsetX<0||crop.offsetY<0||crop.width<1||crop.height<1||
        crop.offsetX+crop.width>d.w||crop.offsetY+crop.height>d.h){
      throw Error('Invalid needle crop: '+name);
     }
     const needle=this.loadTexture(dir,manifest,name,crop.width,crop.height);
     for(const r of geometry.pieces(d)){
      const ref=this.makeLayer(r,shader,true);
      this.refs.push({ref,d,needle:new Needle(28),path:null,t0:this.now()});
      this.c.bind(ref,'u_face',face);
      this.c.bind(ref,'u_needle',needle);
      this.c.uniform(ref,'u_size',[r.w,r.h]);
      this.c.uniform(ref,'u_origin',[r.x,r.y]);
      this.c.uniform(ref,'u_center',[d.x,d.y]);
      this.c.uniform(ref,'u_textureSize',[d.w,d.h]);
      this.c.uniform(ref,'u_needleRect',[crop.offsetX,crop.offsetY,crop.width,crop.height]);
      this.c.uniform(ref,'u_times',[0,.06,.13,.13]);
      const value=mode==='sweep'?0:d.optional?miniValue(this.sample,d,this.now()):this.sample[d.signal];
      const angle=(value===null?0:value)/d.max*d.sweep;
      this.c.uniform(ref,'u_valid',[value===null?0:1]);
      this.c.uniform(ref,'u_angles',[angle,angle,angle,angle]);
     }
    }
   }
   if(this.theme!=='touring'){
    if(geometry.holes.some(hole=>geometry.intersect(fuel.bounds,hole)))throw Error('Fuel gauge crosses a reserved area');
    const ref=this.makeLayer(fuel.bounds,fuel.shader,false,12);
    this.refs.push({ref,isFuel:true});
    this.c.uniform(ref,'u_level',[this.fuelLevel(this.now())]);
   }
   if(this.theme==='round-mask'){
    for(const rect of mask.pieces){
     const ref=this.makeLayer(rect,mask.shader,false,5);
     this.refs.push({ref,isMask:true});
     this.c.uniform(ref,'u_bounds',[rect.x,rect.y,rect.w,rect.h]);
    }
   }
   this.report((this.theme==='touring'?'Map Touring':'M Round')+' · waiting for cluster graphics.');
  }catch(e){this.stop(e.message);throw e;}
 }
 fuelLevel(now){
  const value=fresh(this.sample&&this.sample.fuel,now,15000);
  return value===null?-1:value;
 }
 tick(){if(!this.active)return;const now=this.now();if(this.theme!=='round-stay'&&now-this.started>=LIMIT_MS){this.stop('Test expired. Factory display released.');return;}if(!valid(this.sample,now)){this.stop('Stale data or vehicle moving.');return;}const allShown=this.refs.length>0&&this.refs.every(layer=>layer.state==='shown');
  if(!allShown&&now-this.started>=ACQUIRE_MS){
   const pending=this.refs.find(layer=>layer.state!=='shown');
   const detail=pending&&(pending.reason||pending.state);
   this.stop('Renderer startup timed out'+(detail?': '+detail:'.'));return;
  }
  if(allShown&&!this.showReported){this.showReported=true;this.report('Theme shown. Parked test in progress.');}
  for(const l of this.refs){
   if(l.isMask)continue;
   if(l.isFuel){this.c.uniform(l.ref,'u_level',[this.fuelLevel(now)]);continue;}
   if(this.theme==='touring'&&l.d.signal==='speed'){
    this.c.uniform(l.ref,'u_speed',[this.sample.speed]);
    continue;
   }
   const phase=Math.min(1,(now-this.started)/12000),p=phase<=.5?phase*2:(1-phase)*2,value=this.mode==='sweep'?p*l.d.max:l.d.optional?miniValue(this.sample,l.d,now):this.sample[l.d.signal];if(this.theme!=='touring')this.c.uniform(l.ref,'u_valid',[value===null?0:1]);if(value===null){l.needle=new Needle(28);l.path=null;continue;}const angle=value/l.d.max*l.d.sweep;l.needle.step(angle,now);l.path=nextPath(l.path,(now-l.t0)/1000,.06,.07,l.needle.ahead(angle,130));this.c.uniform(l.ref,'u_times',l.path.t);this.c.uniform(l.ref,'u_angles',l.path.a);}
 }
 stop(reason){const was=this.active;this.active=false;this.refs.forEach(l=>{try{this.c.drop(l.ref);}catch(e){}});this.faceAssets.forEach(ref=>{try{this.c.drop(ref);}catch(e){}});this.refs=[];this.faceAssets=[];this.c.close();if(was)this.report(reason||'Factory display released.');}
}
module.exports={Session,valid,LIMIT_MS,STALE_MS};
