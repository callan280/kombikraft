'use strict';

const { ClusterRender } = require('./cluster_render_client');
const { Session } = require('./session');

let session = null;
let interval = null;
let ending = false;
const startDeadline = setTimeout(() => end('No test requested.'),5000);
let runDeadline = null;

function report(status) {
    if (process.connected) process.send({ status });
}

function end(reason) {
    if (ending) return;
    ending = true;
    clearInterval(interval);
    clearTimeout(startDeadline);
    clearTimeout(runDeadline);
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
            if (message.theme !== 'round-stay') runDeadline=setTimeout(()=>end('Worker time limit reached.'),22000);
            session = new Session(new ClusterRender('kombikraft_test'), { report });
            session.update(message.sample);
            session.start(message.mode, message.theme);
            interval = setInterval(() => {
                session.tick();
                if (!session.active) end();
            }, 33);
        } else if (message.op === 'stop') end('Factory display released.');
    } catch (error) {
        end('Test stopped: ' + error.message);
    }
});

process.on('disconnect', () => end('App disconnected.'));
process.on('SIGTERM', () => end('Test cancelled.'));
