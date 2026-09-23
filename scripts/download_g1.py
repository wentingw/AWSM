from pathlib import Path
import json,hashlib,urllib.request,concurrent.futures,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
tree=json.loads((ROOT/'references/unitree_tree.json').read_text())
revision=tree['sha']
xml=ET.parse(ROOT/'references/g1_12dof.xml')
meshes={n.get('file') for n in xml.findall('.//mesh')}
wanted=['LICENSE','resources/robots/g1_description/README.md','resources/robots/g1_description/scene.xml','resources/robots/g1_description/g1_12dof.xml','resources/robots/g1_description/g1_12dof.urdf','deploy/pre_train/g1/motion.pt','deploy/deploy_mujoco/configs/g1.yaml','deploy/deploy_mujoco/deploy_mujoco.py']
wanted+=['resources/robots/g1_description/meshes/'+m for m in sorted(meshes)]
out=ROOT/'runtime/unitree_rl_gym'
def fetch(rel):
    p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
    url=f'https://raw.githubusercontent.com/unitreerobotics/unitree_rl_gym/{revision}/{rel}'
    if not p.exists():
        with urllib.request.urlopen(url,timeout=60) as response: data=response.read()
        p.write_bytes(data)
    data=p.read_bytes()
    if data.startswith(b'version https://git-lfs'):raise RuntimeError('LFS pointer: '+rel)
    return dict(path=rel,source=url,size=len(data),sha256=hashlib.sha256(data).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    records=list(pool.map(fetch,wanted))
(ROOT/'manifests/g1_assets.json').write_text(json.dumps(dict(repository='unitreerobotics/unitree_rl_gym',revision=revision,files=records,policy='official 12DOF pretrained locomotion; no task training'),indent=2)+'\n')
print(json.dumps(dict(files=len(records),bytes=sum(x['size'] for x in records),status='downloaded')))
