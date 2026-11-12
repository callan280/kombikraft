/* Custom metadata motion only. All glyphs remain the captured BMW font. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ClusterMediaMarquee=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const policy=Object.freeze({startDwellMs:1500,endDwellMs:1000,pixelsPerSecond:28});
 function offset(elapsedMs,textWidth,slotWidth){
  if(![elapsedMs,textWidth,slotWidth].every(Number.isFinite)||elapsedMs<0||textWidth<0||slotWidth<=0)throw Error('Finite media geometry/time required');
  const overflow=Math.max(0,textWidth-slotWidth);if(!overflow)return 0;
  const travel=overflow/policy.pixelsPerSecond*1000,period=policy.startDwellMs+2*travel+policy.endDwellMs;
  let t=elapsedMs%period;if(t<=policy.startDwellMs)return 0;t-=policy.startDwellMs;
  if(t<travel)return -t*policy.pixelsPerSecond/1000;t-=travel;
  if(t<=policy.endDwellMs)return -overflow;t-=policy.endDwellMs;
  return Math.min(0,-overflow+t*policy.pixelsPerSecond/1000);
 }
 function createTimeline(){
  let active=false,paused=false,key=null,last=null,elapsed=0;
  return{observe(next,now){
   if(!next||typeof next.active!=='boolean'||typeof next.paused!=='boolean'||typeof next.key!=='string'||!Number.isFinite(now)||now<0)throw Error('Explicit media visibility and monotonic time required');
   if(last!==null&&now<last)throw Error('Media clock moved backwards');
   if(last!==null&&active&&!paused)elapsed+=now-last;
   if(!next.active||!active||key!==next.key)elapsed=0;
   active=next.active;paused=next.paused;key=next.key;last=now;
   return elapsed;
  },elapsed:()=>elapsed};
 }
 return{policy,offset,createTimeline};
});
