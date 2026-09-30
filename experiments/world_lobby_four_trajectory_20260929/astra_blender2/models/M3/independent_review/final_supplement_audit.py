"""Static export and retained input-pass audit. No render, BVH, or author writes."""
import json, hashlib
from pathlib import Path
import numpy as np
import trimesh
R=Path(__file__).resolve().parent.parent
I=R.parents[1]/'inputs/M3'; O=R/'independent_review'; reads=[]
def rb(p):
 p=Path(p);reads.append(str(p));return p.read_bytes()
def js(p):return json.loads(rb(p))
def sha(p):return hashlib.sha256(rb(p)).hexdigest()
def nz(p):reads.append(str(p));return np.load(p)
ns={};p=R.parents[1]/'tools/depth_math.py';exec(compile(rb(p),str(p),'exec'),ns)
P=js(I/'packet.json');M=js(R/'modelling_manifest.json');X=np.array(M['model_from_input'])
out={'model_sha256':sha(R/'scene.blend'),'glb_sha256':sha(R/'scene.glb'),'input_passes':[]}
for version,name in [(1,'input_v1'),(2,'input_v2'),(3,'input_final')]:
 d=R/'checks'/name;report=js(d/'report.json');a=nz(d/'depth.npz');rh=sha(d/'report.json');dh=sha(d/'depth.npz')
 record=js(d/('coordinator_invocation.json' if version==1 else 'author_invocation.json'))
 row={'directory':str(d),'frames':report['frames'],'rays_per_frame':report['rays_per_frame'],'depth_shape':list(a['prediction_z_m'].shape),'timestamp_match':bool(np.array_equal(a['timestamps_ns'],[f['timestamp_ns'] for f in P['frames']])),'pixel_grid_exact':bool(np.array_equal(a['pixel_uv'],ns['pixel_grid']())),'version_hash_match':report['model_sha256']==sha(R/f'versions/v{version}/scene.blend'),'inverse_transform_error':float(np.max(abs(np.array(report['transform_applied_to_mesh'])-np.linalg.inv(X)))),'all180_report_indices':sorted(f['sample_index'] for f in report['per_frame'])==list(range(180)),'pass_hashes_match_manifest':any(v['report_sha256']==rh and v['depth_sha256']==dh and v['model_sha256']==report['model_sha256'] for v in M['full_input_passes']),'reference_max_error':0.0,'per_frame_mae_max_error':0.0,'invocation_record':record,'late_depth_samples':[]}
 for j,f in enumerate(P['frames']):
  inp=nz(I/f'geometry/{f["sample_index"]:04d}.npz')
  ref=ns['sample_depth'](inp['depth_z_m'],inp['valid_mask'],inp['intrinsics'],a['pixel_uv'],np.array(f['intrinsics']))
  row['reference_max_error']=max(row['reference_max_error'],float(np.nanmax(abs(ref-a['reference_z_m'][j]))))
  if not np.array_equal(np.isfinite(ref),np.isfinite(a['reference_z_m'][j])):row['reference_finite_mask_mismatch']=True
  met=ns['metrics'](a['prediction_z_m'][j],ref)
  row['per_frame_mae_max_error']=max(row['per_frame_mae_max_error'],abs(met['mae_m']-report['per_frame'][j]['mae_m']))
  if j in [33,61,82,108,129,155,160,170,179]:row['late_depth_samples'].append({'frame':j,'median_input_m':float(np.nanmedian(ref)),'median_model_m':float(np.nanmedian(a['prediction_z_m'][j]))})
 if version==1:
  row['origin_record_hashes_match']=record['model_sha256']==report['model_sha256'] and record['report_sha256']==rh and record['depth_sha256']==dh and record['log_sha256']==sha(d/'coordinator_invocation.log')
 out['input_passes'].append(row)
