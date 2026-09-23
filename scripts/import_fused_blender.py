"""Convert a frozen colored TSDF mesh to a renderable baseline artifact."""
import bpy,sys,json
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];folder=Path(args[0]);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.wm.ply_import(filepath=str(folder/'mesh.ply'));obj=bpy.context.object;obj.name='direct_TSDF_surface_no_object_semantics'
mat=bpy.data.materials.new('Baked input RGB vertex color');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1
if obj.data.color_attributes:
 color=nodes.new('ShaderNodeVertexColor');color.layer_name=obj.data.color_attributes[0].name;mat.node_tree.links.new(color.outputs['Color'],em.inputs['Color'])
else:em.inputs['Color'].default_value=(.5,.5,.5,1)
mat.node_tree.links.new(em.outputs[0],output.inputs['Surface']);obj.data.materials.clear();obj.data.materials.append(mat);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.world=bpy.data.worlds.new('Neutral background');scene.world.color=(.1,.1,.1);bpy.ops.wm.save_as_mainfile(filepath=str(folder/'scene.blend'));print('BASELINE_SAVED',folder)
