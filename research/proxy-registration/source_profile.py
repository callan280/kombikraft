"""Admission for a single source profile; no firmware payload is included."""
from pathlib import Path
import hashlib,struct
SOURCE_SHA256="ce831cee2bd80a2f574f0f609314764164a219372344409ab9ff976e543cd669"
def admit_firmware(path):
 p=Path(path).resolve(); b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=SOURCE_SHA256: raise ValueError("unsupported firmware profile; expected SHA256 "+SOURCE_SHA256)
 if b[:6]!=b"\x7fELF\x02\x01": raise ValueError("source profile is not ELF64 little endian")
 if struct.unpack_from("<H",b,18)[0]!=62: raise ValueError("source architecture is not x86-64")
 return p,b
def output_directory(path,source):
 p=Path(path).resolve()
 if p==Path(source).resolve() or p.is_file(): raise ValueError("output must be a directory distinct from the firmware file")
 p.mkdir(parents=True,exist_ok=True);return p
def make_parser(description):
 import argparse
 p=argparse.ArgumentParser(description=description);p.add_argument("--firmware",required=True,type=Path);p.add_argument("--output",required=True,type=Path);return p
def validate_map(actual,expected):
 for key in ['sourceSha256','pltLabels','ranges']:
  if actual.get(key)!=expected.get(key):raise ValueError('carrier map differs from regenerated source field '+key)
