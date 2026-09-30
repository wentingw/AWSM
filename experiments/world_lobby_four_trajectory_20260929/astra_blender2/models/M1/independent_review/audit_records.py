"""Reviewer-only read audit. No renders, reconstruction, or input BVH passes."""
import json, hashlib, struct, collections
from pathlib import Path
import numpy as np
import trimesh

R=Path(__file__).resolve().parent.parent
O=R/'independent_review'
I=R.parent.parent/'inputs/M1'
reads=[]
def data(p):
    p=Path(p); reads.append(str(p)); return p.read_bytes()
def js(p): return json.loads(data(p))
def sha(p): return hashlib.sha256(data(p)).hexdigest()
def save(n,d): (O/n).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
report={}
report['model_sha256']=sha(R/'scene.blend')
report['glb_sha256']=sha(R/'scene.glb')
packet=js(I/'packet.json'); manifest=js(R/'modelling_manifest.json')
report['manifest']=manifest
report['packet_hash_matches']=sha(I/'packet.json')==manifest['input_packet_sha256']
required=['build_scene.py','layout.json','scene.blend','scene.glb','objects.json','colliders.json','cameras.json','input_access_log.json','iteration_log.json','modelling_manifest.json','analysis/object_inventory.json','analysis/measurements.json','analysis/camera_checks.json']
report['missing_required_files']=[n for n in required if not (R/n).is_file()]
report['versions']=[]
for v in sorted((R/'versions').glob('v*')):
    pr=js(R/'checks'/v.name/'paired_report.json')
    versionsha=sha(v/'scene.blend')
    matches={n:sha(v/n)==sha(R/n) for n in ['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','cameras.json']}
    report['versions'].append({'version':v.name,'model_sha256':versionsha,'paired_sha_matches':versionsha==pr['model_sha256'],'indices':pr['indices'],'status':pr['status'],'current_snapshot_matches':matches})
ledger=js(R/'checks/paired_ledger.json')
report['ledger_status_counts']=dict(collections.Counter(x['status'] for x in ledger))
report['ledger_total_events']=len(ledger)
report['ledger_versions']=sorted(set(x['version'] for x in ledger))
cs=js(R/'cameras.json'); cams=cs['frames']; cby={x['sample_index']:x for x in cams}
pby={x['sample_index']:x for x in packet['frames']}
report['camera_frames']=len(cams)
report['camera_sample_ids_complete']=sorted(cby)==list(range(180))
report['camera_valid_count']=sum(bool(c['valid']) for c in cams)
report['camera_convention']={k:v for k,v in cs.items() if k!='frames'}
report['camera_intrinsics_and_identity_unchanged']=all(all(c[k]==pby[c['sample_index']][k] for k in ['sample_index','source_index','timestamp_ns','intrinsics']) for c in cams)
Ts=np.array([c['camera_to_world'] for c in cams]);rots=Ts[:,:3,:3]
report['camera_matrix_checks']={'finite':bool(np.isfinite(Ts).all()),'max_orthonormal_error':float(np.max(np.abs(rots.transpose(0,2,1)@rots-np.eye(3)))),'determinant_range':[float(np.linalg.det(rots).min()),float(np.linalg.det(rots).max())],'bottom_rows_valid':bool(np.allclose(Ts[:,3,:],[0,0,0,1]))}
measure=js(R/'analysis/measurements.json'); js(R/'analysis/camera_checks.json')
res=[]
for obs in measure['observations']:
    T=np.array(cby[obs['sample_index']]['camera_to_world']); K=np.array(cby[obs['sample_index']]['intrinsics'])
    errs=[];delta=[]
    for lm in obs['landmarks']:
        q=(np.array(lm['world_xyz_assumed_m'])-T[:3,3])@T[:3,:3]
        uv=(K@q)[:2]/q[2]; e=uv-lm['pixel_uv'];errs.append(e);delta.append(e-lm['residual_uv_pixels'])
    res.append({'sample_index':obs['sample_index'],'rms_per_coordinate_pixels':float(np.sqrt(np.mean(np.array(errs)**2))),'max_landmark_l2_pixels':float(np.max(np.linalg.norm(errs,axis=1))),'max_delta_vs_saved_pixels':float(np.max(np.abs(delta)))})
report['recomputed_landmark_residuals']=res
report['depth_checks']=[]
indices=[33,61,74,82,91,100,108,118,129,155]
for i in indices:
    pr=js(R/f'checks/v1/{i:04d}_report.json'); dp=R/f'checks/v1/{i:04d}_depth.npz'
    reads.append(str(dp))
    with np.load(dp) as n:
        z=n['model_z_m']; valid=np.isfinite(z); K=np.array(pby[i]['intrinsics'])*np.array([[.5,.5,.5],[.5,.5,.5],[1,1,1]])
        row={'sample_index':i,'shape':list(z.shape),'finite_fraction':float(valid.mean()),'range_m':[float(z[valid].min()),float(z[valid].max())],'median_m':float(np.median(z[valid])),'fraction_under_1m':float((valid&(z<1)).mean()),'positive_finite_depth':bool((z[valid]>0).all()),'hit_mask_matches':bool(np.array_equal(n['model_hit'],valid)),'K_matches':bool(np.allclose(n['intrinsics'],K)),'camera_matches':bool(np.allclose(n['camera_to_world'],cby[i]['camera_to_world'])),'pixel_centres_match':bool(np.allclose(n['pixel_uv'][0,0],[.5,.5]) and np.allclose(n['pixel_uv'][-1,-1],[639.5,479.5])),'input_reference_present':'input_da3_z_m' in n,'depth_hash_matches':sha(dp)==pr['depth_sha256'],'rgb_hash_matches':sha(R/f'checks/v1/{i:04d}_rgb.png')==pr['rgb_sha256'],'model_hash_matches':pr['model_sha256']==report['model_sha256'],'source_hash_matches':sha(I/f'rgb/{i:04d}.png')==pby[i]['rgb_sha256']}
        report['depth_checks'].append(row)
