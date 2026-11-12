"""Authored source-coordinate/admission metadata, never firmware code bytes."""
from . import PROFILE
from ._extended_profile import EXTENDED_PROFILE

SCENE_PROFILE={
    'id':'f97-045.009.002-source-tree-camera-v1',
    'bank':PROFILE['bank'],'scene':PROFILE['scene'],'nor':PROFILE['nor'],
    'dataBank':EXTENDED_PROFILE['dataBank'],
    'expectedNodes':{'Group':116,'Mesh':362,'Billboard':14},
    'expectedCameras':5,
    'coordinates':{'codeBankAnalysisBase':0x10000,'initializedDataBankAnalysisBase':0xf00000,
        'relation':'linked analysis address = code bank offset +0x10000; not a physical boot map',
        'hardwareMappingProven':False},
    'entryBankOffsets':{
        'selectedStaticInitializer':0x115f20,'clearCurrentCameraApi':0x10ce3c,
        'groupFactory':0x11e334,'meshFactory':0x114110,
        'billboardFactory':0x4098f8,'billboardSpecificReader':0x4097e0,
        'commonNodeReader':0x3f02a4,'addChild':0x115764,
        'propertySuffixStart':0x3fa794,'propertySuffixStopBefore':0x3fa808,
        'effectiveAncestorGate':0x115078,'inheritedFactor':0x11510c,
        'actualLocalRenderBinConsumer':0x1172d8,
        'cameraFactory':0x1128b8,'perspectiveFactory':0x11f468,
        'orthographicFactory':0x44fb30,'cameraViewGetter':0x112fc8,
        'cameraCombinedGetter':0x112b2c,'nativeMatrixProduct':0x127628},
    'functionAdapters':[
        {'bankOffset':0x128498,'role':'bounded heap allocation; size inR0, pointer result inR0'},
        {'bankOffset':0x184718,'role':'bounded ordinary-new allocation; size inR0, pointer result inR0'}],
    'architecturalCallerFixture':{'armVfpEnabled':True,'stackBytes':0x4000,
        'heapBytes':0x100000,'freshStaticStorageDeclaredPerCase':True,
        'currentCameraClearedByOriginalApi':True,'wholeCrtOrBootloaderExecuted':False},
    'propertySuffixFixture':{'R6':'serialized descriptor','R7':'original native object',
        'stackWritableOffsets':[0x30,0x34],
        'scope':'interior suffix only; earlier child/material factories are neither executed nor faked'},
    'fullGroupSceneProviderOrKernelStartup':False,'normalFactoryState':False,
    'renderingOrOriginalGpuExecuted':False,'vehicleCompatibilityVerified':False,
    'installationAllowed':False,
}
