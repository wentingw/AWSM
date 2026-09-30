"""Final-review-only read-only artifact audit; no rendering or BVH. Writes here only."""
import json, hashlib, itertools, struct
from pathlib import Path
import numpy as np
import trimesh
R=Path(__file__).resolve().parent.parent
O=R/'independent_review'
I=R.parents[1]/'inputs/M1'
reads=set()
def read(p):
 p=Path(p); reads.add(str(p)); return p.read_bytes()
def js(p): return json.loads(read(p))
def sha(p): return hashlib.sha256(read(p)).hexdigest()
def loadnp(p):
 reads.add(str(p)); return np.load(p)
idx=[33,61,74,82,91,100,108,118,129,155]
report={'scope':'M1 only; existing paired depths only; no new render or BVH','hashes':{},'failures':[]}
def check(ok,desc):
 if not ok: report['failures'].append(desc)
manifest=js(R/'modelling_manifest.json');packet=js(I/'packet.json');cams=js(R/'cameras.json');frames={f['sample_index']:f for f in cams['frames']};inp={f['sample_index']:f for f in packet['frames']}
for name in ['scene.blend','scene.glb','build_scene.py','layout.json','objects.json','colliders.json','cameras.json']:
 report['hashes'][name]=sha(R/name);check(report['hashes'][name]==manifest['artifact_sha256'][name],f'manifest hash {name}')
check(sha(I/'packet.json')==manifest['input_packet_sha256'],'packet sha')
check(manifest['status']=='ready_for_independent_review','manifest status')
check(manifest['model_from_input'] is None,'M1 transform')
ledger=js(R/'checks/paired_ledger.json');iterations=js(R/'iteration_log.json');access=js(R/'input_access_log.json')
report['versions']=[];report['depths']=[]
for ver in [1,2]:
 v=R/f'versions/v{ver}';c=R/f'checks/v{ver}';h=sha(v/'scene.blend');p=js(c/'paired_report.json');l=[x for x in ledger if x['version']==ver];vc=js(v/'cameras.json');vm=js(v/'modelling_manifest.json')
 check(len(l)==10 and sorted(x['sample_index'] for x in l)==idx and all(x['status']=='COMPLETE' and x['model_sha256']==h for x in l),f'ledger v{ver}')
 check(p['model_sha256']==h and p['indices']==idx and p['status']=='COMPLETE' and len(p['frames'])==10,f'paired v{ver}')
 check(sha(v/'cameras.json')==report['hashes']['cameras.json'],f'cameras changed v{ver}')
 check(vm['input_packet_sha256']==manifest['input_packet_sha256'],f'packet changed v{ver}')
 check(vm['geometry_scale']==manifest['geometry_scale'],f'scale changed v{ver}')
 for i in idx:
  rr=js(c/f'{i:04d}_report.json');n=loadnp(c/f'{i:04d}_depth.npz');z=n['model_z_m'];hits=n['model_hit'];K=np.array(inp[i]['intrinsics'],float);K[:2]*=.5
  check(rr['model_sha256']==h and rr['rgb_sha256']==sha(c/f'{i:04d}_rgb.png') and rr['depth_sha256']==sha(c/f'{i:04d}_depth.npz'),f'check hashes v{ver} {i}')
  check(rr==next(x for x in p['frames'] if x['sample_index']==i),f'perframe report v{ver} {i}')
  check(z.shape==(480,640) and np.array_equal(hits,np.isfinite(z)) and np.all((z[hits]>=.01)&(z[hits]<=60)),f'depth domain v{ver} {i}')
  check(np.allclose(n['intrinsics'],K) and np.allclose(n['camera_to_world'],frames[i]['camera_to_world']),f'paired cameras v{ver} {i}')
  u,vv=np.meshgrid(np.arange(640)+.5,np.arange(480)+.5)
  check(np.array_equal(n['pixel_uv'],np.stack([u,vv],axis=-1)),f'pixel centers v{ver} {i}')
  check('input_da3_z_m' not in n.files and rr['input_consistency'] is None,f'M1 depth N/A v{ver} {i}')
  check((c/f'{i:04d}_comparison.jpg').is_file(),f'comparison missing v{ver} {i}')
  report['depths'].append({'version':ver,'frame':i,'hit_fraction':float(hits.mean()),'median_z_m':float(np.nanmedian(z)),'fraction_image_z_below_1m':float(np.mean(z<1)),'reference':'N/A RGB-only'})
 report['versions'].append({'version':ver,'model_sha256':h,'ten_fixed_views':True,'report_and_output_hashes_checked':True,'paired_camera_unchanged':True,'scale_record_unchanged':True})
 if ver==2:
  for name in ['scene.blend','scene.glb','layout.json','build_scene.py','objects.json','cameras.json','colliders.json']:
   check(sha(v/name)==report['hashes'][name],f'current-v2 mismatch {name}')
