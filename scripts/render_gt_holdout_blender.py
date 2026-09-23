#!/usr/bin/env python3
"""Render 20 deterministic new-trajectory GT RGB and optical-z depth views.

The views are derived from GT poses only inside this evaluation script. They
are never written to a modelling manifest. Blender is CPU-only and low-res.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix

def tum(path): return np.loadtxt(path,comments='#',ndmin=2)
def rot_axis(axis,angle):
    axis=np.asarray(axis,float); axis/=np.linalg.norm(axis); x,y,z=axis; c=np.cos(angle); s=np.sin(angle); C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],[y*x*C+z*s,c+y*y*C,y*z*C-x*s],[z*x*C-y*s,z*y*C+x*s,c+z*z*C]])
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--usd',required=True); ap.add_argument('--poses',required=True); ap.add_argument('--frames-csv',required=True); ap.add_argument('--out',required=True); ap.add_argument('--resolution',default='640,480'); ap.add_argument('--start',type=int,default=0); ap.add_argument('--end',type=int,default=20); ap.add_argument('--threads',type=int,default=4); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); W,H=map(int,a.resolution.split(',')); gt=tum(a.poses); frames=list(csv.DictReader(open(a.frames_csv))); picks=np.linspace(0,len(frames)-1,20,dtype=int)[a.start:a.end]
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.usd_import(filepath=a.usd,import_materials=True,import_cameras=False,import_lights=False)
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100; sc.render.threads_mode='FIXED'; sc.render.threads=a.threads; sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
    sc.render.filepath=str(out/'_rgb.png'); sc.view_layers[0].use_pass_z=True; sc.view_layers[0].update_render_passes(); nt=bpy.data.node_groups.new('GT_EVAL_COMPOSITOR','CompositorNodeTree'); sc.compositing_node_group=nt; nt.nodes.clear(); rl=nt.nodes.new('CompositorNodeRLayers'); fo=nt.nodes.new('CompositorNodeOutputFile'); item=fo.file_output_items.new('FLOAT','Depth'); item.format.file_format='OPEN_EXR'; item.format.color_depth='32'; nt.links.new(rl.outputs['Depth'],fo.inputs[0])
    cam=bpy.data.cameras.new('GT_INDEPENDENT_HOLDOUT_CAMERA'); co=bpy.data.objects.new('GT_INDEPENDENT_HOLDOUT_CAMERA',cam); sc.collection.objects.link(co); sc.camera=co; cam.lens=50.0*762.8/1280; cam.sensor_width=50.0; cam.sensor_fit='HORIZONTAL'
    records=[]
    for local_j,fi in enumerate(picks):
        j=a.start+local_j
        fr=frames[int(fi)]; t=float(fr['timestamp_ns'])/1e9; k=min(max(int(np.searchsorted(gt[:,0],t)),1),len(gt)-1); aa,bb=gt[k-1],gt[k]; u=np.clip((t-aa[0])/(bb[0]-aa[0]),0,1); p=aa[1:4]*(1-u)+bb[1:4]*u
        # camera-to-world rotation from TUM; deterministic lateral/up shift and view perturbation
        q=bb[4:8] if u>.5 else aa[4:8]; x,y,z,w=q; q=q/np.linalg.norm(q); R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        off=0.12*R[:,0]-0.04*R[:,1]; Rn=rot_axis(np.array([0,0,1.]),np.deg2rad((j%5-2)*1.5))@R; pn=p+off+np.array([0,0,0.03*((j%3)-1)])
        co.location=pn; co.rotation_mode='QUATERNION'; co.rotation_quaternion=Matrix(Rn@np.diag([1,-1,-1])).to_quaternion(); stem=f'holdout_{j:02d}'; fo.file_name=stem+'_z.exr';  sc.render.filepath=str(out/(stem+'_rgb.png')); bpy.ops.render.render(write_still=True)
        records.append({'view_id':stem,'source_frame_index':int(fr['source_frame_index_zero_based']),'timestamp_s':t,'camera_position_world_m':pn.tolist(),'camera_rotation_world_from_optical':Rn.tolist(),'rgb_path':str(out/(stem+'_rgb.png')),'zdepth_path':str(out/(stem+'_z.exr')),'resolution':[W,H],'intrinsics':[762.8*W/1280,762.8*H/960,640*W/1280,480*H/960],'is_independent_holdout':True,'frontend_access':'forbidden'})
    (out/'manifest.json').write_text(json.dumps({'schema_version':1,'scene_id':'WorldLobby360s','protocol':'new trajectory derived from GT pose; evaluation-only','resolution':[W,H],'depth_axis':'Blender compositor Depth pass: camera optical range; convert to optical z before pixel metrics','views':records},indent=2)+'\n')
if __name__=='__main__': main()
