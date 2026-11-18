/* Export original BMW face/needle meshes through the same WebGL path as the viewer.
 * Usage: NODE_PATH=/path/to/node_modules node .../export_test_art.cjs [preview URL]
 * Requires Playwright and Chromium locally; never connects to a vehicle. */
'use strict';
const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../apps/kombikraft_test/art');
(async()=>{const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
try{const page=await browser.newPage();await page.goto(process.argv[2]||'http://127.0.0.1:8096/design?test=1&preview=flat-base');await page.waitForFunction(()=>typeof ready!=='undefined'&&ready&&F97Gauges.status().available,null,{timeout:90000});
const exports=await page.evaluate(()=>{window.requestAnimationFrame=()=>0;const out=[],size=688,radius=343;
for(const side of ['left','right'])for(const kind of ['face','needle']){const c=document.createElement('canvas');c.width=c.height=size;const g=c.getContext('2d');if(kind==='face'){g.fillStyle='#030609';g.fillRect(0,0,size,size);}const okay=F97Gauges.renderDial(g,side,{x:size/2,y:size/2,radius},{speedKmh:0,rpm:0,mode:'sport',modeAccent:true,deferNeedles:kind==='face',needleOnly:kind==='needle'},{clipY:size});if(!okay)throw Error('Source render failed');const bytes=g.getImageData(0,0,size,size).data;let binary='';for(let i=0;i<bytes.length;i+=16384)binary+=String.fromCharCode.apply(null,bytes.subarray(i,i+16384));out.push({name:side+'-'+kind+'.rgba',width:size,height:size,rgba:btoa(binary)});}for(const kind of ['face','needle']){const c=document.createElement('canvas');c.width=570;c.height=216;const g=c.getContext('2d');if(!F97Gauges.renderMini(g,{x:0,y:0,width:570,height:216},{radius:65,topY:43,centerXs:[95,285,475],oilPosition:0,boostPosition:0,waterPosition:0,mode:'sport',deferNeedles:kind==='face',needleOnly:kind==='needle'},{number,text}))throw Error('Mini export failed');if(kind==='face'){for(const mark of F97Gauges.status().lastMiniInputs.numericScaleMarks){const col=['oil','boost','water'].indexOf(mark.role),b=mark.renderedBounds;if(b.x<col*190||b.x+b.width>(col+1)*190)throw Error('Mini label clipped: '+mark.role+' '+mark.value);}text(g,'°C',95,203,14,'#d9dce2','center');text(g,'psi',285,203,14,'#d9dce2','center');text(g,'°C',475,203,14,'#d9dce2','center');}for(const [i,role]of ['oil','boost','water'].entries()){const bytes=g.getImageData(i*190,0,190,216).data;let binary='';for(let j=0;j<bytes.length;j+=16384)binary+=String.fromCharCode.apply(null,bytes.subarray(j,j+16384));out.push({name:role+'-'+kind+'.rgba',width:190,height:216,rgba:btoa(binary)});}}
return{images:out,geometry:ClusterOverlayContract.dials,obstruction:ClusterOverlayContract.obstruction,source:F97Gauges.status().packageSha256};});
fs.mkdirSync(root,{recursive:true});
for(const entry of exports.images){
 let pixels=Buffer.from(entry.rgba,'base64');
 delete entry.rgba;
 if(entry.name.endsWith('-needle.rgba')){
  const sourceWidth=entry.width,sourceHeight=entry.height;
  let minX=sourceWidth,minY=sourceHeight,maxX=-1,maxY=-1;
  for(let y=0;y<sourceHeight;y++)for(let x=0;x<sourceWidth;x++){
   if(pixels[(y*sourceWidth+x)*4+3]===0)continue;
   minX=Math.min(minX,x);maxX=Math.max(maxX,x);
   minY=Math.min(minY,y);maxY=Math.max(maxY,y);
  }
  if(maxX<0)throw Error('No needle artwork in '+entry.name);
  const offsetX=Math.max(0,minX-2),offsetY=Math.max(0,minY-2);
  const width=Math.min(sourceWidth,maxX+3)-offsetX,height=Math.min(sourceHeight,maxY+3)-offsetY;
  const cropped=Buffer.alloc(width*height*4);
  for(let y=0;y<height;y++){
   const start=((y+offsetY)*sourceWidth+offsetX)*4;
   pixels.copy(cropped,y*width*4,start,start+width*4);
  }
  pixels=cropped;
  Object.assign(entry,{sourceWidth,sourceHeight,offsetX,offsetY,width,height});
 }
 entry.sha256=crypto.createHash('sha256').update(pixels).digest('hex');
 fs.writeFileSync(path.join(root,entry.name),pixels);
}
const manifestPath=path.join(root,'manifest.json');
if(fs.existsSync(manifestPath)){
 const prior=JSON.parse(fs.readFileSync(manifestPath));
 exports.images.push(...prior.images.filter(row=>row.name.startsWith('touring-')||row.name==='right-shift.rgba'));
 if(prior.shiftRingSource)exports.shiftRingSource=prior.shiftRingSource;
 if(prior.touringRpmSource)exports.touringRpmSource=prior.touringRpmSource;
}
exports.schema=1;exports.vehicleVerified=false;exports.fixtureNumbersIncluded=false;fs.writeFileSync(manifestPath,JSON.stringify(exports,null,2)+'\n');console.log('Exported ten source-art RGBA surfaces without mock telemetry.');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
