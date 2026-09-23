"""Render cameras achieved by the physical drone, in the frozen native M3 scene."""
import bpy,sys,json
from pathlib import Path
from mathutils import Matrix
import numpy as np
root=Path(__file__).resolve().parents[1];scene=root/'experiments/world_lobby/M3/astra_model/scene.blend';batch=root/'experiments/tasks/drone_M3/photographic_20';bpy.ops.wm.open_mainfile(filepath=str(scene));s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=640;s.render.resolution_y=480;s.render.resolution_percentage=100;s.render.pixel_aspect_x=1;s.render.pixel_aspect_y=1;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';data=bpy.data.cameras.new('drone_final_camera');cam=bpy.data.objects.new('drone_final_camera',data);s.collection.objects.link(cam);s.camera=cam;data.sensor_width=36;data.sensor_fit='HORIZONTAL';data.lens=762.8/1280*36;data.clip_start=.02;data.clip_end=100
for ep in sorted(batch.glob('episode_*')):
 p=ep/'final_camera.json'
 if not p.exists():continue
 C=np.asarray(json.loads(p.read_text())['camera_to_world']);C[:3,:3]=C[:3,:3]@np.diag([1,-1,-1]);cam.matrix_world=Matrix(C.tolist());s.render.filepath=str(ep/'final_rgb.png');bpy.ops.render.render(write_still=True);print('DRONE_FINAL_RENDER',ep.name,flush=True)
