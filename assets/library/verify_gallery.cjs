/* Offline JS/DOM-fixture checks; does not claim a graphical browser render. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const root=__dirname,els=new Map();let ctx;
class El{constructor(tag='div'){this.tagName=tag;this.children=[];this.style={};this.value='';this.dataset={};this.listeners={};this.textContent='';}append(...xs){for(const x of xs){this.children.push(x);if(this===head&&x.tagName==='script'){vm.runInContext(fs.readFileSync(path.join(root,x.src),'utf8'),ctx);queueMicrotask(()=>x.onload());}}}replaceChildren(...x){this.children=[];this.append(...x);}setAttribute(k,v){this[k]=v;}addEventListener(k,fn){this.listeners[k]=fn;}showModal(){this.open=true;}close(){this.open=false;}}
const head=new El('head');const document={head,documentElement:new El('html'),getElementById:id=>{if(!els.has(id))els.set(id,new El());return els.get(id);},createElement:tag=>new El(tag),fonts:{add(){},delete(){}}};
ctx=vm.createContext({document,console,Set,Map,Promise,Error,String,JSON,FontFace:class{async load(){return this;}}});ctx.window=ctx;
vm.runInContext(fs.readFileSync(path.join(root,'catalog.js'),'utf8'),ctx);
for(const r of ctx.KOMBIKRAFT_LIBRARY.records){if(r.imageSha256)assert.ok(fs.existsSync(path.join(root,'objects',r.imageSha256.slice(0,2),r.imageSha256+'.png')));if(r.resourceSha256)assert.ok(fs.existsSync(path.join(root,'objects',r.resourceSha256.slice(0,2),r.resourceSha256+(r.kind==='font'?'.ttf':'.bin'))));}
document.getElementById('kind').value='images';vm.runInContext(fs.readFileSync(path.join(root,'gallery.js'),'utf8'),ctx);const api=ctx.KombiKraftLibrary;
assert.equal(api.counts().all,16490);assert.equal(api.counts().filtered,9509);assert.equal(els.get('grid').children.length,100);
els.get('kind').value='fonts';api.apply();assert.equal(api.counts().filtered,29);
els.get('kind').value='images';els.get('family').value='F97 older ID6 CE51';api.apply();assert.ok(api.counts().filtered>2000);
els.get('search').value='telltale';api.apply();assert.ok(api.counts().filtered>0);
const first=els.get('grid').children[0].children[0];
(async()=>{await first.onclick();await new Promise(r=>setImmediate(r));assert.ok(els.get('detail').open);assert.match(els.get('metadata').textContent,/nativeControllerBindingVerified/);assert.ok(els.get('detailImage').src.startsWith('objects/'));els.get('close').onclick();assert.equal(els.get('detail').open,false);els.get('search').value='';els.get('family').value='';els.get('kind').value='';els.get('group').value='pictograms';api.apply();assert.ok(api.counts().filtered>100);console.log(JSON.stringify({result:'PASS',kind:'Node VM with DOM fixture, not browser screenshot',records:16490,images:9509,fontsAndContainers:29,actions:['initial render','font filter','F97 family','telltale search','lazy provenance shard','detail close','candidate group']}));})().catch(e=>{console.error(e);process.exitCode=1;});
