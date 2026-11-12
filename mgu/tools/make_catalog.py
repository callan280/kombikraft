#!/usr/bin/env python3
"""Make the lightweight MGU Store catalogue from the reviewed SDK-free package."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[2]
MGU=ROOT/'mgu'


def main():
    spec=json.loads((MGU/'apps/kombikraft/app.json').read_text())
    name=f"{spec['id']}@{spec['version']}.tgz"
    artifact=MGU/'dist'/name
    data=artifact.read_bytes()
    catalog={'schema':2,'components':[{
        'id':spec['id'],'kind':'app','title':'KombiKraft Lab · Offline prototype',
        'description':'Experimental native preferences app. No vehicle-validated release; factory menu injection, HUD rendering and KOMBI skin activation remain unavailable.',
        'version':spec['version'],
        'artifact':{'name':name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                    'url':'https://github.com/callan280/kombikraft/releases/download/catalog/'+name},
        'requires':{'mgu-deploy':'0.2.0'},'uninstallable':True,'mguHmi':['ID7']}]}
    (ROOT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    print(json.dumps(catalog,indent=2))


if __name__=='__main__':main()
