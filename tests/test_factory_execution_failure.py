"""A partially executed source machine cannot service another HTTP command."""
from http.client import HTTPConnection
import json
import threading
import unittest
from kombikraft.server import ViewerServer


class FailingBackend:
    def __init__(self):
        self.calls = 0
        self.status_calls = 0

    def status(self):
        self.status_calls += 1
        if self.calls:
            raise AssertionError('Partially executed source state was read again')
        return {'backend': 'authored-failure-fixture'}

    def receive(self, signal, raw):
        self.calls += 1
        raise ValueError('Authored source execution failure after a partial mutation')


class ExecutionFailureTests(unittest.TestCase):
    def test_invalid_input_does_not_fault_but_execution_failure_requires_new_machine(self):
        backend = FailingBackend()
        server = ViewerServer(0, factory=backend, check_control=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        def request(body=None):
            c = HTTPConnection('127.0.0.1', server.server_address[1])
            path = '/api/factory-controller/status' if body is None else '/api/factory-controller/input'
            c.request('GET' if body is None else 'POST', path,
                      body=None if body is None else json.dumps(body), headers={'Origin': server.origin})
            r = c.getresponse(); value = (r.status, json.loads(r.read())); c.close(); return value
        try:
            self.assertEqual(request({'signal': 'bc', 'raw': True})[0], 400)
            self.assertFalse(server.factory_faulted); self.assertEqual(backend.calls, 0)
            first = request({'signal': 'checkControl', 'raw': {'ccid': 2051}})
            self.assertEqual(first[0], 503); self.assertTrue(first[1]['sourceStateUnavailable'])
            self.assertEqual(backend.calls, 1)
            later = request({'signal': 'bc', 'raw': 1})
            self.assertEqual(later[0], 503); self.assertEqual(backend.calls, 1)
            status = request()
            self.assertEqual(status[0], 200); self.assertFalse(status[1]['available'])
            self.assertFalse(status[1]['checkControl']['available'])
            self.assertTrue(status[1]['checkControl']['sourceStateUnavailable'])
            self.assertEqual(backend.status_calls, 0)
        finally:
            server.shutdown(); server.server_close(); thread.join(2)


if __name__ == '__main__':
    unittest.main()
