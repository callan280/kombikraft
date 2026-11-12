"""Offline local JSON-lines command session; no HTTP/vehicle/renderer endpoint."""
import argparse,json,sys
from pathlib import Path
from .check_control import OriginalCcControllerBackend,load_check_control_banks,check_control_manifest_template


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path)
    p.add_argument('--root',type=Path)
    p.add_argument('--manifest-template',action='store_true')
    p.add_argument('--commands',type=Path,help='Local NDJSON; otherwise read bounded lines from stdin')
    args=p.parse_args(argv)
    if args.manifest_template:print(json.dumps(check_control_manifest_template(),indent=2));return 0
    if args.manifest is None or args.root is None:p.error('Supply --manifest and --root')
    try:
        banks,auxiliary=load_check_control_banks(args.manifest,args.root)
        backend=OriginalCcControllerBackend(banks,auxiliary);backend.initialize()
        print(json.dumps({'status':backend.status(),'localOnly':True}),flush=True)
        stream=args.commands.open() if args.commands else sys.stdin
        try:
            for i in range(1001):
                line=stream.readline(2049)
                if not line:break
                if i>=1000:raise ValueError('Command session bound reached')
                if not line.strip():continue
                if len(line.encode())>2048:raise ValueError('Command exceeds2048bytes')
                result=backend.command(json.loads(line))
                print(json.dumps({'result':result,'originalGraphics':False,'vehicleConnected':False}),flush=True)
        finally:
            if args.commands:stream.close()
    except Exception as exc:p.exit(1,f'Offline Check Control fixture failed: {exc}\n')
    return 0


if __name__=='__main__':raise SystemExit(main())
