"""Read-only M2 independent review measurements. Never save or render the scene."""
import bpy, json, hashlib, itertools, struct
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

OUT=Path(__file__).resolve().parent
MODEL=OUT.parent
BASE=MODEL.parent.parent
READ=[]
def read(path):
    path=Path(path); READ.append(str(path)); return path.read_bytes()
def js(path): return json.loads(read(path))
packet=js(BASE/'inputs/M2/packet.json')
manifest=js(MODEL/'modelling_manifest.json')
cameras=js(MODEL/'cameras.json')
objects=js(MODEL/'objects.json')['objects']
colliders=js(MODEL/'colliders.json')['colliders']
layout=js(MODEL/'layout.json')
access=js(MODEL/'input_access_log.json')
M=np.array(manifest['model_from_input'])
scene_hash=hashlib.sha256(read(MODEL/'scene.blend')).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(MODEL/'scene.blend'))
scene=bpy.context.scene
deps=bpy.context.evaluated_depsgraph_get()
out={'model_sha256':scene_hash}
out['camera_checks']={
    'count':len(cameras['frames']),
    'sample_ids_complete':sorted(f['sample_index'] for f in cameras['frames'])==list(range(180)),
    'max_transform_entry_error':max(float(np.max(np.abs(np.array(g['camera_to_world'])-M@np.array(f['camera_to_world'])))) for f,g in zip(packet['frames'],cameras['frames'])),
    'intrinsics_max_error':max(float(np.max(np.abs(np.array(g['intrinsics'])-np.array(f['intrinsics'])))) for f,g in zip(packet['frames'],cameras['frames'])),
    'source_and_timestamp_match':all((f['source_index'],f['timestamp_ns'])==(g['source_index'],g['timestamp_ns']) for f,g in zip(packet['frames'],cameras['frames'])),
    'transform_det':float(np.linalg.det(M[:3,:3])),
    'transform_orthogonality_max_error':float(np.max(np.abs(M[:3,:3].T@M[:3,:3]-np.eye(3)))),
    'stored_blend_camera_frame0_axis_conversion_error':float(np.max(np.abs(np.array(scene.camera.matrix_world)-np.array(cameras['frames'][0]['camera_to_world'])@np.diag([1,-1,-1,1])))),
    'lens_mm':scene.camera.data.lens,'sensor_width_mm':scene.camera.data.sensor_width,'sensor_fit':scene.camera.data.sensor_fit,
    'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y],
}
out['render_settings']={'engine':scene.render.engine,'device':scene.cycles.device,'samples':scene.cycles.samples,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'resolution_percentage':scene.render.resolution_percentage,'threads':scene.render.threads,'units_scale':scene.unit_settings.scale_length}
mesh_objects={o.name:o for o in scene.objects if o.type=='MESH'}
by_name={}
duplicates={}
for name,o in mesh_objects.items():
    ev=o.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles()
    xyz=np.array([ev.matrix_world@v.co for v in me.vertices])
    mn=xyz.min(0);mx=xyz.max(0)
    by_name[name]={'bounds':[mn.tolist(),mx.tolist()],'semantic_id':o.get('semantic_id'),'category':o.get('category'),'vertices':len(xyz),'triangles':len(me.loop_triangles),'hide_render':o.hide_render}
    rows=np.round(xyz,6)
    rows=rows[np.lexsort((rows[:,2],rows[:,1],rows[:,0]))]
    signature=hashlib.sha256(rows.tobytes()).hexdigest()
    duplicates.setdefault(signature,[]).append(name)
    ev.to_mesh_clear()
