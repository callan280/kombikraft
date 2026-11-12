"""Own all source-machine operations in one disposable process/main thread.

The viewer exchanges local commands/results only. Native emulator failure can
invalidate this worker without taking down the HTTP viewer. This is crash
containment, not a security sandbox or a vehicle transport.
"""
import multiprocessing
from pathlib import Path
import threading
import os

from .backend import FactoryExecutionError


class SourceWorkerError(FactoryExecutionError):
    pass


def _source_main(connection, manifest, root, check_control):
    """Spawn target: construct, initialize, read and execute on this thread."""
    try:
        if check_control:
            from .check_control import OriginalCcControllerBackend, load_check_control_banks
            banks, auxiliary = load_check_control_banks(manifest, root)
            backend = OriginalCcControllerBackend(banks, auxiliary)
        else:
            from .backend import OriginalControllerBackend
            from .inputs import load_banks
            backend = OriginalControllerBackend(load_banks(manifest, root))
        backend.initialize()
        connection.send({'kind': 'ready', 'status': backend.status(),
                         'ownerPid': os.getpid(), 'ownerThread': threading.current_thread().name})
        while True:
            request = connection.recv()
            identifier = request['id']
            operation = request['operation']
            if operation == 'close':
                connection.send({'kind': 'result', 'id': identifier, 'result': None})
                break
            try:
                if operation == 'status':
                    result = backend.status()
                elif operation == 'receive':
                    value = request['value']
                    result = backend.receive(value['signal'], value['raw'])
                else:
                    raise SourceWorkerError('Unsupported local source operation')
                connection.send({'kind': 'result', 'id': identifier, 'result': result})
            except Exception as exc:
                connection.send({'kind': 'failed', 'id': identifier,
                                 'error': f'{type(exc).__name__}: {exc}'})
                break  # A partially executed machine is never reused.
    except EOFError:
        pass  # The owning viewer exited or closed its endpoint.
    except Exception as exc:
        try:
            connection.send({'kind': 'failed', 'error': f'{type(exc).__name__}: {exc}'})
        except (OSError, EOFError, BrokenPipeError):
            pass
    finally:
        connection.close()


class _ProcessControllerTransport:
    """Local process transport; the public subclass fixes the worker target."""
    def __init__(self, target, arguments, timeout=60):
        self._timeout = timeout
        self._lock = threading.RLock()
        self._sequence = 0
        self._failure = None
        self._closed = False
        self._owner = None
        context = multiprocessing.get_context('spawn')
        self._connection, child_connection = context.Pipe(duplex=True)
        self._process = context.Process(target=target, args=(child_connection, *arguments), daemon=True)
        try:
            self._process.start()
            child_connection.close()
            reply = self._read()
            if reply.get('kind') != 'ready' or reply.get('ownerPid') != self._process.pid or reply.get('ownerThread') != 'MainThread':
                raise SourceWorkerError(reply.get('error', 'Source worker did not initialize on its main thread'))
            self._owner = {'pid': reply['ownerPid'], 'thread': reply['ownerThread']}
        except Exception as exc:
            child_connection.close()
            self._fail(str(exc))
            raise SourceWorkerError(self._failure) from exc

    @property
    def worker_pid(self):
        return self._process.pid

    def _read(self):
        if not self._connection.poll(self._timeout):
            raise SourceWorkerError('Source worker exceeded its local response deadline')
        try:
            reply = self._connection.recv()
        except (EOFError, OSError) as exc:
            self._process.join(timeout=0.2)
            raise SourceWorkerError(f'Source worker exited without a result (exit {self._process.exitcode})') from exc
        if not isinstance(reply, dict):
            raise SourceWorkerError('Malformed local source-worker result')
        return reply

    def _cleanup(self):
        self._connection.close()
        if self._process.pid is not None:
            self._process.join(timeout=2)
            if self._process.is_alive():
                self._process.terminate()  # Only this owned Process handle.
                self._process.join(timeout=2)
            if self._process.is_alive():
                self._process.kill()
                self._process.join(timeout=2)

    def _fail(self, message):
        self._failure = message
        self._cleanup()

    def _call(self, operation, value=None):
        with self._lock:
            if self._failure or self._closed:
                raise SourceWorkerError(self._failure or 'Source worker is closed')
            self._sequence += 1
            request = {'id': self._sequence, 'operation': operation}
            if value is not None:
                request['value'] = value
            try:
                self._connection.send(request)
                reply = self._read()
                if reply.get('kind') != 'result' or reply.get('id') != self._sequence:
                    raise SourceWorkerError(reply.get('error', 'Source worker result identity mismatch'))
                return reply['result']
            except Exception as exc:
                self._fail(str(exc))
                raise SourceWorkerError(self._failure) from exc

    def receive(self, signal, raw):
        return self._call('receive', {'signal': signal, 'raw': raw})

    def status(self):
        if self._failure or self._closed:
            return {'available': False, 'backend': 'source-process-unavailable',
                    'executionModel': 'isolated-process-main-thread',
                    'message': 'Source machine is unavailable; restart the viewer for a fresh machine.',
                    'fullFactoryStartup': False, 'factoryGraphics': False, 'physicalTransport': False}
        try:
            result = self._call('status')
            return {**result, 'executionModel': 'isolated-process-main-thread'}
        except SourceWorkerError:
            return self.status()

    def close(self):
        with self._lock:
            if self._closed:
                return
            if self._failure is None:
                try:
                    self._call('close')
                except SourceWorkerError:
                    pass
            self._closed = True
            self._cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class SourceControllerProcess(_ProcessControllerTransport):
    """The original backend is created only after spawn, on the child main thread."""
    def __init__(self, manifest, root, check_control=False, timeout=60):
        super().__init__(_source_main, (str(Path(manifest).expanduser().resolve()),
                                      str(Path(root).expanduser().resolve()), check_control is True), timeout)
