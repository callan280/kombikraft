"""Structural original widget-to-scene joins, without fabricated controllers."""
from pathlib import Path
import hashlib,json,struct

sha=lambda b:hashlib.sha256(b).hexdigest()


def extract(scene,strings,classes):
    def word(at):
        assert 0<=at<=len(scene)-4
        return struct.unpack_from('<I',scene,at)[0]
    nodes=[];widgets=[]
    for at in range(0,len(scene)-28,4):
        size,kind,name=struct.unpack_from('<3I',scene,at)
        if kind not in (0x947,0x94a,0x944,0xa01) or not 12<=size<=len(scene)-at or str(name) not in strings:continue
        record={'headerOffset':at,'endOffset':at+size,'recordBytes':size,
                'classId':kind,'className':classes[kind],'name':strings[str(name)]}
        if kind==0xa01:
            assert size>=28 and str(word(at+12)) in strings
            record['secondaryName']=strings[str(word(at+12))]
            count=word(at+24);assert count<=100 and 28+8*count<=size
            record['bindings']=[]
            for i in range(count):
                key=word(at+28+8*i);encoded=word(at+32+8*i)
                length_at=encoded-12;pointer=length_at+2
                assert str(key) in strings and at+28+8*count<=length_at<pointer<at+size
                end=scene.index(0,pointer,at+size)
                path=scene[pointer:end].decode('utf8')
                assert struct.unpack_from('<H',scene,pointer-2)[0]==end-pointer+1
                record['bindings'].append({'property':strings[str(key)],'serializedOrdinal':i,
                    'encodedValueReference':encoded,'sourceStringRecordOffset':length_at,
                    'sourceValueOffset':pointer,'sourceValue':path})
            widgets.append(record)
        else:nodes.append(record)
    by_path={}
    for node in nodes:
        parents=sorted([r for r in nodes if r['headerOffset']<node['headerOffset'] and node['endOffset']<=r['endOffset']],key=lambda r:r['headerOffset'])
        assert all(p['className']=='Group' for p in parents)
        path='/'.join(r['className']+':'+r['name'] for r in parents+[node])
        assert path not in by_path
        node['structuralPath']=path;node['parentHeaderOffset']=parents[-1]['headerOffset'] if parents else None
        by_path[path]=node
    widget_names={w['name']:w for w in widgets};assert len(widget_names)==len(widgets)
    count={'sceneNodes':0,'sceneRoot':0,'literalStringProperties':0}
    for widget in widgets:
        for binding in widget['bindings']:
            path=binding['sourceValue']
            if path=='/Scene:ki_3d_high':
                binding['joinKind']='scene-root-name';count['sceneRoot']+=1
            elif path.startswith('/Scene:ki_3d_high/'):
                target=by_path[path[len('/Scene:ki_3d_high/'):]]
                binding.update(joinKind='exact-structural-node-path',targetHeaderOffset=target['headerOffset'],targetClass=target['className'],targetName=target['name'])
                count['sceneNodes']+=1
            else:
                assert binding['property']=='TubeCalibrationScope' and path in ('1','2','3','4')
                binding.update(joinKind='literal-string-property',enumMeaningVerified=False)
                count['literalStringProperties']+=1
    return nodes,widgets,count
