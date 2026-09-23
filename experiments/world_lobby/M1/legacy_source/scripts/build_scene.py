"""Astra visual-only reconstruction. All geometry is authored from RGB observation.
No source scene, depth, camera transforms, point clouds, SfM or learned geometry.
Run: blender -b --factory-startup --python scripts/build_scene.py
"""
import bpy, math, random, json, sys, time
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1]
random.seed(4201)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name!='Collection': bpy.data.collections.remove(c)
base=bpy.data.collections.get('Collection');base.name='Architecture'
COL=base

def collection(name):
 global COL
 COL=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(COL)
def move(o,name,mat=None):
 o.name=name
 for c in list(o.users_collection): c.objects.unlink(o)
 COL.objects.link(o)
 if mat:o.data.materials.append(mat)
 return o

def mat(name,color,metal=0,rough=.5,tex=None,scale=(1,1,1),bump=0,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 if tex:
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'assets'/tex));t.image.pack()
  uv=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=scale
  l.new(uv.outputs['UV'],mapping.inputs[0]);l.new(mapping.outputs[0],t.inputs['Vector']);l.new(t.outputs['Color'],p.inputs['Base Color'])
  if bump:
   b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.015;l.new(t.outputs['Color'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
 return m
stone=mat('Warm limestone • fine mineral grain',(.52,.50,.44),rough=.26,tex='limestone.jpg',scale=(3,3,3),bump=.1)
oak=mat('Pale vertical oak',(.58,.52,.41),rough=.49,tex='oak.jpg',bump=.13)
plaster=mat('Ivory plaster',(.69,.67,.61),rough=.8,tex='plaster.jpg',bump=.1)
dark=mat('Charcoal metal',(.025,.027,.026),metal=.65,rough=.27)
joint=mat('Recessed panel joints',(.045,.042,.034),rough=.75)
slat=mat('Dark bronze ceiling fins',(.12,.095,.065),metal=.55,rough=.39)
black=mat('Obsidian polished floor • brass flecks',(.014,.016,.012),metal=.44,rough=.17,tex='black_brass.jpg',scale=(2.5,8,1),bump=.02)
sage=mat('Sage green woven upholstery',(.31,.39,.23),rough=.82,tex='sage_fabric.jpg',scale=(2,2,2),bump=.17)
brass=mat('Champagne brass',(.59,.42,.20),metal=.83,rough=.27)
mirror=mat('Silver circular mirror',(.91,.94,.93),metal=1,rough=.018)
planter=mat('Grey concrete planters',(.26,.27,.26),rough=.78,tex='concrete.jpg',bump=.25)
ceramic=mat('Glazed pale grey ceramic',(.43,.49,.49),metal=.15,rough=.25)
soil=mat('Dark potting soil',(.027,.019,.01),rough=1)
leaf=mat('Olive green leaves',(.105,.16,.047),rough=.73)
leaf2=mat('Pale leaf tips',(.25,.33,.10),rough=.72)
flower=mat('Golden yellow twig foliage',(.57,.42,.045),rough=.75)
stemmat=mat('Woody branches',(.20,.15,.045),rough=.9)
lightmat=mat('Warm glowing diffuser',(1,.66,.30),rough=.45,emission=2.5)
shade=mat('Linen lampshades',(.85,.84,.77),rough=.9,emission=.15)
window=mat('Bright diffuse daylight',(.93,.97,1),rough=.4,emission=1.5)
marble=mat('White marble emblem',(.75,.74,.68),rough=.3,tex='plaster.jpg',bump=.12)


def cube(name,loc,size,material,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=move(bpy.context.object,name,material);o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if material == oak:
  uv=o.data.uv_layers.active
  for poly in o.data.polygons:
   for li in poly.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co
    uv.data[li].uv=(co.y if abs(poly.normal.x)>.5 else co.x,co.z*.3)
 if bevel:
  m=o.modifiers.new('Soft manufactured edges','BEVEL');m.width=bevel;m.segments=3
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def cyl(name,loc,r,depth,material,verts=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc);o=move(bpy.context.object,name,material)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 return o

def uvball(name,loc,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=loc);o=move(bpy.context.object,name,material);o.scale=scale
 for p in o.data.polygons:p.use_smooth=True
 return o

def mesh(name,v,f,material):
 d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update();o=bpy.data.objects.new(name,d);COL.objects.link(o);d.materials.append(material);return o

def line(name,pts,r,material):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=2;c.bevel_depth=r;c.bevel_resolution=2
 s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for p,co in zip(s.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new(name,c);COL.objects.link(o);c.materials.append(material);return o

def torus(name,loc,major,minor,material):
 bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=8,location=loc,major_radius=major,minor_radius=minor);return move(bpy.context.object,name,material)

def lathe(name,loc,profile,material,N=48):
 v=[];f=[]
 for r,z in profile:
  for i in range(N):a=2*pi*i/N;v.append((loc[0]+r*cos(a),loc[1]+r*sin(a),loc[2]+z))
 for j in range(len(profile)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;f.append((a,b,b+N,a+N))
 o=mesh(name,v,f,material)
 for p in o.data.polygons:p.use_smooth=True
 return o

# Coordinate system and scale are manual design choices, not recovered measurements.
W,L,H=10.4,24.0,7.4
cube('Limestone floor',(W/2,L/2,-.12),(W,L,.24),stone)
cube('Dark inset floor',(5.1,11.9,.015),(6.2,19.8,.035),black,.015)
cube('Ceiling',(W/2,L/2,H+.12),(W,L,.24),plaster)
# Panel grid, vertical grain, recessed shadow joints.
def panels_y(y,label):
 cube(label+' backing',(W/2,y+.08,3.7),(W,.16,H),joint)
 for i in range(10):
  for j,(z,h) in enumerate([(1.5,2.98),(4.4,2.78),(6.6,1.58)]):cube(label+f' panel {i:02d}-{j}',((i+.5)*W/10,y-.017,z),(W/10-.021,.11,h),oak,.003)
panels_y(24,'Reception wall')
panels_y(-.13,'Near end • inferred closure')
# Long right wall: mirror bay projects slightly; two steel door bays.
for a,b,x in [(0,6.3,10.35),(6.3,15.2,9.92),(15.2,24,10.35)]:
 cube('Wall backing',(x+.08,(a+b)/2,H/2),(.18,b-a,H),joint)
 count=round((b-a)/1.05);step=(b-a)/count
 for i in range(count):
  y=a+(i+.5)*step
  for j,(z,h) in enumerate([(1.5,2.98),(4.4,2.78),(6.6,1.58)]):
   if j==0 and (abs(y-7)<.65 or abs(y-14.2)<.6 or abs(y-20.8)<.6):continue
   cube(f'Right wall oak {a}-{i}-{j}',(x-.035,y,z),(.12,step-.021,h),oak,.003)
for y,x in [(7.0,9.85),(14.2,9.85),(20.8,10.28)]:
 cube('Steel door recessed reveal',(x+.025,y,1.5),(.045,1.24,3),dark)
 cube('Brushed stainless door',(x-.03,y,1.49),(.035,1.12,2.95),mirror,.004)
 line('Door vertical pull',[(x-.09,y+.43,1.08),(x-.09,y+.43,1.8)],.018,dark)
# Glass facade. Bright exterior card is render-only and excluded from the web model.
exterior=cube('Daylight exterior • rendering only',(-1,12,3.7),(.02,30,11),window)
exterior['render_only']=True
for i in range(25):cube('Window vertical mullion',(0,i,3.7),(.10,.065,7.4),dark,.008)
for z in [0.05,3.2,7.32]:cube('Window transom',(0,12,z),(.12,24,.09),dark,.008)
for y in [5.5,20.0]:
 for yy in [y-.86,y,y+.86]:cube('Bronze entry frame',(-.02,yy,1.58),(.15,.065,3.16),brass,.008)
 for z in [.07,3.13]:cube('Bronze door crossbar',(-.02,y,z),(.15,1.8,.105),brass,.008)
 for yy in [y-.12,y+.12]:line('Entry door pull',[(.09,yy,1.0),(.09,yy,1.85)],.02,dark)
for y in [8.0,17.0]:cyl('Round structural column',(.78,y,H/2),.38,H,stone,64)
for y in [i*.28+.12 for i in range(86)]:
 for x,w in [(1.05,2.1),(9.25,2.3)]:cube('Ceiling transverse bronze fin',(x,y,H-.12),(w,.055,.25),slat,.008)

collection('Lounge furniture')
def chair(x,y,r=.52,angle=None,label='Sage circular seat'):
 cyl(label+' shadow base',(x,y,.12),r*.84,.14,dark)
 o=cyl(label+' upholstered seat',(x,y,.37),r,.48,sage,64);b=o.modifiers.new('Cushion rounding','BEVEL');b.width=.065;b.segments=4;o.modifiers.new('Cushion normals','WEIGHTED_NORMAL')
 for a in [0,pi/2,pi,3*pi/2]:cyl('Seat chrome foot',(x+cos(a)*r*.69,y+sin(a)*r*.69,.075),.025,.15,mirror,12)
 if angle is not None:
  vs=[];fs=[];N=30
  for i in range(N+1):
   a=angle+(-1.1+2.2*i/N)
   for rad,z in [(r-.12,.50),(r+.015,.50),(r+.015,1.03),(r-.12,1.03)]:vs.append((x+rad*cos(a),y+rad*sin(a),z))
  for i in range(N):
   for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
  fs.extend([(0,3,2,1),(N*4,N*4+1,N*4+2,N*4+3)])
  o=mesh('Curved upholstered back',vs,fs,sage);b=o.modifiers.new('Round back edges','BEVEL');b.width=.052;b.segments=4;o.modifiers.new('Smooth back normals','WEIGHTED_NORMAL')
  for p in o.data.polygons:p.use_smooth=True

def table(x,y,r=.8,bowl=True):
 cyl('Black circular coffee tabletop',(x,y,.51),r,.055,dark,64)
 cyl('Coffee table bottom ring',(x,y,.09),r*.52,.025,dark)
 for i in range(24):
  a=i*2*pi/24;line('Radial table base',[(x+cos(a)*r*.51,y+sin(a)*r*.51,.10),(x+cos(a+.12)*r*.32,y+sin(a+.12)*r*.32,.46)],.019,dark)
 if bowl:lathe('Brass table bowl',(x,y,.55),[(.12,0),(.19,.05),(.23,.14),(.22,.16),(.20,.14),(.16,.07),(.08,.05)],brass)
for cx,cy in [(4.55,15.25),(6.25,5.8)]:
 chair(cx-.85,cy-.4,.55,pi);chair(cx-.85,cy+.7,.53,pi)
 chair(cx+.16,cy+.85,.66,None);chair(cx+1.32,cy+.55,.54,0)
 chair(cx+1.17,cy-.55,.56,0);chair(cx-.92,cy-1.5,.56,None)
 table(cx+.1,cy-1.25,.78)
chair(8.4,2.4,.62,0);chair(7.4,2.7,.59,pi/2);table(7.8,1.5,.68,False)

collection('Reception and mirrors')
# Faceted angular dark reception counter, triangulated into visible planes.
v=[(3.1,22.0,.12),(7.5,22.0,.12),(7.85,22.0,.55),(7.4,22.2,1.05),(3.0,22.2,1.05),(2.8,22.0,.5),(3.0,23.0,1.05),(7.4,23.0,1.05),(3.1,23.0,.12),(7.5,23.0,.12),(5.1,21.85,.56)]
f=[(0,1,10),(1,2,10),(2,3,10),(3,4,10),(4,5,10),(5,0,10),(4,3,7,6),(6,7,9,8),(0,5,4,6,8),(1,9,7,3,2),(0,8,9,1)]
o=mesh('Faceted reception desk',v,f,dark)
deskalt=mat('Desk facet graphite',(.095,.102,.098),metal=.45,rough=.36);o.data.materials.append(deskalt)
for i,p in enumerate(o.data.polygons):p.material_index=1 if i in [0,3,5,6] else 0
cube('Desktop workstation',(3.4,22.62,1.26),(.43,.045,.30),dark,.012)
# U-shaped abstract wall emblem and marble shield.
pts=[(3.8,23.88,5.05),(3.8,23.88,4.18)]
for i in range(11):a=pi+i*pi/2/10;pts.append((4.12+.32*cos(a),23.88,4.18+.32*sin(a)))
pts.extend([(6.28,23.88,3.86)])
for i in range(11):a=1.5*pi+i*pi/2/10;pts.append((6.28+.32*cos(a),23.88,4.18+.32*sin(a)))
pts.append((6.6,23.88,5.05));line('Reception emblem dark outline',pts,.025,dark)
pts=[(4.79,23.79,4.1),(5.62,23.79,4.1),(5.62,23.79,3.45)]
for i in range(15):a=i*pi/14;pts.append((5.205+.415*cos(a),23.79,3.45-.42*sin(a)))
mesh('Marble shield wall emblem',pts,[tuple(range(len(pts)))],marble)
# Cluster on east wall; cylinders rotate from Z axis to wall normal.
mirrors=[(10.55,2.1,.84),(9.18,2.83,.39),(9.0,1.96,.24),(9.4,1.14,.40),(11.82,1.63,.66),(12.55,2.54,.46),(11.93,3.37,.34),(11.34,2.91,.25),(10.85,1.03,.25),(12.73,1.46,.20),(8.98,1.4,.18)]
for y,z,r in mirrors:
 o=cyl('Circular silver mirror',(9.78,y,z),r,.032,mirror,64);o.rotation_euler[1]=pi/2
 o=torus('Thin mirror rim',(9.754,y,z),r,.013,brass);o.rotation_euler[1]=pi/2
for x,y in [(9.5,17.9),(9.45,22.0),(9.2,8.0)]:
 cyl('Floor lamp weighted foot',(x,y,.04),.24,.07,mirror)
 cyl('Floor lamp upright',(x,y,1.1),.022,2.15,brass,20)
 cyl('Ivory floor lamp shade',(x,y,2.05),.26,.52,shade)

collection('Botanical planters')
# Foliage is explicit lightweight geometry, authored procedurally from observed silhouettes.
def leaves_mesh(name,leaves,material):
 vs=[];fs=[]
 for center,direction,length,width in leaves:
  d=Vector(direction).normalized();side=d.cross(Vector((0,0,1)))
  if side.length<.001:side=Vector((1,0,0))
  side.normalize();p=Vector(center);i=len(vs)
  vs.extend([p,p+d*length*.43+side*width,p+d*length,p+d*length*.43-side*width,p+d*length*.45+Vector((0,0,width*.35))])
  fs.extend([(i,i+1,i+4),(i+1,i+2,i+4),(i+2,i+3,i+4),(i+3,i,i+4)])
 return mesh(name,vs,fs,material)
def pot(x,y,r=.4,h=.75):
 lathe('Sculpted grey ceramic pot',(x,y,0),[(r*.55,0),(r*.68,.07),(r*.93,h*.4),(r,h*.7),(r*.9,h*.93),(r*.82,h),(r*.74,h),(r*.76,h*.91)],ceramic)
 cyl('Pot soil',(x,y,h*.91),r*.76,.025,soil)
def grass(x,y,r=.58,h=.48):
 lathe('Low bowl planter',(x,y,0),[(r*.48,0),(r*.74,.08),(r*.96,h*.7),(r,h),(r*.91,h)],ceramic)
 cyl('Bowl soil',(x,y,h*.89),r*.9,.03,soil);ls=[]
 for i in range(240):
  a=random.random()*2*pi;rad=random.random()*r*.7;z=h*.83;start=(x+cos(a)*rad,y+sin(a)*rad,z)
  d=(cos(a)*random.uniform(.4,1),sin(a)*random.uniform(.4,1),random.uniform(.4,1.7));ls.append((start,d,random.uniform(.38,.82),random.uniform(.013,.03)))
 leaves_mesh('Long narrow ornamental leaves',ls,leaf);return
for x,y in [(.95,16.0),(.9,3.1),(9.42,23.1)]:grass(x,y)
for x,y in [(9.03,12.0),(9.35,4.0)]:
 pot(x,y,.39,.76);ls=[]
 for i in range(220):
  a=random.random()*2*pi;start=(x+random.uniform(-.15,.15),y+random.uniform(-.15,.15),.7);ls.append((start,(cos(a),sin(a),random.uniform(.5,2)),random.uniform(.32,.7),.018))
 leaves_mesh('Fine leafy ceramic pot plant',ls,leaf2)
def tree(x,y):
 pot(x,y,.36,.85);ls=[]
 for i in range(5):line('Small tree stems',[(x+random.uniform(-.12,.12),y+random.uniform(-.12,.12),.75),(x+random.uniform(-.17,.17),y+random.uniform(-.17,.17),1.85)],.017,stemmat)
 for i in range(1500):
  a=random.random()*2*pi;z=random.uniform(-1,1);r=random.random()**(1/3);s=math.sqrt(1-z*z);p=(x+cos(a)*s*r*.62,y+sin(a)*s*r*.62,2.0+z*r*.44)
  ls.append((p,(random.uniform(-1,1),random.uniform(-1,1),random.uniform(-.2,1)),random.uniform(.07,.15),.023))
 leaves_mesh('Rounded small tree crown',ls,leaf)
for x,y in [(2.7,22.5),(7.9,22.5)]:tree(x,y)
for x,y in [(3.6,18.05),(6.8,18.05)]:
 cube('Rectangular concrete flower planter',(x,y,.43),(2.15,.66,.86),planter,.035);cube('Flower planter soil',(x,y,.87),(2.0,.54,.035),soil)
 ls=[]
 for i in range(100):
  xx=x+random.uniform(-.92,.92);yy=y+random.uniform(-.22,.22);height=random.uniform(.55,1.15);a=random.random()*2*pi;dx=cos(a)*random.uniform(.08,.45);dy=sin(a)*random.uniform(.08,.3)
  line('Yellow flowering twig',[(xx,yy,.87),(xx+dx*.4,yy+dy*.4,.87+height*.55),(xx+dx,yy+dy,.87+height)],.004,stemmat)
  for k in range(6):
   t=.18+k*.13;bx=xx+dx*t;by=yy+dy*t;bz=.87+height*t;ba=a+random.uniform(-2,2);ex=bx+cos(ba)*.23;ey=by+sin(ba)*.23;ez=bz+.22
   line('Fine flowering offshoot',[(bx,by,bz),(ex,ey,ez)],.0025,stemmat)
   for j in range(10):
    q=j/10;ls.append(((bx+(ex-bx)*q,by+(ey-by)*q,bz+.22*q),(cos(ba+j)*.5,sin(ba+j)*.5,.7),random.uniform(.025,.055),.009))
 leaves_mesh('Golden forsythia leaf clusters',ls,flower)
# Tall broad-leaved orange accent plant visible near the right end.
x,y=9.05,2.2;cube('Tall square flower pot',(x,y,.45),(.55,.55,.9),planter,.015)
ls=[]
for i in range(14):
 a=random.random()*2*pi;ls.append(((x,y,.8),(cos(a)*.45,sin(a)*.45,1),random.uniform(.6,1.25),.10))
leaves_mesh('Bird of paradise foliage',ls,leaf)
orange=mat('Bird of paradise orange',(.95,.23,.012),rough=.6)
leaves_mesh('Orange flower bracts',[((x+.03*i,y,1.85+.18*i),(.8,.25,1),.32,.05) for i in range(3)],orange)

collection('Sculptural pendant lights')
# Shallow bowls with concentric faceted bead lattice, warm central discs, dark rims.
def pendant(x,y,z,r):
 lathe('Pendant shallow bowl',(x,y,z),[(r*.22,-.22*r),(r*.36,-.20*r),(r*.60,-.13*r),(r*.83,-.035*r),(r, .09*r),(r*.98,.11*r)],brass,64)
 torus('Pendant dark perimeter',(x,y,z+.09*r),r,.018,dark)
 cyl('Pendant illuminated center',(x,y,z-.225*r),r*.23,.015,lightmat,48)
 for dx,dy in [(-r*.4,0),(r*.4,0),(0,r*.4)]:line('Fine pendant suspension',[(x+dx,y+dy,z+.05),(x+dx,y+dy,H-.1)],.0035,dark)
 vs=[];fs=[]
 # Beads reproduce the visible repeated champagne-metal tessellation.
 for ring in range(11):
  rr=r*(.27+.067*ring);zz=z+(-.22+.31*((rr/r-.22)/.78)**1.6)*r
  num=max(18,round(rr/r*95))
  for j in range(num):
   a=2*pi*(j+(ring%2)*.5)/num;cx=x+rr*cos(a);cy=y+rr*sin(a);w=r*.027;i=len(vs)
   for dz,rad in [(-w*.85,w*.78),(w*.25,w)]:
    for k in range(6):b=a+2*pi*k/6;vs.append((cx+rad*cos(b),cy+rad*sin(b),zz+dz))
   fs.append(tuple(i+k for k in reversed(range(6))))
   for k in range(6):fs.append((i+k,i+(k+1)%6,i+(k+1)%6+6,i+k+6))
 mesh('Pendant champagne tessellated underside',vs,fs,brass)
for j,y in enumerate([2.0,5.2,8.7,12.0,15.4,18.5,21.8]):
 for i,x in enumerate([2.4,5.15,8.05]):pendant(x+random.uniform(-.4,.4),y+random.uniform(-.5,.5),6.25+random.uniform(-.22,.28),random.uniform(.64,.98))

collection('Lighting and presentation')
def area(name,loc,target,power,size,color=(1,.91,.76),size_y=None):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='RECTANGLE' if size_y else 'DISK';d.size=size
 if size_y:d.size_y=size_y
 o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
for y in [3,9,15,21]:area('Large window daylight',(-.5,y,4.2),(6,y,1.8),1050,5,(.91,.95,1),5)
for y in [4,11,18,22]:area('Soft ceiling fill',(5,y,7.12),(5,y,0),180,4,(1,.86,.65))
sun=bpy.data.lights.new('Soft morning sun','SUN');sun.energy=1.25;sun.angle=.06;o=bpy.data.objects.new('Soft morning sun',sun);COL.objects.link(o);o.rotation_euler=(.45,-.7,-.9)
scene=bpy.context.scene;scene.world.color=(.25,.25,.25);scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.46,.50,.57,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.25
views=[('01_lobby',(6.4,.8,3.6),(4.9,21,1.8),23),('02_mirrors',(4.6,16.2,3.35),(9.7,11.0,2.75),24),('03_reception',(6.8,16.9,3.25),(1.5,19.5,3.5),22),('04_reverse',(5.8,21,3.4),(5.4,4.0,2.9),23)]
for name,loc,target,lens in views:
 d=bpy.data.cameras.new(name);d.lens=lens;d.clip_end=150;o=bpy.data.objects.new(name,d);COL.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o['purpose']='Manually composed presentation camera; not an estimated source pose'
scene.camera=bpy.data.objects[views[0][0]]
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='OPTIX';pref.get_devices()
 for d in pref.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
 print('CYCLES DEVICES',[(d.name,d.type,d.use) for d in pref.devices],flush=True)
except Exception as e:print('GPU fallback',e,flush=True)
scene.render.resolution_x=1280;scene.render.resolution_y=960;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.15
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene['reconstruction_method']='GPT-6 Astra • direct visual interpretation of RGB keyframes, manually authored Blender geometry'
scene['not_used']='Depth maps; camera poses; source blend; point clouds; SfM; SLAM; learned reconstruction; IMU'
scene['scale_notice']='All dimensions are approximate design units, not metric measurements.'
scene['source']='stable_orbit_20260921T044401/keyframes_180/images'
# Convert curve geometry for glTF, preserve collection and object names.
for o in list(bpy.data.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
# Export architecture/furniture, excluding presentation cameras and rendering exterior.
for o in scene.objects:o.select_set(o.type=='MESH' and not o.get('render_only'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'scene.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_yup=True)
bpy.ops.object.select_all(action='DESELECT')
# Set initial viewport to the primary camera.
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'scene.blend'))
summary={'method':'RGB-only visual modelling by GPT-6 Astra','blender':bpy.app.version_string,'objects':len(scene.objects),'mesh_objects':sum(o.type=='MESH' for o in scene.objects),'materials':len(bpy.data.materials),'vertices':sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH'),'dimensions':'Approximate; not measured','render_cameras':'4 manual compositions; no source camera poses','collections':{c.name:len(c.objects) for c in bpy.data.collections},'views':[v[0] for v in views]}
(ROOT/'scene_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary),flush=True)
# Render primary view first for visual review.
scene.camera=bpy.data.objects[views[0][0]];scene.render.filepath=str(ROOT/'renders'/f'{views[0][0]}.png');bpy.ops.render.render(write_still=True)
print('VISUAL_RECON_BUILD_COMPLETE',flush=True)
