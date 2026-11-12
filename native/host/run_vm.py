#!/usr/bin/env python3
"""Launch one owned snapshot-only/no-NIC native-preview VM from local dependencies."""
from pathlib import Path
import argparse,hashlib,json,os,re,signal,socket,struct,subprocess,sys,threading,time,tempfile
from runtime import load,wrapper
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from build import digest
H=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime-import',type=Path,required=True);p.add_argument('--root-wrapper-metadata',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--seconds',type=int,default=30);p.add_argument('--preflight-only',action='store_true');a=p.parse_args();procs=[];handles=[];con=None;stop=threading.Event();result={'passed':False,'vmLaunched':False,'network':'none','snapshot':True,'carContact':False,'installationAllowed':False}
 def cleanup():
  stop.set()
  for child in reversed(procs):
   if child.poll()is None:
    assert child.pid>1;child.terminate()
  for child in procs:
   try:child.wait(timeout=8)
   except subprocess.TimeoutExpired:assert child.pid>1;child.kill();child.wait()
  if con:con.close()
  for f in handles:f.close()
 def interrupted(*unused):raise KeyboardInterrupt
 def spawn(args,name):
  f=(run/name).open('wb');handles.append(f);child=subprocess.Popen([str(v)for v in args],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT);procs.append(child);return child
 def send(command):con.sendall((command+'\n').encode())
 try:
  if not 5<=a.seconds<=3600:raise ValueError('Preview duration must be5..3600seconds')
  inputs=load(a.runtime_import);root=wrapper(a.root_wrapper_metadata.resolve());build=a.build.resolve();receipt=json.loads((build/'build-receipt.json').read_text());disk=build/'scene-lab.img'
  if receipt.get('schema')!='kombikraft-public-native-build-v1'or not receipt.get('runtimeImports')or not disk.is_file()or digest(disk)!=receipt['assetDiskSha256']:raise ValueError('Verified build with imported runtime and asset disk required')
  if a.preflight_only:print(json.dumps({'passed':True,'localDependenciesVerified':True,'vmLaunched':False,'installationAllowed':False}));return 0
  run=Path(tempfile.mkdtemp(prefix='kombikraft-native-',dir='/tmp'));result['runDirectory']=str(run);shm='/kombikraft-native-'+str(os.getpid());qargs=[inputs['qemu'],'-L',inputs['qemuShare'],'-M','q35','-cpu','Skylake-Client','-accel','tcg,thread=multi','-smp','1','-m','768M','-kernel',inputs['kernel'],'-append','console=ttyS2,115200 root=PARTUUID=4f344d47-01 rootfstype=ext4 rw rootwait loglevel=4 nokaslr sdhci_pci.power_default_on=1 init=/bin/sh idemu.role=native-f97','-device','sdhci-pci','-drive','if=none,id=sd0,file='+str(root)+',format=raw,snapshot=on','-device','sd-card,drive=sd0','-device','sdhci-pci','-drive','if=none,id=sceneassets,file='+str(disk)+',format=raw,snapshot=on','-device','sd-card,drive=sceneassets','-display','none','-nic','none','-rtc','base=localtime','-chardev','socket,id=inp,path='+str(run/'inp.sock')+',server=on,wait=off','-serial','chardev:inp','-chardev','socket,id=gl,path='+str(run/'gl.sock')+',server=on,wait=off','-serial','chardev:gl','-chardev','socket,id=con,path='+str(run/'con.sock')+',server=on,wait=off','-serial','chardev:con','-monitor','unix:'+str(run/'mon.sock')+',server=on,wait=off','-S','-gdb','unix:'+str(run/'gdb.sock')+',server=on,wait=off','-device','idemu-shm,shm-name='+shm+',size=134217728']
  signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted);gl=spawn([inputs['glHost'],'shm:'+shm,run],'graphics.log');q=spawn(qargs,'qemu.log');fix=spawn([sys.executable,H/'clock_fix.py','--socket',run/'gdb.sock','--kernel',inputs['kernel']],'clock.log');result.update(vmLaunched=True,ownedPid=os.getpid(),children=[{'pid':c.pid,'args':c.args}for c in procs]);(run/'session.json').write_text(json.dumps(result,indent=2)+'\n');console=run/'console.log'
  for _ in range(300):
   if q.poll()is not None or fix.poll()not in[None,0]:raise RuntimeError('Owned VM or guarded clock adapter failed')
   try:con=socket.socket(socket.AF_UNIX);con.connect(str(run/'con.sock'));break
   except OSError:
    if con:con.close()
    con=None;time.sleep(.1)
  if not con:raise RuntimeError('Own console unavailable')
  def reader():
   with console.open('ab',buffering=0)as f:
    while not stop.is_set():
     try:data=con.recv(65536)
     except OSError:break
     if not data:break
     f.write(data)
  threading.Thread(target=reader,daemon=True).start();deadline=time.monotonic()+120
  while not console.exists()or b'/ #'not in console.read_bytes():
   if time.monotonic()>deadline or q.poll()is not None:raise RuntimeError('Owned guest did not reach its shell')
   time.sleep(.2)
  commands=['mount -t proc proc /proc','mount -t sysfs sysfs /sys','mount -t tmpfs tmpfs /tmp','mount -t tmpfs tmpfs /run','mkdir -p /dev/shm /mnt/scene-lab /run/wayland','mount -t tmpfs tmpfs /dev/shm','KOMBIKRAFT_ASSETS=; KOMBIKRAFT_COUNT=0; for d in mmcblk0 mmcblk1; do if test "$(cat /sys/class/block/$d/size)" = 131072; then KOMBIKRAFT_ASSETS=/dev/$d; KOMBIKRAFT_COUNT=$((KOMBIKRAFT_COUNT+1)); fi; done; test "$KOMBIKRAFT_COUNT" = 1 && mount -o ro "$KOMBIKRAFT_ASSETS" /mnt/scene-lab','/sbin/ifconfig lo 127.0.0.1 up','IDEMU_WL_SIZE=1920x720 XDG_RUNTIME_DIR=/run/wayland /usr/bin/idemu-wl >/tmp/kombikraft-wl.log 2>&1 &','export XDG_RUNTIME_DIR=/run/wayland WAYLAND_DISPLAY=wayland-0 LD_LIBRARY_PATH=/mnt/scene-lab/lib:/usr/lib/hmi:/usr/lib','/mnt/scene-lab/native-f97 >/tmp/kombikraft-native.log 2>&1 &']
  for command in commands:send(command)
  end=time.monotonic()+a.seconds;queued=False;request_sequence=-1;initial_ack=None
  while time.monotonic()<end:
   if q.poll()is not None or gl.poll()is not None:raise RuntimeError('Owned graphics/VM process exited')
   send('tail -n8 /tmp/kombikraft-native.log');time.sleep(.5)
   transcript=console.read_text(errors='replace');loops=[int(x)for x in re.findall(r'NATIVE_F97_LOOP=(\d+)',transcript)]
   if not queued and loops and max(loops)>=120:
    frame=run/'frame.rgba'
    if frame.is_file():
     with frame.open('rb')as f:request_sequence=struct.unpack('<III',f.read(12))[2]
    send('echo 1 212 > /tmp/native-semantic-v9-request');queued=True
   for match in re.finditer(r'NATIVE_SEMANTIC_V9_ACK (\{[^\r\n]+\})',transcript):
    candidate=json.loads(match.group(1))
    if candidate.get('id')==1 and candidate.get('index')==212:initial_ack=candidate
  transcript=console.read_text(errors='replace');loops=[int(x)for x in re.findall(r'NATIVE_F97_LOOP=(\d+)',transcript)]
  if not initial_ack or initial_ack.get('readbackVerified')is not True or initial_ack.get('availableMask')!=0:raise RuntimeError('Initial provider-loss graphics fixture was not acknowledged')
  if not loops or max(loops)<120 or re.search(r'(?m)^(CUSTOM_NATIVE_FAILURE|Missing export)',transcript):raise RuntimeError('Native application did not confirm its render loop')
  frame=run/'frame.rgba'
  if not frame.is_file():raise RuntimeError('No framebuffer produced')
  raw=frame.read_bytes();w,h,seq=struct.unpack_from('<III',raw)
  if(w,h)!=(1920,720)or seq<=request_sequence or len(raw)!=64+w*h*4:raise RuntimeError('No valid native framebuffer')
  if not any(raw[64+i]for i in range(0,w*h*4,4)):raise RuntimeError('Native frame has no visible RGB content')
  result.update(passed=True,nativeRenderLoop=max(loops),initialState={'fixtureIndex':212,'availableMask':0,'nativeAcknowledgement':initial_ack,'frameSequenceBeforeRequest':request_sequence},nativeFramebuffer={'width':w,'height':h,'sequence':seq,'file':'frame.rgba'},fullFactoryControllerInitialization=False,vehicleCompatibilityVerified=False)
 except KeyboardInterrupt:result['interrupted']=True
 except(OSError,ValueError,KeyError,RuntimeError,subprocess.SubprocessError)as exc:result['failure']=str(exc)
 finally:
  cleanup();result['ownedChildrenStopped']=all(c.poll()is not None for c in procs)
  if'run'in locals():
   try:
    import ctypes
    ctypes.CDLL(None).shm_unlink(shm.encode())
   except Exception:pass
   (run/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 if not result['passed']:print(json.dumps(result),file=sys.stderr);return 2
 print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())
