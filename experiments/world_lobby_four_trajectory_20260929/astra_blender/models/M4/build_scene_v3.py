"""Clean-room Astra M4 semantic reconstruction. Run Blender -b -t 4 -P build_scene.py.
All dimensions are metres in the supplied native world (Z up). Only files under
this model directory are used at build time; no old scene or ground-truth geometry.
"""
import bpy, bmesh, math, json, random, os, sys, time
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
B=Path(__file__).resolve().parent
L=json.load(open(B/'layout_parameters.json')); C=json.load(open(B/'cameras.json'))
REV=int(os.environ.get('M4_REVISION','1')); RENDER=os.environ.get('M4_RENDER','1')=='1'
random.seed(41007); np.random.seed(41007); START=time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=4
scene.cycles.samples=40;scene.cycles.use_denoising=True;scene.cycles.max_bounces=8;scene.cycles.transparent_max_bounces=8
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('Soft daylight world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.75,.8,.88,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=0
materials={}; records=[]; colliders=[]
def mat(name,color,metal=0,rough=.5,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
 if emission:n.inputs['Emission Color'].default_value=(*color,1);n.inputs['Emission Strength'].default_value=emission
 materials[name]=m;return m
wood=mat('Pale vertical oak panels',(.45,.415,.345),0,.55)
stone=mat('Warm pale limestone',(.39,.375,.335),0,.25)
ceiling=mat('Cream plaster ceiling',(.57,.56,.52),0,.65)
dark=mat('Blackened bronze',(.038,.035,.029),.65,.27)
black=mat('Charcoal table finish',(.028,.030,.026),.05,.58)
slatmat=mat('Dark taupe ceiling fins',(.16,.145,.12),.1,.52)
sage=mat('Sage boucle upholstery',(.18,.245,.125),0,.82)
plantermat=mat('Grey cast-stone planter',(.28,.29,.27),0,.66)
soil=mat('Potting soil',(.026,.02,.012),0,1)
green=mat('Deep olive foliage',(.105,.16,.045),0,.72)
green2=mat('Fresh green leaves',(.19,.25,.067),0,.62)
goldleaf=mat('Golden flowering shrub',(.42,.31,.055),0,.72)
branchmat=mat('Twig wood',(.145,.11,.043),0,.82)
white=mat('Ivory linen',(.77,.77,.70),0,.65)
ceramic=mat('Pale glazed ceramic',(.39,.44,.45),.12,.27)
silver=mat('Brushed stainless steel',(.49,.52,.52),.95,.22)
mirror=mat('Silvered mirror',(.83,.86,.83),1,.035)
rattan=mat('Champagne wicker',(.43,.31,.17),.48,.29)
gold=mat('Warm brass',(.52,.34,.10),.8,.22)
warm=mat('Warm pendant diffuser',(.88,.57,.24),0,.35,1.2)
window=mat('Bright diffuse glazing',(.95,.97,1),0,.05,1.6)
orange=mat('Bird of paradise orange',(.85,.25,.015),0,.5)
# Small native procedural textures are packed; diffuse texture remains available in GLB.
def image_material(m,name,w,h,data,uvscale=1):
 im=bpy.data.images.new(name,width=w,height=h);arr=np.concatenate([data,np.ones((h,w,1))],axis=2).astype(np.float32);im.pixels.foreach_set(arr.ravel());im.filepath_raw=str(B/(name+'.png'));im.file_format='PNG';im.save();im.pack();nodes=m.node_tree.nodes;t=nodes.new('ShaderNodeTexImage');t.image=im;t.extension='REPEAT';m.node_tree.links.new(t.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color']);return im
rng=np.random.default_rng(41007)
a=rng.random((256,256));stripe=rng.random(256)[None,:]*.13;wooddata=np.stack([.53+stripe+a*.035,.49+stripe+a*.035,.41+stripe+a*.035],2);image_material(wood,'oak_grain',256,256,wooddata)
no=rng.random((256,256))*.075;stonedata=np.stack([.43+no,.42+no,.38+no],2);image_material(stone,'limestone_grain',256,256,stonedata)
carpet=mat('Glossy black and gold patterned inset',(.045,.039,.027),.48,.055)
y,x=np.mgrid[:512,:512];tile=((x%28)>8)&((x%28)<19)&((y%38)>7)&((y%38)<23);var=.35+.65*rng.random((14,19));v=var[np.minimum(y//38,13),np.minimum(x//28,18)];base=np.zeros((512,512,3))+np.array([.009,.009,.007]);base+=tile[:,:,None]*v[:,:,None]*np.array([.42,.35,.21]);image_material(carpet,'inset_mosaic',512,512,base)
# Shader micro-bump on cloth, plaster and foliage.
for m,scale,strength in [(sage,115,.11),(ceiling,17,.07),(plantermat,45,.1),(rattan,130,.04)]:
 n=m.node_tree.nodes;no=n.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=scale;bu=n.new('ShaderNodeBump');bu.inputs['Strength'].default_value=strength;bu.inputs['Distance'].default_value=.04;m.node_tree.links.new(no.outputs['Fac'],bu.inputs['Height']);m.node_tree.links.new(bu.outputs['Normal'],n['Principled BSDF'].inputs['Normal'])
def mesh(name,verts,faces,ma):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(ma);o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);return o
def cube(name,loc,dim,ma,bev=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 if bev:
  mod=o.modifiers.new('Soft edge','BEVEL');mod.width=bev;mod.segments=3;mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def cylinder(name,loc,r,depth,ma,vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(ma)
 for f in o.data.polygons:f.use_smooth=True
 be=o.modifiers.new('Fine edge radius','BEVEL');be.width=.008;be.segments=2;return o
def ball(name,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(ma)
 for f in o.data.polygons:f.use_smooth=True
 return o
def tube(name,path,r,ma):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(len(path)-1)
 for p,co in zip(sp.points,path):p.co=(*co,1)
 o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.data.materials.append(ma);return o
def lathe(name,xy,profile,ma,n=48):
 vs=[];fs=[]
 for r,z in profile:
  for j in range(n):a=j*2*math.pi/n;vs.append((xy[0]+r*math.cos(a),xy[1]+r*math.sin(a),z))
 for k in range(len(profile)-1):
  for j in range(n):a=k*n+j;b=k*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 o=mesh(name,vs,fs,ma)
 for f in o.data.polygons:f.use_smooth=True
 return o
def sem(id,cat,fn,evidence,provenance='RGB semantic interpretation + local metric depth; RGB multiview cross-check',collide=True,attrs=None,relations=None):
 before=set(bpy.data.objects);fn();parts=list(set(bpy.data.objects)-before);pts=[]
 for o in parts:
  if o.type in {'MESH','CURVE'}:pts.extend([o.matrix_world@Vector(v) for v in o.bound_box])
 if not pts:return
 lo=[min(v[k] for v in pts) for k in range(3)];hi=[max(v[k] for v in pts) for k in range(3)];root=bpy.data.objects.new(id,None);scene.collection.objects.link(root);root['object_id']=id;root['category']=cat
 for o in parts:o.parent=root;o['semantic_object_id']=id
 record={'object_id':id,'category':cat,'attributes':attrs or {},'center':[(a+b)/2 for a,b in zip(lo,hi)],'bounds':[lo,hi],'spatial_relations':relations or [],'evidence_frame_ids':evidence,'evidence':{'frame_ids':evidence},'geometry_provenance':{'observed':provenance,'inferred':'solid thickness, hidden backs, fastening, exact textile/weave/leaf microgeometry'},'blender_root':id,'part_count':len(parts)};records.append(record)
 if collide:colliders.append({'object_id':id,'type':'AABB','bounds':[lo,hi],'role':cat,'static':True,'friction':.55,'restitution':.05,'physics_provenance':'assumed generic material parameters; not measured'})
def panelwall(id,axis,fixed,a,b,z0=0,z1=5,evid=[0,60,90]):
 def build():
  # Panels have genuine seams and thin backing, all positioned at their observed fronts.
  n=math.ceil((b-a)/1.16);edges=[a+(b-a)*j/n for j in range(n+1)]
  for j in range(n):
   for low,high in zip([z0,1.9,3.25],[1.9,3.25,z1]):
    if high<=low:continue
    loc=[0,0,(low+high)/2];dim=[0,0,high-low-.015];loc[axis]=fixed;loc[1-axis]=(edges[j]+edges[j+1])/2;dim[axis]=.13;dim[1-axis]=edges[j+1]-edges[j]-.014;o=cube(id+f'_panel_{j}_{low}',loc,dim,wood,.006)
    uv=o.data.uv_layers.active
    for poly in o.data.polygons:
     for li in poly.loop_indices:
      vv=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(vv[1-axis]*.9,vv.z*.35)
 sem(id,'wall',build,evid,attrs={'surface':'pale vertical wood veneer','inferred_thickness_m':.13})
sem('floor_stone','floor',lambda:cube('Stone foundation',(17.9,20.7,-.08),(18.15,10.5,.21),stone),[0,90,108,138],attrs={'top_z':.025,'measurement_uncertainty_m':.12})
# Native L footprint: nearer south side y18.1, return x18.55, deep bay south y15.55.
panelwall('wall_south_near',1,18.03,9,18.55)
panelwall('wall_south_recess',1,15.48,18.55,26.8)
panelwall('wall_return',0,18.48,15.55,18.1,evid=[60,80])
panelwall('wall_reception',0,26.87,15.55,25.8,evid=[0,108,126,138])
panelwall('wall_front',0,8.93,18.1,25.8,evid=[90,100])
sem('ceiling_plaster','ceiling',lambda:cube('Plaster soffit',(17.9,20.7,5.12),(18.15,10.5,.24),ceiling),[0,90,126],attrs={'underside_z':5.0,'measurement_uncertainty_m':.2})
sem('floor_dark_inset','floor_finish',lambda:cube('Reflective black gold mosaic',(17.55,22.0,.033),(15.1,5.4,.016),carpet),[0,90,108,138],collide=True,attrs={'appearance':'glossy black with fine gold rectangular dotted pattern'})
# UV floor repeats in metric proportions.
o=bpy.data.objects['Reflective black gold mosaic'];uv=o.data.uv_layers.active
for poly in o.data.polygons:
 for li in poly.loop_indices:
  v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x,v.y)
# Tall continuous glazing and repeated thin metal mullions.
def windows():
 cube('Luminous exterior glazing',(17.9,25.88,2.52),(17.8,.035,5.0),window)
 for x in np.arange(9,26.85,.96):cube('Vertical window mullion',(x,25.75,2.5),(.038,.055,5),dark)
 for z in [.04,2.83,4.98]:cube('Horizontal window transom',(17.9,25.72,z),(17.85,.07,.055),dark)
sem('curtain_wall','window_wall',windows,[0,90,108,126],attrs={'plane_y':25.78,'appearance':'overexposed bright glazing','depth_reliability':'low due to glass'})
for di,(xc,dw) in enumerate([(13.021,2.073),(22.848,1.955)]):
 def door(xc=xc,dw=dw):
  for x in [xc-dw/2+.07,xc,xc+dw/2-.07]:cube('Door stile',(x,25.665,1.42),(.14,.09,2.82),gold,.01)
  for z in [.10,2.78]:cube('Door rail',(xc,25.665,z),(dw,.10,.16),gold,.01)
  for x in [xc-.09,xc+.09]:cube('Door pull',(x,25.54,1.36),(.02,.045,.74),dark,.008)
 sem('glazed_double_door_'+str(di),'door',door,[90,100,108,126],attrs={'state':'closed','double_leaf':True,'inferred_thickness_m':.09})
sem('round_column','column',lambda:cylinder('Column full height',(18.05,25.06,2.51),.36,4.97,stone),[0,90,108,138],attrs={'radius_m':.36,'local_depth_crosscheck':True})
# Upper dark linear ceiling fins flanking a cream center.
def slats():
 for x in np.arange(9.1,26.8,.20):
  cube('North ceiling slat',(x,24.63,4.91),(.055,2.35,.14),slatmat)
  cube('South ceiling slat',(x,18.88,4.91),(.055,2.30,.14),slatmat)
sem('ceiling_fins','ceiling_decoration',slats,[0,90,126],collide=False)
# Discrete silver insets on the wooden walls, kept at wall surface.
for i,(x,y,z,w,h,ax) in enumerate([(16.85,18.115,.95,.95,1.9,1),(10.00,18.115,.95,.9,1.9,1),(22.0,15.565,.92,1.0,1.84,1),(24.8,15.565,.92,.9,1.84,1),(9.015,23.6,1.15,.55,1.15,0)]):
 def plate(x=x,y=y,z=z,w=w,h=h,ax=ax):cube('Brushed metal wall panel',(x,y,z),((w,.025,h) if ax==1 else (.025,w,h)),silver,.005)
 sem('wall_metal_panel_'+str(i),'wall_panel',plate,[0,60,70,80,90],collide=False)
# Rear and front seating: separate solids, partial circular upholstered backrests.
def seat(x,y,r=.53,back=True,theta=0,seat_top=.52):
 cylinder('Low black foot',(x,y,.13),r*.82,.19,dark)
 s=cylinder('Round upholstered seat',(x,y,(seat_top+.12)/2),r,seat_top-.12,sage,64);be=s.modifiers.get('Fine edge radius');be.width=.07;be.segments=4
 if back:
  vs=[];fs=[];n=32
  for z in [seat_top-.15,seat_top+.27]:
   for rad in [r-.105,r+.005]:
    for j in range(n+1):a=theta+math.radians(-78+156*j/n);vs.append((x+rad*math.cos(a),y+rad*math.sin(a),z))
  m=n+1
  for j in range(n):fs.extend([(j,j+1,m+j+1,m+j),(2*m+j,3*m+j,3*m+j+1,2*m+j+1),(j,2*m+j,2*m+j+1,j+1),(m+j,m+j+1,3*m+j+1,3*m+j)])
  fs.extend([(0,m,3*m,2*m),(3*m-1,4*m-1,2*m-1,n)]);o=mesh('Curved padded backrest',vs,fs,sage);bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();be=o.modifiers.new('Rounded upholstery','BEVEL');be.width=.028;be.segments=3
  for f in o.data.polygons:f.use_smooth=(f.index%4 in (2,3))
for i,(x,y,r,b,t) in enumerate([(15.82,23.1,.44,False,0),(16.68,23.07,.44,True,1.5),(17.15,22.24,.51,False,0),(16.68,21.32,.45,True,-1.5),(15.87,21.48,.43,False,0),(12.792,20.491,.36,True,-1.4),(13.396,20.445,.352,False,0),(12.301,20.783,.39,True,-2.7),(12.166,21.635,.41,False,0)]):
 sem('lounge_seat_'+str(i),'chair' if b else 'ottoman',lambda x=x,y=y,r=r,b=b,t=t,i=i:seat(x,y,r,b,t,.42 if i>=5 else .52),[0,60,66,70,90,138],attrs={'fabric':'sage green boucle','seat_height_m':.42 if i>=5 else .52,'geometry_uncertainty_m':.2},relations=[{'relation':'supported_by','object_id':'floor_dark_inset'}])
def table(x,y,rx,ry,theta=0):
 o=cylinder('Oval tabletop',(x,y,.40),1,.065,black,64);o.scale=(rx,ry,1);o.rotation_euler.z=theta
 for j in range(22):
  a=j*2*math.pi/22;tube('Radial sculptural table leg',[(x+.65*rx*math.cos(a),y+.65*ry*math.sin(a),.055),(x+.26*rx*math.cos(a),y+.26*ry*math.sin(a),.36)],.018,dark)
 cylinder('Table base',(x,y,.04),.26,.045,dark)
for i,(x,y,rx,ry) in enumerate([(16.12,22.25,.46,.53),(12.973,21.504,.40,.60)]):
 sem('coffee_table_'+str(i),'table',lambda x=x,y=y,rx=rx,ry=ry,i=i:table(x,y,rx,ry,-.22 if i else 0),[0,60,90,138],attrs={'top_height_m':.433,'finish':'dark matte charcoal'})
 if i==0:sem('coffee_bowl','bowl',lambda:lathe('Decorative black bowl',(x,y),[(.08,.435),(.16,.46),(.17,.54),(.15,.56),(.13,.49),(.01,.47)],dark),[0,138],collide=False)
# Flat-mesh leaves and stems are explicitly inferred botanical detail, not a scan.
def leaves_mesh(name,items,ma):
 vs=[];fs=[]
 for c,l,w,ang,tilt in items:
  c=np.array(c);d=np.array([math.cos(ang)*math.cos(tilt),math.sin(ang)*math.cos(tilt),math.sin(tilt)]);side=np.array([-math.sin(ang),math.cos(ang),0]);k=len(vs);vs.extend([c-d*l*.5,c+side*w*.5,c+d*l*.5,c-side*w*.5,c+np.array([0,0,.02])]);fs.extend([(k,k+1,k+4),(k+1,k+2,k+4),(k+2,k+3,k+4),(k+3,k,k+4)])
 return mesh(name,vs,fs,ma)
def shrub(x,y,z,wx,wy,h,ma=goldleaf,n=50):
 leaves=[]
 for j in range(n):
  bx=x+random.uniform(-wx/2,wx/2);by=y+random.uniform(-wy/2,wy/2);hh=h*random.uniform(.55,1);dx=random.uniform(-.35,.35);dy=random.uniform(-.35,.35);tube('Shrub stem',[(bx,by,z),(bx+dx*.35,by+dy*.35,z+hh*.5),(bx+dx,by+dy,z+hh)],.006,branchmat)
  for k in range(8):
   t=.2+.78*k/8;a=random.random()*6.28;length=random.uniform(.10,.29);c=(bx+dx*t,by+dy*t,z+hh*t);end=(c[0]+math.cos(a)*length,c[1]+math.sin(a)*length,c[2]+length*.45);tube('Fine flowering twig',[c,end],.0025,branchmat)
   for q in range(3):
    tt=(q+1)/3;center=[c[ii]+(end[ii]-c[ii])*tt for ii in range(3)];leaves.append((center,.05,.019,a+.7,.55));leaves.append((center,.045,.017,a-.7,.45))
 leaves_mesh('Fine golden leaves and flowers',leaves,ma)
def planter(x,y,wx,wy):
 cube('Rectangular planter cast body',(x,y,.325),(wx,wy,.60),plantermat,.035);cube('Recessed dark planting bed',(x,y,.638),(wx-.10,wy-.10,.025),soil)
 shrub(x,y,.66,wx*.87,wy*.7,.91,n=42)
for i,(x,y,wx,wy) in enumerate([(18.83,23.02,.72,1.65),(18.83,20.76,.72,1.65)]):
 sem('flower_planter_'+str(i),'planter',lambda x=x,y=y,wx=wx,wy=wy:planter(x,y,wx,wy),[0,80,90,100,138],attrs={'foliage':'golden branching flowering shrubs','body_size_m':[wx,wy,.60],'plant_microgeometry':'inferred'},relations=[{'relation':'behind','object_id':'lounge_seat_2'}])
def grass(x,y,r=.50):
 lathe('Low round ceramic bowl',(x,y),[(.01,.025),(.30,.04),(r*.89,.16),(r,.36),(r*.97,.43),(r*.90,.43),(r*.84,.34),(.01,.13)],ceramic)
 leaves=[]
 for k in range(350):
  a=random.random()*6.28;rr=r*.7*math.sqrt(random.random());bx=x+rr*math.cos(a);by=y+rr*math.sin(a);h=random.uniform(.35,.73);bend=random.uniform(.22,.62);vs=[]
  for j in range(7):
   t=j/6;cx=bx+math.cos(a)*bend*t*t;cy=by+math.sin(a)*bend*t*t;zz=.36+h*(math.sin(t*1.9));ww=.023*(1-t)+.001;vs.extend([(cx-math.sin(a)*ww,cy+math.cos(a)*ww,zz),(cx+math.sin(a)*ww,cy-math.cos(a)*ww,zz)])
  mesh('Arching narrow grass leaf',vs,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(6)],green if k%3 else green2)
for i,(x,y,r) in enumerate([(17.15,25.05,.57),(10.05,24.6,.48),(25.55,16.8,.45)]):
 sem('grass_bowl_'+str(i),'potted_plant',lambda x=x,y=y,r=r:grass(x,y,r),[0,90,100,126,138],attrs={'species':'ornamental grass inferred'})
def vaseplant(x,y,topiary=False):
 lathe('Glazed round urn',(x,y),[(.13,.025),(.24,.08),(.31,.29),(.28,.54),(.21,.66),(.18,.7),(.17,.66)],ceramic)
 if topiary:
  for dx in [-.10,0,.10]:tube('Topiary trunk',[(x+dx,y,.66),(x+dx*.5,y,1.36)],.017,branchmat)
  leaves=[]
  for k in range(750):
   a=random.random()*6.28;zz=random.uniform(-1,1);rr=math.sqrt(1-zz*zz);rad=random.uniform(.7,1);c=(x+.43*rr*math.cos(a)*rad,y+.43*rr*math.sin(a)*rad,1.57+.36*zz*rad);leaves.append((c,.095,.035,a,.3))
  leaves_mesh('Topiary crown',leaves,green)
 else:shrub(x,y,.7,.28,.28,.50,green,n=34)
for i,(x,y,top) in enumerate([(15.79,18.7,False),(26.15,24.3,True),(26.15,19.2,True)]):
 sem('ceramic_plant_'+str(i),'potted_plant',lambda x=x,y=y,top=top:vaseplant(x,y,top),[0,60,70,108,126,138],attrs={'species':'topiary' if top else 'low foliage','finish':'pale grey ceramic'})
# Front tropical accents visible in the reverse view.
def tropical(x,y):
 cube('Tall square plant container',(x,y,.5),(.49,.49,.95),plantermat,.015);leaves=[]
 for k in range(12):
  a=random.random()*6.28;h=random.uniform(.7,1.2);tube('Tropical stem',[(x,y,.9),(x+.15*math.cos(a),y+.15*math.sin(a),.9+h)],.013,green);leaves.append(((x+.2*math.cos(a),y+.2*math.sin(a),1.4+h*.3),.65,.16,a,.9))
 leaves_mesh('Broad tropical leaves',leaves,green2)
 for dx in [-.08,.13]:leaves_mesh('Orange flower bract',[((x+dx,y,1.98),.30,.055,.6,1.1),((x+dx,y,2.03),.25,.045,2.1,.6)],orange)
for i,(x,y) in enumerate([(11.10,20.16),(9.9,23.3)]):sem('tropical_front_'+str(i),'potted_plant',lambda x=x,y=y:tropical(x,y),[60,66,90,100],attrs={'species':'bird of paradise interpreted from RGB'})
# Mirror cluster circles are actual reflective round planar solids.
for i,m in enumerate(L['mirrors']):
 def make(m=m):
  x,y,z=m['center'];o=cylinder('Circular mirror disk',(x,y+.025,z),m['radius'],.022,mirror,80);o.rotation_euler=(math.pi/2,0,0)
  pts=[(x+m['radius']*math.cos(a),y+.045,z+m['radius']*math.sin(a)) for a in np.linspace(0,2*math.pi,81)];tube('Fine mirror perimeter',pts,.009,silver)
 sem('round_wall_mirror_'+str(i),'mirror',make,[60,70,80],provenance='RGB circle silhouettes projected to locally depth-constrained y18.13 wall',collide=False,attrs={'reflective':True,'radius_m':m['radius']})
# Faceted reception desk, black metal front rather than a fused measurement mesh.
def desk():
 vs=[(24.98,20.1,.04),(24.98,23.35,.04),(25.85,23.6,.04),(25.9,20,.04),(24.95,20.1,.87),(25.15,23.35,.77),(26.03,23.6,.88),(25.98,20,.87),(25.34,21.65,.36)]
 fs=[(0,1,8),(1,5,8),(5,4,8),(4,0,8),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7),(0,3,2,1)];mesh('Angular black reception counter',vs,fs,black)
sem('reception_desk','reception_desk',desk,[0,108,126,138],provenance='manual RGB triangulation of counter face; local depth and visible polygon silhouette',attrs={'countertop_height_m':.87,'hidden_back':'inferred closed solid'})
# Crest and linear wall decoration have no inferred writing.
def crest():
 vs=[(26.76,21.39,2.5),(26.76,22.01,2.5),(26.76,22.01,1.79),(26.76,21.91,1.60),(26.76,21.7,1.48),(26.76,21.49,1.60),(26.76,21.39,1.79)];o=mesh('Pale shield silhouette',vs,[tuple(range(7))],stone);sol=o.modifiers.new('Shield thickness','SOLIDIFY');sol.thickness=.045
 for yy in [20.1,23.3]:
  side=1 if yy<21.7 else -1;tube('Thin curved wall line',[(26.73,yy,3.4),(26.73,yy,2.64),(26.73,yy+.15*side,2.51),(26.73,21.7,2.51)],.015,dark)
 tube('Central wall line',[(26.73,21.7,2.51),(26.73,21.7,3.45)],.012,dark)
sem('reception_wall_emblem','wall_decoration',crest,[0,126,138],collide=False)
# Standing white drum lamps.
def floorlamp(x,y):
 cylinder('Lamp base',(x,y,.055),.24,.06,silver);cylinder('Lamp slender stem',(x,y,.86),.025,1.6,silver)
 lathe('White drum shade',(x,y),[(.22,1.57),(.22,1.95),(.20,1.95),(.20,1.57)],white);cylinder('Lamp glow',(x,y,1.60),.18,.016,warm)
for i,(x,y) in enumerate([(25.15,18.13),(18.80,17.8),(9.8,20.0)]):sem('standing_lamp_'+str(i),'floor_lamp',lambda x=x,y=y:floorlamp(x,y),[0,60,80,90,138],attrs={'height_m':1.95})
# Woven suspended bowls authored as parametric crossed ribs and rings.
def pendant(m):
 x,y,z=m['center'];r=m['radius'];rr=r*.24
 for k in range(12):
  rad=rr+(r-rr)*k/11;zz=z+.22*(rad/r)**1.4;tube('Concentric wicker ring',[(x+rad*math.cos(a),y+rad*math.sin(a),zz) for a in np.linspace(0,2*math.pi,65)],.009,rattan)
 for k in range(64):
  a=k*2*math.pi/64;pts=[]
  for j in range(14):
   rad=rr+(r-rr)*j/13;zz=z+.22*(rad/r)**1.4+.008*math.sin(j*math.pi+k*math.pi);pts.append((x+rad*math.cos(a),y+rad*math.sin(a),zz))
  tube('Radial wicker weave',pts,.011,rattan)
 cylinder('Warm circular diffuser',(x,y,z+.02),rr,.025,warm)
 tube('Dark broad shade rim',[(x+r*math.cos(a),y+r*math.sin(a),z+.22) for a in np.linspace(0,2*math.pi,81)],.014,dark)
 tube('Suspension cable',[(x,y,z+.10),(x,y,4.98)],.006,dark);cylinder('Ceiling rose',(x,y,4.985),.045,.025,dark)
for m in L['lamps']:sem(m['id'],'pendant_light',lambda m=m:pendant(m),m['evidence'],provenance=m['provenance'],collide=False,attrs={'construction':'parametric crossed wicker ribs and rings','radius_m':m['radius'],'suspension_uncertainty_m':.6})
# A few warm emitter lights create the observed pools and mirrored highlights.
def area(name,loc,target,power,size,color=(1,1,1),size_y=None):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='RECTANGLE';d.size=size;d.size_y=size_y or size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Window daylight',(18,25.55,3.0),(18,20,1.0),1150,16,(1,.96,.89),4.4)
area('Ceiling soft fill',(18,21.8,4.86),(18,21.8,0),100,10,(1,.91,.82),5)
for m in L['lamps'][::3]:
 x,y,z=m['center'];area('Pendant local warm light '+m['id'],(x,y,z-.02),(x,y,0),22,.25,(1,.61,.26))
# Import exact OpenCV c2w poses, with only optical-axis convention converted for Blender.
cam_objs={}
for rec in C['cameras']:
 i=rec['frame_id'];d=bpy.data.cameras.new('Input_camera_%03d'%i);o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);T=np.array(rec['camera_to_world']);o.matrix_world=Matrix(T.tolist())@Matrix.Diagonal((1,-1,-1,1));K=np.array(rec['K']);w,h=rec['image_size'];d.type='PERSP';d.lens=K[0,0]*36/w;d.sensor_width=36;d.sensor_fit='HORIZONTAL';d.shift_x=(w/2-K[0,2])/w;d.shift_y=(K[1,2]-h/2)/w;d.clip_start=.05;d.clip_end=150;o['input_frame_id']=i;cam_objs[i]=o
scene.camera=cam_objs[0];scene.render.resolution_x=518;scene.render.resolution_y=392;scene.render.resolution_percentage=100
# Parent semantic roots have identity transforms; all exported bounds remain native metric coordinates.
bpy.context.view_layer.update()
# Recompute modifier-evaluated bounds after all placements and parent updates.
for rec in records:
 root=bpy.data.objects[rec['object_id']];pts=[]
 for o in root.children:
  if o.type in {'MESH','CURVE'}:pts.extend([o.matrix_world@Vector(v) for v in o.bound_box])
 lo=[min(v[k] for v in pts) for k in range(3)];hi=[max(v[k] for v in pts) for k in range(3)];rec['bounds']=[lo,hi];rec['center']=[(a+b)/2 for a,b in zip(lo,hi)]
 for co in colliders:
  if co['object_id']==rec['object_id']:co['bounds']=[lo,hi]
# Explicit relations and uncertainty methods required by clean review M4-R08.
for rec in records:
 id=rec['object_id'];cat=rec['category'];rels=rec['spatial_relations']
 if cat in {'table','chair','ottoman','planter'} and not rels:rels.append({'relation':'supported_by','object_id':'floor_dark_inset'})
 if cat in {'potted_plant','floor_lamp','reception_desk','column','door'}:rels.append({'relation':'supported_by','object_id':'floor_stone'})
 if cat=='mirror':rels.append({'relation':'mounted_on','object_id':'wall_south_near'})
 if cat=='pendant_light':rels.append({'relation':'suspended_from','object_id':'ceiling_plaster'})
 if cat=='floor_finish':rels.append({'relation':'supported_by','object_id':'floor_stone'})
 if cat=='bowl':rels.append({'relation':'supported_by','object_id':'coffee_table_0'})
 if cat=='wall_decoration':rels.append({'relation':'mounted_on','object_id':'wall_reception'})
 if any('uncertainty' in k for k in rec['attributes']):rec['attributes']['uncertainty_method']='heuristic author estimate from cross-view inconsistency; not calibrated confidence or measured accuracy'
 if id.startswith('lounge_seat_') and int(id.rsplit('_',1)[1])>=5:rec['geometry_provenance']['measurement_reference']='revision3_measurements.json: near_ottoman_left / near_chair_mid / near_chair_right / missing_ottoman';rec['geometry_provenance']['observed']='manual silhouettes in frames0,60,66,138 projected using supplied K and metric poses; near seat plane z0.42 inferred from triangulated furniture'
 if id=='coffee_table_1':rec['geometry_provenance']['measurement_reference']='revision3_measurements.json: near_table';rec['geometry_provenance']['observed']='manual tabletop outline rays from frames60/138; fitted ellipse with residual retained in measurement file'
 if id=='tropical_front_0':rec['geometry_provenance']['measurement_reference']='revision3_measurements.json and review M4-R04; frame60 top/base rays; reverse90 semantic cross-check'
 if id.startswith('glazed_double_door_'):rec['geometry_provenance']['measurement_reference']='revision3_measurements.json: door_front / door_rear'
 if id.startswith('pendant_'):rec['geometry_provenance']['measurement_reference']='layout_parameters.json and revision3_pendant_matches.json; rejected matches retained'
 if id.startswith('round_wall_mirror'):rec['geometry_provenance']['measurement_reference']='layout_parameters.json: mirrors, frame70 silhouettes on depth-constrained y18.13 plane'
for co in colliders:
 if co['object_id']=='floor_dark_inset':co['role']='floor';co['contact_surface_z']=co['bounds'][1][2];co['note']='Visible raised floor finish; use highest supporting floor top for contact.'
mesh_checks=[]
for o in bpy.data.objects:
 if o.type=='MESH' and o.name.startswith('Curved padded backrest'):
  bm=bmesh.new();bm.from_mesh(o.data);mesh_checks.append({'mesh':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)});bm.free()
json.dump({'backrest_meshes':mesh_checks,'all_manifold_positive_volume':all(x['nonmanifold_edges']==0 and x['signed_volume']>0 for x in mesh_checks)},open(B/f'mesh_checks_v{REV}.json','w'),indent=2)
metadata={'method_id':'M4','units':'m','coordinate_frame':'native supplied metric camera world','T_input_model':np.eye(4).tolist(),'model_world_up':[0,0,1],'gravity':[0,0,-9.81],'objects':records}
json.dump(metadata,open(B/'objects.json','w'),indent=2)
json.dump({'units':'m','T_input_model':np.eye(4).tolist(),'model_world_up':[0,0,1],'gravity':[0,0,-9.81],'colliders':colliders,'contact_model':'static semantic AABBs; foliage included conservatively in planter bounds; door state closed'},open(B/'colliders.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(B/'scene.blend'))
bpy.ops.export_scene.gltf(filepath=str(B/'scene.glb'),export_format='GLB',export_apply=True,export_yup=False,export_cameras=True,export_lights=False,export_extras=True)
render_ids=[0,60,90,108,138];rr=B/f'renders_v{REV}';rr.mkdir(exist_ok=True)
if RENDER:
 for i in render_ids:
  scene.camera=cam_objs[i];rec=next(r for r in C['cameras'] if r['frame_id']==i);w,h=rec['image_size'];scene.render.resolution_x=w;scene.render.resolution_y=h;scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=rec['K'][0][0]/rec['K'][1][1];scene.render.filepath=str(rr/f'frame_{i:03d}.png');bpy.ops.render.render(write_still=True)
json.dump({'revision':REV,'elapsed_seconds':time.time()-START,'render_ids':render_ids if RENDER else [],'cycles_device':'CPU','threads':4,'samples':40,'objects':len(records),'blender_objects':len(bpy.data.objects),'glb_axes':'native Z up; export_yup=False'},open(B/f'build_stats_v{REV}.json','w'),indent=2)
print('M4_BUILD_COMPLETE',len(records),len(colliders),'seconds',time.time()-START)
