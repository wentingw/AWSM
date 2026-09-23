"""Independent same-scene novel-camera depth audit. Blender CPU, exact BVHs."""
import sys,json,hashlib,time
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_blend_surface_blender import collect
OUT=ROOT/'results/evaluation/novel_depth';OUT.mkdir(parents=True,exist_ok=True)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def metrics(gt,pred):
 domain=np.isfinite(gt)&(gt>=.1)&(gt<=30);valid=domain&np.isfinite(pred)&(pred>=.1)&(pred<=30);n=int(domain.sum());nv=int(valid.sum());e=np.abs(pred[valid]-gt[valid])
 return {'pixels_domain':n,'pixels_valid':nv,'valid_coverage':nv/n,'absrel':float(np.mean(e/gt[valid])),'mae_m':float(np.mean(e)),'rmse_m':float(np.sqrt(np.mean(e**2))),'missing_penalty_mae_m':float((e.sum()+30*(n-nv))/n),'sum_absolute_error_m':float(e.sum()),'sum_squared_error_m2':float(np.sum(e**2))}
def casts(bvh,views,uv):
 optical=np.column_stack([(uv[:,0]-320)/381.4,(uv[:,1]-240)/381.4,np.ones(len(uv))]);norm=np.linalg.norm(optical,axis=1);dirs=optical/norm[:,None];z=np.full((len(views),len(uv)),np.nan)
 for j,q in enumerate(views):
  C=np.asarray(q['camera_rotation_world_from_optical']);origin=Vector(q['camera_position_world_m'])
  for i,d in enumerate(dirs@C.T):
   hit=bvh.ray_cast(origin,Vector(d),50)
   if hit[0] is not None:z[j,i]=hit[3]/norm[i]
 return z

def main():
 t=time.monotonic();manifest=ROOT/'results/ground_truth/independent_holdout_20/manifest.json';views=json.loads(manifest.read_text())['views'];specpath=ROOT/'results/ground_truth/cycles_novel_20/model_specs.json';specs=json.loads(specpath.read_text());rng=np.random.default_rng(23);uv=np.column_stack([rng.integers(0,640,5000),rng.integers(0,480,5000)])
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.wm.usd_import(filepath=specs['__GT__']['path'],import_materials=False,import_cameras=False,import_lights=False);v,tri=collect([o for o in bpy.context.scene.objects if o.type=='MESH']);nt=len(tri);assert nt==9984967,(nt,'wrong GT scene');bv=BVHTree.FromPolygons(v,tri,all_triangles=True);gt=casts(bv,views,uv);del bv,v,tri
 old=np.array([np.load(q['zdepth_path'])[uv[:,1],uv[:,0]] for q in views]);oldcheck=metrics(gt,old);np.savez_compressed(OUT/'gt_samples.npz',pixel_uv=uv,optical_z_m=gt,old_optical_z_diagnostic=old,seed=23)
 report={'status':'complete','scope':'20 deterministic pose perturbations in same simulated scene; no independent capture','gttriangles':nt,'ray_seed':23,'rays_per_view':5000,'camera_resolution_wh':[640,480],'K':[381.4,381.4,320,240],'gt_domain':'finite optical Z in [0.1,30]m; fixed GT-only mask','invalid_prediction':'nonfinite or outside [0.1,30]m','penalty_definition':'(sum valid absolute errors + 30m * missing count) / GT domain count','old_depth_status':'quarantined_invalid_depth_definition','old_depth_validation':oldcheck,'pose_manifest_sha256':sha(manifest),'model_specs':{},'rows':[],'rgb':'unscored; renderer-domain mismatch'}
 for m,s in specs.items():
  if m=='__GT__':continue
  T=np.asarray(s['transform']);expected=json.loads((ROOT/('results/M1/render_manifest.json' if m=='M1' else f'results/{m}/model_registration.json' if m in ['M2','M3','M4'] else f'results/evaluation/pose/current/{dict(B1="M2",B2="B2",B2p="M3")[m]}_registration.json')).read_text());assert np.allclose(T,expected.get('transform',expected.get('T_gt_model')))
  bpy.ops.wm.open_mainfile(filepath=s['path']);v,tri=collect([o for o in bpy.context.scene.objects if o.type=='MESH'],T);ntri=len(tri);b=BVHTree.FromPolygons(v,tri,all_triangles=True);pred=casts(b,views,uv);del b,v,tri;np.savez_compressed(OUT/f'{m}_samples.npz',predicted_z_m=pred,pixel_uv=uv)
  row={'method':m,'model_triangles':ntri,**metrics(gt,pred),'per_frame':[dict(view_id=q['view_id'],**metrics(gt[i],pred[i])) for i,q in enumerate(views)]};report['rows'].append(row);report['model_specs'][m]={'path':s['path'],'sha256':sha(s['path']),'transform':T.tolist(),'alignment':'GT-assisted Sim3' if m=='M1' else 'single native SE3'};print('NOVEL_DEPTH',m,{k:row[k] for k in ['absrel','rmse_m','valid_coverage','missing_penalty_mae_m']},flush=True)
 report['seconds']=time.monotonic()-t;report['article_zh']='20 个补充视角由同一仿真轨迹的确定性小扰动产生。每视角固定 5,000 条随机射线（seed=23），直接投射到独立 GT 三角网格，与所有冻结模型使用同一组相机和射线。这是同场景新位姿深度诊断，不是新场景或独立实景测试。旧渲染 Z 深度未通过 BVH 数值核验，已排除；新视角 RGB 因渲染域差异不评分。';report['article_en']='Twenty supplementary views are deterministic perturbations of the same simulated trajectory. Each uses 5,000 fixed random rays (seed 23) cast directly into the independent GT triangle mesh, with the same cameras and rays for every frozen model. This tests same-scene novel-pose depth, not a new scene or independent capture. Legacy rendered Z failed numerical BVH validation and is excluded; novel-view RGB is unscored because of renderer differences.'
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('COMPLETE',report['seconds'],flush=True)
if __name__=='__main__':main()
