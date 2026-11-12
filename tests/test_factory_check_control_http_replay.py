"""Opt-in actual original-code replay through the loopback simulator route."""
from http.client import HTTPConnection
import json,os,threading,unittest


class CheckControlHttpReplayTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('KOMBIKRAFT_CC_MANIFEST') and os.environ.get('KOMBIKRAFT_FIRMWARE_ROOT'),
                         'Local 14-bank Check Control inputs are not supplied')
    def test_actual_source_cc_and_existing_lamps_share_http_command_set(self):
        from kombikraft.factory.worker import SourceControllerProcess
        from kombikraft.server import ViewerServer
        from kombikraft.assets import AssetPack
        backend=SourceControllerProcess(os.environ['KOMBIKRAFT_CC_MANIFEST'],os.environ['KOMBIKRAFT_FIRMWARE_ROOT'],check_control=True)
        pack=AssetPack(os.environ['KOMBIKRAFT_ASSET_PACK']) if os.environ.get('KOMBIKRAFT_ASSET_PACK') else None
        server=ViewerServer(0,assets=pack,factory=backend,check_control=True)
        serving=threading.Thread(target=server.serve_forever,daemon=True);serving.start()
        def request(signal,raw):
            command={'signal':signal,'raw':raw};connection=HTTPConnection('127.0.0.1',server.server_address[1],timeout=60)
            connection.request('POST','/api/factory-controller/input',json.dumps(command),{'Origin':server.origin})
            response=connection.getresponse();result=json.loads(response.read());connection.close()
            self.assertEqual(response.status,200,result);self.assertEqual(result['requestedInput'],command)
            self.assertFalse(result['physicalTransport']);self.assertFalse(result['vehicleConnected'])
            if signal=='checkControl':
                plan=result['previewPlan'];selected=result['result']['selected']['selectedCcid']
                self.assertEqual(plan['status'],'supported' if pack and selected in (0,2051,212) else 'unsupported')
                if plan['status']=='supported':self.assertEqual(plan['action'],'clear' if selected==0 else 'show')
                self.assertFalse(result['graphicsAttached'])
            return result['result']
        try:
            self.assertEqual(request('bc',1)['events'],[0x98])
            active=request('checkControl',{'ccid':2051});selected=active['selected']
            self.assertEqual(selected['textLines'],['Emissions failure.',''])
            self.assertEqual((selected['sourceVariantIndex'],selected['sourceCollectionBankOrdinal'],selected['sourceLanguageOrdinal']),(1,1,2))
            duplicate=request('checkControl',{'ccid':2051})
            self.assertEqual(duplicate['payloadConsumerCalls'],0);self.assertEqual(duplicate['selected'],selected)
            self.assertEqual(request('leftLamp',1)['events'],[0x13d])
            self.assertEqual(request('rightLamp',1)['events'],[0x13f])
            self.assertEqual(request('checkControl',{'ccid':212})['selected']['textLines'],['Stop carefully.','Switch off engine.'])
            self.assertEqual(request('checkControl',{'ccid':2051,'mode':2})['selected']['selectedCcid'],34)
            clear=request('checkControl',{'ccid':0,'mode':0})['selected']
            self.assertEqual(clear['textLines'],[None,None]);self.assertIsNone(clear['primaryIcon'])
            self.assertEqual((clear['iconSelector'],clear['textSelector']),(255,255))
            self.assertEqual(request('leftLamp',0)['events'],[0x13c])
            self.assertEqual(request('rightLamp',0)['events'],[0x13e])
            self.assertEqual(request('bc',0)['events'],[0x99])
        finally:
            server.shutdown();server.server_close();serving.join(2)


if __name__=='__main__':unittest.main()
