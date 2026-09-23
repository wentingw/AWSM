import bpy,csv,math,os
from mathutils import Vector,Quaternion
R="/home/hchen/Documents/astraBlenderTest/world_model_blog"; rows=list(csv.DictReader(open(R+"/experiments/tasks/drone_M3/photographic_20/episode_05/drone_trajectory.csv"))); sel=[rows[i] for i in sorted(set(round(i*(len(rows)-1)/79) for i in range(80)))]
S=bpy.context.scene; S.render.engine='BLENDER_WORKBENCH'; S.render.resolution_x=320; S.render.resolution_y=240; S.render.resolution_percentage=100; S.render.image_settings.file_format='PNG'
C=bpy.data.collections.new("PRESENTATION_1KG_QUAD"); S.collection.children.link(C)
def link(o):
 [c.objects.unlink(o) for c in list(o.users_collection)]; C.objects.link(o)
def M(n,c,e=0):
 m=bpy.data.materials.new(n); m.use_nodes=True; b=m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value=(*c,1); b.inputs["Roughness"].default_value=.3
 if e:b.inputs["Emission Color"].default_value=(*c,1);b.inputs["Emission Strength"].default_value=e
 return m
def cube(n,sc,ma):
 bpy.ops.mesh.primitive_cube_add();o=bpy.context.object;o.name=n;o.scale=sc;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);link(o);o.data.materials.append(ma);return o
def cyl(n,ma):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.09,depth=.018);o=bpy.context.object;o.name=n;link(o);o.data.materials.append(ma);return o
black=M("quad",(0.03,.04,.05)); red=M("red",(.8,.02,.01),2); blue=M("blue",(.02,.2,1),2); white=M("label",(1,1,1),3)
body=cube("Simplified_1kg_quad_body",(.18,.12,.045),black); arms=[]
for s in [-1,1]:
 for t in [-1,1]:
  o=cyl("quad_rotor",blue if s*t>0 else red); arms.append((o,Vector((s*.23,t*.16,0))))
bpy.ops.object.text_add(); lab=bpy.context.object;lab.name="LABEL_simplified_1kg_quad";lab.data.body="SIMPLIFIED 1 kg QUAD";lab.data.align_x='CENTER';lab.data.size=.12;lab.data.materials.append(white);link(lab)
for i,r in enumerate(sel):
 p=Vector((float(r["x"]),float(r["y"]),float(r["z"])));q=Quaternion((float(r["qw"]),float(r["qx"]),float(r["qy"]),float(r["qz"])))
 body.location=p;body.rotation_mode='QUATERNION';body.rotation_quaternion=q;body.keyframe_insert("location",frame=i+1);body.keyframe_insert("rotation_quaternion",frame=i+1)
 for o,off in arms:o.location=p+off;o.rotation_mode='QUATERNION';o.rotation_quaternion=q;o.keyframe_insert("location",frame=i+1);o.keyframe_insert("rotation_quaternion",frame=i+1)
 lab.location=p+Vector((0,0,.2));lab.keyframe_insert("location",frame=i+1)
bpy.ops.object.camera_add(location=(-3.5,-3.8,1.4));cam=bpy.context.object;link(cam);S.camera=cam;cam.data.lens=42
for i,r in enumerate(sel):
 p=Vector((float(r['x']),float(r['y']),float(r['z']))); cam.location=p+Vector((-2.6,-2.8,1.4)); cam.rotation_euler=(p+Vector((0,0,.5))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.keyframe_insert('location',frame=i+1); cam.keyframe_insert('rotation_euler',frame=i+1)
bpy.ops.object.light_add(type='AREA',location=(-1,-2,4));light=bpy.context.object;link(light);light.data.energy=1400;light.data.size=5
os.makedirs(R+"/experiments/tasks/drone_M3/presentation/frames",exist_ok=True)
for i in range(1,len(sel)+1):S.frame_set(i);S.render.filepath=R+"/experiments/tasks/drone_M3/presentation/frames/drone_"+str(i).zfill(4)+".png";bpy.ops.render.render(write_still=True)
