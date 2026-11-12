"""Execute original loader callback bodies; imported registries are explicitly captured, not simulated as production registries."""
from pathlib import Path
import json,struct,hashlib
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64,UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn.x86_const import *
from source_profile import admit_firmware,output_directory,make_parser,validate_map
parser=make_parser(__doc__);parser.add_argument('--carrier-map',required=True,type=Path);args=parser.parse_args()
P,b=admit_firmware(args.firmware);H=output_directory(args.output,P);m=json.loads(args.carrier_map.read_text())
if m.get('sourceSha256')!=hashlib.sha256(b).hexdigest():raise ValueError('carrier map source hash mismatch')
# Validate every imported PLT label against the admitted source ELF, not untrusted labels.
import subprocess,sys,tempfile
with tempfile.TemporaryDirectory(prefix='kombikraft-proxy-admit-')as temporary:
 subprocess.run([sys.executable,str(Path(__file__).with_name('make_carrier.py')),'--firmware',str(P),'--output',temporary],check=True,capture_output=True)
 exact=json.loads((Path(temporary)/'mgu-proxy-registration-complete-analysis-map.json').read_text())
 validate_map(m,exact)
po=struct.unpack_from('<Q',b,32)[0];pe,pn=struct.unpack_from('<HH',b,54);loads=[struct.unpack_from('<IIQQQQQQ',b,po+i*pe)for i in range(pn)]
imports={int(x['va'],16):x['name']for x in m['pltLabels']}
def run(entry,fill):
 u=Uc(UC_ARCH_X86,UC_MODE_64)
 for p in loads:
  if p[0]!=1:continue
  a=p[3]&~4095;size=(p[3]+p[6]+4095)//4096*4096-a;u.mem_map(a,size);u.mem_write(p[3],b[p[2]:p[2]+p[5]])
 stack=0x70000000;heap=0x10000000;fs=0x72000000;ret=0x71000000
 for a,n in [(stack,0x20000),(heap,0x20000),(fs,0x1000),(ret,0x1000)]:u.mem_map(a,n)
 u.mem_write(heap,bytes([fill])*0x20000);u.reg_write(UC_X86_REG_FS_BASE,fs);u.mem_write(fs+0x28,struct.pack('<Q',0x51c0decafef00d))
 sp=stack+0x1f008;u.mem_write(sp,struct.pack('<Q',ret));u.reg_write(UC_X86_REG_RSP,sp)
 calls=[];count=0;nextheap=heap
 def q(a):return struct.unpack('<Q',u.mem_read(a,8))[0]
 def r(reg):return u.reg_read(reg)
 def string(a):return bytes(u.mem_read(q(a),q(a+8))).decode()
 def return_(value=0):
  u.reg_write(UC_X86_REG_RAX,value);s=r(UC_X86_REG_RSP);u.reg_write(UC_X86_REG_RIP,q(s));u.reg_write(UC_X86_REG_RSP,s+8)
 def hook(uc,addr,size,data):
  nonlocal nextheap,count
  count+=1
  if addr==ret:u.emu_stop();return
  name=imports.get(addr)
  if not name:return
  a=[r(x)for x in [UC_X86_REG_RDI,UC_X86_REG_RSI,UC_X86_REG_RDX,UC_X86_REG_RCX,UC_X86_REG_R8,UC_X86_REG_R9]]
  if name.endswith('7Factory3getEv')or name.endswith('17AddressTranslator3getEv'):
   kind='factory'if'Factory'in name else'translator';pointer=0x11000000 if kind=='factory'else 0x12000000
   u.mem_write(a[0],struct.pack('<QQ',pointer,0));calls.append({'import':name,'adapter':'explicit inert singleton handle','kind':kind});return_(a[0])
  elif '9_M_createERmm'in name:
   n=q(a[1]);out=nextheap;nextheap+=(n+1+15)&~15;calls.append({'import':name,'adapter':'bounded string allocation','size':n+1});return_(out)
  elif 'registerInterface' in name:
   calls.append({'import':name,'adapter':'capture only; callback queue not implemented','factory':hex(a[0]),'callback':hex(a[1])});return_()
  elif 'AddressTranslator6insert' in name:
   calls.append({'import':name,'adapter':'capture only; address registry not implemented','address':string(a[1]),'service':a[2],'instance':a[3],'major':a[4],'minor':a[5]});return_(1)
  elif 'registerProxyCreateMethod'in name:
   calls.append({'import':name,'adapter':'capture only; proxy registry not implemented','interface':string(a[1]),'creator':hex(a[2])});return_()
  elif name=='_ZdlPv':calls.append({'import':name,'adapter':'bounded allocator free receipt','pointer':hex(a[0])});return_()
  else:raise RuntimeError('Unadmitted source import '+name)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(entry,ret,count=20000)
 assert r(UC_X86_REG_RIP)==ret,'instruction budget exhausted'
 return {'entry':hex(entry),'allocationFill':fill,'originalInstructionsAndImportStops':count,'returned':True,'calls':calls}
cases=[run(entry,fill)for entry in [0xc3340,0x28fd80]for fill in [0,0xa5]]
for c in cases:
 if c['entry']=='0xc3340':assert [x.get('callback')for x in c['calls']if'callback'in x]==['0x28fd80']
 else:
  rec=next(x for x in c['calls']if'address'in x);assert(rec['address'],rec['service'],rec['instance'],rec['major'],rec['minor'])==('local:de.bmw.infotainment.KombiIF:v1_0:1',46363,1,1,0)
  rec=next(x for x in c['calls']if'creator'in x);assert(rec['interface'],rec['creator'])==('de.bmw.infotainment.KombiIF:v1_0','0x299cd0')
report={'schema':'original-proxy-registration-execution-v1','source':P.name,'sourceSha256':hashlib.sha256(b).hexdigest(),'cases':cases,'passed':True,'scope':'Original constructor-registration bodies execute. Factory/get, string allocations and registration imports explicitly adapted/captured. No original registry dispatch or actual proxy/backend/network execution proved.','actualRuntimeBackendSelected':False,'mguSetterToKombiTransport399':False,'carContact':False}
report_path=H/'original-proxy-registration-execution.json'
if report_path.resolve()==P:raise ValueError('output would overwrite source')
report_path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(cases),'sourceInstructions':[c['originalInstructionsAndImportStops']for c in cases]}))
