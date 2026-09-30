"""Author static validation, no render or input-camera depth pass."""
import bpy,bmesh,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(R/'scene.blend'));deps=bpy.context.evaluated_depsgraph_get();closed=[];negative=[];degenerate=[];meshes={}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(deps);m=ev.to_mesh();m.calc_loop_triangles();v=np.array([ev.matrix_world@x.co for x in m.vertices]);t=np.array([x.vertices for x in m.loop_triangles]);a=v[t];areas=np.linalg.norm(np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]),axis=1)/2;volume=float(np.einsum('ij,ij->i',a[:,0],np.cross(a[:,1],a[:,2])).sum()/6);bm=bmesh.new();bm.from_mesh(m);isclosed=all(e.is_manifold for e in bm.edges);bm.free();meshes[o.name]={'bounds':[v.min(0).tolist(),v.max(0).tolist()],'closed':isclosed,'signed_volume_m3':volume,'min_triangle_area_m2':float(areas.min()),'near_zero_faces':int((areas<1e-12).sum())}
 if isclosed:closed.append(o.name)
 if isclosed and volume<=0:negative.append(o.name)
 if np.any(areas<1e-12):degenerate.append(o.name)
 ev.to_mesh_clear()
requests=json.loads((R/'analysis/rod_requests.json').read_text());endpoint=[]
for r in requests:
 o=bpy.data.objects[r['name']];v=np.array([x.co for x in o.data.vertices]);zmin=v[:,2].min();zmax=v[:,2].max();a=np.array(o.matrix_world@Vector((0,0,float(zmin))));b=np.array(o.matrix_world@Vector((0,0,float(zmax))));err=max(np.linalg.norm(a-r['a']),np.linalg.norm(b-r['b']));endpoint.append({'name':r['name'],'max_endpoint_error_m':float(err)})
C=json.loads((R/'colliders.json').read_text());p=C['portals'][0];xmin=Lx=p['plane_x']-.3;xmax=p['plane_x']+.4;y0,y1=p['y_range'];z0,z1=p['z_range'];probe=[xmin,xmax,y0+.025,y1-.025,z0+.025,z1-.025];blockers=[]
for c in C['colliders']:
 if c['type']!='AABB':continue
 lo,hi=np.array(c['bounds']);qlo=np.array([xmin,y0+.025,z0+.025]);qhi=np.array([xmax,y1-.025,z1-.025]);overlap=np.minimum(hi,qhi)-np.maximum(lo,qlo)
 if (overlap>1e-6).all():blockers.append(c)
# All seat solid footprints are separated by common halfplanes; polygon intersection area validates.
def clip(poly,n,d):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  da=np.dot(a,n)-d;db=np.dot(b,n)-d
  if da<=0:out.append(a)
  if (da<0)!=(db<0):out.append((np.array(a)+(np.array(b)-a)*da/(da-db)).tolist())
 return out
def intersect(pa,pb):
 p=pa
 for a,b in zip(pb,pb[1:]+pb[:1]):
  a=np.array(a);b=np.array(b);n=np.array([b[1]-a[1],a[0]-b[0]]);p=clip(p,n,float(np.dot(n,a)))
  if not p:return 0.
 return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1])))/2
seats=[c for c in C['colliders'] if c['type']=='convex_prism'];overlaps=[]
for i,a in enumerate(seats):
 for b in seats[i+1:]:
  area=intersect(a['polygon_xy'],b['polygon_xy'])
  if area>1e-9:overlaps.append({'a':a['id'],'b':b['id'],'intersection_area_m2':area})
cam=json.loads((R/'cameras.json').read_text());packet=json.loads((R.parent.parent/'inputs/M2/packet.json').read_text());manifest=json.loads((R/'modelling_manifest.json').read_text());X=np.array(manifest['model_from_input']);camera_errors=[float(np.max(np.abs(np.array(c['camera_to_world'])-X@np.array(f['camera_to_world'])))) for c,f in zip(cam['frames'],packet['frames'])]
report={'role':'author static validation; not independent review','scene_sha256':hashlib.sha256((R/'scene.blend').read_bytes()).hexdigest(),'meshes':meshes,'closed_components':len(closed),'negative_closed_components':negative,'degenerate_components':degenerate,'rod_endpoint_checks':endpoint,'maximum_rod_endpoint_error_m':max(r['max_endpoint_error_m'] for r in endpoint),'passage_clearance':{'tested_box':[xmin,xmax,y0+.025,y1-.025,z0+.025,z1-.025],'blocking_proxy_intersections':blockers,'nominal_clear_width_m':y1-y0,'nominal_clear_height_m':z1-z0,'scope':'static portal aperture traversal into bounded inferred vestibule; no claim of full navigation simulation'},'seat_solid_intersections':overlaps,'camera_max_error':max(camera_errors),'camera_count':len(cam['frames']),'scale':manifest['geometry_scale'],'status':'PASS' if not negative and not degenerate and not blockers and not overlaps and max(camera_errors)<1e-10 and max(r['max_endpoint_error_m'] for r in endpoint)<1e-5 else 'FAIL'}
(R/'checks/author_geometry_audit.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['meshes','rod_endpoint_checks']})
