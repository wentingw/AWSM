from pathlib import Path
import json,shutil
R=Path(__file__).parent
for f in ['colliders.json','analysis/rod_requests.json','checks/author_geometry_audit.json','checks/author_geometry_audit.log','analysis/revision_evidence.json']:
 d=R/'versions/v2'/f;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/f,d)
s=(R/'build_scene.py').read_text()
s=s.replace("loc=(mid,start[1]+.10,(bottom+cz)/2) if horizontal else", "back_offset=-.10 if id in ['near_wall','recess_return'] else .10\n  loc=(mid,start[1]+back_offset,(bottom+cz)/2) if horizontal else")
s=s.replace("(w,.9,.045),'dark',.025)","(w,.9,.045),'dark',0)")
# Seat tops/base smooth only on curved vertical sides; planar caps remain flat.
s=s.replace("return mesh(suffix,vv,ff,mat)\nfor s in L['seats']:","o=mesh(suffix,vv,ff,mat)\n for p in o.data.polygons:\n  if len(p.vertices)==4 and abs(p.normal.z)<.1:p.use_smooth=True\n return o\nfor s in L['seats']:")
# Shader floor pattern uses a packed procedural raster to preserve appearance in GLB.
a=s.index('# Inferred regular brass dashes');b=s.index('for key in [',a)
s=s[:a]+'''# Inferred brass-dash material generated from scratch and packed/exportable; no input textures.
nt=M['blackfloor'].node_tree
width,height=512,2048;xx,yy=np.meshgrid((np.arange(width)+.5)/width,(np.arange(height)+.5)/height);periods=np.array(L['carpet']['dimensions'][:2])*14
mask=((xx*periods[0])%1<.23)&((yy*periods[1])%1<.56)
rgba=np.empty((height,width,4),np.float32);rgba[:]=[.014,.012,.01,1];rgba[mask]=[.17,.125,.055,1]
im=bpy.data.images.new('inferred_floor_dashes',width=width,height=height,alpha=True);im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/'floor_pattern.png');im.file_format='PNG';im.save();im.pack();texf=nt.nodes.new('ShaderNodeTexImage');texf.image=im;nt.links.new(texf.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
''' + s[b:]
s=s.replace("group('floor_inset','floor_finish',[33,91,100,108,155]);box('inset',L['carpet']['center'],L['carpet']['dimensions'],'blackfloor')", "group('floor_inset','floor_finish',[33,91,100,108,155]);o=box('inset',L['carpet']['center'],L['carpet']['dimensions'],'blackfloor')\nfor face in o.data.polygons:\n for index in face.loop_indices:\n  v=o.data.vertices[o.data.loops[index].vertex_index].co;o.data.uv_layers.active.data[index].uv=(v.x/L['carpet']['dimensions'][0]+.5,v.y/L['carpet']['dimensions'][1]+.5)")
(R/'build_scene.py').write_text(s)
L=json.loads((R/'layout.json').read_text());L['version']=3;L['notes'].append('V3 geometry only removes desk counter bevel and moves near-wall/recess-return backing behind visible panel faces. Lamp triangulations unchanged from v2: distant correspondences remain LIMITED. Floor texture now packed for GLB.');(R/'layout.json').write_text(json.dumps(L,indent=2)+'\n')
m=json.loads((R/'modelling_manifest.json').read_text());m.update(revisions=3,input_bvh_pass_count=2);(R/'modelling_manifest.json').write_text(json.dumps(m,indent=2)+'\n')
changes=[{'parameter':'reception_desk counter bevel','before':.025,'after':0,'frames':[33,100,108,118,129],'rgb_regions':[[575,443,678,465],[920,580,1080,780],[1080,530,1280,700],[1080,510,1280,650],[919,568,1014,594]],'reason':'V2 author geometry audit finds near-zero triangles from bevel wider than half the 0.045m counter thickness. Top plane and counter dimensions unchanged.','residuals':'analysis/revision_evidence.json reception/desk regions','provenance':'technical topology correction'}, {'parameter':'near_wall and recess_return structural backing offset along Y','before':.10,'after':-.10,'frames':[61,74,82,91],'rgb_regions':[[0,90,285,455],[0,0,300,600],[350,270,520,690],[390,100,665,245]],'reason':'V2 actual comparison shows dark backing covering finish on the room-facing +Y side. Place behind panels, maintaining continuous seams.','residuals':'analysis/revision_evidence.json near_wall / wall_recess / mirror wall regions','provenance':'inferred thickness placement; observed panel finish remains same plane'}, {'parameter':'seat side shading','before':'all faceted','after':'smooth vertical quad normals, flat top/bottom','frames':[33,61,129,155],'reason':'preserve observed curved upholstery while keeping clipped solids; no position/dimension change'}, {'parameter':'floor pattern representation','before':'procedural nodes unsupported by GLB','after':'same14/m dash formula in packed512x2048 texture with explicit XY UV','frames':[33,91,100,108,129],'reason':'Keep floor appearance portable; no geometry or depth changes'}]
(R/'analysis/v3_changes.json').write_text(json.dumps(changes,indent=2)+'\n')
