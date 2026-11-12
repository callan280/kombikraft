/* Original compact rear-seat meshes/material and original Show/Hide output contract.
 * Explicit raw-state fixture only: occupancy, timing and live F40 coding are unbound. */
(function(root){'use strict';
const packageHash='6c536b49921cf8528c472190c45726406e5c1ca028bd522d363cf4fa48c6be5d',contractHash='461969fee63b02583e2ead1d670e79041592cfa52d5cd181ced863eb6a6ac278';
const hash=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(x=>x.toString(16).padStart(2,'0')).join('');
let gl,canvas,program,parts=[],states=[],proof=null,error=null,available=false;
async function checked(url,expected){const r=await fetch(url);if(!r.ok)throw Error('Missing seatbelt source: '+url);const b=await r.arrayBuffer();if(await hash(b)!==expected)throw Error('Seatbelt source hash mismatch');return b;}
function draw(raw,show){
 if(!Array.isArray(raw)||raw.length!==3||raw.some(x=>!Number.isInteger(x)||x<0||x>7)||typeof show!=='boolean')throw Error('Three raw rear-seat states 0–7 and explicit Show/Hide required');
 if(gl.isContextLost())throw Error('Seatbelt WebGL context lost');
 gl.viewport(0,0,1920,720);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.disable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.disable(gl.BLEND);gl.useProgram(program);
 parts.forEach((p,i)=>{const s=states.find(s=>s.rawInputByte===raw[i]).evaluated;if(!show||!s.parentVisible||s.opacity===0)return;
  for(const a of p.attributes){gl.bindBuffer(gl.ARRAY_BUFFER,a.buffer);gl.enableVertexAttribArray(a.location);gl.vertexAttribPointer(a.location,a.size,gl.FLOAT,false,0,0);}
  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,p.indices);gl.uniformMatrix4fv(gl.getUniformLocation(program,'u_MVPMatrix'),false,p.matrix);
  gl.uniform1f(gl.getUniformLocation(program,'Brightness'),1);gl.uniform1f(gl.getUniformLocation(program,'Opacity'),s.opacity);gl.uniform4fv(gl.getUniformLocation(program,'Color'),s.color);
  gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,p.texture);gl.uniform1i(gl.getUniformLocation(program,'tex0'),0);gl.drawElements(gl.TRIANGLES,p.count,gl.UNSIGNED_SHORT,0);
 });gl.finish();if(gl.getError()!==gl.NO_ERROR)throw Error('Seatbelt GPU error');
}
async function load(){try{
 const base='/seatbelt-source/render-package/',data=JSON.parse(new TextDecoder().decode(await checked(base+'factory-seatbelt-package.json',packageHash))),contract=JSON.parse(new TextDecoder().decode(await checked('/seatbelt-source/controller/state-render-contract-v2.json',contractHash)));states=contract.stateRows;
 canvas=document.createElement('canvas');canvas.width=1920;canvas.height=720;gl=canvas.getContext('webgl',{alpha:true,premultipliedAlpha:false,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL unavailable');
 const source=data.programs[data.meshes[0].effect],compile=(type,code)=>{const s=gl.createShader(type);gl.shaderSource(s,code);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
 program=gl.createProgram();gl.attachShader(program,compile(gl.VERTEX_SHADER,source.vertex));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,source.fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 for(const node of [378,385,382]){
  const mesh=data.meshes.find(x=>x.node===node),p={node,attributes:[],count:mesh.indices.length};let tx=0,tz=0;
  for(const a of mesh.ancestorChain){const t=a.transform;if(t.scale.some(x=>x!==1)||t.rotation_degrees.some(x=>Math.abs(x)>1e-6))throw Error('Unimplemented original seat transform');tx+=t.translation[0];tz+=t.translation[2];}
  p.matrix=[2/1920,0,0,0,0,0,0,0,0,2/720,0,0,2*tx/1920,2*tz/720,0,1];
  for(const [name,a]of Object.entries(mesh.attributes)){const location=gl.getAttribLocation(program,name);if(location<0)continue;const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(a.values),gl.STATIC_DRAW);p.attributes.push({location,buffer,size:a.size});}
  p.indices=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,p.indices);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(mesh.indices),gl.STATIC_DRAW);
  const t=data.textures[mesh.textures.tex0],b=await checked(base+t.file,t.pngSha256),im=new Image(),url=URL.createObjectURL(new Blob([b],{type:'image/png'}));im.src=url;try{await im.decode();}finally{URL.revokeObjectURL(url);}if(im.width!==t.width||im.height!==t.height)throw Error('Seat texture dimensions differ');
  p.texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,p.texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);for(const f of [gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,f,gl.LINEAR);for(const f of [gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,f,gl.CLAMP_TO_EDGE);parts.push(p);
 }
 const cases=[];for(const raw of [0,1,2,3,4,5,6,7,0]){draw([raw,raw,raw],true);const pixels=new Uint8Array(1920*720*4);gl.readPixels(0,0,1920,720,gl.RGBA,gl.UNSIGNED_BYTE,pixels);let visible=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i])visible++;const expected=[1,2,4,5].includes(raw);if(expected!==(visible>0))throw Error('Original raw visibility differs');cases.push({raw,visible,sha256:await hash(pixels)});}
 if(cases[0].sha256!==cases.at(-1).sha256)throw Error('Seatbelt OFF restoration failed');draw([1,2,5],false);const hidden=new Uint8Array(1920*720*4);gl.readPixels(0,0,1920,720,gl.RGBA,gl.UNSIGNED_BYTE,hidden);if(await hash(hidden)!==cases[0].sha256)throw Error('Original Hide output differs');
 proof={passed:true,packageHash,contractHash,originalGlsl:true,originalMeshes:true,originalUv:true,originalTextures:true,originalStateOutputs:true,cases,hideRestoresExact:true,nativePixelEquivalenceVerified:false,liveF40BindingVerified:false};available=true;
 }catch(e){error=e.message;available=false;}return status();}
function render(c,raw,show){if(!available)return false;try{draw(raw,show);c.drawImage(canvas,0,0);return true;}catch(e){error=e.message;available=false;return false;}}
function status(){return {available:available&&!gl?.isContextLost(),error,proof};}
root.FactorySeatbelt={load,render,status};
})(globalThis);
