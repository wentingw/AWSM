"""Post-execution M4 G1 visibility evaluator.

Builds one evaluated Blender BVH from the frozen M4 scene and assigns every
triangle to its semantic object through the declared blender_root parent
chain.  It uses only each episode's selected target_id and final robot pose;
the evaluator-only expected-target file is intentionally never opened.
"""
import bpy, json, math, hashlib, csv
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SCENE=ROOT/'experiments/world_lobby/M4/astra_model/scene.blend'
META=ROOT/'experiments/world_lobby/M4/astra_model/objects.json'
BATCH=ROOT/'experiments/tasks/g1_M4/replay_20260924'
OUT=ROOT/'results/evaluation/tasks/g1_M4_20260924'
W,H=640,480; FX=FY=381.4; CX,CY=320.0,240.0; STEP=4

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_json(path): return json.loads(Path(path).read_text())
def parent_names(o):
    out=[]
    while o:
        out.append(o.name); o=o.parent
    return out

def semantic_for_object(o, roots):
    names=parent_names(o)
    for n in names:
        if n in roots: return n
    for n in names:
        for r in roots:
            if n.startswith(r+'.') or n.startswith(r+'_'): return r
    for r in roots:
        if o.name.startswith(r+'.') or o.name.startswith(r+'_'): return r
    return None

def build_bvh(roots):
    # Aggregate evaluated world-space triangles, retaining a semantic label per face.
    deps=bpy.context.evaluated_depsgraph_get(); verts=[]; polys=[]; labels=[]; mapped=0; skipped=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or not o.visible_get(): continue
        sid=semantic_for_object(o,roots)
        if sid is None: skipped+=1
        eo=o.evaluated_get(deps); me=eo.to_mesh(); me.calc_loop_triangles()
        base=len(verts); mat=np.array(eo.matrix_world, dtype=float)
        for v in me.vertices:
            p=mat@np.array([v.co.x,v.co.y,v.co.z,1.0]); verts.append(tuple(p[:3]))
        for tri in me.loop_triangles:
            vs=tri.vertices
            polys.append((base+vs[0],base+vs[1],base+vs[2])); labels.append(sid)
        mapped+=1; eo.to_mesh_clear()
    if not polys: raise RuntimeError('No semantic mesh triangles mapped from M4 scene')
    tree=BVHTree.FromPolygons(verts,polys,all_triangles=True,epsilon=1e-7)
    return tree,labels,{'mesh_objects_mapped':mapped,'mesh_objects_skipped':skipped,'triangles':len(polys),'semantic_roots':len(roots)}

def camera_basis(summary, trajectory):
    rows=list(csv.reader(trajectory.open()))
    if len(rows)<2: raise ValueError('trajectory has no samples')
    vals=np.asarray(rows[-1][1:8],float); pos=vals[:3].copy(); qraw=vals[3:7]; assert abs(np.linalg.norm(qraw)-1.0)<2e-3, f'non-unit terminal quaternion {qraw}'; q=Quaternion((qraw[0],qraw[1],qraw[2],qraw[3])); R=np.asarray(q.to_matrix(),float)
    # Actual camera: base offset [0.08,0,0.35], body +X forward, pitched down 20 deg.
    off=R@np.array([.08,0,.35]); origin=pos+off
    a=math.radians(20); fbody=np.array([math.cos(a),0,-math.sin(a)]); forward=R@fbody; upref=R@np.array([0,0,1.])
    right=np.cross(forward,upref); right/=np.linalg.norm(right); up=np.cross(right,forward); up/=np.linalg.norm(up)
    C=np.column_stack([right,up,-forward]); assert np.allclose(C.T@C,np.eye(3),atol=2e-5); assert abs(np.linalg.norm(off)-math.sqrt(.08**2+.35**2))<1e-5; return origin,C,float(rows[-1][0])

