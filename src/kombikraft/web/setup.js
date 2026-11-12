'use strict';
async function initialise(){
 const status=await(await fetch('/api/toolkit/status')).json();
 document.querySelector('#status').textContent=status.assets.layoutAvailable?`${status.assets.files} local asset files verified. Required layout entry points are present; the viewer checks dependent graphics while loading.`:status.assets.available?`Local pack verified, but ${status.assets.missingLayoutRoutes.length} required layout routes are missing.`:'No local graphics pack is loaded. Supply --assets to display the existing cluster layouts.';
 document.querySelector('#preview').hidden=!status.assets.layoutAvailable;
 const available=status.factory.available;
 document.querySelector('#factory-status').textContent=available?'Original partial controller backend initialized. Graphics startup is incomplete.':'Matching local firmware banks are not loaded. Fixture controls are unavailable.';
 for(const button of document.querySelectorAll('[data-signal]')){
  button.disabled=!available;
  button.onclick=async()=>{for(const b of document.querySelectorAll('[data-signal]'))b.disabled=true;try{const response=await fetch('/api/factory-controller/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({signal:button.dataset.signal,raw:Number(button.dataset.raw)})});const result=await response.json();document.querySelector('#result').textContent=JSON.stringify(result,null,2);}catch(error){document.querySelector('#result').textContent=error.message;}finally{for(const b of document.querySelectorAll('[data-signal]'))b.disabled=!available;}};
 }
}
initialise().catch(error=>{document.querySelector('#status').textContent='Toolkit status unavailable: '+error.message;});
