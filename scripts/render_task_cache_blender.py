"""Render native model camera candidates, without GT registration or pose access."""
import bpy,json,sys
from pathlib import Path
import numpy as np
from mathutils import Matrix
args=sys.argv[sys.argv.index('--')+1:];scene_path=Path(args[0]);packet_path=Path(args[1]);out=Path(args[2]);out.mkdir(parents=True,exist_ok=True);packet=json.loads(packet_path.read_text());bpy.ops.wm.open_mainfile(filepath=str(scene_path));s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=320;s.render.resolution_y=240;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';data=bpy.data.cameras.new('task_sensor');cam=bpy.data.objects.new('task_sensor',data);s.collection.objects.link(cam);s.camera=cam;data.sensor_width=36;data.sensor_fit='HORIZONTAL';data.lens=762.8/1280*36;data.clip_start=.02;data.clip_end=100
manifest_path=scene_path.parent/'modelling_manifest.json';m=json.loads(manifest_path.read_text());T=np.asarray(m.get('T_input_model',np.eye(4)));views=[]
for f in packet['frames']:
 k=f['keyframe_index']
 if k%6!=0 or 'geometry' not in f:continue
 C=T@np.load(f['geometry'])['camera_to_world'];M=C.copy();M[:3,:3]=C[:3,:3]@np.diag([1,-1,-1]);cam.matrix_world=Matrix(M.tolist());path=out/f'{k:03d}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);views.append(dict(view_id=k,rgb=str(path.resolve()),camera_to_world=C.tolist()));print('TASK_CACHE_VIEW',k,flush=True)
(out/'manifest.json').write_text(json.dumps({'status':'complete','model':str(scene_path.resolve()),'scope':'native reconstructed world candidates; no GT','K':[190.7,190.7,160,120],'resolution_wh':[320,240],'views':views},indent=2)+'\n')
