/* Original CC pairs are inspection fixtures, never synthetic fault bindings. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClusterOriginalCc=api;})(globalThis,function(){'use strict';
function validColours(entry){
 const palette={1:[80,214,0],2:[255,180,0],3:[255,0,0],4:[255,157,0]},white=[255,255,255];
 const selector=entry.sourceColorSelectorBits,alpha=entry.sourceFormat===32;
 return Number.isInteger(selector)&&selector>=0&&selector<=7&&[16,32].includes(entry.sourceFormat)&&entry.colorSelectorApplied===alpha&&entry.preserveDecodedRgb===!alpha&&entry.textSelector===5&&JSON.stringify(entry.textRgb)===JSON.stringify(white)&&JSON.stringify(entry.iconRgb)===JSON.stringify(alpha?(palette[selector]||white):white);
}
function entries(manifest){
 if(manifest?.schema!=='original-cc-preview-v2'||manifest.vehicleCompatibilityVerified!==false||manifest.nativeWarningLifecycleVerified!==false)throw Error('Invalid original CC preview scope');
 const ids=new Set();return manifest.entries.map(entry=>{
  if(!Number.isInteger(entry.ccid)||entry.id!=='source-cc:'+entry.ccid||ids.has(entry.id)||entry.nativeSignalBindingVerified!==false||entry.nativeUploadOrientationVerified!==false||entry.sourceVariantMeaningVerified!==false||!validColours(entry)||entry.inspectionVerticalFlip!==true||!Array.isArray(entry.originalLines)||!entry.originalLines.every(x=>typeof x==='string')||entry.text!==entry.originalLines.filter(Boolean).join('\n')||!/^assets\/[0-9a-f]+-\d{3}\.png$/.test(entry.file))throw Error('Invalid original CC source entry');
  ids.add(entry.id);return {...entry,originalLines:entry.originalLines.slice()};
 });
}
function project(state,entry){
 if(!entry)return state;
 return {...state,popup:{...entry,originalLines:entry.originalLines.slice(),placementFixture:true,originalCcFixture:true},placementFixture:true};
}
return{entries,project};
});
