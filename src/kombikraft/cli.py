"""KombiKraft offline commands."""
import argparse
from importlib import metadata
import json
import sys
from .assets import AssetPack, AssetError

def doctor():
    dependencies = {}
    for name in ("unicorn", "Pillow"):
        try:
            dependencies[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            dependencies[name] = None
    return {"project": "KombiKraft", "python": sys.version.split()[0],
            "optionalDependencies": dependencies, "firmwareBundled": False,
            "wholeSystemBoot": False, "vehicleInstallationAllowed": False}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Report local tools and explicit coverage limits")
    commands.add_parser("factory-manifest", help="Print metadata-only template for the supported local firmware banks")
    assets = commands.add_parser("assets", help="Check a private local asset directory")
    assets.add_argument("action", choices=["verify"])
    assets.add_argument("directory")
    serve = commands.add_parser("serve", help="Start the loopback viewer")
    serve.add_argument("--port", type=int, default=8084)
    serve.add_argument("--assets", help="Private locally prepared source-graphics pack")
    serve.add_argument("--firmware-manifest", help="Exact supported source-bank manifest")
    serve.add_argument("--firmware-root", help="Directory containing locally supplied banks")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            print(json.dumps(doctor(), indent=2))
            return 0
        if args.command == "factory-manifest":
            from .factory.inputs import manifest_template
            print(json.dumps(manifest_template(), indent=2))
            return 0
        if args.command == "assets":
            print(json.dumps(AssetPack(args.directory).status(), indent=2))
            return 0
        if not 0 <= args.port <= 65535:
            parser.error("Port must be between 0 and 65535")
        if bool(args.firmware_manifest) != bool(args.firmware_root):
            parser.error("Supply both --firmware-manifest and --firmware-root")
        pack = AssetPack(args.assets) if args.assets else None
        factory = None
        if args.firmware_manifest:
            from .factory.inputs import load_banks
            from .factory.backend import OriginalControllerBackend
            factory = OriginalControllerBackend(load_banks(args.firmware_manifest, args.firmware_root))
            factory.initialize()
        from .server import ViewerServer
        with ViewerServer(args.port, pack, factory) as server:
            print(f"KombiKraft: {server.origin}/", flush=True)
            print("Offline only. Factory graphics startup and vehicle deployment remain unfinished.", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
        return 0
    except (AssetError, OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"KombiKraft: {exc}\n")
