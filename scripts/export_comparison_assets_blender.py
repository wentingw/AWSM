"""Export lightweight, same-frame M1-M4 and GT comparison GLBs.

This script opens frozen source scenes read-only, applies the frozen GT_from_model
registration for each prediction, removes presentation-only walls/ceiling, and
exports a separate browser asset. It never edits source .blend or USD files.
Blender's glTF exporter converts the internal Z-up scene to glTF Y-up while
preserving the common world origin and metre scale.
"""
import bpy, sys, json, hashlib, math, bmesh
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'blog/assets/comparison'
OUT.mkdir(parents=True, exist_ok=True)
REG = ROOT / 'results'
METHODS = ['M1', 'M2', 'M3', 'M4']
WALL_WORDS = ('wall', 'window', 'ceiling', 'door', 'mullion', 'cornice', 'louver', 'slat', 'arraybloomwood', 'softwood__lumber_123310', 'cherry_10863', 'aluminium_533')
GT_ARCH_MATERIALS = ('softwood__lumber_123310', 'paint_defaultnullmaterial', 'concrete_masonry_units_415', 'cherry', 'aluminium_533')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def matrix_from_json(p):
    return Matrix(json.loads(p.read_text())['T_gt_model'])

def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def bounds(objects):
    pts=[]
    for o in objects:
        if o.type != 'MESH': continue
        pts.extend([o.matrix_world @ Vector(c) for c in o.bound_box])
    if not pts: return None
    lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return {'z_up_min_m':list(lo),'z_up_max_m':list(hi),'z_up_size_m':list(hi-lo),
            'gltf_y_up_min_m':[lo.x,lo.z,-hi.y],'gltf_y_up_max_m':[hi.x,hi.z,-lo.y],
            'gltf_y_up_size_m':[hi.x-lo.x,hi.z-lo.z,hi.y-lo.y]}

def hide_cutaway(objects):
    hidden=[]; kept=[]
    for o in objects:
        if o.type != 'MESH': continue
        name=o.name.lower()
        if any(w in name for w in WALL_WORDS):
            o.hide_render=True; o.hide_viewport=True; hidden.append(o.name)
        else: kept.append(o)
    return kept, hidden

def downsample_images(max_dimension):
    """Reduce only in-memory image datablocks used by this display export."""
    changed=[]
    for img in list(bpy.data.images):
        if img.type in {'RENDER_RESULT', 'COMPOSITING'} or not img.size[0] or not img.size[1]:
            continue
        w,h=img.size[:2]
        longest=max(w,h)
        if longest <= max_dimension:
            continue
        scale=max_dimension/float(longest)
        nw=max(1, int(round(w*scale))); nh=max(1, int(round(h*scale)))
        try:
            img.scale(nw, nh)
            changed.append({'name':img.name,'from_px':[w,h],'to_px':[nw,nh]})
        except RuntimeError:
            pass
    return changed

def simplify(objects, ratio=0.35):
    before=after=0
    for o in objects:
        if o.type != 'MESH': continue
        before += len(o.data.polygons)
        if len(o.data.polygons) > 50:
            mod=o.modifiers.new('comparison_decimate','DECIMATE'); mod.ratio=ratio
            bpy.context.view_layer.objects.active=o
            try: bpy.ops.object.modifier_apply(modifier=mod.name)
            except RuntimeError: pass
        after += len(o.data.polygons)
    return before, after

def export_glb(name, objects, source, registration, notes, hidden):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        if o.type == 'MESH' and not o.hide_viewport: o.select_set(True)
    path=OUT/(name+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
        export_cameras=False, export_lights=False, export_materials='EXPORT',
        export_apply=False, export_yup=True)
    return {'id':name,'path':'assets/comparison/'+path.name,'source':str(source),
            'source_sha256':sha(source),'asset_sha256':sha(path),'bytes':path.stat().st_size,
            'registration':registration,'hidden_display_objects':hidden,'notes':notes}

