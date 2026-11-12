/* Consistent browser text composition around the recovered BMW CC component. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClusterPopupLayout=api;})(globalThis,function(){'use strict';
const sourceIconQuad={x:712,y:588,width:64,height:64};
function layout(value,measure,options={}){
 const width=440,paragraphs=Array.isArray(options.originalLines)?options.originalLines.filter(Boolean):[String(value)],lines=[];let row='';
 for(const paragraph of paragraphs){
 for(const word of paragraph.trim().split(/\s+/)){
  let rest=word;
  while(measure(rest).width>width){
   if(row){lines.push(row);row='';}
   let cut=1;while(cut<rest.length&&measure(rest.slice(0,cut+1)).width<=width)cut++;
   lines.push(rest.slice(0,cut));rest=rest.slice(cut);
  }
  const next=row?row+' '+rest:rest;if(measure(next).width>width&&row){lines.push(row);row=rest;}else row=next;
 }
 if(row)lines.push(row);row='';
 }
 if(!lines.length)lines.push('');
 const truncated=lines.length>3;lines.length=Math.min(lines.length,3);
 if(truncated){let last=lines[2];while(last&&measure(last+'…').width>width)last=last.slice(0,-1);lines[2]=last+'…';}
 const step=44,centerY=628;
 const boxes=lines.map((text,i)=>{const m=measure(text),ascent=m.actualBoundingBoxAscent??22,descent=m.actualBoundingBoxDescent??0,left=m.actualBoundingBoxLeft??0,right=m.actualBoundingBoxRight??m.width;return{text,baseline:i*step,width:left+right,advanceWidth:m.width,ascent,descent,inkLeft:left,inkRight:right};});
 const yOffset=centerY-(Math.min(...boxes.map(b=>b.baseline-b.ascent))+Math.max(...boxes.map(b=>b.baseline+b.descent)))/2;
 const textWidth=Math.max(...boxes.map(b=>b.width)),iconPresent=options.iconPresent!==false,iconWidth=iconPresent?(options.iconWidth??48):0,gap=iconPresent?18:0,groupWidth=iconWidth+gap+textWidth,left=960-groupWidth/2,textCenter=left+iconWidth+gap+textWidth/2;
 for(const row of boxes){row.baseline+=yOffset;row.top=row.baseline-row.ascent;row.bottom=row.baseline+row.descent;row.x=textCenter+(row.inkLeft-row.inkRight)/2;row.align='left';row.visibleCenterX=textCenter;}
 return{lines:boxes,groupBounds:{left,right:left+groupWidth,centerX:960,centerY},icon:iconPresent?{centerX:left+iconWidth/2,centerY,maxInkSize:48,width:iconWidth}:null,sourceIconQuad,textIsCustomComposition:true,sourceGlyphInkMetricsVerified:false,truncated};
}
return{layout,sourceIconQuad};
});
