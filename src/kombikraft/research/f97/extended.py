"""Optional exact-profile F97 image, controller and widget experiments."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from . import PROFILE, read_input, scene_bindings
from ._extended_profile import EXTENDED_PROFILE

SUITES=('all','image-sampling','loaded-images','controller','widgets')


def admit(data,role):
    """Reject unsupported bytes before any emulator module is imported."""
    expected=EXTENDED_PROFILE['dataBank'] if role=='dataBank' else PROFILE[role]
    if not isinstance(data,bytes) or hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError(f'{role}: unsupported source hash for {EXTENDED_PROFILE["id"]}')
    return data


def read_data_bank(path):
    path=Path(path)
    if path.stat().st_size>64*1024*1024:raise ValueError('dataBank: input exceeds64MiB')
    return admit(path.read_bytes(),'dataBank')


def admit_bitmaps(bitmaps):
    expected=EXTENDED_PROFILE['bitmaps']
    if not isinstance(bitmaps,dict) or set(bitmaps)!=set(expected):
        raise ValueError('Supply all19 named bitmap payloads from the supported source profile')
    for name,digest in expected.items():
        if not isinstance(bitmaps[name],bytes) or hashlib.sha256(bitmaps[name]).hexdigest()!=digest:
            raise ValueError(f'Unsupported source bitmap hash: {name}')
    return bitmaps


def read_bitmaps(manifest,root=None):
    """Read selected local CE51-extractor manifest files, never container data."""
    manifest=Path(manifest)
    if manifest.stat().st_size>32*1024*1024:raise ValueError('Bitmap manifest exceeds32MiB')
    document=json.loads(manifest.read_text())
    rows=document.get('resources') if isinstance(document,dict) else None
    if not isinstance(rows,list) or len(rows)>100000:raise ValueError('Invalid bounded CE51 resource manifest')
    root=Path(root) if root is not None else manifest.parent
    selected={}
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Invalid resource manifest row')
        name=row.get('name')
        if not isinstance(name,str) or name not in EXTENDED_PROFILE['bitmaps']:continue
        if name in selected:raise ValueError(f'Duplicate selected resource: {name}')
        value=row.get('decodedFile')
        if row.get('kind')!='0x7' or not isinstance(value,str) or not 1<=len(value)<=4096:
            raise ValueError(f'Invalid bitmap resource entry: {name}')
        path=Path(value);path=path if path.is_absolute() else root/path
        if path.stat().st_size>16*1024*1024:raise ValueError('Bitmap payload exceeds16MiB')
        selected[name]=path.read_bytes()
    return admit_bitmaps(selected)


def source_tables(bank,nor):
    """Bounded original class-name table and complete NOR string pool."""
    def word(data,at):
        if not 0<=at<=len(data)-4:raise ValueError('Source word outside input')
        return struct.unpack_from('<I',data,at)[0]
    pool=word(nor,0x58);length,count=word(nor,pool),word(nor,pool+4)
    if not 8<=length<=len(nor)-pool or count>100000:raise ValueError('Invalid source string pool')
    strings={};at=pool+8
    for _ in range(count):
        if at+2>pool+length:raise ValueError('Truncated source string length')
        size=struct.unpack_from('<H',nor,at)[0]
        if not size or at+2+size>pool+length:raise ValueError('Truncated source string')
        raw=nor[at+2:at+2+size]
        if raw[-1]!=0:raise ValueError('Unterminated source string')
        strings[str(at-pool)]=raw[:-1].decode('utf8');at=(at+2+size+3)&~3
    if at!=pool+length:raise ValueError('Source string-pool extent mismatch')
    classes={}
    for at in range(0x9bd244,0x9bd3d4,8):
        pointer,kind=struct.unpack_from('<2I',bank,at);p=pointer-0x10000
        if not 0<=p<len(bank):raise ValueError('Class-name pointer outside bank')
        end=bank.find(b'\0',p,min(p+256,len(bank)))
        if end<0:raise ValueError('Unterminated class name')
        classes[kind]=bank[p:end].decode('ascii')
    return strings,classes


def run(bank,scene=None,nor=None,data_bank=None,bitmaps=None,suite='all'):
    """Execute only admitted local inputs; no vehicle or transport adapter."""
    if suite not in SUITES:raise ValueError('Unknown extended suite')
    admit(bank,'bank')
    if suite!='controller':
        admit(scene,'scene');admit(nor,'nor')
    if suite in ('all','loaded-images'):
        admit(data_bank,'dataBank');admit_bitmaps(bitmaps)
    # All input admission is complete before optional Unicorn imports below.
    counts={};cases={};widget_data=None
    if suite!='controller':
        _,rows=scene_bindings(bank,scene,nor)
        textures=[t for row in rows for t in row['textures']]
    if suite in ('all','image-sampling'):
        from ._image_sampling import observe
        cases['imageSampling']=[observe(bank,scene,t,f) for t in textures for f in (0,0xa5)]
        cases['imagePropertyWitnesses']=[observe(bank,scene,textures[0],0xa5,(a,b,c))
            for a in (0,1) for b in (0,1,2) for c in (0,1)]
        counts.update(imageSamplingGenuine=48,imagePropertyWitnesses=12)
    if suite in ('all','loaded-images'):
        from ._loaded_image import observe
        loaded=[]
        for texture in textures:
            h=texture['record']['headerOffset']
            fields=[struct.unpack_from('<I',scene,h+o)[0] for o in (0x78,0x7c,0x80,0x88,0x8c)]
            if struct.unpack_from('<I',scene,h+0x84)[0]!=0:raise ValueError('Source mip-generation flag mismatch')
            item={**texture,'samplingFields':fields}
            loaded.extend(observe(bank,data_bank,bitmaps[item['bitmapResourceName']],item,f) for f in (0,0xa5))
        cases['loadedBitmapImages']=loaded;counts['loadedBitmapImages']=len(loaded)
    if suite in ('all','controller'):
        from ._speedometer_inputs import observe
        cases['speedometerInputs']=[observe(bank,v,s,r,f) for v in (0,4,5,255) for s in range(5)
            for r in ((0,0,0),(10000,20000,30000),(41600,65535,1)) for f in (0,0xa5)]
        counts.update(speedometerFixtures=120,speedometerOriginalInputCalls=600)
    if suite in ('all','widgets'):
        from ._widget_bindings import extract
        strings,classes=source_tables(bank,nor)
        nodes,widgets,joins=extract(scene,strings,classes)
        if len(nodes)!=492 or len(widgets)!=40 or joins!={'sceneNodes':177,'sceneRoot':1,'literalStringProperties':7}:
            raise ValueError('Supported source widget coverage mismatch')
        widget_data={'nodes':nodes,'widgets':widgets,'joinCounts':joins}
        counts.update(sceneNodes=492,widgetRecords=40,widgetProperties=185,exactWidgetNodePaths=177)
    inputs={'bank':hashlib.sha256(bank).hexdigest()}
    if suite!='controller':inputs.update(scene=hashlib.sha256(scene).hexdigest(),nor=hashlib.sha256(nor).hexdigest())
    if suite in ('all','loaded-images'):inputs['dataBank']=hashlib.sha256(data_bank).hexdigest()
    return {'schema':'kombikraft-f97-extended-research-v1','profile':EXTENDED_PROFILE['id'],'suite':suite,
        'passed':True,'inputSha256':inputs,'counts':counts,'cases':cases,'structuralWidgets':widget_data,
        'limits':{'originalImageConstructionAndAttachment':suite in ('all','loaded-images'),
            'boundedAllocationAdapterWhereDeclared':True,'selectedFreshZeroGlobalsExplicit':suite in ('all','loaded-images'),
            'ownerAndInteriorCallerStateExplicit':True,'propertyWitnessMutationsExplicit':True,
            'widgetJoinsAreStructuralOnly':True,'datastoreIdsAreNotCanIds':True,
            'providerOrCacheStartup':False,'fullSceneOrWidgetLifecycle':False,
            'originalGraphicsOrKernelExecuted':False,'vehicleCompatibilityVerified':False,'installationAllowed':False}}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',action='store_true',help='Print exact input hashes without firmware or Unicorn')
    p.add_argument('--suite',choices=SUITES,default='all')
    for name in ('bank','scene','nor','data-bank','bitmap-manifest','bitmap-root','output'):p.add_argument('--'+name,type=Path)
    args=p.parse_args(argv)
    if args.profile:
        print(json.dumps({**EXTENDED_PROFILE,'bank':PROFILE['bank'],'scene':PROFILE['scene'],'nor':PROFILE['nor'],'suites':SUITES},indent=2));return 0
    required=['bank','output']+([] if args.suite=='controller' else ['scene','nor'])
    if args.suite in ('all','loaded-images'):required+=['data_bank','bitmap_manifest']
    if not all(getattr(args,key) for key in required):p.error('Required inputs: '+', '.join('--'+x.replace('_','-') for x in required))
    if args.output.exists():p.error('Output exists; choose a new receipt path')
    try:
        bank=read_input(args.bank,'bank');scene=read_input(args.scene,'scene') if args.suite!='controller' else None
        nor=read_input(args.nor,'nor') if args.suite!='controller' else None
        data=read_data_bank(args.data_bank) if args.suite in ('all','loaded-images') else None
        images=read_bitmaps(args.bitmap_manifest,args.bitmap_root) if args.suite in ('all','loaded-images') else None
        result=run(bank,scene,nor,data,images,args.suite)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
    except (OSError,ValueError,AssertionError,ImportError,RuntimeError) as exc:p.exit(1,f'Extended checks failed: {exc}\n')
    print(json.dumps({k:result[k] for k in ('profile','suite','passed','counts','limits')},indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
