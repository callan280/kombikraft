'use strict';
const {ClusterRender}=require('./cluster_render_client');
const {Session}=require('./session');
let session=null,interval=null;
function end(reason){if(interval)clearInterval(interval);interval=null;if(session)session.stop(reason);if(process.connected)process.send({status:reason});setTimeout(()=>process.exit(0),50);}
process.on('message',m=>{try{if(m.op==='sample'&&session)session.update(m.sample);else if(m.op==='start'&&!session){session=new Session(new ClusterRender('kombikraft_test'),{report:status=>{if(process.connected)process.send({status});}});session.update(m.sample);session.start(m.mode,m.theme);interval=setInterval(()=>{session.tick();if(!session.active)end('Factory display released.');},33);}else if(m.op==='stop')end('Factory display released.');}catch(e){end('Test stopped: '+e.message);}});
process.on('disconnect',()=>end('App disconnected.'));
process.on('SIGTERM',()=>end('Test cancelled.'));
// Independent worker lifetime: it cannot be extended by preferences or repeated clicks.
setTimeout(()=>end('Worker time limit reached.'),22000);