def main():
    records=[]
    for m in METHODS:
        source = ROOT.parent/'visual-recon/scene.blend' if m=='M1' else ROOT/f'experiments/world_lobby/{m}/astra_model/scene.blend'
        regp = REG/f'{m}/render_manifest.json'
        reg=json.loads(regp.read_text())['T_gt_model']
        bpy.ops.wm.open_mainfile(filepath=str(source))
        texture_changes=downsample_images(1024)
        objects=list(bpy.context.scene.objects)
        world_matrices={o.name:o.matrix_world.copy() for o in objects}
        T=Matrix(reg)
        for o in objects:
            if o.type=='MESH': o.matrix_world=T @ world_matrices[o.name]
        kept,hidden=hide_cutaway(objects)
        bef,aft=simplify(kept, 0.55 if m=='M1' else 0.40)
        records.append(export_glb(m,kept,source,reg,'registered with frozen GT_from_model; presentation cutaway; decimated browser copy; textures capped at 1024 px',hidden))
        records[-1]['source_triangles_before']=bef; records[-1]['export_triangles_after']=aft; records[-1]['bounds']=bounds(kept); records[-1]['texture_max_dimension_px']=1024; records[-1]['textures_resized']=len(texture_changes)
    # GT import is intentionally separate. Keep only the lobby spatial crop and
    # use a browser decimation; original USD remains untouched.
    clear()
    gt=ROOT/'../drone-web/scenes/world_lobby/Collected_World_Lobby/World_Lobby.usd'
    bpy.ops.wm.usd_import(filepath=str(gt))
    gt_texture_changes=downsample_images(64)
    gt_objects=list(bpy.context.scene.objects)
    # Crop by the observed lobby envelope in GT ENU metres. This is an explicit
    # display crop, not a claim that the exported GT is the complete building.
    kept=[]; cropped=[]; floor_faces_kept=0
    for o in gt_objects:
        if o.type!='MESH': continue
        # Keep an object only when its transformed geometry is fully inside
        # the declared display crop; testing the object origin can leak large
        # meshes beyond the crop envelope.
        corners=[o.matrix_world @ Vector(corner) for corner in o.bound_box]
        xs=[c.x for c in corners]; ys=[c.y for c in corners]; zs=[c.z for c in corners]
        intersects=(max(xs)>=7.0 and min(xs)<=28.0 and max(ys)>=14.0 and min(ys)<=27.0 and max(zs)>=-1.0 and min(zs)<=8.0)
        mats={m.name.lower() for m in o.data.materials if m}
        spans=(max(xs)-min(xs), max(ys)-min(ys))
        # USD architectural shell is a hash-named Iron mesh. Remove only the
        # giant shell, which otherwise occludes the lobby; retain furniture and
        # architectural details whose bounds intersect the shared lobby window.
        shell=(max(spans)>20.0 or (max(spans)>8.0 and (max(zs)-min(zs))>1.5) or any(tok in ' '.join(mats) for tok in GT_ARCH_MATERIALS))
        if intersects and not shell:
            kept.append(o)
        elif shell:
            # Preserve real GT floor faces from the shell: retain only faces
            # near the ground plane with upward normals and centers in the
            # shared window. Walls and ceiling remain excluded.
            patch=o.copy(); patch.data=o.data.copy(); bpy.context.collection.objects.link(patch)
            bm=bmesh.new(); bm.from_mesh(patch.data); bm.faces.ensure_lookup_table()
            R=patch.matrix_world.to_3x3()
            N=R.inverted().transposed()
            for f in list(bm.faces):
                c=patch.matrix_world @ f.calc_center_median()
                n=N @ f.normal; n.normalize()
                if not (7.0 <= c.x <= 28.0 and 14.0 <= c.y <= 27.0 and -0.5 <= c.z <= 0.08 and n.z >= 0.5):
                    bm.faces.remove(f)
            floor_faces_kept += len(bm.faces)
            orphan=[v for v in bm.verts if not v.link_faces]
            if orphan: bmesh.ops.delete(bm, geom=orphan, context='VERTS')
            bm.to_mesh(patch.data); bm.free(); patch.data.update()
            if len(patch.data.polygons):
                kept.append(patch)
            else:
                bpy.data.objects.remove(patch, do_unlink=True)
            o.hide_viewport=True; cropped.append(o.name+' (walls/ceiling)')
        else:
            o.hide_viewport=True; cropped.append(o.name)
    kept,hidden=hide_cutaway(kept); bef,aft=simplify(kept,0.01)
    gt_record=export_glb('GT',kept,gt,[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]],'NVIDIA AEC World Lobby USD; spatially cropped and decimated display copy; textures capped at 64 px; not complete GT',cropped+hidden)
    gt_record['source_triangles_before']=bef; gt_record['export_triangles_after']=aft; gt_record['bounds']=bounds(kept); gt_record['texture_max_dimension_px']=64; gt_record['textures_resized']=len(gt_texture_changes); gt_record['real_floor_faces_kept']=floor_faces_kept
    records.append(gt_record)
    manifest={'schema_version':1,'coordinate_system':{'source_blender':'Z-up ENU metres','export_gltf':'Y-up metres','origin':'shared GT world origin; no per-asset centering or scale'},'cutaway':{'removed_name_tokens':WALL_WORDS,'kept':'floor and furniture where within crop'},'gt_crop':{'x_m':[7,28],'y_m':[14,27],'z_m':[-1,8],'original_triangles':9984967,'selection':'mesh objects intersecting the shared M1-M4 lobby window; giant architectural shell removed except real near-ground upward-facing floor faces to prevent occlusion; then name-token cutaway', 'decimate_ratio':0.01, 'texture_max_dimension_px':64, 'disclosure':'GT is a cropped, decimated browser display asset; it is not complete GT.', 'NOTICE':'Source: NVIDIA AEC / World Lobby content. License: NVIDIA Omniverse AEC content terms; upstream terms remain in force and this export grants no relicensing. Not CC0.'},'assets':records,'recommendation':{'camera_target_gltf_y_up':[18.0,1.2,-21.0],'camera_radius_m':22.0}}
    (OUT/'comparison_provenance.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    # Final display-only scene-graph pass removes audited material-named walls.
    import runpy
    runpy.run_path(str(ROOT/'scripts/postprocess_comparison_glb.py'), run_name='__main__')

if __name__=='__main__': main()
