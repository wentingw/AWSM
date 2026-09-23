import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];scene=bpy.context.scene
cam=bpy.data.objects['01_lobby'];cam.location=(6.4,.8,3.6);target=Vector((4.9,21,1.8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
# Fix manual reference associations before truth files are accessed.
association={'01_lobby':0,'02_mirrors':78,'03_reception':105,'04_reverse':90}
cameras=[]
for name,frame in association.items():
 o=bpy.data.objects[name];bpy.context.view_layer.update();cameras.append({'camera':name,'reference_frame':frame,'location':list(o.location),'camera_to_world_blender':[list(r) for r in o.matrix_world],'lens_mm':o.data.lens,'sensor_width_mm':o.data.sensor_width,'association':'Approximate visual composition chosen before truth evaluation; not solved from source pixels'})
(root/'manual_cameras.json').write_text(json.dumps({'kind':'four manually composed viewpoints; not an estimated 180-frame trajectory','cameras':cameras},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'scene.blend'))
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64;scene.render.filepath=str(root/'renders/01_lobby.png');bpy.ops.render.render(write_still=True)
