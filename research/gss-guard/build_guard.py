#!/usr/bin/env python3
"""Build the authored guard into a separate QEMU executable. GPL-2.0-or-later."""
from pathlib import Path
import argparse,hashlib,json,shlex,subprocess

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu-build-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();build=args.qemu_build_dir.resolve();out=args.output_dir.resolve()
    if out==build or build in out.parents:parser.error('Use a NEW output directory outside the existing QEMU build')
    records=json.loads((build/'compile_commands.json').read_text())
    example=next((r for r in records if r['file'].endswith('/hw/core/generic-loader.c')),None)
    if example is None:parser.error('QEMU build must include its upstream generic-loader device')
    out.mkdir(parents=True,exist_ok=False)
    source=HERE/'guarded-memory.c';obj=out/'guarded-memory.o';binary=out/'qemu-kombikraft-guard'
    original=shlex.split(example['command']);filtered=[];skip=False
    for item in original:
        if skip:skip=False;continue
        if item in ['-MQ','-MF','-o']:skip=True;continue
        if item in ['-MD','-c',example['file']]:continue
        filtered.append(item)
    compile_args=filtered+['-c',str(source),'-o',str(obj)]
    subprocess.run(compile_args,cwd=build,check=True)
    commands=subprocess.run(['ninja','-t','commands','qemu-system-x86_64'],cwd=build,
                            capture_output=True,text=True,check=True).stdout.splitlines()
    link=None
    for command in reversed(commands):
        parts=shlex.split(command)
        if '-o'in parts and Path(parts[parts.index('-o')+1]).name in ['qemu-system-x86_64','qemu-system-x86_64-unsigned']:
            link=parts;break
    if link is None:raise RuntimeError('Could not identify the existing QEMU compiler link command')
    link[link.index('-o')+1]=str(binary);link.append(str(obj))
    subprocess.run(link,cwd=build,check=True)
    version=subprocess.run([str(binary),'--version'],check=True,capture_output=True,text=True)
    receipt={'schema':'kombikraft-authored-guard-build-v1','guardSourceSha256':sha(source),
             'binarySha256':sha(binary),'objectSha256':sha(obj),'compileArgv':compile_args,
             'linkArgv':link,'version':version.stdout,'existingBuildOutputsRewritten':False}
    (out/'build-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(binary)


if __name__=='__main__':main()
