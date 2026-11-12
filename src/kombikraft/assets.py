"""Admit private local graphics without adding them to source distributions."""
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import hashlib
import json
import re

REQUIRED_LAYOUT_ROUTES = frozenset({
    *("/design/assets/"+name for name in ("digits.png","m-logo.png","model.png","fuel.png","speed-unit.png","rpm-unit.png","speed-limit-sign.png","speed-limit-digits.png")),
    "/design/fonts/BMWTARG.ttf", "/design/factory-consumption.js",
    "/f97-reference/render-package/f97-gauges-package.json",
    "/factory-cc/render-package/factory-cc-package.json",
    "/factory-rpm/render-package/factory-rpm-package.json",
    "/sport-factory/render-package/factory-sport-package.json",
    "/factory-mini/render-package/factory-mini-package.json",
    "/factory-mini/render-package/factory-motor-temp-package.json",
    "/design/factory-media/assets/provenance.json",
    "/design/factory-gear/assets/manifest.json",
    "/design/factory-stats/assets/provenance.json",
    "/design/factory-consumption/assets/factory-consumption-package.json",
    "/seatbelt-source/render-package/factory-seatbelt-package.json",
    "/seatbelt-source/controller/state-render-contract-v2.json",
    "/design/simulation/icon-manifest.json",
    "/design/simulation/expanded-icons/manifest.json",
    "/design/original-cc/manifest.json", "/design/warning-pictos/manifest.json",
    "/traction-research/glyph-manifest.json",
})
REQUIRED_LAYOUT_ROUTES |= frozenset(json.loads(Path(__file__).with_name("layout_routes.json").read_text())["requiredRoutes"])

class AssetError(ValueError):
    pass

def confined_file(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise AssetError("Invalid local asset path")
    parts = PurePosixPath(relative)
    if parts.is_absolute() or any(x in ("..", ".") for x in relative.split("/")):
        raise AssetError("Local asset path must be relative and confined")
    root = Path(root).resolve()
    candidate = root.joinpath(*parts.parts)
    for component in (candidate, *candidate.parents):
        if component == root:
            break
        if component.is_symlink():
            raise AssetError("Asset symlinks are not admitted")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise AssetError("Local asset file is unavailable")
    return resolved

@dataclass(frozen=True)
class LocalAsset:
    route: str
    file: str
    sha256: str

class AssetPack:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        try:
            manifest = json.loads(confined_file(self.root, "manifest.json").read_text())
        except (OSError, ValueError) as exc:
            raise AssetError("Cannot read local asset manifest") from exc
        if not isinstance(manifest, dict) or manifest.get("schema") != "kombikraft-local-assets-v1":
            raise AssetError("Unsupported local asset-pack schema")
        rows = manifest.get("entries")
        if not isinstance(rows, list) or not 1 <= len(rows) <= 4096:
            raise AssetError("Expected a bounded nonempty asset list")
        self.entries = {}
        self.bytes = 0
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"route", "file", "sha256"}:
                raise AssetError("Invalid local asset metadata")
            route = row["route"]
            if not isinstance(route, str) or not re.fullmatch(r"/[A-Za-z0-9_./#-]+", route) or ".." in route or route.startswith("/api/") or route in ("/", "/design", "/setup"):
                raise AssetError("Asset route is not admitted")
            if route in self.entries or not isinstance(row["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
                raise AssetError("Duplicate route or invalid asset hash")
            asset = LocalAsset(**row)
            self.entries[route] = asset
            content = self.read(route)
            self.bytes += len(content)
            if self.bytes > 512 * 1024 * 1024:
                raise AssetError("Asset pack exceeds the viewer's bounded import size")

    def read(self, route):
        asset = self.entries.get(route)
        if asset is None:
            raise AssetError("Asset route is not in the local manifest")
        content = confined_file(self.root, asset.file).read_bytes()
        if hashlib.sha256(content).hexdigest() != asset.sha256:
            raise AssetError("Local asset bytes changed; import verification failed")
        return content

    def status(self):
        missing = sorted(REQUIRED_LAYOUT_ROUTES - self.entries.keys())
        return {"available": True, "layoutAvailable": not missing,
                "missingLayoutRoutes": missing, "files": len(self.entries), "bytes": self.bytes,
                "source": "user-supplied local assets", "vehicleCompatibilityVerified": False}