mapped=[n for rec in objects for n in rec['component_names']]
out['semantic_mapping']={'semantic_records':len(objects),'mesh_count':len(mesh_objects),'triangles':sum(v['triangles'] for v in by_name.values()),'unmapped_meshes':sorted(set(mesh_objects)-set(mapped)),'missing_components':sorted(set(mapped)-set(mesh_objects)),'components_mapped_multiple_times':sorted(n for n in set(mapped) if mapped.count(n)>1),'property_mismatches':[n for rec in objects for n in rec['component_names'] if n in by_name and by_name[n]['semantic_id']!=rec['id']],'empty_evidence':[rec['id'] for rec in objects if not rec.get('evidence_sample_ids')],'invalid_evidence':[rec['id'] for rec in objects if any(i<0 or i>179 for i in rec['evidence_sample_ids'])]}
out['duplicate_world_vertex_sets']=[v for v in duplicates.values() if len(v)>1]
out['record_bounds_errors']=[]
for rec in objects:
    vals=[by_name[n]['bounds'] for n in rec['component_names'] if n in by_name]
    actual=np.array([np.min(np.array(vals)[:,0,:],axis=0),np.max(np.array(vals)[:,1,:],axis=0)])
    recorded=np.array([rec['bounds_model_m']['min'],rec['bounds_model_m']['max']])
    err=float(np.max(np.abs(actual-recorded)))
    if err>1e-5: out['record_bounds_errors'].append({'id':rec['id'],'max_error_m':err})
out['collider_mapping']={'count':len(colliders),'missing_object_ids':[c['object_id'] for c in colliders if c['object_id'] not in {r['id'] for r in objects}],'missing_components':[n for c in colliders for n in c['component_names'] if n not in mesh_objects],'door_colliders':[c for c in colliders if 'door' in c['object_id']],'wall_collider_types':{c['object_id']:c['shape'] for c in colliders if c['object_id'].startswith('wall_')}}
out['selected_bounds']={n:d for n,d in by_name.items() if ('wall_near_end__joint' in n or 'wall_near_end__panel_000' in n or 'door_side_0__' in n or n.endswith('__padded_seat'))}
seats=[o for n,o in mesh_objects.items() if n.endswith('__padded_seat')]
out['seat_cushion_intersections']=[]
for a,b in itertools.combinations(seats,2):
    ba=np.array(by_name[a.name]['bounds']);bb=np.array(by_name[b.name]['bounds'])
    overlap=np.minimum(ba[1],bb[1])-np.maximum(ba[0],bb[0])
    if np.all(overlap>0):
        treea=BVHTree.FromObject(a,deps);treeb=BVHTree.FromObject(b,deps)
        # All authored cushions have identity rotation/scale, local origin at their centre.
        # Transform evaluated vertices explicitly for an unambiguous world-space overlap check.
        def tree(obj):
            ev=obj.evaluated_get(deps);me=ev.to_mesh()
            v=[ev.matrix_world@x.co for x in me.vertices];f=[list(p.vertices) for p in me.polygons]
            t=BVHTree.FromPolygons(v,f);ev.to_mesh_clear();return t
        pairs=tree(a).overlap(tree(b))
        if pairs:
            ra=(ba[1,0]-ba[0,0])/2;rb=(bb[1,0]-bb[0,0])/2
            dist=float(np.linalg.norm((ba.mean(0)-bb.mean(0))[:2]))
            out['seat_cushion_intersections'].append({'a':a.name,'b':b.name,'triangle_or_polygon_overlap_pairs':len(pairs),'horizontal_circle_penetration_m':float(ra+rb-dist),'note':'Circle penetration applies to these circular upright cushion meshes; triangle overlap independently confirms intersection.'})
out['support_gaps']=[]
for rec in objects:
    for relation in rec.get('spatial_relations',[]):
        if relation['relation']=='supported_by':
            target=next((r for r in objects if r['id']==relation['target']),None)
            if target:
                gap=rec['bounds_model_m']['min'][2]-target['bounds_model_m']['max'][2]
                if gap>.01:out['support_gaps'].append({'id':rec['id'],'support':target['id'],'vertical_bound_gap_m':gap})
