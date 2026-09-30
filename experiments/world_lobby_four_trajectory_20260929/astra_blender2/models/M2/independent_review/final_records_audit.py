"""Audit existing M2 records and arrays, with no input raycasting or rendering."""
import json,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent.parent;I=R.parent.parent/'inputs/M2';T=R.parent.parent/'tools';read=[]
def path(p):
 p=Path(p);p=p if p.is_absolute() else R/p;read.append(str(p));return p
def get(p):return json.loads(path(p).read_text())
def sha(p):return hashlib.sha256(path(p).read_bytes()).hexdigest()
def arr(p):return np.load(path(p))
ns={};exec(compile(path(T/'depth_math.py').read_text(),str(T/'depth_math.py'),'exec'),ns)
sample=ns['sample_depth'];metric=ns['metrics']
packet=get(I/'packet.json');man=get('modelling_manifest.json');cams=get('cameras.json');ledger=get('checks/paired_ledger.json');X=np.array(man['model_from_input']);K=np.array(packet['intrinsics']);fixed=[33,61,74,82,91,100,108,118,129,155]
errors=[]
def check(ok,label):
 if not ok:errors.append(label)
hashes={f:sha(f) for f in ['scene.blend','scene.glb','cameras.json','build_scene.py','layout.json']}
check(man['scene_sha256']==hashes['scene.blend'],'manifest model hash');check(man['glb_sha256']==hashes['scene.glb'],'manifest glb hash');check(man['input_packet_sha256']==sha(I/'packet.json'),'packet hash')
poseerr=0
for i,(p,c) in enumerate(zip(packet['frames'],cams['frames'])):
 poseerr=max(poseerr,float(np.max(np.abs(np.array(c['camera_to_world'])-X@np.array(p['camera_to_world'])))))
 check(all(c[k]==p[k] for k in ['sample_index','source_index','timestamp_ns']),'camera identity '+str(i));check(c['intrinsics']==packet['intrinsics'] and c['valid'],'camera K/valid '+str(i))
check(len(cams['frames'])==180 and poseerr==0,'camera count/pose');check(man['geometry_scale']==1 and np.allclose(X[:3,:3].T@X[:3,:3],np.eye(3)) and np.isclose(np.linalg.det(X[:3,:3]),1),'rigid unit scale')
npzs={}
for i in fixed:npzs[i]=arr(I/f'geometry/{i:04d}.npz')
versions=[];pairdata={}
def boundary(z):
 good=np.isfinite(z);base=np.nan_to_num(z);dx=np.zeros_like(good);dy=dx.copy();dx[:,1:]=good[:,1:]&good[:,:-1]&(np.abs(base[:,1:]-base[:,:-1])>np.maximum(.15,.05*base[:,1:]));dy[1:]=good[1:]&good[:-1]&(np.abs(base[1:]-base[:-1])>np.maximum(.15,.05*base[1:]));return dx|dy
