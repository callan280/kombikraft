"""Offline route admission and shared-machine serialization; authored backend."""
from http.client import HTTPConnection
import json
import threading
import unittest
from kombikraft.server import ViewerServer


class RecordingBackend:
    def __init__(self):self.calls=[]
    def status(self):return {'fullFactoryStartup':False,'factoryGraphics':False}
    def receive(self,signal,raw):
        self.calls.append((signal,raw))
        return {'signal':signal,'events':[],'selected':{'selectedCcid':raw.get('ccid',0)} if isinstance(raw,dict) else None}


class CheckControlServerTests(unittest.TestCase):
    def setUp(self):
        self.backend=RecordingBackend();self.server=ViewerServer(0,factory=self.backend,check_control=True)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2)
    def request(self,body=None,path='/api/factory-controller/input',**headers):
        connection=HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=4)
        connection.request('GET' if body is None else 'POST',path,body=body,
                           headers={'Origin':self.server.origin,**headers})
        response=connection.getresponse();result=response.status,json.loads(response.read());connection.close();return result

    def test_enabled_cc_uses_existing_command_set_and_retains_actual_result(self):
        command={'signal':'checkControl','raw':{'ccid':2051}}
        status,reply=self.request(json.dumps(command));self.assertEqual(status,200)
        self.assertEqual(reply['requestedInput'],command)
        self.assertEqual(reply['result']['selected']['selectedCcid'],2051)
        self.assertEqual(reply['previewPlan']['status'],'unsupported');self.assertFalse(reply['graphicsAttached'])
        for signal in ('bc','leftLamp','rightLamp'):
            self.assertEqual(self.request(json.dumps({'signal':signal,'raw':1}))[0],200)
        state=self.request(path='/api/factory-controller/status')[1]['checkControl']
        self.assertTrue(state['available']);self.assertEqual(state['lastRequest'],command)
        self.assertEqual(state['lastResult'],reply['result']);self.assertEqual(state['previewPlan'],reply['previewPlan'])
        self.assertFalse(state['previewAdapter']['available'])
        self.assertEqual([row[0] for row in self.backend.calls],['checkControl','bc','leftLamp','rightLamp'])

    def test_explicit_capability_required_before_backend_execution(self):
        self.server.factory_check_control=False
        self.assertEqual(self.request(json.dumps({'signal':'checkControl','raw':{'ccid':2051}}))[0],503)
        self.assertFalse(self.backend.calls)
        self.assertEqual(self.request(json.dumps({'signal':'bc','raw':1}))[0],200)

    def test_shape_type_unknown_keys_and_lengths_rejected_before_execution(self):
        malformed=[{'signal':[],'raw':0},{'signal':'checkControl','raw':{'ccid':True}},
                   {'signal':'checkControl','raw':{'ccid':-1}},
                   {'signal':'checkControl','raw':{'ccid':1,'mode':False}},
                   {'signal':'checkControl','raw':{'ccid':1,'quality':256}},
                   {'signal':'checkControl','raw':{'ccid':1,'address':123}},
                   {'signal':'checkControl','raw':{'record66Hex':'gg'*66}},
                   {'signal':'checkControl','raw':{'record66Hex':'00'*65}},
                   {'signal':'bc','raw':True},{'signal':'bc','raw':3},
                   {'signal':'speed','raw':1}, {'signal':'bc','raw':1,'other':0}]
        for row in malformed:
            with self.subTest(row=row):self.assertEqual(self.request(json.dumps(row))[0],400)
        self.assertEqual(self.request(' '*257)[0],400)
        self.assertEqual(self.request('{')[0],400)
        self.assertFalse(self.backend.calls)

    def test_native66_fixture_is_bounded_and_preserved(self):
        raw={'record66Hex':bytes(range(66)).hex(),'quality':133,'mode':0}
        command={'signal':'checkControl','raw':raw};body=json.dumps(command)
        self.assertLessEqual(len(body.encode()),256)
        self.assertEqual(self.request(body)[0],200)
        self.assertEqual(self.backend.calls,[('checkControl',raw)])

    def test_host_and_origin_still_required(self):
        body=json.dumps({'signal':'checkControl','raw':{'ccid':1}})
        self.assertEqual(self.request(body,Origin='http://elsewhere.invalid')[0],403)
        self.assertEqual(self.request(body,Host='elsewhere.invalid')[0],403)
        self.assertFalse(self.backend.calls)


class SharedMachineSerializationTests(unittest.TestCase):
    def test_cc_bc_and_status_share_one_lock(self):
        class Backend(RecordingBackend):
            def __init__(self):
                super().__init__();self.running=threading.Event();self.release=threading.Event();self.bc_entered=threading.Event();self.concurrent_read=False
            def receive(self,signal,raw):
                if signal=='checkControl':
                    self.running.set()
                    if not self.release.wait(3):raise RuntimeError('Fixture release timeout')
                else:self.bc_entered.set()
                return super().receive(signal,raw)
            def status(self):
                self.concurrent_read|=self.running.is_set() and not self.release.is_set()
                return super().status()
        backend=Backend();server=ViewerServer(0,factory=backend,check_control=True)
        serving=threading.Thread(target=server.serve_forever,daemon=True);serving.start()
        results={};status_done=threading.Event()
        def request(key,command=None):
            connection=HTTPConnection('127.0.0.1',server.server_address[1],timeout=4)
            connection.request('GET' if command is None else 'POST',
                               '/api/factory-controller/status' if command is None else '/api/factory-controller/input',
                               None if command is None else json.dumps(command),{'Origin':server.origin})
            response=connection.getresponse();results[key]=response.status;response.read();connection.close()
            if command is None:status_done.set()
        cc=threading.Thread(target=request,args=('cc',{'signal':'checkControl','raw':{'ccid':2051}}))
        bc=threading.Thread(target=request,args=('bc',{'signal':'bc','raw':1}))
        status=threading.Thread(target=request,args=('status',))
        try:
            cc.start();self.assertTrue(backend.running.wait(2));bc.start();status.start()
            self.assertFalse(backend.bc_entered.wait(.1));self.assertFalse(status_done.wait(.1))
            backend.release.set()
            for worker in (cc,bc,status):worker.join(3);self.assertFalse(worker.is_alive())
            self.assertEqual(results,{'cc':200,'bc':200,'status':200});self.assertFalse(backend.concurrent_read)
        finally:
            backend.release.set();server.shutdown();server.server_close();serving.join(2)


if __name__=='__main__':unittest.main()
