import sys,json
from pathlib import Path
import bpy,numpy as np
r=Path(__file__).resolve().parents[1];p=r/'provenance/synthetic_pair_smoke';p.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.mesh.primitive_plane_add(size=20)
s=bpy.context.scene;s.world=bpy.data.worlds.new('World');s.world.color=(.8,.8,.8)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'scene.blend'))
T=np.diag([1.,-1.,-1.,1.]);T[2,3]=3.;K=[[762.8,0,640],[0,762.8,480],[0,0,1]]
f={'sample_index':33,'source_index':33,'timestamp_ns':33,'camera_to_world':T.tolist(),'intrinsics':K,'valid':False}
(p/'packet.json').write_text(json.dumps({'method_id':'M1','frames':[f]}));(p/'cameras.json').write_text(json.dumps({'frames':[f]}));(p/'modelling_manifest.json').write_text(json.dumps({'revisions':1,'checking_render_count':0,'model_from_input':None}))
sys.path.insert(0,str(r/'tools'));import paired_check_blender as pair
pair.INDICES=[33];sys.argv=['blender','--','--method-dir',str(p),'--packet',str(p/'packet.json')];pair.main()
z=np.load(p/'checks/v1/0033_depth.npz')['model_z_m'];assert np.isfinite(z).all() and np.max(abs(z-3))<1e-5
(r/'provenance/generic_pair_validation.json').write_text(json.dumps({'status':'PASS','reference':'synthetic frontoparallel plane at opticalZ=3m','render_and_bvh_projection_checks':'PASS','maximum_z_error_m':float(np.max(abs(z-3)))},indent=2)+'\n')
