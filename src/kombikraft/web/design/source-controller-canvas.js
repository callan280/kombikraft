/* Bind the explicitly enabled original controller to this simulator's canvas. */
(function(){'use strict';
 const model=ClusterSourceControllerPreview.create();
 const button=document.getElementById('original-controller-release-preview');
 function redraw(){if(typeof draw==='function')draw();}
 function release(){model.release();if(button)button.disabled=true;redraw();}
 window.KombiKraftComputedCcPreview={project(base,entries){return model.project(base,entries);},release,snapshot:model.snapshot};
 if(button)button.onclick=release;
 document.getElementById('controller-enable')?.addEventListener('change',event=>{if(!event.target.checked)release();});
 window.KombiKraftOriginalController.setPreviewHandler(async(plan,result)=>{
  if(result?.signal!=='checkControl')return {applied:false,ignored:true};
  const accepted=model.accept(plan,result);
  if(button)button.disabled=false;
  placementCycling=false;
  document.getElementById('placement-popup').value='';
  document.getElementById('original-cc-popup').value='';
  redraw();
  if(typeof nativeCustomActive==='function'&&nativeCustomActive())return {applied:false,error:'The original-output canvas adapter is not attached to the native renderer'};
  const projected=model.project(simSnapshot,originalCcEntries);
  const status=projected?.originalControllerPreview;
  if(!accepted.applied||status?.status==='unsupported'||status?.status==='waiting-for-assets')return {applied:false,error:status?.error||accepted.error||'Reviewed warning graphics are not ready'};
  if(!ready)return {applied:false,error:'Cluster graphics are still loading'};
  if(theme==='factory')return {applied:false,error:'Choose M Round or Map Touring for the custom canvas composition'};
  return {...accepted,composition:'custom canvas',originalFactoryGraphics:false};
 });
})();
