"""Blender BVH depth, either input-only consistency or supplied evaluation cameras.

Input mode: blender -b --threads 4 --python raycast_scene.py -- --model scene.blend
 --input-packet packet.json --model-manifest modelling_manifest.json --out checks/input_v1
Other mode: --cameras cameras.json --mesh-transform transform.json --out evaluation_path
"""
import argparse,fcntl,hashlib,json,sys,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from depth_math import pixel_grid,sample_depth,metrics

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def collect_meshes(transform):
    vertices=[];tris=[];offset=0;names=[];deps=bpy.context.evaluated_depsgraph_get()
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or obj.hide_render or obj.get('exclude_from_evaluation',False): continue
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        v=np.empty((len(mesh.vertices),3),np.float64);mesh.vertices.foreach_get('co',v.ravel())
        t=np.empty((len(mesh.loop_triangles),3),np.int32);mesh.loop_triangles.foreach_get('vertices',t.ravel())
        W=transform@np.array(ev.matrix_world);v=v@W[:3,:3].T+W[:3,3]
        if len(v) and len(t): vertices.append(v);tris.append(t+offset);offset+=len(v);names.append(obj.name)
        ev.to_mesh_clear()
    if not vertices: raise ValueError('No visible evaluation meshes')
    return np.vstack(vertices),np.vstack(tris),names

def cast(bvh,T,K,uv,near_z=0.0,far_z=None):
    q=np.column_stack(((uv[:,0]-K[0,2])/K[0,0],(uv[:,1]-K[1,2])/K[1,1],np.ones(len(uv))))
    norms=np.linalg.norm(q,axis=1); dirs=(q/norms[:,None])@T[:3,:3].T
    origin=Vector(T[:3,3]); result=np.full(len(q),np.nan,np.float32)
    for i,d in enumerate(dirs):
        start=origin+Vector(d)*float(near_z*norms[i])
        distance=60. if far_z is None else float((far_z-near_z)*norms[i])
        hit=bvh.ray_cast(start,Vector(d),distance)
        if hit[0] is not None: result[i]=hit[3]/norms[i]+near_z
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--input-packet');p.add_argument('--model-manifest');p.add_argument('--cameras');p.add_argument('--mesh-transform');p.add_argument('--out',required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
    model_sha=sha(a.model); start=time.monotonic(); transform=np.eye(4)
    if a.input_packet and (out/'report.json').exists():
        old=json.loads((out/'report.json').read_text())
        assert old['model_sha256']==model_sha,'Completed pass directory belongs to another model'
        if old.get('mode')=='input_consistency' and old.get('frames')==180:
            print('Reusing completed same-model input pass; no new BVH pass');return
    if a.input_packet:
        data=json.loads(Path(a.input_packet).read_text());manifest=json.loads(Path(a.model_manifest).read_text())
        transform=np.linalg.inv(np.array(manifest['model_from_input'],float)); mode='input_consistency'
        if data['geometry_frames']!=180: raise ValueError('Input checker requires 180 geometry frames')
        # Budget only committed full passes; interrupted runs remain identifiable logs.
        previous=list(out.parent.glob('input*/report.json'))
        distinct=[f for f in previous if f.parent!=out and json.loads(f.read_text()).get('mode')=='input_consistency']
        if len(distinct)>=3: raise ValueError('Three input consistency passes already exist')
    else:
        data=json.loads(Path(a.cameras).read_text()); mode='supplied_cameras'
        if a.mesh_transform: transform=np.array(json.loads(Path(a.mesh_transform).read_text())['transform'],float)
    bpy.ops.wm.open_mainfile(filepath=str(Path(a.model).resolve()))
    v,t,names=collect_meshes(transform);bvh=BVHTree.FromPolygons(v,t,all_triangles=True)
    uv=pixel_grid();pred=[];truth=[];rows=[];timestamps=[]
    for i,f in enumerate(data['frames']):
        K=np.array(f.get('intrinsics',data.get('intrinsics')),float);T=np.array(f['camera_to_world'],float)
        z=cast(bvh,T,K,uv);pred.append(z);timestamps.append(f['timestamp_ns'])
        if a.input_packet:
            with np.load(f['geometry']) as n: reference=sample_depth(n['depth_z_m'],n['valid_mask'],n['intrinsics'],uv,K)
            truth.append(reference);rows.append({'sample_index':f['sample_index'],'timestamp_ns':f['timestamp_ns'],**metrics(z,reference)})
        if i%30==0: print(json.dumps({'frame':i,'total':len(data['frames']),'elapsed':time.monotonic()-start}),flush=True)
    arrays={'prediction_z_m':np.array(pred),'pixel_uv':uv,'timestamps_ns':np.array(timestamps,dtype=np.int64)}
    report={'mode':mode,'model_sha256':model_sha,'frames':len(pred),'rays_per_frame':len(uv),'mesh_objects':len(names),'triangles':len(t),'seconds':time.monotonic()-start,'transform_applied_to_mesh':transform.tolist(),'depth_axis':'camera optical Z metres'}
    if truth:
        arrays['reference_z_m']=np.array(truth,np.float32); report.update(aggregate=metrics(np.array(pred),np.array(truth)),per_frame=rows,scope='model versus own predicted input depth; no ground truth')
    np.savez_compressed(out/'depth.npz',**arrays)
    assert sha(a.model)==model_sha,'Model changed during check'
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='per_frame'},indent=2))
if __name__=='__main__':main()
