"""Optional original CC fixtures beside original BC/lamp inputs.

The selected text/icon data come from the constructed original CC owner. This
module has no network, car or renderer. Descriptor references require a separate
custom-preview bridge; they do not prove factory warning pixels or arbitration.
"""
from pathlib import Path
import hashlib
import json
import struct

from .backend import OriginalControllerBackend,FactoryExecutionError,DATA,PHASES
from .inputs import FactoryInputError,SourceBank,load_banks,validate_bank_file,manifest_template
from .profile import REQUIRED_BANKS,PROFILE

EXTRA=('18-203d0000.bin',0x3c80000,'54b2fd92d5e3beb84a8163a47092fbde61486e82ca1b47d713a037b119af9932')
CC_WATCH={0x2237e58:'ucv86-receiver',0x2240512:'record66-decoder',0x2213554:'ccm-to-hmi-callback',
    0x2bb8d2f:'cc-avoidcheck-aggregation',0x2bdac16:'cc-producer',0x2bdb907:'pending-reset',
    0x2c41190:'registered-widget-thunk',0x2c4067e:'cc-widget-input',0x2c40486:'cc-widget-update'}


def check_control_manifest_template():
    result=manifest_template()
    result['banks'].append({'name':EXTRA[0],'file':EXTRA[0],'base':hex(EXTRA[1]),'sha256':EXTRA[2]})
    return result


def load_check_control_banks(manifest,root):
    banks=load_banks(manifest,root)
    rows=json.loads(Path(manifest).read_text())['banks']
    if {r['name'] for r in rows}!={r[0] for r in REQUIRED_BANKS}|{EXTRA[0]}:
        raise FactoryInputError('Successor requires exactly14 named source banks')
    row=next(r for r in rows if r['name']==EXTRA[0])
    try:base=int(str(row['base']),0)
    except (ValueError,TypeError,KeyError) as exc:raise FactoryInputError('Invalid auxiliary bank metadata') from exc
    if base!=EXTRA[1] or row.get('sha256')!=EXTRA[2]:raise FactoryInputError('Auxiliary bank profile mismatch')
    data=validate_bank_file(root,row['file'],EXTRA[2])
    return banks,SourceBank(EXTRA[0],base,EXTRA[2],data)


def cc_fixture(raw):
    """Normalize an explicit internal native66 record or selected-ID fixture."""
    if not isinstance(raw,dict) or set(raw)-{'ccid','record66Hex','quality','mode'}:
        raise FactoryExecutionError('Expected a bounded checkControl fixture object')
    if ('ccid' in raw)==('record66Hex' in raw):raise FactoryExecutionError('Choose ccid or record66Hex')
    quality=raw.get('quality',0);mode=raw.get('mode')
    if type(quality) is not int or not 0<=quality<=255:raise FactoryExecutionError('Quality must be one opaque source byte')
    if mode is not None and (type(mode) is not int or mode not in (0,2)):
        raise FactoryExecutionError('Only source mode fixtures0/2 are admitted')
    if 'ccid' in raw:
        ccid=raw['ccid']
        if type(ccid) is not int or not 0<=ccid<=65535:raise FactoryExecutionError('CCID must be UInt16')
        native=struct.pack('<8H',ccid,0,0,0,0,0,0,0)+bytes(50)
        origin='authored-selected-id-fixture'
    else:
        text=raw['record66Hex']
        if not isinstance(text,str) or len(text)!=132:raise FactoryExecutionError('record66Hex must encode exactly66 bytes')
        try:native=bytes.fromhex(text)
        except ValueError as exc:raise FactoryExecutionError('Malformed native66 record') from exc
        if len(native)!=66:raise FactoryExecutionError('Malformed native66 record')
        origin='caller-supplied-internal-native66-fixture'
    wire=struct.pack('>8H',*struct.unpack_from('<8H',native))+native[16:]+bytes([quality])
    return native,wire,quality,mode,origin


