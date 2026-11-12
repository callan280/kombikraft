"""Loopback-only viewer for local graphics and explicit original-code fixtures."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path, PurePosixPath
import json
import mimetypes
import os
import threading
from urllib.parse import unquote, urlsplit
from .assets import AssetError, confined_file

class ViewerServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128
    def __init__(self, port=8084, assets=None, factory=None, library=None, check_control=False):
        from .factory.backend import OriginalControllerBackend
        if isinstance(factory, OriginalControllerBackend):
            raise ValueError('HTTP requires SourceControllerProcess; do not share a native emulator across request threads')
        self.assets = assets
        self.factory = factory
        self.factory_faulted = False
        self.factory_check_control = check_control is True
        self.factory_last_request = None
        self.factory_last_result = None
        self.factory_preview_plan = None
        self.factory_preview_adapter = None
        if self.factory_check_control:
            from .factory.preview_contract import SourceCcPreviewContract
            self.factory_preview_adapter = SourceCcPreviewContract(assets)
        self.library = Path(library).resolve() if library else None
        if self.library:
            confined_file(self.library, 'index.html')
            confined_file(self.library, 'catalog.js')
        self.factory_lock = threading.Lock()
        super().__init__(("127.0.0.1", port), ViewerHandler)
        self.origin = f"http://127.0.0.1:{self.server_address[1]}"

    def server_close(self):
        super().server_close()
        from .factory.worker import SourceControllerProcess
        if isinstance(self.factory, SourceControllerProcess):
            self.factory.close()

def factory_status(backend):
    if backend is None:
        return {"available": False, "backend": "not-loaded", "fullFactoryStartup": False,
                "factoryGraphics": False, "physicalTransport": False,
                "message": "Matching local firmware banks have not been supplied."}
    return {"available": True, **backend.status()}

def validate_factory_input(value):
    """Validate authored internal fixtures before invoking an original backend."""
    if not isinstance(value, dict) or set(value) != {"signal", "raw"} or not isinstance(value["signal"], str):
        raise ValueError("Expected a signal/raw fixture")
    if value["signal"] == "checkControl":
        from .factory.check_control import cc_fixture
        from .factory.backend import FactoryExecutionError
        try:
            cc_fixture(value["raw"])
        except FactoryExecutionError as exc:
            raise ValueError("Invalid internal Check Control fixture") from exc
    elif value["signal"] not in ("bc", "leftLamp", "rightLamp") or type(value["raw"]) is not int or value["raw"] not in (0, 1, 2, 255):
        raise ValueError("Only bounded offline controller fixtures are supported")
    return value

class ViewerHandler(BaseHTTPRequestHandler):
    def log_message(self, message, *args):
        if os.environ.get("KOMBIKRAFT_HTTP_DEBUG") == "1":
            print(message % args, "host="+str(self.headers.get("Host")), flush=True)

    def send(self, content, mime="application/json", status=200):
        if isinstance(content, dict):
            content = json.dumps(content).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def host_ok(self):
        return self.headers.get("Host") == self.server.origin.removeprefix("http://")

    def factory_snapshot(self):
        # Unicorn state is read only while the same lock excludes emulation.
        with self.server.factory_lock:
            result = ({"available": False, "backend": "execution-failed", "fullFactoryStartup": False,
                       "factoryGraphics": False, "physicalTransport": False,
                       "message": "Original controller execution failed; restart the viewer for a fresh source machine."}
                      if self.server.factory_faulted else factory_status(self.server.factory))
            if self.server.factory is not None and result.get("available") is False:
                self.server.factory_faulted = True
                self.server.factory_preview_plan = None
            result["checkControl"] = {
                "available": result.get("available") is True and self.server.factory_check_control and not self.server.factory_faulted,
                "sourceStateUnavailable": self.server.factory_faulted,
                "inputBoundary": "Authored internal record fixture; not CAN or SOME/IP",
                "graphicsAttached": False,
                "lastRequest": self.server.factory_last_request,
                "lastResult": self.server.factory_last_result,
                "previewPlan": self.server.factory_preview_plan,
                "previewAdapter": self.server.factory_preview_adapter.status() if self.server.factory_preview_adapter else {"available": False, "reason": "Original Check Control is not enabled"},
                "masterArbitrationVerified": False, "vehicleConnected": False,
            }
            return result

    def do_GET(self):
        if not self.host_ok():
            return self.send({"error": "Loopback viewer Host required"}, status=403)
        route = unquote(urlsplit(self.path).path)
        if route == "/api/toolkit/status":
            return self.send({"project": "KombiKraft", "assets": self.server.assets.status() if self.server.assets else {"available": False},
                              "factory": self.factory_snapshot(), "vehicleConnected": False,
                              "installationAllowed": False, "wholeSystemBoot": False,
                              "visualLibraryAvailable": self.server.library is not None})
        if route in ('/library', '/library/') or route.startswith('/library/'):
            if self.server.library is None:
                return self.send({'error': 'Visual library has not been supplied'}, status=404)
            relative = route.removeprefix('/library').lstrip('/') or 'index.html'
            try:
                file = confined_file(self.server.library, relative)
                if file.suffix not in ('.html','.js','.json','.md','.png','.ttf','.otf','.bin','.pixels'):
                    raise AssetError('Unsupported visual library file type')
                mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
                return self.send(file.read_bytes(), mime)
            except (AssetError, OSError):
                return self.send({'error':'Visual library file is unavailable'}, status=404)
        if route == "/api/factory-controller/status":
            return self.send(self.factory_snapshot())
        if route in ("/api/status", "/api/native-custom/status", "/api/factory-inputs"):
            return self.send({"state": "not-started", "available": False, "enabled": False,
                              "supportedControls": [], "nativeControls": [],
                              "fullFactoryStartup": False, "vehicleConnected": False,
                              "message": "No graphics runtime attached. Original-controller fixture status is available separately."})
        if route in ("/", "/setup") or route in ("/design", "/design/") and (self.server.assets is None or not self.server.assets.status()["layoutAvailable"]):
            return self.web("setup.html", "text/html; charset=utf-8")
        if route in ("/design", "/design/"):
            return self.web("design/index.html", "text/html; charset=utf-8")
        if route in ("/setup.js", "/setup.css"):
            return self.web(route[1:], "text/javascript" if route.endswith(".js") else "text/css")
        if route.startswith("/design/") and route.endswith(".js"):
            relative = route.removeprefix("/")
            if relative.startswith("design/simulation/"):
                relative = relative.removeprefix("design/")
            if self.web(relative, "text/javascript", missing_ok=True):
                return
        if self.server.assets is not None and route in self.server.assets.entries:
            try:
                data = self.server.assets.read(route)
            except (AssetError, OSError):
                return self.send({"error": "Local asset integrity check failed"}, status=409)
            mime = mimetypes.guess_type(route)[0] or "application/octet-stream"
            return self.send(data, mime)
        return self.send({"error": "Local route is unavailable"}, status=404)

    def web(self, name, mime, missing_ok=False):
        if ".." in name or PurePosixPath(name).is_absolute():
            return False
        path = resources.files("kombikraft").joinpath("web", *PurePosixPath(name).parts)
        if not path.is_file():
            if missing_ok:
                return False
            self.send({"error": "Viewer resource missing"}, status=404)
            return True
        self.send(path.read_bytes(), mime)
        return True

    def do_POST(self):
        if not self.host_ok() or self.headers.get("Origin") != self.server.origin:
            return self.send({"error": "Same-origin loopback request required"}, status=403)
        if urlsplit(self.path).path != "/api/factory-controller/input":
            return self.send({"error": "This package has no vehicle or native-scene write route"}, status=404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 256:
                raise ValueError("Expected a bounded fixture request")
            value = validate_factory_input(json.loads(self.rfile.read(length)))
            if value["signal"] == "checkControl" and not self.server.factory_check_control:
                return self.send({"error": "Original Check Control is not enabled; start the local viewer with --check-control"}, status=503)
            if self.server.factory is None:
                return self.send({"error": "Local factory backend is unavailable"}, status=503)
            with self.server.factory_lock:
                if self.server.factory_faulted:
                    return self.send({"error": "Original controller execution failed; restart the viewer for a fresh source machine",
                                      "sourceStateUnavailable": True}, status=503)
                try:
                    result = self.server.factory.receive(value["signal"], value["raw"])
                except Exception as exc:
                    self.server.factory_faulted = True
                    self.server.factory_preview_plan = None
                    raise RuntimeError("Original controller execution failed") from exc
                if value["signal"] == "checkControl":
                    self.server.factory_last_request = value
                    self.server.factory_last_result = result
                    self.server.factory_preview_plan = self.server.factory_preview_adapter.plan(result.get("selected"))
                preview_plan = self.server.factory_preview_plan if value["signal"] == "checkControl" else None
            return self.send({"result": result, "requestedInput": value, "previewPlan": preview_plan,
                              "graphicsAttached": False, "fullFactoryStartup": False,
                              "physicalTransport": False, "vehicleConnected": False})
        except (ValueError, TypeError, KeyError):
            return self.send({"error": "Invalid offline fixture input"}, status=400)
        except Exception:
            return self.send({"error": "Original-controller fixture failed; restart the viewer for a fresh source machine",
                              "sourceStateUnavailable": self.server.factory_faulted}, status=503)
