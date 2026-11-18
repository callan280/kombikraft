'use strict';

const { ClusterRender } = require('./cluster_render_client');
const { Session } = require('./session');

let session = null;
let interval = null;
let ending = false;
let lastTelemetry = -Infinity;
const startDeadline = setTimeout(() => end('No test requested.'),5000);

function report(status) {
    if (process.connected) process.send({ status });
}

function end(reason) {
    if (ending) return;
    ending = true;
    clearInterval(interval);
    clearTimeout(startDeadline);
    if (session && session.active) session.stop(reason);
    else if (reason) report(reason);
    setTimeout(() => process.exit(0), 50);
}

process.on('message', message => {
    if (ending) return;
    try {
        if (message.op === 'sample' && session) session.update(message.sample);
        else if (message.op === 'start' && !session) {
            clearTimeout(startDeadline);
            session = new Session(new ClusterRender('kombikraft_test'), { report });
            session.update(message.sample);
            session.start();
            interval = setInterval(() => {
                session.tick();
                const now=session.now();
                if(session.active&&process.connected&&now-lastTelemetry>=5000){
                    lastTelemetry=now;
                    process.send({telemetry:{speedKmh:session.sample.speed,rpm:session.sample.rpm,
                        ageMs:Math.round(now-session.sample.at),
                        shown:session.refs.filter(layer=>layer.state==='shown').length,total:session.refs.length}});
                }
                if (!session.active) end();
            }, 33);
        } else if (message.op === 'stop') end('Factory display released.');
    } catch (error) {
        end('Test stopped: ' + error.message);
    }
});

process.on('disconnect', () => end('App disconnected.'));
process.on('SIGTERM', () => end('Test cancelled.'));
