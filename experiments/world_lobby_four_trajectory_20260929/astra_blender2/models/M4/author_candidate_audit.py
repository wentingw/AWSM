"""Author audit of declared objects/colliders/cameras and measured geometry. No render/BVH."""
import json,itertools,numpy as np,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;I=R.parent.parent/'inputs/M4';load=lambda n:json.load(open(R/n));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
L=load('layout.json');ob=load('objects.json')['objects'];co=load('colliders.json');ins=load('checks/artifact_inspection.json');cams=load('cameras.json');p=json.load(open(I/'packet.json'));m=load('modelling_manifest.json')
components=[n for r in ob for n in r['component_names']];meshes={r['name']:r for r in ins['meshes']};assert len(set(components))==len(components) and set(components)==set(meshes)
assert all(a['sample_index']==b['sample_index'] and a['camera_to_world']==b['camera_to_world'] and a['intrinsics']==b['intrinsics'] for a,b in zip(cams['frames'],p['frames'])) and len(cams['frames'])==180
assert np.array_equal(m['model_from_input'],np.eye(4)) and m['geometry_scale']==1
penetrations=[];clearances=[]
for a,b in itertools.combinations(L['chairs'],2):
 clearance=float(np.linalg.norm(np.array(a['center'][:2])-b['center'][:2])-a['radius']-b['radius']);clearances.append(dict(a=a['id'],b=b['id'],conservative_clearance_m=clearance))
 if clearance< -1e-5:penetrations.append(clearances[-1])
for a in L['tables']:
 for b in L['chairs']:
  clearance=float(np.linalg.norm(np.array(a['center'][:2])-b['center'][:2])-max(a['radii'])-b['radius']);clearances.append(dict(a=a['id'],b=b['id'],conservative_clearance_m=clearance))
  if clearance< -1e-5:penetrations.append(clearances[-1])
portal_rows=[]
for portal in co['portals']:
 lo,hi=np.array(portal['opening_bounds']);obstacles=[];closed_leaves=[]
 for obj in co['colliders']:
  for part in obj['parts']:
   a,b=np.array(part['bounds']);intersect=np.minimum(b,hi)-np.maximum(a,lo)
   if np.all(intersect>1e-5):
    (closed_leaves if part['state']=='door_leaf_closed' else obstacles).append(part['component_name'])
 portal_rows.append(dict(id=portal['id'],static_obstacles=obstacles,closed_leaf_obstacles=closed_leaves,opening_bounds=portal['opening_bounds'],pass_without_leaves=not obstacles,interpretation='Geometric proxy aperture test, not dynamics or a claim about unknown destination'))
supports=[]
for r in ob:
 if r['id']=='reception_desk' or r['id'].startswith(('seat_','coffee_table_','side_table_')):
  z=min(meshes[n]['bounds'][0][2] for n in r['components']);supports.append(dict(id=r['id'],lowest_world_z=z,inlay_top=.011,gap_m=z-.011))
report=dict(role='AUTHOR validation, not independent review',version=L['version'],model_sha256=sha(R/'scene.blend'),glb_sha256=sha(R/'scene.glb'),semantic_objects=len(ob),semantic_components=len(components),component_names_coverage='PASS',camera_count=180,exact_packet_cameras=True,scale=1,model_from_input='identity',solid_furniture_penetrations=penetrations,minimum_conservative_furniture_clearance_m=min(x['conservative_clearance_m'] for x in clearances),support_checks=supports,portal_checks=portal_rows,limitations=['Compound boxes approximate curved/concave objects; no dynamic physics simulation','Closed source doors block current passage; removing named leaf parts frees aperture; exterior/interior destinations unknown','Foliage noncolliding; open leaf sheets intentional'])
(R/'checks/author_candidate_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
assert not penetrations
assert all(x['pass_without_leaves'] for x in portal_rows)
assert all(abs(x['gap_m'])<1e-5 for x in supports)
