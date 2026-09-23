"""Read-only structural verification of this model after clean review fixes."""
import bpy,bmesh,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector,Matrix
O=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(O/'scene.blend'));report={'revision':5,'read_only_scene_check':True};seats=[]
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob.name.startswith('lounge_') and ob.name.endswith('.seat'):seats.append(ob)
rows=[];seat_rows=[]
for a in seats:
 for b in seats:
  if a.name>=b.name or a.name.split('_')[1]!=b.name.split('_')[1]:continue
  d=(a.location.xy-b.location.xy).length;seat_rows.append({'a':a.name,'b':b.name,'horizontal_clearance_m':d-a.dimensions.x/2-b.dimensions.x/2})
 for prefix in ['lounge_A','lounge_B']:
  if not a.name.startswith(prefix):continue
  table=bpy.data.objects[prefix+'_table.top'];d=(a.location.xy-table.location.xy).length;rows.append({'table':prefix+'_table','seat':a.name.rsplit('.',1)[0],'horizontal_clearance_m':d-a.dimensions.x/2-table.dimensions.x/2})
report['seat_table_clearances']=rows;report['min_seat_table_clearance_m']=min(r['horizontal_clearance_m'] for r in rows);report['min_seat_seat_clearance_m']=min(r['horizontal_clearance_m'] for r in seat_rows);assert report['min_seat_table_clearance_m']>0;assert report['min_seat_seat_clearance_m']>0
ob=bpy.data.objects['reception_desk.faceted_counter'];bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update();report['reception_desk']={'signed_volume_m3':bm.calc_volume(signed=True),'all_edges_manifold':all(e.is_manifold for e in bm.edges),'top_normals':[list(f.normal) for f in bm.faces if f.calc_center_median().z>.96],'bottom_normals':[list(f.normal) for f in bm.faces if f.calc_center_median().z<.09]};assert report['reception_desk']['signed_volume_m3']>0;assert report['reception_desk']['all_edges_manifold'];bm.free()
colliders=json.load(open(O/'colliders.json'))['colliders']
def inside(c,p):return all(a-1e-7<=v<=b+1e-7 for a,v,b in zip(c['bounds']['min'],p,c['bounds']['max']))
report['fixed_window_portal_blockers']=[c for c in colliders if c['object_id']=='window_wall' and inside(c,[-4.45,12.04,1])];report['closed_door_sample_blockers']=[c for c in colliders if c['object_id']=='glass_entry_double_door' and inside(c,[-4.34,12.04,1])];assert not report['fixed_window_portal_blockers'];assert any(c['state']=='closed_leaf' for c in report['closed_door_sample_blockers'])
cs=json.load(open(O/'cameras.json'));pose_err=0
for c in cs['cameras']:
 target=Matrix(c['c2w_model'])@Matrix.Diagonal((1,-1,-1,1));actual=bpy.data.objects['input_%03d'%c['frame_id']].matrix_world;pose_err=max(pose_err,max(abs(actual[r][k]-target[r][k]) for r in range(4) for k in range(4)))
report['max_camera_matrix_error']=pose_err;report['saved_blend_pixel_aspect']=[bpy.context.scene.render.pixel_aspect_x,bpy.context.scene.render.pixel_aspect_y];expected=cs['cameras'][0]['K'][1][1]/cs['cameras'][0]['K'][0][0];assert abs(report['saved_blend_pixel_aspect'][0]/report['saved_blend_pixel_aspect'][1]-expected)<1e-7
raw=(O/'scene.glb').read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);errors=[]
for ca in g['cameras']:
 if not ca.get('name','').startswith('input_'):continue
 c=cs['cameras'][int(ca['name'].split('_')[-1])];pers=ca['perspective'];fy=c['height']/(2*math.tan(pers['yfov']/2));fx=c['width']/(2*math.tan(pers['yfov']/2)*pers['aspectRatio']);errors.append([fx-c['K'][0][0],fy-c['K'][1][1]])
report['max_glb_intrinsic_error_px']=max(abs(e) for row in errors for e in row);assert report['max_glb_intrinsic_error_px']<1e-7
report['camera_json_sha256']=hashlib.sha256((O/'cameras.json').read_bytes()).hexdigest();report['camera_json_unchanged_from_review']=report['camera_json_sha256']==json.load(open(O/'independent_review/review.json'))['artifact_hashes']['cameras.json'];assert report['camera_json_unchanged_from_review']
json.dump(report,open(O/'final_geometry_validation.json','w'),indent=2);print(json.dumps({k:v for k,v in report.items() if k not in ['seat_table_clearances','closed_door_sample_blockers']},indent=2))
