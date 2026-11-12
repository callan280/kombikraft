#!/usr/bin/env python3
"""Captured-kernel-specific workaround, restricted to an owned local QEMU Unix socket.
No network endpoint or vehicle interface. Changes disposable guest RAM only.
"""
import argparse,hashlib,json,socket,struct,time
from pathlib import Path
KERNEL_SHA='6a0ffde4cde7c91b4e5ead26e9a0747964b94c37d1263638248fe61f8b78273a'
BP=0xffffffff81d36c14; CS=0xffffffff81c25280

def read_packet(s):
 while s.recv(1)!=b'$':pass
 data=bytearray()
 while True:
  c=s.recv(1)
  if not c:raise EOFError('QEMU disconnected')
  if c==b'#':break
  data.extend(c)
 checksum=s.recv(2)
 if int(checksum,16)!=(sum(data)&255):raise RuntimeError('GDB packet checksum mismatch')
 s.sendall(b'+');return data.decode('ascii')
def send(s,text):
 data=text.encode();s.sendall(b'$'+data+b'#'+('%02x'%(sum(data)&255)).encode())
 if s.recv(1)!=b'+':raise RuntimeError('GDB did not acknowledge command')
def command(s,text):send(s,text);return read_packet(s)
def memory(s,addr,n):
 data=command(s,'m%x,%x'%(addr,n))
 if len(data)!=n*2:raise RuntimeError('Unexpected memory response '+data[:80])
 return bytes.fromhex(data)
def run(sock,kernel):
 p=Path(sock)
 if not str(p.parent).startswith('/tmp/kombikraft-native-') or p.name!='gdb.sock':raise RuntimeError('Only task-owned emulator socket supported')
 if hashlib.sha256(Path(kernel).read_bytes()).hexdigest()!=KERNEL_SHA:raise RuntimeError('Wrong kernel capture')
 s=socket.socket(socket.AF_UNIX);s.settimeout(300)
 for _ in range(100):
  try:s.connect(sock);break
  except (FileNotFoundError,ConnectionRefusedError):time.sleep(.1)
 else:raise RuntimeError('QEMU GDB socket unavailable')
 try:
  command(s,'qSupported:swbreak+;hwbreak+')
  if command(s,'Z0,%x,1'%BP)!='OK':raise RuntimeError('Breakpoint rejected')
  print('Waiting at verified timekeeping call',flush=True)
  send(s,'c');stop=read_packet(s)
  if not stop.startswith('T05') and not stop.startswith('S05'):raise RuntimeError('Unexpected stop '+stop)
  if command(s,'z0,%x,1'%BP)!='OK':raise RuntimeError('Could not remove breakpoint')
  regs=bytes.fromhex(command(s,'g'));rip=int.from_bytes(regs[16*8:17*8],'little')
  if rip!=BP:raise RuntimeError('Unexpected RIP '+hex(rip))
  if memory(s,BP,5)!=bytes.fromhex('e877ae3aff'):raise RuntimeError('Kernel instruction guard mismatch')
  if int.from_bytes(memory(s,CS,8),'little')!=0xffffffff8101fa70:raise RuntimeError('Clock read function guard mismatch')
  prior=memory(s,CS+16,8);mult,shift=struct.unpack('<II',prior)
  changed=False
  if mult==0:
   for addr,value in [(CS+16,1<<24),(CS+20,24)]:
    if command(s,'M%x,4:%s'%(addr,struct.pack('<I',value).hex()))!='OK':raise RuntimeError('Clock write failed')
   if memory(s,CS+16,8)!=struct.pack('<II',1<<24,24):raise RuntimeError('Clock readback mismatch')
   changed=True
  print(json.dumps({'breakpoint':hex(BP),'prior_mult':mult,'prior_shift':shift,'changed':changed,'guards_passed':True}),flush=True)
  send(s,'c');print('Guest continued',flush=True)
 finally:s.close()
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--socket',required=True);a.add_argument('--kernel',required=True);o=a.parse_args();run(o.socket,o.kernel)
