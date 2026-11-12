"""Original exact-profile node tree/defaults and effective Camera research.

Use four admitted local inputs. No private research directory, VM, original
runtime library, vehicle transport or graphics rendering is required.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
from . import read_input
from .extended import admit,read_data_bank,source_tables
from ._scene_profile import SCENE_PROFILE

sha=lambda b:hashlib.sha256(b).hexdigest()


def _json_domain(value):
    """Authored tuple metadata becomes arrays; no fields/numbers are dropped."""
    return json.loads(json.dumps(value))


def run(bank,scene,nor,data_bank):
    """Admit all input identities before importing optional emulation code."""
    for role,value in [('bank',bank),('scene',scene),('nor',nor),('dataBank',data_bank)]:
        admit(value,role)
    strings,classes=source_tables(bank,nor)
    from ._widget_bindings import extract
    nodes,widgets,joins=extract(scene,strings,classes)
    if len(nodes)!=492 or dict(Counter(n['className']for n in nodes))!=SCENE_PROFILE['expectedNodes']:
        raise ValueError('Unsupported source node coverage')
    # Original worlds/policies and Cameras execute in SEPARATE bounded units.
    # There is no fabricated provider result or co-resident full-scene claim.
    from ._scene_tree import observe as tree
    tree_cases=[_json_domain(tree(bank,data_bank,scene,{'nodes':nodes},fill))for fill in(0,0xa5)]
    if tree_cases[0]['nodePolicies']!=tree_cases[1]['nodePolicies']:
        raise AssertionError('Original policy outputs differ across heap fills')
    if [r['worldBytesHex']for r in tree_cases[0]['hierarchy']]!=[r['worldBytesHex']for r in tree_cases[1]['hierarchy']]:
        raise AssertionError('Original world matrix bytes differ across heap fills')
    models=[]
    for row in tree_cases[0]['hierarchy']:
        node=row['node']
        if node['className']in('Mesh','Billboard'):
            models.append({'owner':{'meshHeaderOffset':node['headerOffset'],
                'className':node['className'],'name':node['name'],'structuralPath':node['structuralPath']},
                'world':row['world']})
    if len(models)!=376:raise AssertionError('Original model-world handoff coverage mismatch')
    from ._scene_cameras import observe as camera
    camera_cases=[_json_domain(camera(bank,data_bank,scene,{'nodes':nodes},strings,models,fill))for fill in(0,0xa5)]
    for first,second in zip(camera_cases[0]['cameras'],camera_cases[1]['cameras']):
        for field in('world','viewMatrix','projectionMatrix','combinedMatrix'):
            if struct.pack('<16f',*first[field])!=struct.pack('<16f',*second[field]):
                raise AssertionError('Original Camera matrix bytes differ across heap fills')
        if first['modelProducts']!=second['modelProducts']:
            raise AssertionError('Original Camera/model product observations differ across fills')
    policies=tree_cases[0]['nodePolicies']
    counts={'sourceNodesPerFill':492,'sourceGroups':116,'sourceMeshes':362,'sourceBillboards':14,
        'originalNodeConstructions':984,'originalAddChildAttachments':982,
        'originalPropertySuffixExecutions':984,'originalInheritedGateQueries':984,
        'originalInheritedFactorQueries':984,
        'actualLocalRenderBinSkips':sum(p['localRenderBinSkipExecuted']for c in tree_cases for p in c['nodePolicies']),
        'originalCameraConstructions':sum(len(c['cameras'])for c in camera_cases),
        'originalModelCameraProducts':sum(len(cam['modelProducts'])for c in camera_cases for cam in c['cameras'])}
    if counts['actualLocalRenderBinSkips']!=346 or counts['originalCameraConstructions']!=10 or counts['originalModelCameraProducts']!=3760:
        raise AssertionError('Supported original-code execution coverage mismatch')
    summary={'localRenderBinExclusionsPerFill':sum(p['localRenderBinSkipExecuted']for p in policies),
        'actualInheritedGateFalsePerFill':sum(not p['originalEffectiveB8']for p in policies),
        'nativeGateAndFactorOutputsExactAcrossFills':True,'nativeWorldBytesExactAcrossFills':True,
        'nativeCameraAndMvpOutputsExactAcrossFills':True,
        'treeSourceTracesEqualAcrossFills':tree_cases[0]['originalTraceSha256']==tree_cases[1]['originalTraceSha256'],
        'cameraSourceTracesEqualAcrossFills':camera_cases[0]['originalTraceSha256']==camera_cases[1]['originalTraceSha256']}
    files=['scene.py','_scene_profile.py','_scene_tree.py','_scene_cameras.py','_widget_bindings.py']
    return {'schema':'kombikraft-f97-original-tree-camera-v1','profile':SCENE_PROFILE['id'],'passed':True,
        'inputSha256':{role:sha(value)for role,value in [('bank',bank),('scene',scene),('nor',nor),('dataBank',data_bank)]},
        'implementationSha256':{name:sha((Path(__file__).parent/name).read_bytes())for name in files},
        'sourceContract':SCENE_PROFILE,'counts':counts,'summary':summary,
        'cases':{'nodeTreeDefaults':tree_cases,'effectiveCameras':camera_cases},
        'limits':{'boundedHeapAllocationOnlyFunctionAdapters':True,
            'freshStaticStorageAndArchitecturalCallerStateExplicit':True,
            'originalPropertySuffixInteriorCallerFrameExplicit':True,
            'wholeGroupReaderOrAsyncProviderExecuted':False,
            'originalInheritedGateAndFactorApisExecuted':True,
            'actualLocalRenderBinShortCircuitExecuted':True,
            'originalEnabledCollectorOrOuterTraversalExecuted':False,
            'nonzeroFactorAppliedToShaders':False,'normalOperatingOrCodingStateProved':False,
            'cameraWorldInputsAreExplicitOriginalTreeOutputHandoffs':True,
            'coResidentFullSceneExecution':False,'actualCameraSelectionProved':False,
            'wholeCrtKernelBootOrGpuExecuted':False,'vehicleTransportPresent':False,
            'vehicleCompatibilityVerified':False,'installationAllowed':False}}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',action='store_true',help='Print exact input identities/coordinates without firmware or Unicorn')
    for name in('bank','scene','nor','data-bank','output'):parser.add_argument('--'+name,type=Path)
    args=parser.parse_args(argv)
    if args.profile:print(json.dumps(SCENE_PROFILE,indent=2));return 0
    if not all(getattr(args,key)for key in('bank','scene','nor','data_bank','output')):
        parser.error('Supply --bank, --scene, --nor, --data-bank and a NEW --output')
    if args.output.exists():parser.error('Output exists; choose a new receipt path')
    try:
        bank,scene,nor=[read_input(getattr(args,role),role)for role in('bank','scene','nor')]
        data=read_data_bank(args.data_bank)
        result=run(bank,scene,nor,data)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    except(OSError,ValueError,AssertionError,ImportError,RuntimeError)as error:
        parser.exit(1,f'Original scene research failed: {error}\n')
    print(json.dumps({key:result[key]for key in('profile','passed','counts','summary','limits')},indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