class OriginalCcControllerBackend(OriginalControllerBackend):
    """One isolated source machine, sharing the BC/lamp/CC command envelope."""
    def __init__(self,banks,auxiliary,owner_fill=0):
        if owner_fill not in (0,0xa5):raise FactoryInputError('Only the reviewed owner fills0/A5 are admitted')
        if not isinstance(auxiliary,SourceBank) or (auxiliary.name,auxiliary.base,auxiliary.sha256)!=EXTRA or hashlib.sha256(auxiliary.data).hexdigest()!=EXTRA[2]:
            raise FactoryInputError('Exact auxiliary bank18 is required')
        self.cc_events=[];self.cc_owner=None;self.cc_fill=owner_fill;self.fill_next_cc_owner=False
        self.cc_last_receive=None;self.command_count=0;self.cc_setup=[];self.cc_payload_observations=0
        super().__init__(banks)
        size=(len(auxiliary.data)+4095)&~4095
        self.uc.mem_map(auxiliary.base,size);self.uc.mem_write(auxiliary.base,auxiliary.data)
        self.regions.append((auxiliary.base,auxiliary.base+len(auxiliary.data)))
        self.source_identity.append({'name':auxiliary.name,'sha256':auxiliary.sha256})

    def allocate(self,size):
        ptr=super().allocate(size)
        if self.fill_next_cc_owner:
            if size!=0x120:raise FactoryExecutionError('Unexpected original CC owner allocation')
            self.uc.mem_write(ptr,bytes([self.cc_fill])*size)
            self.filled_cc_owner=ptr;self.fill_next_cc_owner=False
        return ptr

    def _code(self,uc,address,size,user):
        if address in CC_WATCH:
            self.cc_events.append({'function':CC_WATCH[address],'originalVa':hex(address),
                'arguments':[uc.reg_read(r) for r in (self.r.UC_X86_REG_RDI,self.r.UC_X86_REG_RSI,self.r.UC_X86_REG_RDX)]})
            if address==0x2c4067e and uc.reg_read(self.r.UC_X86_REG_RSI)==0x42c:
                self.cc_payload_observations+=1
        super()._code(uc,address,size,user)

    def initialize(self):
        calls=super().initialize()
        for entry in (0x2b21efc,0x2b1fde9,0x2be1878,0x2bb8cfc,0x2bda95c,0x2c40d7d):
            self.cc_setup.append(self._invoke(entry))
        self.fill_next_cc_owner=True
        self.cc_setup.append(self._invoke(0x2c13140,DATA+0x17000,0xffffffffffffffff))
        self.cc_owner=self.qword(DATA+0x17008)
        if self.cc_owner!=self.filled_cc_owner or self.qword(self.cc_owner+8)!=0x39cd990 or self.qword(0x7baa0d8)!=self.cc_owner:
            raise FactoryExecutionError('Original CC owner/registration identity mismatch')
        self._typed_set(0xd,b'\x02')
        self._phases();self._phases()
        if self.uc.mem_read(self.cc_owner+0x118,1)[0]!=0:
            raise FactoryExecutionError('Unexpected graphics availability in isolated CC fixture')
        return {'base':calls,'cc':self.cc_setup,'graphicsBackend':False}

    def _typed_set(self,channel,payload):
        size=struct.unpack('<H',self.uc.mem_read(0x37958a0+2*channel,2))[0]
        if size!=len(payload):raise FactoryExecutionError('Typed source payload size mismatch')
        self.uc.mem_write(DATA+0x1000,payload)
        return self._invoke(0x2b17352,DATA+0x1000,channel)

    def _text(self,ptr):
        if not ptr:return None
        out=bytearray()
        for i in range(384):
            byte=self.uc.mem_read(ptr+i,1)[0]
            if not byte:return out.decode('utf8')
            out.append(byte)
        raise FactoryExecutionError('Original CC text exceeded its output-buffer bound')

    def _descriptor(self,ptr):
        if not ptr:return None
        if not any(lo<=ptr and ptr+16<=hi for lo,hi in self.regions):
            raise FactoryExecutionError('Original CC descriptor outside admitted source banks')
        width,height,fmt,opaque,pixels=struct.unpack('<4HQ',bytes(self.uc.mem_read(ptr,16)))
        if not 0<width<=16384 or not 0<height<=16384 or fmt not in (0x10,0x20):
            raise FactoryExecutionError('Unsupported original CC descriptor')
        return {'sourceProfile':PROFILE,'descriptorVa':hex(ptr),'width':width,'height':height,
            'format':fmt,'sourcePayloadVa':hex(pixels),'opaqueWord':opaque,
            'rendererReferenceOnly':True,'originalPixelsRendered':False}

    def selected_cc(self):
        if self.cc_owner is None:raise FactoryExecutionError('CC owner has not initialized')
        owner=self.cc_owner;ptrs=[self.qword(owner+o) for o in (0x38,0x40,0x48,0x50)]
        record_ptr=self.qword(0x3792b20+8*0x19b);record=bytes(self.uc.mem_read(record_ptr,64))
        payload_ptr=self.qword(0x3792b20+8*0x42c);payload=bytes(self.uc.mem_read(payload_ptr,72))
        icon_selector=self.uc.mem_read(owner+0x58,1)[0];text_selector=self.uc.mem_read(owner+0x59,1)[0]
        matched=(ptrs==[struct.unpack_from('<Q',payload,o)[0] for o in (0,8,16,32)]
                 and (icon_selector,text_selector)==(payload[66],payload[64]))
        if self.cc_payload_observations and not matched:
            raise FactoryExecutionError('Original CC consumer does not match its committed payload')
        slots=[]
        if ptrs[3]:
            for i in range(16):
                pointer,x,y=struct.unpack('<Qhh',bytes(self.uc.mem_read(ptrs[3]+16*i,12)))
                slots.append({'slot':i,'descriptor':self._descriptor(pointer),
                    'sourceSignedPlacement':[x,y] if pointer else None})
        self._invoke(0x2c40288,0,DATA+0x1400,icon_selector)
        palette=list(struct.unpack('<4f',bytes(self.uc.mem_read(DATA+0x1400,16))))
        self._invoke(0x2c40288,0,DATA+0x1400,text_selector)
        text_palette=list(struct.unpack('<4f',bytes(self.uc.mem_read(DATA+0x1400,16))))
        variant=self.uc.mem_read(0x44cce92,1)[0]
        return {'sourceProfile':PROFILE,'selectedCcid':struct.unpack_from('<H',record)[0],
            'selectedRecord64Hex':record.hex(),'sourcePayload72Hex':payload.hex(),
            'originalPayloadConsumerObserved':bool(self.cc_payload_observations),
            'payloadReadbackMatchesConsumer':matched,
            'sourceConsumerState':'original-42c-observed' if self.cc_payload_observations else 'awaiting-first-original-42c-callback',
            'textLines':[self._text(p) for p in ptrs[:2]],'primaryIcon':self._descriptor(ptrs[2]),
            'collectionSlots':slots,'iconSelector':icon_selector,'textSelector':text_selector,
            'iconSelectorHelperRGBA':palette,'textSelectorHelperRGBA':text_palette,
            'sourceLanguageOrdinal':self.uc.mem_read(0x7b9af81,1)[0],
            'sourceVariantIndex':variant,
            'sourceCollectionBankOrdinal':self.uc.mem_read(0x40bf520+variant,1)[0] if variant<64 else None,
            'currentCarCodingVerified':False,'opaqueMode136Cached':self.uc.mem_read(0x7afa660,1)[0],
            'originalGraphicsReady':bool(self.uc.mem_read(owner+0x118,1)[0]),
            'rendererBoundary':'descriptor/text data for separate custom-preview bridge; no original factory pixels',
            'masterArbitrationVerified':False,'physicalCanMappingVerified':False}

    def receive(self,signal,raw,quality=0):
        if signal!='checkControl':return super().receive(signal,raw,quality)
        if not self.initialized or self.cc_owner is None:raise FactoryExecutionError('Initialize backend before CC replay')
        native,wire,quality,mode,origin=cc_fixture(raw)
        before=len(self.cc_events);self.uc.mem_write(DATA+0x1000,wire)
        receive=self._invoke(0x2248ca6,0x86,DATA+0x1000,67)
        getter=self._invoke(0x224898e,0x12,0,DATA+0x1200)
        stored=bytes(self.uc.mem_read(DATA+0x1200,66))
        if stored!=native:raise FactoryExecutionError('Original CC decoder/native record mismatch')
        if mode is not None:self._typed_set(0x136,bytes([mode]))
        cycles=[self._phases(),self._phases()]
        events=self.cc_events[before:]
        selected=self.selected_cc()
        consumers=[e for e in events if e['function']=='cc-widget-input' and e['arguments'][1]==0x42c]
        self._invoke(0x2c40486,self.cc_owner)
        if self.uc.mem_read(self.cc_owner+0x5c,1)[0]!=0:raise FactoryExecutionError('Original CC update did not consume dirty state')
        self.command_count+=1
        result={'signal':signal,'fixtureOrigin':origin,'internalTransportRecord':0x86,
            'native66Hex':stored.hex(),'internalWire67Hex':wire.hex(),'qualityFixture':quality,
            'sourceGetterQuality':getter['return'],'qualitySemanticsVerified':False,
            'sourceMode136Fixture':mode,'receiver':receive,'cycles':cycles,'sourceEntries':events,
            'payloadConsumerCalls':len(consumers),'selected':selected,'commandIndex':self.command_count,
            'originalWidgetUpdateInvokedDirectly':True,'originalGraphicsRendered':False,
            'liveVehicleConnected':False,'installationAllowed':False}
        self.cc_last_receive={'commandIndex':self.command_count,'payloadConsumerCalls':len(consumers),
            'selectedCcid':selected['selectedCcid'],'qualityFixture':quality,'sourceGetterQuality':getter['return']}
        return result

    def command(self,value):
        if not isinstance(value,dict) or set(value)!={'signal','raw'}:
            raise FactoryExecutionError('Expected the existing signal/raw command envelope')
        if not isinstance(value['signal'],str) or value['signal'] not in ('bc','leftLamp','rightLamp','checkControl'):
            raise FactoryExecutionError('Unsupported offline source signal')
        return self.receive(value['signal'],value['raw'])

    def status(self):
        result=super().status()
        result.update(backend='original-controller-cc-offline-fixture',
            supportedSignals=['bc','leftLamp','rightLamp','checkControl'],
            cc={'ownerConstructed':self.cc_owner is not None,'extraBank':EXTRA[0],
                'lastReceive':self.cc_last_receive,'masterArbitrationVerified':False,
                'originalGraphicsRendered':False,'physicalCanMappingVerified':False})
        return result
