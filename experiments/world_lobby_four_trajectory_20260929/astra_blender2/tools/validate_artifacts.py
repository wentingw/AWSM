"""Validate frozen-candidate GLB loading and semantic component mappings."""
import argparse, hashlib, json, struct
from pathlib import Path
import numpy as np
import trimesh

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--method-dir', required=True)
    a = p.parse_args()
    root = Path(a.method_dir)
    scene = root / 'scene.glb'
    content = scene.read_bytes()
    assert content[:4] == b'glTF' and struct.unpack('<I', content[8:12])[0] == len(content)
    length, kind = struct.unpack('<II', content[12:20])
    assert kind == 0x4E4F534A
    gltf = json.loads(content[20:20 + length])
    node_names = {n['name'] for n in gltf['nodes'] if 'mesh' in n}
    records = json.loads((root / 'objects.json').read_text())['objects']
    ids = [r['id'] for r in records]
    assert len(ids) == len(set(ids)), 'Duplicate semantic IDs'
    components = [name for r in records for name in r.get('component_names',r.get('components',[]))]
    assert len(components) == len(set(components)), 'Multiple ownership of mesh components'
    inspection = json.loads((root / 'checks/artifact_inspection.json').read_text())
    assert inspection['model_sha256'] == sha(root / 'scene.blend')
    mesh_names = {n['name'] for n in inspection['meshes']}
    assert set(components) == mesh_names, {'missing': sorted(set(components) - mesh_names), 'unowned': sorted(mesh_names - set(components))}
    assert set(components) <= node_names, {'glb_missing': sorted(set(components) - node_names)}
    loaded = trimesh.load(scene, force='scene', process=False)
    assert len(loaded.geometry) and np.isfinite(loaded.bounds).all()
    for record in records:
        assert record['category'] and record.get('component_names',record.get('components'))
        dimensions = np.array(record.get('dimensions', record.get('dimensions_m')))
        assert dimensions.shape == (3,) and np.isfinite(dimensions).all() and (dimensions >= 0).all(), record['id']
    report = {'status': 'PASS', 'scene_sha256': sha(scene), 'model_sha256': sha(root / 'scene.blend'),
              'geometry_count': len(loaded.geometry), 'bounds': loaded.bounds.tolist(),
              'semantic_objects': len(ids), 'semantic_components': len(components),
              'semantic_component_mapping': 'PASS', 'GLB_mesh_nodes': len(node_names)}
    (root / 'checks/glb_load.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
