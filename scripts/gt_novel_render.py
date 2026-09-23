#!/usr/bin/env python3
"""CPU Cycles RGB plus optical-Z and sparse BVH validation for GT novel views."""
import bpy,sys,csv,json,argparse
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector

def rotz(a):
 c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1.]])
def pose(rows,t):
 i=min(max(int(np.searchsorted(rows[:,0],t)),1),len(rows)-1); a,b=rows[i-1],rows[i]; u=np.clip((t-a[0])/(b[0]-a[0]),0,1)
 p=a[1:4]*(1-u)+b[1:4]*u; q=b[4:8] if u>.5 else a[4:8]; x,y,z,w=q/np.linalg.norm(q)
 R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 return p,R
def args():
 ap=argparse.ArgumentParser(); ap.add_argument('--usd',required=True); ap.add_argument('--poses',required=True); ap.add_argument('--frames-csv',required=True); ap.add_argument('--out',required=True); ap.add_argument('--threads',type=int,default=4); ap.add_argument('--resolution',default='640,480'); ap.add_argument('--start',type=int,default=0); ap.add_argument('--end',type=int,default=20); return ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
def main():
 a=args(); W,H=map(int,a.resolution.split(',')); out=Path(a.out); out.mkdir(parents=True,exist_ok=True); rows=np.loadtxt(a.poses,comments='#',ndmin=2); frames=list(csv.DictReader(open(a.frames_csv))); picks=np.linspace(0,len(frames)-1,20,dtype=int)[a.start:a.end]
 bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.usd_import(filepath=a.usd,import_materials=True,import_cameras=False,import_lights=True)
 sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=8; sc.cycles.use_denoising=True; sc.render.threads_mode='FIXED'; sc.render.threads=a.threads; sc.render.resolution_x=W; sc.render.resolution_y=H; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False; sc.view_settings.view_transform='AgX'; sc.view_settings.exposure=-10
 if sc.world is None: sc.world=bpy.data.worlds.new('GT_World')
 sc.world.use_nodes=True; nt=sc.world.node_tree; nt.nodes.clear(); bg=nt.nodes.new('ShaderNodeBackground'); wo=nt.nodes.new('ShaderNodeOutputWorld'); nt.links.new(bg.outputs[0],wo.inputs[0]); bg.inputs['Color'].default_value=(1,1,1,1); bg.inputs['Strength'].default_value=12000
 # Source MDL marks both glass materials thin-walled. Preserve transmission/IOR and set the corresponding Blender flag.
 for m in bpy.data.materials:
  if m.name in ('Tinted_Glass','Clear_Glass') and m.node_tree:
   for n in m.node_tree.nodes:
    if n.bl_idname=='ShaderNodeBsdfPrincipled':
     if 'Thin Wall' in n.inputs: n.inputs['Thin Wall'].default_value=True
     if m.name=='Tinted_Glass': n.inputs['Base Color'].default_value=(.35,.35,.35,1); n.inputs['IOR'].default_value=1.52; n.inputs['Roughness'].default_value=0.0
     else: n.inputs['Base Color'].default_value=(1,1,1,1); n.inputs['IOR'].default_value=1.52; n.inputs['Roughness'].default_value=0.0
 cam=bpy.data.cameras.new('GT_NOVEL_CAMERA'); co=bpy.data.objects.new('GT_NOVEL_CAMERA',cam); sc.collection.objects.link(co); sc.camera=co; cam.sensor_fit='HORIZONTAL'; cam.sensor_width=50.; cam.lens=50.*381.4/W
 sc.use_nodes=True; sc.view_layers[0].use_pass_z=True; sc.view_layers[0].update_render_passes(); comp=bpy.data.node_groups.new('GT_Z_OUTPUT','CompositorNodeTree'); sc.compositing_node_group=comp; comp.nodes.clear(); rl=comp.nodes.new('CompositorNodeRLayers'); fo=comp.nodes.new('CompositorNodeOutputFile'); fo.format.file_format='OPEN_EXR_MULTILAYER'; fo.format.color_depth='32'; item=fo.file_output_items.new('FLOAT','Depth'); comp.links.new(rl.outputs['Depth'],fo.inputs[0]); records=[]
 for j,fi in enumerate(picks):
  fr=frames[int(fi)]; t=float(fr.get('timestamp_ns',fr.get('timestamp [ns]',fr.get('#timestamp [ns]'))))/1e9; p,R=pose(rows,t); off=.20*R[:,0]-.08*R[:,1]; Rn=rotz(np.deg2rad((j%5-2)*2.0))@R; pn=p+off+np.array([0,0,.04*((j%3)-1)])
  co.location=pn; co.rotation_mode='QUATERNION'; co.rotation_quaternion=Matrix(Rn@np.diag([1,-1,-1])).to_quaternion(); stem=f'view_{j:02d}'; sc.render.filepath=str(out/(stem+'_rgb.png')); fo.file_name=stem+'_z.exr'
  # Blender Z pass is camera optical-axis distance. Save explicitly alongside EXR for auditability.
  zfile=Path('/tmp')/(stem+'_z.exr');  bpy.context.scene.render.filepath=str(out/(stem+'_rgb.png')); bpy.ops.render.render(write_still=True); zi=bpy.data.images.load(str(zfile),check_existing=False); z=np.array(zi.pixels[:],dtype=np.float32).reshape(H,W,4)[:,:,0]; np.save(out/(stem+'_optical_z.npy'),z); bpy.data.images.remove(zi)
  records.append({'view_id':stem,'source_frame_index':int(fr['source_frame_index_zero_based']),'timestamp_s':t,'camera_position_world_m':pn.tolist(),'camera_rotation_world_from_optical':Rn.tolist(),'rgb_path':str(out/(stem+'_rgb.png')),'optical_z_path':str(out/(stem+'_optical_z.npy')),'resolution':[W,H],'intrinsics':[381.4,381.4,320,240],'renderer':'Cycles CPU 4 threads','rgb_status':'converted_USD_materials_renderer_domain_only','is_independent_novel_view':True})
 (out/'manifest.json').write_text(json.dumps({'schema_version':1,'scene_id':'WorldLobby360s','protocol':'GT mesh novel trajectory; poses derived from source GT timestamps','resolution':[W,H],'depth_axis':'optical_z','views':records},indent=2)+'\n')
 (out/'provenance.json').write_text(json.dumps({'source_usd':a.usd,'source_materials':'Collected_World_Lobby/Materials/Base/Glass/{Tinted_Glass,Clear_Glass}.mdl','conversion':['USD MDL thin_walled=true -> Principled Thin Wall=true','Tinted transmission_color=(.35,.35,.35), IOR=1.52, roughness=0','Clear transmission_color=(1,1,1), IOR=1.52, roughness=0'],'limitations':['Cycles/Blender renderer domain differs from Isaac RTX MDL; RGB is not pixel-equivalent','DomeLight has no texture and uses source intensity=12000; external appearance may differ']},indent=2)+'\n')
if __name__=='__main__': main()