# Recheck exported actual geometry, weld only for topology analysis, never save GLB.
reads.append(str(R/'scene.glb'));s=trimesh.load(R/'scene.glb',force='scene',process=False)
inspection=js(O/'final_scene_inspection.json');bounds={r['name']:np.array(r['bounds']) for r in inspection['meshes']}
out['glb']={'mesh_count':len(s.geometry),'selected_topology':[],'component_bounds_max_error_m':0.,'bounds_mismatch_names':[],'nonfinite':[]}
for node in s.graph.nodes_geometry:
 T,key=s.graph[node];mesh=s.geometry[key]
 if not np.isfinite(mesh.vertices).all():out['glb']['nonfinite'].append(node)
 pts=trimesh.transform_points(mesh.vertices,T);pts=pts[:,[0,2,1]]*np.array([1,-1,1]);bb=np.stack((pts.min(0),pts.max(0)))
 err=float(np.max(abs(bb-bounds[node])));out['glb']['component_bounds_max_error_m']=max(out['glb']['component_bounds_max_error_m'],err)
 if err>1e-5:out['glb']['bounds_mismatch_names'].append(node)
 if 'curved_back' not in node and 'reception_desk' not in node:continue
 mesh=mesh.copy();mesh.merge_vertices(merge_tex=True,merge_norm=True)
 out['glb']['selected_topology'].append({'component':node,'watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),'degenerate_triangles':int((mesh.area_faces<1e-12).sum()),'positive_volume':bool(mesh.volume>0)})
# Version invariants and stored edge/mask evidence.
out['version_invariants']=[]
for v in [1,2,3]:
 vm=js(R/f'versions/v{v}/modelling_manifest.json')
 out['version_invariants'].append({'version':v,'camera_bytes_unchanged':sha(R/f'versions/v{v}/cameras.json')==sha(R/'cameras.json'),'scale':vm['geometry_scale'],'rigid_transform_unchanged':bool(np.array_equal(vm['model_from_input'],M['model_from_input']))})
def boundary(z):
 good=np.isfinite(z);base=np.nan_to_num(z);dx=np.zeros_like(good);dy=dx.copy()
 dx[:,1:]=good[:,1:]&good[:,:-1]&(np.abs(base[:,1:]-base[:,:-1])>np.maximum(.15,.05*base[:,1:]))
 dy[1:]=good[1:]&good[:-1]&(np.abs(base[1:]-base[:-1])>np.maximum(.15,.05*base[1:]))
 return dx|dy
out['edge_masks']=[]
for v in [1,2,3]:
 for n in [33,61,74,82,91,100,108,118,129,155]:
  d=nz(R/f'checks/v{v}/{n:04d}_depth.npz');e=nz(R/f'checks/v{v}/{n:04d}_errors.npz');z=d['model_z_m'];ref=d['input_da3_z_m'];domain=d['input_valid_domain'];valid=domain&np.isfinite(z)&(z>=.1)&(z<=30)
  out['edge_masks'].append({'version':v,'sample_index':n,'input_edges_equal':bool(np.array_equal(boundary(ref),e['input_edges'])),'model_edges_equal':bool(np.array_equal(boundary(z),e['model_edges'])),'domain_equal':bool(np.array_equal(domain,e['input_domain'])),'valid_equal':bool(np.array_equal(valid,e['model_valid']))})
out['patches']=[]
for n,label,box in [(118,'column',[30,80,65,340]),(108,'column',[146,90,166,235]),(61,'pendant7',[238,24,340,68]),(74,'pendant7',[390,5,485,38]),(129,'pendant6',[255,8,425,68]),(82,'divider',[282,353,370,425]),(91,'divider',[175,218,265,264]),(33,'reception_wall',[235,150,275,210]),(129,'reception_wall',[460,195,560,260]),(155,'reception_wall',[240,130,280,195]),(82,'unmatched_pendants',[210,0,400,105])]:
  row={'frame':n,'object_or_region':label,'box_640x480':box};x0,y0,x1,y1=box
  for v in [1,3]:
   a=nz(R/f'checks/v{v}/{n:04d}_errors.npz')['signed_z_residual_m'][y0:y1,x0:x1]
   row[f'v{v}']={'median_signed_m':float(np.nanmedian(a)),'median_absolute_m':float(np.nanmedian(abs(a))),'valid_pixels':int(np.isfinite(a).sum())}
  out['patches'].append(row)
out['paths_read']=sorted(set(reads));(O/'final_supplement_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print('STATIC_SUPPLEMENT_COMPLETE',out['model_sha256']);print('GLB',out['glb']);print('PASSES',[{k:v for k,v in r.items() if k not in ['invocation_record','late_depth_samples']} for r in out['input_passes']])
