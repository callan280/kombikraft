"""Status and receive must serialize access to one original-code backend."""
from http.client import HTTPConnection
import json
import threading
import unittest
from kombikraft.server import ViewerServer

class BlockingFixtureBackend:
    def __init__(self):
        self.receiving = threading.Event()
        self.release = threading.Event()
        self.read_during_receive = False

    def receive(self, signal, raw):
        self.receiving.set()
        if not self.release.wait(3):
            raise RuntimeError("Test did not release its bounded receive")
        return {"events": []}

    def status(self):
        active = self.receiving.is_set() and not self.release.is_set()
        self.read_during_receive |= active
        return {"fullFactoryStartup": False, "readDuringReceive": active}

class FactoryServerConcurrencyTests(unittest.TestCase):
    def test_both_status_routes_wait_for_the_original_backend(self):
        for route in ("/api/factory-controller/status", "/api/toolkit/status"):
            with self.subTest(route=route):
                backend = BlockingFixtureBackend()
                server = ViewerServer(0, factory=backend)
                serving = threading.Thread(target=server.serve_forever, daemon=True)
                serving.start()
                result = {}
                done = threading.Event()

                def request(method, path, body=None):
                    connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=4)
                    headers = {"Origin": server.origin} if method == "POST" else {}
                    connection.request(method, path, body, headers)
                    response = connection.getresponse()
                    value = (response.status, json.loads(response.read()))
                    connection.close()
                    return value

                def get_status():
                    try:
                        result["get"] = request("GET", route)
                    finally:
                        done.set()

                post = threading.Thread(target=lambda: result.update(post=request(
                    "POST", "/api/factory-controller/input", json.dumps({"signal": "bc", "raw": 1}))))
                get = threading.Thread(target=get_status)
                try:
                    post.start()
                    self.assertTrue(backend.receiving.wait(2))
                    get.start()
                    self.assertFalse(done.wait(0.15), "Status bypassed the active original-code receive lock")
                    backend.release.set()
                    post.join(3)
                    get.join(3)
                    self.assertFalse(post.is_alive())
                    self.assertFalse(get.is_alive())
                    self.assertEqual(result["post"][0], 200)
                    self.assertEqual(result["get"][0], 200)
                    self.assertFalse(backend.read_during_receive)
                finally:
                    backend.release.set()
                    server.shutdown()
                    server.server_close()
                    serving.join(2)
                    if post.ident:
                        post.join(3)
                    if get.ident:
                        get.join(3)

if __name__ == "__main__":
    unittest.main()