for v in [1,2,3]:
 prefix=f'checks/v{v}';snap=f'versions/v{v}';h=sha(f'{snap}/scene.blend');report=get(f'{prefix}/paired_report.json');entries=[e for e in ledger if e['version']==v];check(report['indices']==fixed and len(report['frames'])==10 and sorted(e['sample_index'] for e in entries)==fixed,'fixed ten v'+str(v));check(report['model_sha256']==h and all(e['model_sha256']==h and e['status']=='COMPLETE' for e in entries),'version hash/ledger '+str(v))
 sm=get(f'{snap}/modelling_manifest.json');check(sm['model_from_input']==man['model_from_input'] and sm['geometry_scale']==1,'snapshot scale '+str(v));check(sha(f'{snap}/cameras.json')==hashes['cameras.json'],'snapshot camera '+str(v))
 for f in ['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','colliders.json']:
  check((R/snap/f).exists(),'snapshot missing '+str(v)+' '+f)
  if v==3:check(sha(f'{snap}/{f}')==sha(f),'final snapshot current '+f)
 rows=[]
 for i in fixed:
  f=f'{prefix}/{i:04d}';r=get(f+'_report.json');a=arr(f+'_depth.npz');e=arr(f+'_errors.npz');pairdata[v,i]={k:a[k] for k in a.files}
  check(r['model_sha256']==h and r['rgb_sha256']==sha(f+'_rgb.png') and r['depth_sha256']==sha(f+'_depth.npz'),'paired hashes '+f);check((R/(f+'_comparison.jpg')).exists(),'comparison missing '+f)
  check(np.array_equal(a['intrinsics'],K*np.array([[.5,.5,.5],[.5,.5,.5],[1,1,1]])),'paired K '+f);check(np.array_equal(a['camera_to_world'],np.array(cams['frames'][i]['camera_to_world'])),'paired pose '+f)
  uv=a['pixel_uv'];check(uv.shape==(480,640,2) and np.array_equal(uv[0,:,0],np.arange(640)+.5) and np.array_equal(uv[:,0,1],np.arange(480)+.5),'pixel centres '+f)
  n=npzs[i];ref=sample(n['depth_z_m'],n['valid_mask'],n['intrinsics'],uv.reshape(-1,2),a['intrinsics']).reshape(480,640);domain=np.isfinite(ref)&(ref>=.1)&(ref<=30);z=a['model_z_m'];valid=domain&np.isfinite(z)&(z>=.1)&(z<=30);signed=np.where(valid,z-ref,np.nan)
  check(np.allclose(ref,a['input_da3_z_m'],equal_nan=True,atol=1e-9) and np.array_equal(domain,a['input_valid_domain']),'input sample/domain '+f)
  for name,target in [('signed_z_residual_m',signed),('absolute_error_m',np.abs(signed)),('relative_error',np.abs(signed)/ref),('input_domain',domain),('model_valid',valid),('input_edges',boundary(ref)),('model_edges',boundary(z))]:check(np.allclose(e[name],target,equal_nan=True,atol=1e-9),'error array '+f+' '+name)
  m=metric(z,ref);check(abs(m['mae_m']-r['input_consistency']['mae_m'])<1e-8,'MAE '+f);rows.append({'sample':i,'mae_m':m['mae_m'],'domain':m['pixels_domain'],'missing':m['pixels_domain']-m['pixels_valid']})
 versions.append({'version':v,'model_sha256':h,'paired_count':len(entries),'rows':rows,'aggregate':report['aggregate_input_consistency']})
full=[];previous=None;fullarrays={}
for v,directory in [(1,'input_v1'),(2,'input_v2'),(3,'input_final')]:
 pre=f'checks/{directory}';r=get(pre+'/report.json');a=arr(pre+'/depth.npz');z=a['prediction_z_m'];ref=a['reference_z_m'];fullarrays[v]={k:a[k] for k in a.files};domain=np.isfinite(ref)&(ref>=.1)&(ref<=30)
 check(z.shape==(180,19200) and r['frames']==180 and len(r['per_frame'])==180,'full count '+pre);check(r['model_sha256']==versions[v-1]['model_sha256'],'full hash '+pre);check(np.allclose(r['transform_applied_to_mesh'],np.linalg.inv(X)),'full transform '+pre);check(np.array_equal(a['timestamps_ns'],[f['timestamp_ns'] for f in packet['frames']]),'full timestamps '+pre);check([f['sample_index'] for f in r['per_frame']]==list(range(180)),'full indices '+pre)
 if previous is not None:check(np.array_equal(ref,previous,equal_nan=True),'full reference unchanged '+pre)
 previous=ref.copy();m=metric(z.astype(float),ref.astype(float));check(abs(m['mae_m']-r['aggregate']['mae_m'])<1e-6,'full MAE '+pre)
 full.append({'version':v,'directory':pre,'model_sha256':r['model_sha256'],'frames':180,'shape':list(z.shape),'recomputed':m,'reference_sha256':hashlib.sha256(ref.tobytes()).hexdigest(),'domain_sha256':hashlib.sha256(domain.tobytes()).hexdigest()})
