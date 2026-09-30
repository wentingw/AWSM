"""Author technical checks; no rendering, input full-pass, or independent certification."""
import json,hashlib,itertools
from pathlib import Path
import numpy as np,trimesh
R=Path(__file__).resolve().parents[2];I=R.parents[1]/'inputs/M1';J=lambda n:json.loads((R/n).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
objects=J('objects.json')['objects'];by={o['id']:o for o in objects};C=J('cameras.json');P=json.loads((I/'packet.json').read_text());manifest=J('modelling_manifest.json')
assert len(C['frames'])==180 and sha(R/'cameras.json')==sha(R/'versions/v1/cameras.json')
for c,p in zip(C['frames'],P['frames']):
 for k in ['sample_index','source_index','timestamp_ns','intrinsics']:assert c[k]==p[k],(k,c['sample_index'])
 T=np.array(c['camera_to_world']);assert T.shape==(4,4) and np.isfinite(T).all() and np.allclose(T[3],[0,0,0,1]) and np.allclose(T[:3,:3].T@T[:3,:3],np.eye(3),atol=1e-6) and abs(np.linalg.det(T[:3,:3])-1)<1e-6
 assert c['valid'] is False
assert manifest['input_packet_sha256']==sha(I/'packet.json')
# Verify world component ownership and references, including exported mesh extras.
components=[n for o in objects for n in o['component_names']];assert len(components)==len(set(components))
inspection=J('checks/artifact_inspection.json');assert set(components)=={r['name'] for r in inspection['meshes']}
for o in objects:
 for relation in ['supported_by','attached_to','planted_in','suspended_from']:
  if relation in o['relations']:assert o['relations'][relation] in by,(o['id'],relation)
# Full GLB mesh winding and degeneracies; foliage/profile boundaries are legitimate modeled sheets.
scene=trimesh.load(R/'scene.glb',force='scene',process=False);curved=[];all_bad=[]
for name,g in scene.geometry.items():
 if not g.is_winding_consistent:all_bad.append(name)
 if 'curved_back' in name:
  g=g.copy();g.merge_vertices();row={'name':name,'watertight':bool(g.is_watertight),'winding_consistent':bool(g.is_winding_consistent),'degenerate_triangles':int((g.area_faces<1e-12).sum()),'positive_volume':bool(g.volume>0)};curved.append(row)
  assert row['watertight'] and row['winding_consistent'] and row['degenerate_triangles']==0 and row['positive_volume'],row
assert len(curved)==8
assert not all_bad,all_bad
# Physical body clearance using known exact max cylindrical radii, not group bounding boxes.
L=J('layout.json');seats=[]
for group in L['seating_groups']:
 gx,gy=group['center']
 for j,(dx,dy) in enumerate(L['seat_offsets']):seats.append((f"{group['id']}_seat_{j+1}",np.array([gx+dx,gy-dy*group['facing_y']]),.47))
for j,xy in enumerate(L['side_seats_xy']):seats.append(('south_side_seat_'+str(j),np.array(xy),.45))
pairs=[]
for a,b in itertools.combinations(seats,2):
 clearance=float(np.linalg.norm(a[1]-b[1])-a[2]-b[2]);pairs.append({'objects':[a[0],b[0]],'body_clearance_m':clearance});assert clearance>=-1e-6,(a[0],b[0],clearance)
# Enterable south recess: test the full clear prism against every enabled proxy except supporting floor.
coll=J('colliders.json');parts=[]
for c in coll['colliders']:
 assert c['object_id'] in by
 if c['enabled']:
  for p in c.get('parts',[c]):parts.append((c['id'],np.array(p['bounds_min']),np.array(p['bounds_max'])))
lo=np.array([6.2,3.55,.02]);hi=np.array([7.85,4.3,2.55]);hits=[n for n,a,b in parts if (np.minimum(b,hi)-np.maximum(a,lo)>1e-5).all()];assert hits==[],hits
point=np.array([6.85,3.925,1]);hits_point=[n for n,a,b in parts if (point>a).all() and (point<b).all()];assert not hits_point
closed=np.array([6.88,10.075,1]);assert 'north_metal_door' in [n for n,a,b in parts if (closed>a).all() and (closed<b).all()]
# Support contact at floor; seat feet extend to0; insert is .016m thick.
for name in ['south_side_seat_0','south_side_seat_1','south_side_seat_2','reception_desk']:assert by[name]['bbox_min'][2]<=.016+1e-6,name
ledger=J('checks/paired_ledger.json');complete=[x for x in ledger if x['status']=='COMPLETE'];assert len(complete)==20
fixed=[33,61,74,82,91,100,108,118,129,155]
for v in [1,2]:
 rp=J(f'checks/v{v}/paired_report.json');assert rp['indices']==fixed and rp['status']=='COMPLETE'
 assert rp['model_sha256']==sha(R/f'versions/v{v}/scene.blend')
 for row in rp['frames']:
  i=row['sample_index'];assert row['rgb_sha256']==sha(R/f'checks/v{v}/{i:04d}_rgb.png') and row['depth_sha256']==sha(R/f'checks/v{v}/{i:04d}_depth.npz')
assert sha(R/'scene.blend')==sha(R/'versions/v2/scene.blend')
report={'status':'PASS','role':'author technical verification only; independent review pending','model_sha256':sha(R/'scene.blend'),'glb_sha256':sha(R/'scene.glb'),'semantic_objects':len(objects),'semantic_components':len(components),'camera_file_byte_identical_to_v1':True,'camera_entries':180,'unvalidated_camera_entries':180,'input_identity_K_rigidity':'PASS','curved_back_GLB_meshes':curved,'GLB_inconsistent_winding':all_bad,'minimum_seat_body_clearance_m':min(r['body_clearance_m'] for r in pairs),'all_seat_pairs':pairs,'open_portal_clear_prism':{'min':lo.tolist(),'max':hi.tolist(),'blocking_colliders':hits},'original_review_probe_blocking_colliders':hits_point,'north_door_closed_proxy':'PASS','supports':'PASS, hidden support shape inferred','full_versions':2,'actual_paired_views':20,'supplemental_views':0,'input_full180_bvh_passes':0,'M1_depth_reference':'N/A; RGB-only'}
(R/'checks/author/technical_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['all_seat_pairs','curved_back_GLB_meshes']},indent=2))
