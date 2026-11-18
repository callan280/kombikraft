'use strict';
// Offline proof of the actual Session shaders, textures, layer bounds and uniforms.
// NODE_PATH=/Users/callan/node_modules node mgu/tools/preview_theme.cjs [output]
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),{EventEmitter}=require('events');
const stage=fs.mkdtempSync(path.join(require('os').tmpdir(),'kombikraft-preview-'));
const version=require('../apps/kombikraft_test/app.json').version;
require('child_process').execFileSync('tar',['-xzf',path.resolve(__dirname,'../dist/kombikraft_test@'+version+'.tgz'),'-C',stage]);
const app=path.join(stage,'package/javascript');
const {Session}=require(app+'/session'),geometry=require(app+'/geometry'),mask=require(app+'/factory-mask');
const out=path.resolve(process.argv[2]||'mgu/dist/curved-mini-proof');fs.mkdirSync(out,{recursive:true});
class Client extends EventEmitter{
 constructor(){super();this.id=0;this.assets={};this.layers={};}
 asset(o){this.assets[++this.id]={...o};return this.id;}
 pixels(ref,unused,bytes){this.assets[ref].base64=bytes.toString('base64');return true;}
 effect(o){this.layers[++this.id]={...o,uniforms:{},textures:{}};return this.id;}
 bind(ref,key,asset){this.layers[ref].textures[key]=asset;}
 uniform(ref,key,value){this.layers[ref].uniforms[key]=value;}
 connect(){this.backend='id7';this.targets='panel:1920x720';this.emit('ready');}
 drop(){} close(){}
}
(async()=>{
 let now=1000;const client=new Client(),session=new Session(client,{now:()=>now,art:app+'/art'});
 const sample={speed:0,rpm:850,at:now,mode:{value:'sport',at:now},gear:{value:'P',at:now},oil:{value:95,at:now},water:{value:90,at:now},boost:{value:0,at:now}};
 session.update(sample);session.start();session.refs.forEach(l=>client.emit('layer',l.ref,'shown'));session.tick();
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const page=await browser.newPage();
 const render=async(name,comparison)=>{
 const result=await page.evaluate(({assets,layers,reservations,comparison,tach,elapsed})=>{
  const c=document.createElement('canvas');c.width=1920;c.height=720;
  const gl=c.getContext('webgl',{preserveDrawingBuffer:true,alpha:false,antialias:false});
  if(!gl)throw Error('WebGL unavailable');const etc=gl.getExtension('WEBGL_compressed_texture_etc');if(!etc)throw Error('ETC2 unavailable');
  const compile=(kind,source)=>{const s=gl.createShader(kind);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  const vertex=compile(gl.VERTEX_SHADER,'attribute vec2 a_position;varying vec2 v_uv;void main(){gl_Position=vec4(a_position,0.,1.);v_uv=vec2((a_position.x+1.)*.5,(1.-a_position.y)*.5);}');
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
  const textures={};for(const [id,a]of Object.entries(assets)){
   const t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);
   const bytes=Uint8Array.from(atob(a.base64),x=>x.charCodeAt(0));
   if(a.format==='etc2rgba')gl.compressedTexImage2D(gl.TEXTURE_2D,0,etc.COMPRESSED_RGBA8_ETC2_EAC,a.w,a.h,0,bytes);
   else gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,a.w,a.h,0,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
   for(const param of [gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,param,a.sampling==='nearest'?gl.NEAREST:gl.LINEAR);
   for(const param of [gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,param,gl.CLAMP_TO_EDGE);textures[id]=t;
  }
  gl.clearColor(.03,.06,.08,1);gl.clear(gl.COLOR_BUFFER_BIT);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
  for(const l of Object.values(layers).sort((a,b)=>a.z-b.z)){
   const p=gl.createProgram();gl.attachShader(p,vertex);gl.attachShader(p,compile(gl.FRAGMENT_SHADER,l.fs));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));gl.useProgram(p);
   const pos=gl.getAttribLocation(p,'a_position');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);
   for(const [i,[key,asset]]of Object.entries(l.textures).entries()){gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,textures[asset]);gl.uniform1i(gl.getUniformLocation(p,key),i);}
   for(const [key,value]of Object.entries(l.uniforms))gl['uniform'+value.length+'fv'](gl.getUniformLocation(p,key),value);
   gl.uniform1f(gl.getUniformLocation(p,'u_time'),elapsed);gl.viewport(l.x,720-l.y-l.h,l.w,l.h);gl.drawArrays(gl.TRIANGLES,0,6);
  }
  if(gl.getError()!==gl.NO_ERROR)throw Error('WebGL error');
  let ringPixelsChanged=null;
  if(comparison){
   const radius=Math.ceil(200*tach.scale),side=2*radius;
   const pixels=new Uint8Array(side*side*4);
   gl.readPixels(tach.x-radius,720-tach.y-radius,side,side,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
   if(comparison==='reference')window.referenceRing=pixels;
   else{
    ringPixelsChanged=0;
    for(let i=0;i<pixels.length;i+=4){
     const delta=Math.max(...[0,1,2].map(k=>Math.abs(pixels[i+k]-window.referenceRing[i+k])));
     if(delta>8)ringPixelsChanged++;
    }
   }
  }
  const raw=c.toDataURL();const canvas=document.createElement('canvas');canvas.width=1920;canvas.height=720;const ctx=canvas.getContext('2d');ctx.drawImage(c,0,0);
  ctx.font='16px sans-serif';ctx.lineWidth=2;
  for(const r of reservations){ctx.strokeStyle='#77b7c7';ctx.fillStyle='#77b7c7';ctx.strokeRect(r.x,r.y,r.w,r.h);ctx.fillText(r.label,r.x+4,r.y+20);}
  return {raw,ringPixelsChanged,guides:canvas.toDataURL(),shaderCompiled:true,layers:Object.keys(layers).length};
 },{comparison,elapsed:(now-session.started)/1000,tach:{...geometry.dials[1],scale:geometry.scale(geometry.dials[1])},assets:client.assets,layers:client.layers,reservations:[{...geometry.box,label:'Black-box clearance'},{...mask.reserves.find(r=>r.id==='parking-lamp'),label:'(P)'},{...geometry.centreWarning,label:'Factory warning opening'}]});
 for(const key of ['raw','guides']){fs.writeFileSync(path.join(out,name+'-'+key+'.png'),Buffer.from(result[key].split(',')[1],'base64'));delete result[key];}return result;
 };
 const fresh=await render('fresh');now+=3001;session.update({...sample,at:now});session.tick();const stale=await render('stale-temperature');
 // Compare each illuminated frame with its own lights-off frame at identical RPM.
 const shiftProof={};
 now+=10000;
 for(const rpm of [5200,6150,6500]){
  const heldSport={...sample,rpm,speed:60,gear:{value:'M3',at:now}};
  for(let n=0;n<24;n++){
   now+=33;
   heldSport.at=now;
   for(const key of ['oil','water','boost'])heldSport[key]={...sample[key],at:now};
   session.update({...heldSport,shiftLights:false});session.tick();
  }
  session.update({...heldSport,shiftLights:false});session.tick();
  await render('shift-'+rpm+'-reference','reference');
  session.update({...heldSport,shiftLights:true});session.tick();
  const on=await render('shift-'+rpm,'compare');
  if(!on.ringPixelsChanged)throw Error('Shift stage produced no visible change at '+rpm);
  shiftProof[rpm]=on.ringPixelsChanged;
  if(rpm===6500){
   now+=200;session.update({...heldSport,at:now,shiftLights:true});session.tick();
   const stages=session.refs.filter(l=>l.shiftStage!==undefined);
   if(!stages.length||stages.some(l=>l.shiftStage!==0))throw Error('Flash failed to enter its dark phase');
  }
 }
 const proof={fresh,stale,shiftProof,vehicleValidated:false,minis:geometry.minis.map(d=>({...d,bounds:geometry.bounds(d)}))};fs.writeFileSync(path.join(out,'proof.json'),JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>fs.rmSync(stage,{recursive:true,force:true}));
