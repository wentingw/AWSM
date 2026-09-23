"""Audit imported WorldLobby USD materials, glass and window occlusion.

This script is intentionally read-only with respect to the source USD.  It
creates a compact JSON report useful for deciding whether Cycles RGB is a
credible appearance target.
"""
import bpy, json, argparse
from pathlib import Path
from mathutils import Vector

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--usd',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.usd_import(filepath=a.usd, import_materials=True, import_cameras=False, import_lights=True)
    mats=[]
    for m in bpy.data.materials:
        rec={'name':m.name,'use_nodes':bool(m.use_nodes),'blend_method':getattr(m,'surface_render_method',None),'nodes':[]}
        if m.node_tree:
            for n in m.node_tree.nodes:
                x={'type':n.bl_idname,'name':n.name,'label':n.label}
                if n.bl_idname in ('ShaderNodeBsdfPrincipled','ShaderNodeBsdfGlass','ShaderNodeBsdfTransparent','ShaderNodeBsdfDiffuse','ShaderNodeBsdfTranslucent'):
                    x['inputs']={i.name:(list(i.default_value) if hasattr(i.default_value,'__len__') and not isinstance(i.default_value,str) else i.default_value) for i in n.inputs if not i.is_linked}
                if n.bl_idname=='ShaderNodeTexImage': x['image']=n.image.name if n.image else None
                rec['nodes'].append(x)
        mats.append(rec)
    objs=[]
    for o in bpy.context.scene.objects:
        if o.type not in {'MESH','LIGHT'}: continue
        bb=[tuple(o.matrix_world@Vector(c)) for c in o.bound_box] if o.type=='MESH' else []
        names=[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []
        objs.append({'name':o.name,'type':o.type,'materials':names,'bounds':bb,'light_type':o.data.type if o.type=='LIGHT' else None,'energy':o.data.energy if o.type=='LIGHT' else None})
    out={'usd':a.usd,'material_count':len(bpy.data.materials),'image_count':len(bpy.data.images),'light_count':len(bpy.data.lights),'materials':mats,'objects':objs}
    Path(a.out).write_text(json.dumps(out,indent=2,default=str))
    print('AUDIT',len(mats),len(bpy.data.images),len(bpy.data.lights),len(objs))
main()