check(len(ledger)==20 and manifest['checking_render_count']==20 and manifest['revisions']==2,'budgets')
report['budget']={'versions':2,'paired_views':20,'supplemental_views':0,'input_bvh_passes':manifest['input_bvh_pass_count'],'three_pass_requirement':'N/A; M2-M4 only'}
check(manifest['input_bvh_pass_count']==0,'M1 BVH passes')
check(len(frames)==180 and set(frames)==set(range(180)),'camera frame count')
rigid=[]
for f in cams['frames']:
 i=f['sample_index'];T=np.array(f['camera_to_world']);r=T[:3,:3]
 check(np.isfinite(T).all() and np.allclose(r.T@r,np.eye(3),atol=1e-6) and np.isclose(np.linalg.det(r),1) and np.allclose(T[3],[0,0,0,1]),f'camera rigid {i}')
 check(f['intrinsics']==inp[i]['intrinsics'] and f['source_index']==inp[i]['source_index'] and f['timestamp_ns']==inp[i]['timestamp_ns'],f'input identity/K {i}')
report['cameras']={'count':180,'validated':sum(f['valid'] for f in cams['frames']),'all_rigid_finite':True,'all_public_K_and_identity_preserved':True,'pose_convention':cams.get('pose_convention'),'camera108':frames[108]['camera_to_world']}
for i in idx: check(sha(I/f'rgb/{i:04d}.png')==inp[i]['rgb_sha256'],f'input RGB sha {i}')
# Current actual scene bounds and semantic ownership from fresh Blender inspection.
art=js(O/'final_artifact_inspection.json');geo=js(O/'final_geometry_audit.json');obj=js(R/'objects.json')['objects'];cols=js(R/'colliders.json');layout=js(R/'layout.json');oldlayout=js(R/'versions/v1/layout.json');inv=js(R/'analysis/object_inventory.json')
meshes={x['name']:x for x in art['meshes']};top={x['name']:x for x in geo['meshes']};owners={};ids={x['id'] for x in obj}
for x in obj:
 check(bool(x['evidence_frames']) and bool(x['provenance']) and bool(x['category']),f'object evidence {x["id"]}')
 for n in x['component_names']:
  check(n in meshes and n not in owners,f'ownership {n}');owners[n]=x['id'];check(top[n]['semantic_id']==x['id'],f'semantic_id {n}')
 pts=np.array([meshes[n]['bounds'] for n in x['component_names']]);lo=pts[:,0].min(0);hi=pts[:,1].max(0)
 check(np.allclose(hi-lo,x['dimensions'],atol=1e-5),f'dimensions {x["id"]}')
check(set(owners)==set(meshes),'unmapped meshes')
report['semantics']={'objects':len(obj),'mesh_components':len(meshes),'mapping_complete':set(owners)==set(meshes),'mirror_disks':len([x for x in obj if x['category']=='wall_mirror']),'notes':'Group relation labels are logical groups; reflected inventory not duplicated.'}
# All seat profiles fit inside measured XY circles, so positive clearance proves no body intersection.
seats=[]
for n,m in meshes.items():
 if n.endswith('__upholstered_seat') or n.startswith('south_side_seat_') and n.endswith('__seat'):
  a,b=np.array(m['bounds']);ctr=(a[:2]+b[:2])/2;rad=float(max(b[:2]-a[:2])/2);seats.append((owners[n],ctr,rad))
pairs=[{'objects':[a[0],b[0]],'body_clearance_m':float(np.linalg.norm(a[1]-b[1])-a[2]-b[2])} for a,b in itertools.combinations(seats,2)]
report['seat_clearance']={'count':len(seats),'minimum':min(pairs,key=lambda x:x['body_clearance_m']),'penetrating_pairs':[p for p in pairs if p['body_clearance_m']< -1e-5]}
check(not report['seat_clearance']['penetrating_pairs'],'seat intersections')
flat=[]
for c in cols['colliders']:
 check(c['object_id'] in ids,f'collider owner {c["id"]}')
 if c['enabled']:
  for part in c.get('parts',[c]): flat.append((c['id'],np.array(part['bounds_min']),np.array(part['bounds_max'])))
