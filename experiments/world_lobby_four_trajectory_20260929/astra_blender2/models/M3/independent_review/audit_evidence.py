"""Independent M3 static evidence audit. No render, no BVH, no author writes."""
import hashlib, json, struct, sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent.parent
I=R.parent.parent/'inputs/M3'
O=R/'independent_review'
reads=[]
def rb(p):
 p=Path(p);reads.append(str(p));return p.read_bytes()
def js(p):return json.loads(rb(p))
def sha(p):return hashlib.sha256(rb(p)).hexdigest()
def nz(p):reads.append(str(p));return np.load(p)
M=js(R/'modelling_manifest.json');P=js(I/'packet.json');C=js(R/'cameras.json')
X=np.array(M['model_from_input']);cf={f['sample_index']:f for f in C['frames']}
out={'method_id':'M3','model_sha256':sha(R/'scene.blend'),'glb_sha256':sha(R/'scene.glb'),'packet_hash_matches':sha(I/'packet.json')==M['input_packet_sha256']}
out['camera']={'count':len(C['frames']),'indices_exact':sorted(cf)==list(range(180)),'coordinate_frame':C.get('coordinate_frame'),'pose_convention':C.get('pose_convention'),'max_matrix_error':max(float(np.max(np.abs(np.array(cf[f['sample_index']]['camera_to_world'])-X@f['camera_to_world']))) for f in P['frames']),'max_intrinsics_error':max(float(np.max(np.abs(np.array(cf[f['sample_index']]['intrinsics'])-f['intrinsics']))) for f in P['frames']),'identities_preserved':all(all(cf[f['sample_index']][k]==f[k] for k in ['source_index','timestamp_ns']) for f in P['frames']),'rotation_determinant':float(np.linalg.det(X[:3,:3])),'orthogonality_error':float(np.max(np.abs(X[:3,:3].T@X[:3,:3]-np.eye(3)))),'geometry_scale':M['geometry_scale']}
out['required_missing']=[s for s in ['build_scene.py','layout.json','scene.blend','scene.glb','objects.json','colliders.json','cameras.json','input_access_log.json','iteration_log.json','modelling_manifest.json','analysis/object_inventory.json','analysis/measurements.json','analysis/camera_checks.json'] if not (R/s).exists()]
out['input_pass_directories']=[str(p) for p in (R/'checks').glob('input*')]
ledger=js(R/'checks/paired_ledger.json');out['ledger_count']=len(ledger)
out['versions']=[]
fixed=[33,61,74,82,91,100,108,118,129,155]
T=R.parent.parent/'tools/depth_math.py';namespace={};exec(compile(rb(T),str(T),'exec'),namespace)
out['paired_arrays']=[]
for d in sorted((R/'versions').glob('v*')):
 v=int(d.name[1:]);h=sha(d/'scene.blend');rep=js(R/f'checks/v{v}/paired_report.json')
 out['versions'].append({'version':v,'sha256':h,'current_match':h==out['model_sha256'],'report_match':h==rep['model_sha256'],'indices_exact':rep['indices']==fixed,'all_ledger_complete_same_hash':len([r for r in ledger if r['version']==v])==10 and all(r['status']=='COMPLETE' and r['model_sha256']==h for r in ledger if r['version']==v),'snapshots_current_equal':{s:sha(d/s)==sha(R/s) for s in ['scene.glb','build_scene.py','layout.json','objects.json','cameras.json']}})
 for f in rep['frames']:
  n=f['sample_index'];base=R/f'checks/v{v}/{n:04d}';dr=nz(str(base)+'_depth.npz');er=nz(str(base)+'_errors.npz');inp=nz(I/f'geometry/{n:04d}.npz')
  K=np.array(P['frames'][n]['intrinsics'],float);K[:2]*=.5
  uv=dr['pixel_uv'].reshape(-1,2);reference=namespace['sample_depth'](inp['depth_z_m'],inp['valid_mask'],inp['intrinsics'],uv,K).reshape(480,640)
  z=dr['model_z_m'];domain=np.isfinite(reference)&(reference>=.1)&(reference<=30);valid=domain&np.isfinite(z)&(z>=.1)&(z<=30)
  signed=np.where(valid,z-reference,np.nan)
  out['paired_arrays'].append({'frame':n,'version':v,'shape':list(z.shape),'rgb_hash_match':sha(str(base)+'_rgb.png')==f['rgb_sha256'],'depth_hash_match':sha(str(base)+'_depth.npz')==f['depth_sha256'],'report_file_same':js(str(base)+'_report.json')==f,'stored_camera_max_error':float(np.max(np.abs(dr['camera_to_world']-cf[n]['camera_to_world']))),'K_max_error':float(np.max(np.abs(dr['intrinsics']-K))),'pixel_centres_exact':bool(np.array_equal(uv,np.stack(np.meshgrid(np.arange(640)+.5,np.arange(480)+.5),-1).reshape(-1,2))),'reference_equal':bool(np.allclose(reference,dr['input_da3_z_m'],equal_nan=True)),'untrimmed_domain_equal':bool(np.array_equal(domain,dr['input_valid_domain'])),'signed_equal':bool(np.allclose(signed,er['signed_z_residual_m'],equal_nan=True)),'absolute_equal':bool(np.allclose(abs(signed),er['absolute_error_m'],equal_nan=True)),'relative_equal':bool(np.allclose(abs(signed)/reference,er['relative_error'],equal_nan=True)),'median_signed_m':float(np.nanmedian(signed)),'mae_m':float(np.nanmean(abs(signed)))})
