import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];scene=bpy.context.scene
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
for d in pref.devices:d.use=d.type=='OPTIX'
scene.cycles.device='GPU';scene.cycles.samples=64
for name in ['02_mirrors','03_reception','04_reverse']:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(root/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