objs=js(R/'objects.json')['objects']; coll=js(R/'colliders.json')['colliders']; inspection=js(O/'artifact_inspection.json'); inv=js(R/'analysis/object_inventory.json')['inventory']
parts=[p for o in objs for p in o['component_names']]; meshes={m['name']:m for m in inspection['meshes']}
g=data(R/'scene.glb'); size,kind=struct.unpack_from('<II',g,12); gltf=json.loads(g[20:20+size]); nodes={n['name']:n for n in gltf['nodes'] if 'mesh' in n}
report['semantic_mapping']={'objects':len(objs),'components':len(parts),'unique_ids':len(set(o['id'] for o in objs))==len(objs),'unique_components':len(set(parts))==len(parts),'missing_blend':sorted(set(parts)-set(meshes)),'unowned_blend':sorted(set(meshes)-set(parts)),'missing_glb':sorted(set(parts)-set(nodes)),'unowned_glb':sorted(set(nodes)-set(parts)),'inventory_matches':inv==objs,'glb_extras_match':all(nodes[p].get('extras',{}).get('semantic_id')==o['id'] for o in objs for p in o['component_names'])}
reads.append(str(R/'scene.glb')); loaded=trimesh.load(R/'scene.glb',force='scene',process=False)
report['glb_loading']={'header_ok':g[:4]==b'glTF' and struct.unpack_from('<I',g,8)[0]==len(g),'geometry_count':len(loaded.geometry),'bounds_finite':bool(np.isfinite(loaded.bounds).all()),'bounds_gltf_y_up':loaded.bounds.tolist()}
bound_errors=[];normal_issues=[]
for name in loaded.graph.nodes_geometry:
    transform,gn=loaded.graph[name]; mesh=loaded.geometry[gn]
    pts=trimesh.transform_points(mesh.vertices,transform);pts=pts[:,[0,2,1]]*np.array([1,-1,1]);bounds=np.array([pts.min(0),pts.max(0)])
    if name in meshes:
        err=float(np.max(np.abs(bounds-np.array(meshes[name]['bounds']))))
        if err>1e-4: bound_errors.append({'name':name,'error_m':err})
    if not np.isfinite(mesh.vertices).all() or not np.isfinite(mesh.vertex_normals).all():normal_issues.append(name)
report['glb_loading']['bounds_mismatch_components']=bound_errors
report['glb_loading']['nonfinite_geometry_or_normals']=normal_issues
report['semantic_dimensions_mismatches']=[]
for o in objs:
    b=np.array([meshes[n]['bounds'] for n in o['component_names']]);dim=b[:,1].max(0)-b[:,0].min(0)
    error=float(np.max(np.abs(dim-o['dimensions'])))
    if error>.002:report['semantic_dimensions_mismatches'].append({'id':o['id'],'max_error_m':error})
report['selected_objects']=[o for o in objs if o['id'] in ['mirror_partition','south_opening','north_metal_door','reception_desk','south_side_seat_0','south_side_seat_1','south_side_seat_2']]
report['camera_108']={'position':Ts[108,:3,3].tolist(),'forward':Ts[108,:3,2].tolist(),'overlapping_component_AABBs':[n for n,m in meshes.items() if np.all(Ts[108,:3,3]>np.array(m['bounds'][0])) and np.all(Ts[108,:3,3]<np.array(m['bounds'][1]))]}
report['portal_proxy_probe']={}
for label,p in [('south_opening_mouth',[6.85,3.925,1.0]),('north_door_mouth',[6.85,10.075,1.0])]:
    report['portal_proxy_probe'][label]={'point_m':p,'enabled_containing_AABBs':[c['id'] for c in coll if c['enabled'] and np.all(np.array(p)>c['bounds_min']) and np.all(np.array(p)<c['bounds_max'])]}
report['floor_support_candidates']=[{'id':o['id'],'minimum_z_m':o['bbox_min'][2],'relations':o['relations']} for o in objs if o['category'] in ['modular_lounge_seat','coffee_table','reception_counter','planter','floor_lamp']]
save('record_audit.json',report);save('audit_paths_read.json',sorted(set(reads)))
print(json.dumps({k:report[k] for k in ['model_sha256','missing_required_files','versions','camera_matrix_checks','semantic_mapping','glb_loading','semantic_dimensions_mismatches','camera_108','portal_proxy_probe']},indent=2))
print('DEPTH',json.dumps(report['depth_checks']))
print('RESIDUALS',json.dumps(res))