# Object/frame patches are fixed image rectangles, NOT new visibility/raycast passes.
patches=[(33,'reception_wall',[235,150,275,210]),(129,'reception_wall',[460,195,560,260]),(155,'reception_wall',[240,130,280,195]),(118,'window_column_source_silhouette',[30,80,65,340]),(33,'pendant_group',[170,40,540,140]),(129,'pendant_group',[240,35,540,180]),(61,'missing_pendant',[238,24,340,68]),(74,'missing_pendant',[390,5,485,38]),(82,'divider_left',[286,335,360,394]),(91,'divider_boxes',[180,224,380,260]),(108,'divider_left',[90,340,160,425])]
out['regional_residuals']=[]
for n,label,box in patches:
 d=nz(R/f'checks/v1/{n:04d}_errors.npz');x0,y0,x1,y1=box;a=d['signed_z_residual_m'][y0:y1,x0:x1]
 out['regional_residuals'].append({'frame':n,'object_or_region':label,'pixel_box_640x480':box,'valid_pixels':int(np.isfinite(a).sum()),'median_signed_model_minus_DA3_m':float(np.nanmedian(a)),'median_absolute_m':float(np.nanmedian(abs(a))),'p10_p90_signed_m':np.nanquantile(a,[.1,.9]).tolist()})
# Parse the actual GLB buffer/accessors, not just its manifest.
b=rb(R/'scene.glb');magic,version,length=struct.unpack_from('<4sII',b);chunks=[];offset=12
while offset<len(b):
 size,kind=struct.unpack_from('<II',b,offset);chunks.append((kind,b[offset+8:offset+8+size]));offset+=8+size
g=json.loads(chunks[0][1]);blob=next(data for kind,data in chunks if kind==0x004e4942)
types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'};sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];dt=np.dtype(types[a['componentType']]);sz=sizes[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0)
 return np.ndarray((a['count'],sz),dtype=dt,buffer=blob,offset=off,strides=(v.get('byteStride',dt.itemsize*sz),dt.itemsize))
objects=js(R/'objects.json')['objects'];names=[c for o in objects for c in o['components']];meshnodes=[n for n in g['nodes'] if 'mesh' in n]
normal_errors=[];bad=[];triangles=0
for n in meshnodes:
 for p in g['meshes'][n['mesh']]['primitives']:
  pos=acc(p['attributes']['POSITION']);norm=acc(p['attributes']['NORMAL']);ix=acc(p['indices']).ravel();triangles+=len(ix)//3
  if not np.isfinite(pos).all() or not np.isfinite(norm).all() or int(ix.max())>=len(pos):bad.append(n['name'])
  normal_errors.append(float(np.max(abs(np.linalg.norm(norm,axis=1)-1))))
out['glb']={'magic':magic.decode(),'version':version,'length_matches':length==len(b),'external_uris':[d['uri'] for k in ['buffers','images'] for d in g.get(k,[]) if 'uri' in d],'mesh_nodes':len(meshnodes),'triangles':triangles,'bad_geometry_or_normals':bad,'max_normal_length_error':max(normal_errors),'semantic_names_missing':sorted(set(names)-{n['name'] for n in meshnodes}),'unmapped_meshes':sorted({n['name'] for n in meshnodes}-set(names)),'semantic_id_mismatches':[n['name'] for n in meshnodes if n.get('extras',{}).get('semantic_id')!=n['name'].split('__')[0]]}
ins=js(O/'scene_inspection.json');out['semantic']={'object_count':len(objects),'component_count':len(names),'duplicate_component_names':len(names)-len(set(names)),'unmapped_blender_meshes':sorted({m['name'] for m in ins['meshes']}-set(names)),'missing_components':sorted(set(names)-{m['name'] for m in ins['meshes']}),'metadata_missing':[{ 'id':o['id'],'missing':[k for k in ['category','dimensions','relations','evidence_frames','provenance'] if not o.get(k)]} for o in objects if any(not o.get(k) for k in ['category','dimensions','relations','evidence_frames','provenance'])]}
out['paths_read']=sorted(set(reads));(O/'evidence_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['paths_read','paired_arrays']},indent=2));print('paired_arrays_all_integrity_checks',all(all(v for k,v in r.items() if k.endswith('_match') or k.endswith('_equal') or k in ['reference_equal','signed_equal','absolute_equal','relative_equal','pixel_centres_exact','report_file_same']) for r in out['paired_arrays']))
