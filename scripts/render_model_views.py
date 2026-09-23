"""Frozen model evaluation renders. Never save the source .blend."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
args=sys.argv[sys.argv.index('--')+1:]
manifest=Path(args[0]); m=json.loads(manifest.read_text());out=Path(m['output']);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=m['model_path'])
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=640;scene.render.resolution_y=480;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.film_transparent=False
scene.view_settings.view_transform=m.get('view_transform','AgX')
truth=np.loadtxt(m['truth_pose_path']);T=np.array(m['T_gt_model']);sc=np.cbrt(np.linalg.det(T[:3,:3]));R=T[:3,:3]/sc
camdata=bpy.data.cameras.new('evaluation_camera');cam=bpy.data.objects.new('evaluation_camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
fx,fy,cx,cy=m['K'];sw,sh=m['source_resolution'];camdata.sensor_fit='HORIZONTAL';camdata.sensor_width=36;camdata.lens=fx/sw*36;camdata.shift_x=(sw/2-cx)/sw;camdata.shift_y=(cy-sh/2)/sw;camdata.clip_start=.01;camdata.clip_end=200
scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=fx/fy

def qmat(q):
 x,y,z,w=q/np.linalg.norm(q)
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
records=[]
for i in m['render_indices']:
 row=truth[i];C=np.eye(4);C[:3,:3]=R.T@qmat(row[4:8])@np.diag([1,-1,-1]);C[:3,3]=np.linalg.solve(T[:3,:3],row[1:4]-T[:3,3]);cam.matrix_world=Matrix(C.tolist());path=out/f'{i:03d}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);records.append({'keyframe_index':i,'rgb':str(path),'camera_model_blender':C.tolist()});(out/'render_progress.json').write_text(json.dumps({'completed':len(records),'total':len(m['render_indices'])}));print('RENDER_DONE',i,flush=True)
(out/'renders.json').write_text(json.dumps({'method':m['method_id'],'alignment':m['alignment'],'resolution':[640,480],'samples':16,'renderer':'Cycles CPU','views':records},indent=2)+'\n')
