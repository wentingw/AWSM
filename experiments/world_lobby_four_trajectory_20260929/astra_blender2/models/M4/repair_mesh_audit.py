"""Author mesh validation during construction, not independent review. No renders/BVH."""
audit={'role':'revision author construction validation','version':L['version'],'closed_negative_volume':[],'inconsistent_winding':[],'degenerate_triangles':[],'open_surface_components':[],'cleanup':[]}
for o in S.objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 # Recalculate only closed solid normals, preserving explicitly open botanical surfaces.
 closed=all(e.is_manifold for e in bm.edges)
 if closed:
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
  bm.to_mesh(o.data)
  vol=bm.calc_volume(signed=True)
  if vol<=0:audit['closed_negative_volume'].append({'name':o.name,'volume':vol})
 else:audit['open_surface_components'].append(o.name)
 bad=sum(1 for e in bm.edges if e.is_manifold and not e.is_contiguous)
 if bad:audit['inconsistent_winding'].append({'name':o.name,'edges':bad})
 bm.free();o.data.calc_loop_triangles();bad=0
 for t in o.data.loop_triangles:
  a,b,c=[o.data.vertices[j].co for j in t.vertices]
  if (b-a).cross(c-a).length*.5<1e-12:bad+=1
 if bad:audit['degenerate_triangles'].append({'name':o.name,'count':bad})
json.dump(audit,open(R/f'checks/author_mesh_audit_v{L["version"]}.json','w'),indent=2)
assert not audit['closed_negative_volume'],audit['closed_negative_volume']
assert not audit['inconsistent_winding'],audit['inconsistent_winding']
assert not audit['degenerate_triangles'],audit['degenerate_triangles']
print('AUTHOR_MESH_VALIDATION_PASS',flush=True)
