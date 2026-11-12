"""Authored owner-thread and fatal-exit fixtures; no firmware or Unicorn."""
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
import json
import os
import threading
import unittest

from kombikraft.factory.worker import _ProcessControllerTransport, SourceWorkerError
from kombikraft.factory.backend import OriginalControllerBackend
from kombikraft.server import ViewerServer


def authored_worker(connection):
    count = 0
    connection.send({'kind': 'ready', 'ownerPid': os.getpid(),
                     'ownerThread': threading.current_thread().name, 'status': {}})
    try:
        while True:
            request = connection.recv(); operation = request['operation']
            if operation == 'close':
                connection.send({'kind': 'result', 'id': request['id'], 'result': None}); break
            if operation == 'receive' and request['value']['raw'] == 255:
                os._exit(71)  # Deliberate process death, not a native-emulator result.
            if operation == 'receive': count += 1
            result = {'available': True, 'ownerPid': os.getpid(),
                      'ownerThread': threading.current_thread().name, 'count': count}
            connection.send({'kind': 'result', 'id': request['id'], 'result': result})
    finally:
        connection.close()


class SourceWorkerTests(unittest.TestCase):
    def test_concurrent_callers_stay_on_one_owned_main_thread(self):
        with _ProcessControllerTransport(authored_worker, (), timeout=10) as worker:
            pid = worker.worker_pid
            self.assertNotEqual(pid, os.getpid())
            with ThreadPoolExecutor(max_workers=6) as callers:
                results = list(callers.map(lambda n: worker.receive('bc', n % 2), range(12)))
            self.assertEqual({r['ownerPid'] for r in results}, {pid})
            self.assertEqual({r['ownerThread'] for r in results}, {'MainThread'})
            self.assertEqual(sorted(r['count'] for r in results), list(range(1, 13)))
            self.assertEqual(worker.status()['count'], 12)
        self.assertFalse(worker._process.is_alive())
        self.assertFalse(worker.status()['available'])

    def test_fatal_worker_exit_does_not_kill_viewer_or_reuse_state(self):
        with _ProcessControllerTransport(authored_worker, (), timeout=10) as worker:
            server = ViewerServer(0, factory=worker)
            serving = threading.Thread(target=server.serve_forever, daemon=True); serving.start()
            def request(body=None):
                c = HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
                route = '/api/factory-controller/status' if body is None else '/api/factory-controller/input'
                c.request('GET' if body is None else 'POST', route,
                          None if body is None else json.dumps(body), {'Origin': server.origin})
                r = c.getresponse(); value = (r.status, json.loads(r.read())); c.close(); return value
            try:
                self.assertEqual(request({'signal': 'bc', 'raw': 1})[0], 200)
                failed = request({'signal': 'bc', 'raw': 255})
                self.assertEqual(failed[0], 503); self.assertTrue(failed[1]['sourceStateUnavailable'])
                self.assertFalse(worker._process.is_alive())
                self.assertEqual(request()[0], 200); self.assertFalse(request()[1]['available'])
                self.assertEqual(request({'signal': 'bc', 'raw': 1})[0], 503)
            finally:
                server.shutdown(); server.server_close(); serving.join(2)

    def test_raw_native_backend_cannot_be_shared_by_http_threads(self):
        uninitialized = object.__new__(OriginalControllerBackend)
        with self.assertRaisesRegex(ValueError, 'SourceControllerProcess'):
            ViewerServer(0, factory=uninitialized)

    def test_status_discovers_an_exited_owner_without_reading_old_source_state(self):
        with _ProcessControllerTransport(authored_worker, (), timeout=10) as worker:
            server = ViewerServer(0, factory=worker, check_control=True)
            serving = threading.Thread(target=server.serve_forever, daemon=True); serving.start()
            try:
                worker._process.terminate(); worker._process.join(5)
                c = HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
                c.request('GET', '/api/factory-controller/status')
                response = c.getresponse(); state = json.loads(response.read()); c.close()
                self.assertEqual(response.status, 200); self.assertFalse(state['available'])
                self.assertTrue(state['checkControl']['sourceStateUnavailable'])
                self.assertIsNone(state['checkControl']['previewPlan'])
                self.assertTrue(server.factory_faulted)
            finally:
                server.shutdown(); server.server_close(); serving.join(2)


if __name__ == '__main__':
    unittest.main()
