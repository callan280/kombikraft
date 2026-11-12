/* Offline layout inspection: no signal injection and no factory startup claim. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClusterPlacement=api;})(globalThis,function(){'use strict';
function selectLamps(entries){
 const groups=[];
 for(const e of entries){
  if(!e.exactGlyphPixels||!e.colorVerified||!Array.isArray(e.authoredProjectedQuadBounds)||/_(US|China)_/.test(e.name))continue;
  const b=e.authoredProjectedQuadBounds;if(b.length!==4||b.some(v=>!Number.isFinite(v)))continue;
  const score=/RedShape/.test(e.name)?4:/YellowShape/.test(e.name)?3:/GreenShape|ActiveShape/.test(e.name)?2:/Grey|Gray|Off|Inactive/.test(e.name)?0:1;
  const group=groups.find(g=>Math.abs(g.bounds[0]-b[0])<=12&&Math.abs(g.bounds[1]-b[1])<=12);
  if(!group)groups.push({bounds:b,entry:e,score});else if(score>group.score)Object.assign(group,{entry:e,score});
 }
 return groups.map(g=>g.entry);
}
function project(snapshot,message){if(!snapshot||!message)return snapshot;return {...snapshot,popup:{...message,text:message.label,placementFixture:true},placementFixture:true};}
return{selectLamps,project,policy:{offlineOnly:true,mutatesSignals:false,factoryStartupVerified:false,region:'AU candidate: excludes US/China variants; equipment coding unverified',variantChoice:'One glyph per authored slot; red then amber then active, for placement only'}};
});
