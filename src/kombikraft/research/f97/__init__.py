"""Pinned older-F97 material-reader experiments using user-supplied firmware."""
from pathlib import Path
import hashlib
import struct

PROFILE = {
    "id": "f97-4ceb-045.009.002-materials",
    "bank": "a94c4a848491e6582ac6dcb40f54283fc31bacca51d07cb93ff5792e64a00984",
    "scene": "2e09dc8471fb148d6c8486b1acc3b78a0d463d487ded2980a02f374ac4dc2151",
    "nor": "31e4151f9f10bc35ecaabaced532dc0542d782b82558dda0dd0540245e3571a8",
}
PROGRAM = "Global_Import#Global#fx_mdm_ring_msportShaderProgram"


def read_input(path, role):
    """Admit the exact source profile before importing or executing Unicorn."""
    path = Path(path)
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError(f"{role}: input exceeds the 64 MiB profile limit")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != PROFILE[role]:
        raise ValueError(f"{role}: unsupported source hash for {PROFILE['id']}")
    return data


def scene_bindings(bank, scene, nor):
    """Recover the records needed by the probes without a private art catalogue.

    Class names come from the original bank; instance/program names come from
    the original NOR string pool. Encoded scene references include a 12-byte
    omitted resource prefix. The returned record headers match the complete
    original UniformSetter reader's reference origin.
    """
    def word(data, at):
        if not 0 <= at <= len(data)-4:
            raise ValueError("Source word outside its admitted buffer")
        return struct.unpack_from('<I', data, at)[0]

    def cstring(data, at):
        if not 0 <= at < len(data):
            raise ValueError("Source string outside its admitted buffer")
        end = data.find(b'\0', at, min(len(data), at+1024))
        if end < 0:
            raise ValueError("Unterminated source name")
        return data[at:end].decode('utf-8')

    pool = word(nor, 0x58)
    name = lambda ref: cstring(nor, pool+ref+2)
    classes = {}
    for at in range(0x9bd244, 0x9bd3d4, 8):
        classes[word(bank, at+4)] = cstring(bank, word(bank, at)-0x10000)
    for kind, expected in ((0xa41,'Appearance'),(0xa43,'RenderMode'),
                           (0xa44,'UniformSetter'),(0xa46,'Texture')):
        if classes.get(kind) != expected:
            raise ValueError("Original class/name table mismatch")

    def record(payload, kind):
        header = payload-12
        size = word(scene, header)
        if word(scene, header+4) != kind or size <= 0 or payload+size > len(scene):
            raise ValueError("Invalid typed source record")
        return {'headerOffset':header,'payloadOffset':payload,'endOffset':payload+size,
                'payloadBytes':size,'classId':kind,'className':classes[kind],
                'name':name(word(scene,header+8))}

    rows = []
    for header in range(0,len(scene)-40,4):
        if word(scene,header+4) != 0xa41:
            continue
        if name(word(scene,header+12)) != PROGRAM:
            continue
        appearance = record(header+12,0xa41)
        payload,end = appearance['payloadOffset'],appearance['endOffset']
        setter = record(word(scene,payload+24),0xa44)
        list_pointer = word(scene,payload+28)
        count = word(scene,list_pointer-8)
        if count not in (2,3):
            raise ValueError("Unsupported M-ring texture list")
        textures = []
        for ordinal in range(count):
            if word(scene,list_pointer-4+8*ordinal) != 1:
                raise ValueError("Missing texture-list presence flag")
            texture = record(word(scene,list_pointer+8*ordinal),0xa46)
            lo,hi = texture['payloadOffset'],texture['endOffset']
            at = scene.find(b'/Bitmap:',lo,hi)
            stop = scene.find(b'\0',at,hi) if at >= 0 else -1
            if at < 2 or stop < 0:
                raise ValueError("Missing source bitmap identifier")
            if struct.unpack_from('<H',scene,at-2)[0] != stop-at+1:
                raise ValueError("Source bitmap string length mismatch")
            if not payload <= texture['headerOffset'] < hi <= end:
                raise ValueError("Texture outside its appearance")
            textures.append({'record':texture,'serializedOrdinal':ordinal,
                'bitmapPathOffset':at,'bitmapResourceName':scene[at+8:stop].decode()})
        rows.append({'appearance':appearance,'parameterSetter':setter,'textures':textures})
    if len(rows) != 11 or sum(len(r['textures']) for r in rows) != 24:
        raise ValueError("Original M-ring scene coverage mismatch")
    return pool,rows


def run(bank, scene, nor):
    """Run original constructors/readers with explicitly scoped host inputs."""
    # Validate byte inputs too: API callers receive the same admission as CLI.
    for role,data in (('bank',bank),('scene',scene),('nor',nor)):
        if hashlib.sha256(data).hexdigest() != PROFILE[role]:
            raise ValueError(f"{role}: unsupported source hash")
    pool,rows = scene_bindings(bank,scene,nor)
    from ._uniform_loader import observe as uniforms
    from ._asset_identifier import observe as identifiers
    from ._texture_cache import observe as textures
    uniform_cases = [uniforms(bank,scene,nor,pool,row,fill,value)
        for row in rows for fill in (0,0xa5) for value in (1,0,0.375)]
    identifier_cases = [identifiers(bank,scene,t,fill)
        for row in rows for t in row['textures'] for fill in (0,0xa5)]
    texture_cases = [textures(bank,scene,nor,pool,t,fill,flag)
        for row in rows for t in row['textures'] for fill in (0,0xa5) for flag in (0,1)]
    return {'schema':'kombikraft-f97-material-checks-v1','profile':PROFILE['id'],
        'passed':True,'inputSha256':{role:hashlib.sha256(data).hexdigest()
            for role,data in (('bank',bank),('scene',scene),('nor',nor))},
        'cases':{'uniforms':uniform_cases,'identifiers':identifier_cases,'textureCacheBoundary':texture_cases},
        'counts':{'uniforms':len(uniform_cases),'identifiers':len(identifier_cases),'textureCacheBoundary':len(texture_cases)},
        'limits':{'hostAllocationAndFreeAdapters':True,'providerVtableCallerFixture':True,
            'referenceOriginAdjustment':-12,'wholeSceneLoaded':False,'cacheFactoryExecuted':False,
            'graphicsExecuted':False,'vehicleCompatibilityVerified':False,'installationAllowed':False}}