def raycast(tree,labels,origin,C,u,v):
    dc=np.array([(u-CX)/FX,-(v-CY)/FY,-1.],float); dc/=np.linalg.norm(dc); dw=C@dc
    hit,normal,index,dist=tree.ray_cast(Vector(origin),Vector(dw),1000.)
    return (labels[index] if index is not None else None), hit, dw, dist

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SCENE)); meta=load_json(META); objects=meta['objects']; roots={o['blender_root'] for o in objects if o.get('blender_root')}; byid={o['object_id']:o for o in objects}
    tree,labels,build=build_bvh(roots); (OUT/'visibility_masks').mkdir(parents=True,exist_ok=True); (OUT/'endpoint_rgb').mkdir(parents=True,exist_ok=True)
    # Cycles output is the actual camera view, not a target-pose render.
    s=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=16; s.cycles.use_denoising=True; s.render.threads_mode='FIXED'; s.render.threads=4; s.render.resolution_x=W; s.render.resolution_y=H; s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGB'
    camdat=bpy.data.cameras.new('m4_g1_evaluated_camera'); cam=bpy.data.objects.new('m4_g1_evaluated_camera',camdat); s.collection.objects.link(cam); s.camera=cam; camdat.sensor_width=36; camdat.sensor_fit='HORIZONTAL'; camdat.lens=FX/W*36; camdat.clip_start=.02; camdat.clip_end=1000
    rows=[]; grid=[(u+.5,v+.5) for v in range(0,H,STEP) for u in range(0,W,STEP)]; total=len(grid)
    for ep in sorted(BATCH.glob('episode_*')):
        summ=ep/'summary.json'; traj=ep/'trajectory.csv'; rec={'episode_id':int(ep.name.split('_')[-1]),'visible':False,'sample_count':total}
        if not summ.exists() or not traj.exists(): rec.update(status='not_executed',reason='missing summary or trajectory'); rows.append(rec); continue
        d=load_json(summ); rec.update(status=d.get('status'),target_id=d.get('target_id'),camera_convention='robot base +X forward; optical axis pitched down 20deg; offset [0.08,0,0.35]m')
        if 'final_position' not in d: rec.update(reason='no final robot pose'); rows.append(rec); continue
        try: origin,C,pose_time=camera_basis(d,traj)
        except Exception as e: rec.update(reason=f'pose_parse_error:{e}'); rows.append(rec); continue
        target=d.get('target_id'); mask=np.zeros((H//STEP,W//STEP),np.uint8); hits={}; points=[]
        for j,(u,v) in enumerate(grid):
            sid,hit,dw,dist=raycast(tree,labels,origin,C,u,v)
            if sid: hits[sid]=hits.get(sid,0)+1
            if sid==target: mask[int(v//STEP),int(u//STEP)]=255; points.append((u,v))
        count=int(mask.sum()/255); frac=count/total; rec.update(trajectory_pose_time_s=pose_time,summary_stop_time_s=d.get('simulated_seconds'),pose_time_delta_s=(float(d['simulated_seconds'])-pose_time if d.get('simulated_seconds') is not None else None),target_pixel_count=count,target_pixel_fraction=frac,visible=bool(frac>=.001),threshold=0.001,first_hit_counts=hits,final_camera_position_m=origin.tolist(),target_bbox_sampled=None)
        if points: rec['target_bbox_sampled']=[float(min(p[0] for p in points)),float(min(p[1] for p in points)),float(max(p[0] for p in points)),float(max(p[1] for p in points))]
        Image=None
        # Save a compact ray mask; RGB is rendered below by Blender from this same camera.
        import bpy as _bpy; _bpy.data.images.new(f'visibility_{rec["episode_id"]:02d}',width=W//STEP,height=H//STEP,alpha=False); im=_bpy.data.images[-1]; rgba=np.ones((H//STEP,W//STEP,4),np.float32); rgba[:,:,:3]=np.flipud(mask/255.)[:,:,None]; im.pixels.foreach_set(rgba.reshape(-1).tolist()); im.filepath_raw=str(OUT/'visibility_masks'/f'episode_{rec["episode_id"]:02d}_mask.png'); im.file_format='PNG'; im.save(); _bpy.data.images.remove(im)
        M=np.eye(4); M[:3,:3]=C; M[:3,3]=origin; cam.matrix_world=Matrix(M.tolist()); s.render.filepath=str(OUT/'endpoint_rgb'/f'episode_{rec["episode_id"]:02d}.png'); bpy.ops.render.render(write_still=True)
        rows.append(rec); print('M4_G1_VISIBILITY',rec['episode_id'],rec['status'],target,frac,rec['visible'],flush=True)
    report={'scene_method':'M4','scene_blend_sha256':sha(SCENE),'objects_sha256':sha(META),'evaluator':'Blender evaluated scene mesh + BVH triangle first-hit ray casting','target_source':'selected target_id from each post-execution summary; expected_targets.json not read','camera':{'resolution_wh':[W,H],'fx_fy':[FX,FY],'cx_cy':[CX,CY],'offset_body_m':[.08,0,.35],'body_forward_axis':'+X','pitch_down_deg':20,'sampling':'pixel centers every 4 pixels in both axes','samples_per_frame':total},'bvh':build,'threshold_fraction':.001,'episodes':rows,'counts':{'episodes':len(rows),'executed':sum('target_pixel_fraction' in r for r in rows),'visible':sum(r.get('visible',False) for r in rows),'not_executed':sum(r.get('status')=='not_executed' for r in rows)}}
    report.update(status='complete',evaluator_script_sha256=sha(Path(__file__)))
    (OUT/'visibility.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report['counts'],indent=2))
if __name__=='__main__': main()
