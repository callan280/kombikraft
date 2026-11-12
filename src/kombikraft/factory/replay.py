"""Replay the bounded BC and actual lamp-status controller fixture."""
import argparse
import json
from .inputs import load_banks

def replay(backend):
    backend.initialize()
    cases = []
    for signal, on, off in (("bc", 0x98, 0x99), ("leftLamp", 0x13D, 0x13C),
                            ("rightLamp", 0x13F, 0x13E)):
        for raw, expected in zip((1, 1, 0, 0, 2, 255, 1, 0),
                                 (on, None, off, None, None, None, on, off)):
            result = backend.receive(signal, raw)
            if result["events"] != ([expected] if expected is not None else []):
                raise RuntimeError(f"Original event mismatch for {signal}, raw {raw}")
            if result["callbackCount"] != 1 or len(result["phases"]) != 5:
                raise RuntimeError("Original callback/scheduler path was not observed")
            cases.append({"signal": signal, "raw": raw, "events": result["events"]})
    return {"passed": True, "cases": cases, "status": backend.status()}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Local source-bank JSON manifest")
    parser.add_argument("--root", required=True, help="Root containing locally imported firmware banks")
    args = parser.parse_args(argv)
    from .backend import OriginalControllerBackend
    try:
        report = replay(OriginalControllerBackend(load_banks(args.manifest, args.root)))
    except Exception as exc:
        parser.exit(1, f"Factory fixture failed: {exc}\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
