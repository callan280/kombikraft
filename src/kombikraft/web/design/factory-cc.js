/* Original BMW CCPanel mesh, UVs, shader and texture; browser graphics port only. */
(function(root){'use strict';
const packageSha256='4974e322b6dae5be4e94a41778371d8a50ce0f759d34732692e7d77a4c78f75b';
const digest=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',b))).map(v=>v.toString(16).padStart(2,'0')).join('');
let gl,canvas,program,mesh,texture,indexBuffer,attributes=[],uniforms={},loaded=false,error=null,proof=null;
function draw(parentZ,opacity){
 if(!Number.isFinite(parentZ)||!Number.isFinite(opacity)||opacity<0||opacity>1)throw Error('Invalid CC graphics fixture');
 if(gl.isContextLost())throw Error('CC graphics context lost');
 gl.viewport(0,0,1920,720);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.disable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.disable(gl.BLEND);gl.useProgram(program);
 for(const a of attributes){gl.bindBuffer(gl.ARRAY_BUFFER,a.buffer);gl.enableVertexAttribArray(a.location);gl.vertexAttribPointer(a.location,a.size,gl.FLOAT,false,0,0);}
 gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indexBuffer);
 gl.uniformMatrix4fv(uniforms.u_MVPMatrix,false,[2/1920,0,0,0,0,0,0,0,0,2/720,0,0,0,2*parentZ/720,0,1]);
 gl.uniform1f(uniforms.u_ExtendX,mesh.uniforms.u_ExtendX);gl.uniform1f(uniforms.oparam0,opacity);
 gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.uniform1i(uniforms.tex0,0);gl.drawElements(gl.TRIANGLES,mesh.indices.length,gl.UNSIGNED_SHORT,0);gl.finish();
 if(gl.getError()!==gl.NO_ERROR)throw Error('CC graphics draw failed');
}
function render(c,placement='popup'){
 if(!loaded||!proof?.passed)return false;
 try{draw(placement==='baseline'?-147:-243,1);c.drawImage(canvas,0,0);return true;}catch(e){error=e.message;loaded=false;return false;}
}
async function load(base='/factory-cc/render-package/'){
 try{
 const response=await fetch(base+'factory-cc-package.json');if(!response.ok)throw Error('CC package missing');const bytes=await response.arrayBuffer();if(await digest(bytes)!==packageSha256)throw Error('CC package SHA mismatch');
 const data=JSON.parse(new TextDecoder().decode(bytes));if(data.format!=='captured-bmw-ccpanel-v1')throw Error('CC format mismatch');mesh=data.meshes.find(m=>m.node===1031);if(!mesh)throw Error('Original CC main mesh missing');
 canvas=document.createElement('canvas');canvas.width=1920;canvas.height=720;gl=canvas.getContext('webgl',{alpha:true,premultipliedAlpha:false,preserveDrawingBuffer:true});if(!gl)throw Error('WebGL unavailable');
 const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
 const source=data.programs[mesh.effect];program=gl.createProgram();gl.attachShader(program,compile(gl.VERTEX_SHADER,source.vertex));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,source.fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
 for(const[name,a]of Object.entries(mesh.attributes)){const location=gl.getAttribLocation(program,name);if(location<0)continue;const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(a.values),gl.STATIC_DRAW);attributes.push({location,buffer,size:a.size});}
 indexBuffer=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,indexBuffer);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(mesh.indices),gl.STATIC_DRAW);
 for(const name of['u_MVPMatrix','u_ExtendX','oparam0','tex0'])uniforms[name]=gl.getUniformLocation(program,name);
 const t=data.textures[mesh.textures.tex0],r=await fetch(base+t.file);if(!r.ok)throw Error('CC texture missing');const b=await r.arrayBuffer();if(await digest(b)!==t.pngSha256)throw Error('CC texture SHA mismatch');
 const image=new Image(),url=URL.createObjectURL(new Blob([b],{type:'image/png'}));image.src=url;try{await image.decode();}finally{URL.revokeObjectURL(url);}if(image.width!==t.width||image.height!==t.height)throw Error('CC texture dimensions differ');
 texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);for(const f of[gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,f,gl.LINEAR);for(const f of[gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,f,gl.CLAMP_TO_EDGE);
 const cases=[];for(const opacity of[0,1,0]){draw(-243,opacity);const pixels=new Uint8Array(1920*720*4);gl.readPixels(0,0,1920,720,gl.RGBA,gl.UNSIGNED_BYTE,pixels);let count=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]>16)count++;cases.push({opacity,visiblePixels:count,rgbaSha256:await digest(pixels)});}
 if(cases[0].visiblePixels||cases[1].visiblePixels<100||cases[2].visiblePixels||cases[0].rgbaSha256!==cases[2].rgbaSha256)throw Error('CC opacity/restoration proof failed');
 proof={passed:true,cases,packageSha256,originalGlsl:true,originalMesh:true,originalUv:true,originalTexture:true,popupParentZ:-243,baselineReuseParentZ:-147,baselineReuseIsCustom:true,factoryWarningArbitrationVerified:false,nativePixelEquivalenceVerified:false};loaded=true;error=null;
 }catch(e){error=e.message;loaded=false;}return status();
}
function status(){return{available:loaded&&!gl.isContextLost()&&proof?.passed===true,error,proof,packageSha256};}
root.FactoryCc={load,render,status};
})(globalThis);