reference_max=0;outliers=[]
for i,p in enumerate(packet['frames']):
 n=npzs[i] if i in npzs else arr(I/f'geometry/{i:04d}.npz');check(sha(I/f'geometry/{i:04d}.npz')==p['geometry_sha256'],'input geometry hash '+str(i));ref=sample(n['depth_z_m'],n['valid_mask'],n['intrinsics'],fullarrays[3]['pixel_uv'],K);target=fullarrays[3]['reference_z_m'][i];check(np.allclose(ref,target,equal_nan=True,atol=3e-6),'full input resample '+str(i));reference_max=max(reference_max,float(np.nanmax(np.abs(ref-target))))
 if i in [20,21,22,166,167,168,175]:
  prev=np.array(packet['frames'][i-1]['camera_to_world']);now=np.array(p['camera_to_world']);valid=np.isfinite(target)&(target>=.1)&(target<=30)&np.isfinite(fullarrays[3]['prediction_z_m'][i]);delta=fullarrays[3]['prediction_z_m'][i]-target
  outliers.append({'frame':i,'selected_window':p['selected_window'],'depth_median_m':float(np.nanmedian(ref)),'translation_step_m':float(np.linalg.norm(now[:3,3]-prev[:3,3])),'rotation_step_deg':float(np.degrees(np.arccos(np.clip((np.trace(prev[:3,:3].T@now[:3,:3])-1)/2,-1,1)))),'signed_median_m':float(np.median(delta[valid]))})
regions=[];revision=get('analysis/revision_evidence.json')
for r in revision['regions']:
 if not any(s in r['name'] for s in ['desk','end_wall','lamp','seat_near_mid','planter_far']):continue
 i=r['frame'];x0,y0,x1,y1=r['rgb_box'];vals={}
 for v in [1,3]:
  a=pairdata[v,i];uv=a['pixel_uv']*2;mask=(uv[:,:,0]>=x0)&(uv[:,:,0]<x1)&(uv[:,:,1]>=y0)&(uv[:,:,1]<y1)&a['input_valid_domain']&np.isfinite(a['model_z_m']);delta=a['model_z_m']-a['input_da3_z_m'];vals['v'+str(v)]=float(np.median(delta[mask]))
 regions.append({'name':r['name'],'frame':i,'rgb_box':r['rgb_box'],'signed_medians_m':vals})
required=['build_scene.py','layout.json','scene.blend','scene.glb','objects.json','colliders.json','cameras.json','input_access_log.json','iteration_log.json','modelling_manifest.json','analysis/object_inventory.json','analysis/measurements.json','analysis/camera_checks.json']
check(all((R/f).is_file() for f in required),'required evidence missing');check(man['revisions']==3 and man['checking_render_count']==30 and man['input_bvh_pass_count']==3 and len(ledger)==30,'manifest counts')
logs=[]
for f in ['input_access_log.json','revision_access_log.json']:
 d=get(f);pp=d.get('paths_read',[])+d.get('own_output_paths_read',[]);outside=[]
 for p in pp:
  if not isinstance(p,str):continue
  if p.startswith('/') and not (p.startswith(str(R)+'/') or p.startswith(str(I)+'/') or p==str(R.parent.parent/'configs/modelling_contract.md') or p in [str(T/x) for x in ['paired_check_blender.py','visualize_checks.py','raycast_scene.py','depth_math.py','inspect_scene.py','validate_artifacts.py']]):outside.append(p)
 logs.append({'file':f,'declared_path_count':len(pp),'out_of_scope_paths':outside,'declared_prohibited_sources_read':d.get('prohibited_sources_read')});check(not outside,'declared access scope '+f)
out={'status':'PASS' if not errors else 'FAIL','errors':errors,'hashes':hashes,'camera_count':len(cams['frames']),'camera_matrix_max_error':poseerr,'rigid_determinant':float(np.linalg.det(X[:3,:3])),'geometry_scale':man['geometry_scale'],'versions':versions,'full_input_passes':full,'full_input_reference_resampling_max_error_m':reference_max,'outliers':outliers,'regions':regions,'access_logs':logs,'paths_read':sorted(set(read)),'scope':'Existing arrays only; no new BVH pass. DA3 prediction consistency, not ground truth accuracy.'}
(R/'independent_review/final_records_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['paths_read','versions','full_input_passes','regions']},indent=2));print('REGIONS',json.dumps(regions,indent=2))
