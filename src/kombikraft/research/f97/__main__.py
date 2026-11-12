"""Check the supported older-F97 materials using three local source inputs."""
import argparse
import json
from pathlib import Path
from . import PROFILE,read_input,run


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',action='store_true',help='Print source hashes and exit')
    p.add_argument('--bank',type=Path,help='Unmodified decoded 4CEB NORboot bank13')
    p.add_argument('--scene',type=Path,help='Decoded ki_3d_high scene payload')
    p.add_argument('--nor',type=Path,help='Original older-F97 NOR CE51 container')
    p.add_argument('--output',type=Path,help='New local JSON receipt; existing files are not overwritten')
    args=p.parse_args(argv)
    if args.profile:
        print(json.dumps(PROFILE,indent=2));return 0
    if not all((args.bank,args.scene,args.nor,args.output)):
        p.error('Supply --bank, --scene, --nor and --output, or use --profile')
    if args.output.exists():
        p.error('Output exists; choose a new local receipt path')
    try:
        result=run(*(read_input(getattr(args,role),role) for role in ('bank','scene','nor')))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as stream:
            stream.write(json.dumps(result,indent=2)+'\n')
    except (OSError,ValueError,AssertionError,ImportError,RuntimeError) as exc:
        p.exit(1,f'Material checks failed: {exc}\n')
    print(json.dumps({k:result[k] for k in ('profile','passed','counts','limits')},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
