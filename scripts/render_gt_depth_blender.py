#!/usr/bin/env python3
"""CPU Blender GT z-depth renderer; GT-only and never called by modelling runs."""
import argparse,csv,json,sys
from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix,Quaternion

def tum(path): return np.loadtxt(path,comments='#',ndmin=2)
def pose_at(rows,t):
    i=min(max(int(np.searchsorted(rows[:,0],t)),1),len(rows)-1); a,b=rows[i-1],rows[i]; u=np.clip((t-a[0])/(b[0]-a[0]),0,1)
    p=a[1:4]*(1-u)+b[1:4]*u; q=Quaternion((a[7],a[4],a[5],a[6])).slerp(Quaternion((b[7],b[4],b[5],b[6])),float(u))
    R=np.asarray(q.to_matrix()); return p,R
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--usd',required=True); ap.add_argument('--poses',required=True); ap.add_argument('--frames-csv',required=True); ap.add_argument('--out',required=True); ap.add_argument('--limit',type=int,default=0); ap.add_argument('--resolution',default='1280,960'); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); W,H=map(int,a.resolution.split(',')); rows=tum(a.poses); frames=list(csv.DictReader(open(a.frames_csv))); frames=frames[:a.limit] if a.limit else frames
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.usd_import(filepath=a.usd,import_materials=False,import_cameras=False,import_lights=False)
    sc=bpy.context.scene; sc.render.engine='BLENDER_WORKBENCH'; sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='OPEN_EXR'; sc.render.image_settings.color_depth='32'; sc.render.film_transparent=True
    cam=bpy.data.cameras.new('GT_EVAL_CAMERA'); co=bpy.data.objects.new('GT_EVAL_CAMERA',cam); sc.collection.objects.link(co); sc.camera=co; cam.lens=50; cam.sensor_width=50
    # Optical pinhole: shift/lens chosen from fx; 50 mm sensor width is arbitrary but exact FOV.
    cam.lens=50.0; cam.sensor_width=50.0; cam.sensor_fit='HORIZONTAL'; cam.lens=50.0*762.8/W
    rows_out=[]
    for fr in frames:
        t=float(fr['timestamp_ns'])/1e9; p,R=pose_at(rows,t); co.location=p; co.rotation_mode='QUATERNION'; co.rotation_quaternion=Matrix(R@np.diag([1,-1,-1])).to_quaternion()
        sc.render.filepath=str(out/f"frame_{int(fr['source_frame_index_zero_based']):06d}.exr"); bpy.ops.render.render(write_still=True); rows_out.append({'source_frame_index':int(fr['source_frame_index_zero_based']),'timestamp_s':t,'path':sc.render.filepath,'axis':'optical_z','renderer':'BLENDER_WORKBENCH_CPU'})
    (out/'manifest.json').write_text(json.dumps({'resolution':[W,H],'intrinsics':[762.8,762.8,640,480],'frames':rows_out,'gt_only':True},indent=2)+'\n')
main()