out['targeted_rays']=[]
for name,origin,direction,length in [
    ('mirror_wall_open_passage_candidate',(3.0,-.42,1.0),(1,0,0),1.2),
    ('mirror_wall_other_metal_door',(3.0,6.24,1.0),(1,0,0),1.2),
    ('near_end_upper_surface',(0,0,3.0),(0,-1,0),4.0),
]:
    hit,loc,normal,index,obj,mat=scene.ray_cast(deps,Vector(origin),Vector(direction),distance=length)
    out['targeted_rays'].append({'name':name,'origin':origin,'direction':direction,'max_distance':length,'hit':hit,'object':obj.name if obj else None,'point':list(loc) if hit else None})
out['projections_640']={}
selected=['column_facade','table_far','table_near','grass_wall_mid','door_side_0','mirror_cluster','reception_desk','planter_yellow_left','planter_yellow_right']
for i in [0,45,66,75,90,135,179]:
    f=cameras['frames'][i];C=np.linalg.inv(np.array(f['camera_to_world']));K=np.array(f['intrinsics'])*.5;K[2,2]=1
    result={}
    for rec in objects:
        if rec['id'] in selected:
            point=C@np.r_[rec['centroid_m'],1];uv=K@point[:3];result[rec['id']]={'centroid_uv':(uv[:2]/uv[2]).tolist(),'z':float(point[2])}
    out['projections_640'][str(i)]=result
out['materials']={}
for name in ['polished black inset','true circular reflective mirror','overexposed frosted exterior glazing']:
    mat=bpy.data.materials.get(name);p=mat.node_tree.nodes.get('Principled BSDF')
    out['materials'][name]={'roughness':p.inputs['Roughness'].default_value,'metallic':p.inputs['Metallic'].default_value,'emission_strength':p.inputs['Emission Strength'].default_value}
out['depth_samples']=[]
for i in [0,15,21,45,90,135,167,175,179]:
    path=BASE/f'inputs/M2/geometry/{i:04d}.npz'
    raw=read(path)
    with np.load(path) as z:
        depth=z['depth_z_m'];valid=z['valid_mask'] & np.isfinite(depth)&(depth>0)
        out['depth_samples'].append({'frame':i,'shape':list(depth.shape),'intrinsics':z['intrinsics'].tolist(),'pose_packet_error':float(np.max(np.abs(z['input_camera_to_world']-np.array(packet['frames'][i]['camera_to_world'])))),'sha256_matches_packet':hashlib.sha256(raw).hexdigest()==packet['frames'][i]['geometry_sha256'],'valid_fraction':float(valid.mean()),'p10_median_p90_m':np.quantile(depth[valid],[.1,.5,.9]).tolist()})
allowed=[str(BASE/'inputs/M2'),str(MODEL),str(BASE/'configs/modelling_contract.md'),str(BASE/'configs/review_contract.md'),str(BASE/'tools/inspect_scene.py'),str(BASE/'tools/raycast_scene.py'),str(BASE/'tools/depth_math.py')]
out['author_access_log_out_of_scope_entries']=[x for x in access['intentional_read_paths'] if not any(str(x).startswith(y) for y in allowed)]
out['packet_hash_matches_manifest']=hashlib.sha256(read(BASE/'inputs/M2/packet.json')).hexdigest()==manifest['input_packet_sha256']
raw=read(MODEL/'scene.glb')
magic,version,total=struct.unpack_from('<4sII',raw);chunklen,chunktype=struct.unpack_from('<II',raw,12);gltf=json.loads(raw[20:20+chunklen])
out['glb_container']={'magic':magic.decode(),'version':version,'declared_bytes':total,'actual_bytes':len(raw),'node_count':len(gltf.get('nodes',[])),'mesh_count':len(gltf.get('meshes',[])),'external_uris':[x.get('uri') for k in ['buffers','images'] for x in gltf.get(k,[]) if x.get('uri') and not x['uri'].startswith('data:')]}
out['scene_hash_after']=hashlib.sha256(read(MODEL/'scene.blend')).hexdigest()
out['input_files_read']=sorted(set(READ))
(OUT/'review_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['projections_640','selected_bounds','collider_mapping','input_files_read']},indent=2))

