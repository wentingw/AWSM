"""Validate final-review provenance, model interfaces and freeze each method."""
import argparse,hashlib,json,struct,time
from pathlib import Path
import numpy as np
RUN=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--method',choices=['M1','M2','M3','M4'],required=True);a=p.parse_args();d=RUN/'models'/a.method
    required=['scene.blend','scene.glb','build_scene.py','objects.json','colliders.json','cameras.json','input_access_log.json','iteration_log.json','modelling_manifest.json','analysis/object_inventory.json','analysis/measurements.json','analysis/camera_checks.json','independent_review/final_review.json','checks/artifact_inspection.json']
    for f in required:assert (d/f).is_file(),f
    m=json.loads((d/'modelling_manifest.json').read_text());review=json.loads((d/'independent_review/final_review.json').read_text())
    assert review['model_sha256']==sha(d/'scene.blend'),'Final review belongs to different scene'
    assert review['reviewer_model']=='gpt-6-astra' and review['independent_fresh_context'] is True
    assert review['status'] in ['PASS','PASS_WITH_LIMITATIONS','LIMITED'],'Final review incomplete'
    assert not review.get('technical_protocol_blockers',review.get('blockers',[])),'Unresolved technical or input protocol blockers'
    assert review.get('review_complete') is True,'Final review reports incomplete'
    inspection=json.loads((d/'checks/artifact_inspection.json').read_text());assert inspection['status']=='PASS' and inspection['model_sha256']==sha(d/'scene.blend')
    glbcheck=json.loads((d/'checks/glb_load.json').read_text());assert glbcheck['status']=='PASS' and glbcheck['scene_sha256']==sha(d/'scene.glb')
    assert glbcheck.get('semantic_component_mapping')=='PASS','Semantic GLB component mapping has not been validated'
    rebuild=json.loads((d/'checks/rebuild_verification.json').read_text())
    assert rebuild['status']=='PASS' and rebuild['source_model_sha256']==sha(d/'scene.blend'),'Rebuild verification must belong to final candidate'
    assert rebuild['source_files_unchanged'] is True
    assert m['method_id']==a.method and m['model_id']=='gpt-6-astra'
    assert m['revisions']<=5 and m['checking_render_count']<=50
    fixed=[33,61,74,82,91,100,108,118,129,155]
    pairs=[]
    for version in range(1,m['revisions']+1):
        check=json.loads((d/f'checks/v{version}/paired_report.json').read_text())
        assert check['status']=='COMPLETE' and check['indices']==fixed and len(check['frames'])==10
        for frame in check['frames']:
            idx=frame['sample_index'];assert sha(d/f'checks/v{version}/{idx:04d}_rgb.png')==frame['rgb_sha256']
            assert sha(d/f'checks/v{version}/{idx:04d}_depth.npz')==frame['depth_sha256']
            assert (d/f'checks/v{version}/{idx:04d}_comparison.jpg').is_file()
        pairs.append(check)
    assert pairs[-1]['model_sha256']==sha(d/'scene.blend'),'Final paired check belongs to another model'
    assert m['checking_render_count']==10*m['revisions']
    assert (d/'independent_review/initial_review.json').exists()
    packet=json.loads((RUN/f'inputs/{a.method}/packet.json').read_text())
    assert m['input_packet_sha256']==sha(RUN/f'inputs/{a.method}/packet.json')
    cams=json.loads((d/'cameras.json').read_text()); assert cams['pose_convention']=='OpenCV RDF camera-to-world' and cams['coordinate_frame']=='model'
    if a.method!='M1':
        X=np.array(m['model_from_input']);assert np.allclose(X[:3,:3].T@X[:3,:3],np.eye(3),atol=1e-5) and abs(np.linalg.det(X[:3,:3])-1)<1e-5
        c={f['sample_index']:f for f in cams['frames']};assert len(c)==180
        for f in packet['frames']:
            camera=c[f['sample_index']];assert camera.get('valid',True)
            assert camera['timestamp_ns']==f['timestamp_ns']
            assert np.allclose(np.array(camera['camera_to_world']),X@np.array(f['camera_to_world']),atol=2e-5)
        checks=list(d.glob('checks/input*/report.json'));assert len(checks)==3,'Exactly three full input passes required'
        assert all(json.loads(f.read_text())['frames']==180 for f in checks)
        assert m.get('input_bvh_pass_count',len(checks))<=3
        assert any(json.loads(f.read_text())['model_sha256']==sha(d/'scene.blend') for f in checks),'No final-model input consistency pass'
    content=(d/'scene.glb').read_bytes();assert content[:4]==b'glTF' and struct.unpack('<I',content[8:12])[0]==len(content)
    m['status']='frozen_for_independent_GT_evaluation';m['frozen_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());m['final_review_status']=review['status'];m.setdefault('quality_status','limited' if review['status']!='PASS' else 'pass')
    (d/'modelling_manifest.json').write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
    files={str(f.relative_to(d)):sha(f) for f in sorted(d.rglob('*')) if f.is_file() and f.name not in ['freeze_manifest.json','SHA256SUMS'] and f.suffix not in ['.pyc','.blend1'] and '__pycache__' not in f.parts}
    (d/'freeze_manifest.json').write_text(json.dumps({'method_id':a.method,'status':m['status'],'frozen_utc':m['frozen_utc'],'files':files},indent=2)+'\n')
    (d/'SHA256SUMS').write_text(''.join(f'{h}  {name}\n' for name,h in files.items()))
    print(json.dumps({'method':a.method,'files':len(files),'scene_sha256':files['scene.blend'],'final_review':review['status']},indent=2))
if __name__=='__main__':main()
