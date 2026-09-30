"""Ten fixed input-camera RGB + optical-Z checks, no ground truth access.

blender -b --threads 2 --python this.py -- --method-dir DIR --packet PACKET
Then python3 visualize_checks.py --method-dir DIR --packet PACKET --version N
"""
import argparse,fcntl,hashlib,json,sys,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from raycast_scene import collect_meshes,cast
from depth_math import sample_depth,metrics
INDICES=[33,61,74,82,91,100,108,118,129,155]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--method-dir',required=True);p.add_argument('--packet',required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=Path(a.method_dir);packet=json.loads(Path(a.packet).read_text())
    (root/'checks').mkdir(exist_ok=True)
    lock=(root/'checks/paired_check.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
    m=json.loads((root/'modelling_manifest.json').read_text());version=int(m['revisions']);assert 1<=version<=5
    digest=sha(root/'scene.blend');out=root/'checks'/f'v{version}';out.mkdir(parents=True,exist_ok=True)
    if (out/'paired_report.json').exists():
        prior=json.loads((out/'paired_report.json').read_text());assert prior['model_sha256']==digest,'Changed model must have new version'
        if prior.get('status')=='COMPLETE':print('Already completed same model/version');return
    saved=root/'versions'/f'v{version}';saved.mkdir(parents=True,exist_ok=True)
    import shutil
    for name in ['scene.blend','scene.glb','layout.json','build_scene.py','objects.json','cameras.json','modelling_manifest.json']:
        if (root/name).exists():
            if (saved/name).exists():
                if name!='modelling_manifest.json':assert sha(saved/name)==sha(root/name),'Version evidence changed'
            else:shutil.copyfile(root/name,saved/name)
    cameras=json.loads((root/'cameras.json').read_text());by={f['sample_index']:f for f in cameras['frames']}
    inputs={f['sample_index']:f for f in packet['frames']}
    X=None if packet['method_id']=='M1' else np.array(m['model_from_input'],float)
    bpy.ops.wm.open_mainfile(filepath=str(root/'scene.blend'))
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.cycles.seed=20260930
    data=bpy.data.cameras.new('paired_check_camera');cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam
    data.type='PERSP';data.sensor_fit='HORIZONTAL';data.sensor_width=36;data.clip_start=.01;data.clip_end=60
    vertices,tris,names=collect_meshes(np.eye(4));bvh=BVHTree.FromPolygons(vertices,tris,all_triangles=True);del vertices,tris
    u,v=np.meshgrid(np.arange(640)+.5,np.arange(480)+.5);uv=np.column_stack([u.ravel(),v.ravel()])
    records=[];start=time.monotonic()
    for index in INDICES:
        f=inputs[index];c=by[index];T=np.array(c['camera_to_world'],float)
        if X is not None:assert np.allclose(T,X@np.array(f['camera_to_world']),atol=2e-5),'Input camera altered'
        K=np.array(f['intrinsics'],float);K[:2]*=.5
        data.lens=K[0,0]*36/640;data.shift_x=(320-K[0,2])/640;data.shift_y=(K[1,2]-240)/640
        cam.matrix_world=Matrix((T@np.diag([1,-1,-1,1])).tolist());bpy.context.view_layer.update()
        for uu,vv in [(80.5,70.5),(320.5,240.5),(550.5,400.5)]:
            pc=np.linalg.inv(K)@np.array([uu,vv,1.])*3;pw=T[:3,:3]@pc+T[:3,3]
            ndc=world_to_camera_view(scene,cam,Matrix.Translation(pw).translation)
            assert abs(ndc.x*640-uu)<.01 and abs((1-ndc.y)*480-vv)<.01,'Blender projection mismatch'
        report_path=out/f'{index:04d}_report.json'
        if report_path.exists():
            r=json.loads(report_path.read_text());assert r['model_sha256']==digest;records.append(r);continue
        ledger_path=root/'checks/paired_ledger.json';ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else []
        completed=[r for r in ledger if r.get('status')=='COMPLETE']
        assert len(completed)<50,'Paired check budget exhausted'
        event=dict(version=version,sample_index=index,model_sha256=digest,status='RUNNING',started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
        ledger.append(event);save(ledger_path,ledger)
        scene.render.filepath=str(out/f'{index:04d}_rgb.png');bpy.ops.render.render(write_still=True)
        z=cast(bvh,T,K,uv,near_z=data.clip_start,far_z=data.clip_end);z[(z<.01)|(z>60)]=np.nan
        arrays=dict(model_z_m=z.reshape(480,640),pixel_uv=uv.reshape(480,640,2),model_hit=np.isfinite(z).reshape(480,640),intrinsics=K,camera_to_world=T)
        stats=None
        if X is not None:
            with np.load(f['geometry']) as n:reference=sample_depth(n['depth_z_m'],n['valid_mask'],n['intrinsics'],uv,K)
            domain=np.isfinite(reference)&(reference>=.1)&(reference<=30)
            arrays.update(input_da3_z_m=reference.reshape(480,640),input_valid_domain=domain.reshape(480,640))
            stats=metrics(z,reference,domain)
        np.savez_compressed(out/f'{index:04d}_depth.npz',**arrays)
        r=dict(sample_index=index,timestamp_ns=f['timestamp_ns'],model_sha256=digest,rgb_sha256=sha(out/f'{index:04d}_rgb.png'),depth_sha256=sha(out/f'{index:04d}_depth.npz'),camera_valid=c.get('valid',True),input_consistency=stats)
        save(report_path,r);records.append(r)
        event.update(status='COMPLETE',completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));save(ledger_path,ledger)
        m['checking_render_count']=len([r for r in ledger if r['status']=='COMPLETE']);save(root/'modelling_manifest.json',m)
        print('PAIRED_COMPLETE',index,flush=True)
    aggregate=None
    if X is not None:
        zs=[];refs=[]
        for i in INDICES:
            n=np.load(out/f'{i:04d}_depth.npz');zs.append(n['model_z_m']);refs.append(n['input_da3_z_m'])
        aggregate=metrics(np.array(zs),np.array(refs))
    save(out/'paired_report.json',dict(status='COMPLETE',version=version,model_sha256=digest,indices=INDICES,frames=records,aggregate_input_consistency=aggregate,depth_reference='none; M1 self-occlusion only' if X is None else 'own predicted DA3 input; not ground truth',resolution=[640,480],pixel_centres=True,engine='CPU Cycles',samples=12,depth_backend='Blender BVH same mesh/camera/pixel centres; first opaque geometric surface; optical Z',clip_range_m=[.01,60],seconds=time.monotonic()-start))
    assert sha(root/'scene.blend')==digest
if __name__=='__main__':main()