pr=cols['portals'][0];plo=np.array(pr['clear_bounds_min']);phi=np.array(pr['clear_bounds_max']);point=np.array([6.85,3.925,1]);overlap=lambda a,b,c,d: bool(np.all(np.minimum(b,d)-np.maximum(a,c)>1e-6))
report['portal']={'clear_prism':pr,'enabled_colliders_intersecting_prism':[n for n,a,b in flat if overlap(a,b,plo,phi)],'enabled_colliders_containing_initial_issue_point':[n for n,a,b in flat if np.all(point>=a)&np.all(point<=b)],'mesh_AABBs_intersecting_prism':[n for n,m in meshes.items() if overlap(np.array(m['bounds'][0]),np.array(m['bounds'][1]),plo,phi)]}
check(not report['portal']['enabled_colliders_intersecting_prism'] and not report['portal']['mesh_AABBs_intersecting_prism'],'portal clear prism')
report['supports']=[]
for oid in ['south_side_seat_0','south_side_seat_1','south_side_seat_2','reception_desk']:
 x=next(x for x in obj if x['id']==oid);ns=[n for n in x['component_names'] if '__leg_' in n or '__inferred_plinth' in n]
 report['supports'].append({'id':oid,'relation':x['relations'],'support_components':[{'name':n,'bounds':meshes[n]['bounds']} for n in ns]})
 check(bool(ns),f'missing support {oid}')
# GLB load, coordinate conversion, semantic extras, current actual triangles.
blob=read(R/'scene.glb');check(blob[:4]==b'glTF','GLB magic');ln,typ=struct.unpack_from('<II',blob,12);gd=json.loads(blob[20:20+ln]);nodes=[n for n in gd['nodes'] if 'mesh' in n]
check({n['name'] for n in nodes}==set(meshes),'GLB component names')
for n in nodes: check(n.get('extras',{}).get('semantic_id')==owners[n['name']],f'GLB semantic extras {n["name"]}')
reads.add(str(R/'scene.glb'));g=trimesh.load(str(R/'scene.glb'),force='scene',process=False)
report['glb']={'sha256':report['hashes']['scene.glb'],'geometry_count':len(g.geometry),'bounds':g.bounds.tolist(),'curved_backs':[],'finite_vertices':True,'bounds_mismatches':[]}
for node in g.graph.nodes_geometry:
 transform,key=g.graph[node];mesh=g.geometry[key];pts=trimesh.transform_points(mesh.vertices,transform);p=pts[:,[0,2,1]]*np.array([1,-1,1]);b=np.array([p.min(0),p.max(0)])
 check(np.isfinite(pts).all(),f'GLB finite {node}')
 if node in meshes and not np.allclose(b,meshes[node]['bounds'],atol=2e-5):report['glb']['bounds_mismatches'].append(node)
 if '__curved_back' in node:
  m=mesh.copy();m.merge_vertices();row={'name':node,'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'volume':float(m.volume)};report['glb']['curved_backs'].append(row);check(row['watertight'] and row['winding_consistent'] and row['volume']>0,f'GLB curved back {node}')
check(not report['glb']['bounds_mismatches'],'GLB/Blender world bounds')
# Read repair and evidence records; summaries do not treat author checks as fresh results.
repair=js(R/'author_repair_notes.json');measure=js(R/'analysis/author_repair/rgb_ray_plane_measurements.json');camcheck=js(R/'analysis/camera_checks.json');initial=js(O/'initial_review.json');visual=js(R/'analysis/paired_visual_inspection_v2.json')
report['initial_issue_ids']=[x['id'] for x in initial['issues']];report['author_dispositions']=repair['issues'];report['camera_landmark_rms']=[{'frame':x['sample_index'],'rms_pixels':x['rms_pixels']} for x in camcheck['check_pose_estimates']]
report['room_scale_unchanged']=layout['room']==oldlayout['room'];report['access_log_present']=bool(access);report['initial_record_history_caveat']=iterations.get('historical_note')
report['inspection_summary']=geo['summary'];report['source_depth_residuals']='N/A; no predicted/measured input depth in M1. Model Z used only for self-occlusion.'
(O/'final_record_audit.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');(O/'final_audit_paths_read.json').write_text(json.dumps(sorted(reads),indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['failures','hashes','budget','semantics','seat_clearance','portal','glb','inspection_summary']},indent=2))
