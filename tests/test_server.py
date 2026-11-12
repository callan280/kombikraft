from http.client import HTTPConnection
import json
import threading
import unittest
from kombikraft.server import ViewerServer

class ViewerTests(unittest.TestCase):
    def setUp(self):
        self.server=ViewerServer(0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.port=self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2)

    def request(self,path,body=None,**headers):
        connection=HTTPConnection("127.0.0.1",self.port)
        connection.request("GET"if body is None else"POST",path,body=body,headers=headers)
        response=connection.getresponse();status=response.status;content=response.read();connection.close()
        return status,content

    def test_no_firmware_is_honest_and_viewer_resources_are_bundled(self):
        status,data=self.request("/api/toolkit/status")
        self.assertEqual(status,200);value=json.loads(data)
        self.assertFalse(value["factory"]["available"])
        self.assertFalse(value["wholeSystemBoot"])
        self.assertFalse(value["installationAllowed"])
        self.assertIn(b"KombiKraft",self.request("/")[1])
        self.assertEqual(self.request("/design/f97-gauges.js")[0],200)
        self.assertEqual(self.request("/design/factory-consumption.js")[0],404)
        self.assertEqual(self.request("/design/../../LICENSE")[0],404)

    def test_host_origin_and_no_live_write_routes(self):
        self.assertEqual(self.request("/api/toolkit/status",Host="remote.example")[0],403)
        body=json.dumps({"signal":"bc","raw":1})
        self.assertEqual(self.request("/api/factory-controller/input",body)[0],403)
        self.assertEqual(self.request("/api/factory-controller/input",body,Origin=self.server.origin)[0],503)
        self.assertEqual(self.request("/api/control",body,Origin=self.server.origin)[0],404)
        self.assertEqual(self.request("/api/factory-controller/input",json.dumps({"signal":"speed","raw":1}),Origin=self.server.origin)[0],400)

if __name__=="__main__":unittest.main()
