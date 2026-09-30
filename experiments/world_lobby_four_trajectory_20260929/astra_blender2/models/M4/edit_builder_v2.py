from pathlib import Path
R=Path(__file__).resolve().parent;p=R/'build_scene.py';s=p.read_text()
s=s.replace('import bpy,math,json,random,os','import bpy,bmesh,math,json,random,os')
s=s.replace("M={}; records=[]; current=None","M={}; records=[]; current=None; C=L['repair_construction']\nbpy.context.preferences.filepaths.save_version=0")
a=s.index('def cube(');b=s.index('def mesh(',a)
s=s[:a]+'''def cube(name,loc,scale,material,bevel=0):
 vs=[(x*scale[0]/2,y*scale[1]/2,z*scale[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 o=mesh(name,vs,fs,material);o.location=loc
 if bevel:mod=o.modifiers.new('soft_edges','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
 return o

def cyl(name,loc,r,depth,material,vertices=48,rotation=None):
 vs=[(r*cos(2*pi*j/vertices),r*sin(2*pi*j/vertices),zz) for zz in [-depth/2,depth/2] for j in range(vertices)]
 fs=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,2*vertices))]+[(j,(j+1)%vertices,(j+1)%vertices+vertices,j+vertices) for j in range(vertices)]
 o=mesh(name,vs,fs,material);o.location=loc
 if rotation:o.rotation_euler=rotation
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 return o

''' + s[b:]
# Grain visible in color as well as normal.
a=s.index('\ndef group(')
s=s[:a]+'''
# Inferred visual texture from source61/74. No image assets or external texture reads.
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(.20,.18,.14,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.59,.55,.44,1);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
# Persistent small rectangular metallic inlays; shader only, geometric depth unchanged.
m=M['black_polished_stone'];n=m.node_tree.nodes;l=m.node_tree.links;pbr=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Object'],sep.inputs[0]);outs=[]
for axis,fill in [('X',.47),('Y',.36)]:
 mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=1/C['floor_grid_pitch'];l.new(sep.outputs[axis],mul.inputs[0]);fr=n.new('ShaderNodeMath');fr.operation='FRACT';l.new(mul.outputs[0],fr.inputs[0]);lt=n.new('ShaderNodeMath');lt.operation='LESS_THAN';lt.inputs[1].default_value=fill;l.new(fr.outputs[0],lt.inputs[0]);outs.append(lt.outputs[0])
mm=n.new('ShaderNodeMath');mm.operation='MULTIPLY';l.new(outs[0],mm.inputs[0]);l.new(outs[1],mm.inputs[1]);mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.012,.011,.009,1);mix.inputs[2].default_value=(.25,.17,.07,1);l.new(mm.outputs[0],mix.inputs[0]);l.new(mix.outputs[0],pbr.inputs['Base Color']);pbr.inputs['Metallic'].default_value=.65;pbr.inputs['Roughness'].default_value=.22
''' + s[a:]
# mirror fern separate form
s=s.replace("elif kind=='tall':", """elif kind=='vase':
  for k in range(650):
   a=random.uniform(0,2*pi);rr=.40*random.random()**.5;zz=.87+.30*math.sqrt(max(0,1-(rr/.42)**2));aa=(x+rr*cos(a),y+rr*sin(a),z+zz);bb=(aa[0]+random.uniform(-.08,.08),aa[1]+random.uniform(-.08,.08),aa[2]+random.uniform(-.06,.04));leafsets[k%2].append((aa,bb,.007))
 elif kind=='tall':""")
# replace paneled construction
start=s.index('def paneled_wall(');end=s.index('# Metallic inset',start)
s=s[:start]+'''def paneled_wall(id,axis,value,a,b,z0,z1,evidence):
 group(id,'architecture_wall',evidence,relations=['bounded_by:floor','bounded_by:ceiling']);length=b-a
 holes=[]
 if id=='mirror_feature_wall':holes=[(16.60,17.60,0,2.05)]
 if id=='south_recess_wall':holes=[(19.9,20.9,0,2.05),(22.6,23.6,0,2.05)]
 def wallbox(name,aa,bb,za,zb,offset,thick,material):
  pieces=[(aa,bb,za,zb)]
  for ha,hb,hz0,hz1 in holes:
   nxt=[]
   for x0,x1,y0,y1 in pieces:
    if x1<=ha or x0>=hb or y0>=hz1 or y1<=hz0:nxt.append((x0,x1,y0,y1));continue
    if x0<ha:nxt.append((x0,ha,y0,y1))
    if x1>hb:nxt.append((hb,x1,y0,y1))
    if y1>hz1:nxt.append((max(x0,ha),min(x1,hb),hz1,y1))
   pieces=nxt
  for k,(x0,x1,y0,y1) in enumerate(pieces):
   if x1-x0<1e-5 or y1-y0<1e-5:continue
   loc=[(x0+x1)/2,value+offset,(y0+y1)/2] if axis=='y' else [value+offset,(x0+x1)/2,(y0+y1)/2];dims=[x1-x0,thick,y1-y0] if axis=='y' else [thick,x1-x0,y1-y0];cube(name+'_'+str(k),loc,dims,material)
 wallbox('backing',a,b,z0,z1,0,.16,'panel_shadow')
 steps=round(length/.95);levels=[z0,z1] if z1-z0<2.8 else [z0,z0+2,z0+3.6,z1]
 for i in range(steps):
  for j in range(len(levels)-1):
   offset=.0975 if axis=='y' else .0975*C['wall_panel_x_sign'].get(id,-1)
   wallbox(f'panel_{i}_{j}',a+i*length/steps+.008,a+(i+1)*length/steps-.008,levels[j]+.009,levels[j+1]-.009,offset,.035,'ivory_oak')
paneled_wall('east_end_wall','x',27.5,16,26,0,5,[33,129,155]);paneled_wall('west_end_wall','x',8,16,26,0,5,[91,100]);paneled_wall('south_recess_wall','y',16,8,27.5,0,5,[82,33]);paneled_wall('mirror_feature_wall','y',17.88,11.1,18.2,0,5,[61,74,82]);paneled_wall('feature_return_east','x',18.2,16,17.9,0,5,[82]);paneled_wall('feature_return_west','x',11.1,16,17.9,0,5,[91]);
''' + s[end:]
# all panels changed .0075 systematic track later
start=s.index("cube('panes'");end=s.index("group('window_column'",start)
s=s[:start]+'''# Split glazing around observed closed doors. No facade collider crosses an aperture.
spans=[8]+[v for d in sorted(L['doors'],key=lambda d:d['x']) for v in [d['x']-d['width']/2,d['x']+d['width']/2]]+[27.5]
for j in range(0,len(spans)-1,2):
 a,b=spans[j:j+2];cube('pane_segment_'+str(j),((a+b)/2,26.055,2.5),(b-a,.05,5),'window_white');cube('sill_'+str(j),((a+b)/2,25.98,.045),(b-a,.08,.09),'aluminium')
for d in L['doors']:cube('overdoor_'+d['id'],(d['x'],26.055,(5+d['height'])/2),(d['width'],.05,5-d['height']),'window_white')
for j in range(24):
 x=8+j*19.5/23;inside=next((d for d in L['doors'] if abs(x-d['x'])<d['width']/2+.03),None);z0=inside['height'] if inside else 0
 cube(f'mullion_{j}',(x,26,(z0+5)/2),(.045,.075,5-z0),'table_dark')
cube('transom',(17.75,25.98,3.03),(19.5,.075,.055),'table_dark')
for d in L['doors']:
 group(d['id'],'door',[33,100,108,118],provenance='Observed CLOSED double door; frame/leaf dimensions inferred; collider leaves may be disabled for aperture test, exterior unobserved.');x=d['x'];w=d['width'];h=d['height'];y=25.93;g=C['door_frame_width']
 for dx in [-w/2,w/2]:cube('static_jamb_'+str(dx),(x+dx,y,h/2),(g,.10,h),'bronze')
 cube('static_header',(x,y,h),(w,.1,.12),'bronze')
 for side in [-1,1]:
  xc=x+side*w/4;prefix='leaf_'+str(side)
  cube(prefix+'_glass',(xc,y+.015,h/2),(w/2-g,.035,h-.20),'window_white')
  for dx in [-w/4,w/4]:cube(prefix+'_stile_'+str(dx),(xc+dx,y,h/2),(g,.10,h),'bronze')
  for z in [.065,h-.05]:cube(prefix+'_rail_'+str(z),(xc,y,z),(w/2,.1,.13),'bronze')
  line(prefix+'_handle',(x+side*.10,y-.1,.85),(x+side*.10,y-.1,1.6),.015,'bronze',12)
''' + s[end:]
s=s.replace("for k in range(4):\n  a=pi/4+k*pi/2;line", "for k in range(4):\n  a=pi/4+k*pi/2;cyl('foot_pad_'+str(k),(x+rad*.72*cos(a),y+rad*.72*sin(a),.023),.029,.024,'aluminium',12);line")
s=s.replace("(N,2*m-1,4*m-1,3*m-1)","(3*m-1,4*m-1,2*m-1,N)")
s=s.replace("o=mesh('curved_back',vs,fs,'sage_fabric');mod=o.modifiers", "o=mesh('curved_back',vs,fs,'sage_fabric');bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();mod=o.modifiers")
s=s.replace("mod.width=.06;mod.segments=4", "mod.width=C['chair_back_bevel'];mod.segments=3")
s=s.replace("for k in range(24):\n  a=k*2*pi/24;line", "for k in range(24):\n  a=k*2*pi/24;cyl('base_pad_'+str(k),(x+.34*cos(a),y+.28*sin(a),.0275),.024,.033,'table_dark',8);line")
s=s.replace('for k in range(100):','for k in range(C[\'shrub_branches\']):').replace('reach=random.uniform(.15,.65)','reach=random.uniform(*C[\'shrub_reach\'])').replace('h+random.uniform(.35,1.0)','h+random.uniform(*C[\'shrub_height_above_pot\'])').replace("Vector((.14*cos(a),.14*sin(a),.04));leaves.append((mid,tip,.015))","Vector((.07*cos(a),.07*sin(a),.025));leaves.append((mid,tip,.005))")
s=s.replace("mesh('faceted_body',vs,fs,'desk_grey');cube('top'", "mesh('faceted_body',vs,[tuple(reversed(f)) for f in fs],'desk_grey');cube('hidden_support',(25.58,21.8,.0605),(.62,2.5,.099),'table_dark');cube('top'")
# replace many operators for weaving with combined manifold tube segments.
a=s.index(' for k in range(56):');b=s.index(" line('suspension'",a)
s=s[:a]+''' # Real underside ridges, aggregated into one semantic mesh for reproducible fast builds.
 vs=[];fs=[]
 def tube(a,b,rr=.008):
  a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
  if u.length<1e-5:u=d.cross(Vector((0,1,0)))
  u.normalize();v=d.cross(u);off=len(vs);N=5
  for q in [a,b]:
   for k in range(N):vs.append(q+rr*(u*cos(2*pi*k/N)+v*sin(2*pi*k/N)))
  fs.extend([tuple(off+k for k in range(N-1,-1,-1)),tuple(off+N+k for k in range(N))]);fs.extend([(off+k,off+(k+1)%N,off+(k+1)%N+N,off+k+N) for k in range(N)])
 def underside(t):
  knots=[(.19,0),(.32,.015),(.55,height*.23),(.78,height*.57),(1,height)]
  for (a,za),(b,zb) in zip(knots,knots[1:]):
   if a<=t<=b:return za+(zb-za)*(t-a)/(b-a)-.013
  return -.013
 for k in range(64):
  for j in range(12):
   t0=.26+.74*j/12;t1=.26+.74*(j+1)/12;a=2*pi*k/64+.22*t0;b=2*pi*k/64+.22*t1;tube((x+r*t0*cos(a),y+r*t0*sin(a),z+underside(t0)),(x+r*t1*cos(b),y+r*t1*sin(b),z+underside(t1)))
 for j in range(11):
  t=.29+j*.064
  for k in range(96):
   a=k*2*pi/96;b=(k+1)*2*pi/96;tube((x+r*t*cos(a),y+r*t*sin(a),z+underside(t)-.007),(x+r*t*cos(b),y+r*t*sin(b),z+underside(t)-.007),.006)
 mesh('underside_weave',vs,fs,'bronze')
''' + s[b:]
s=s.replace("default_value=.25","default_value=C['ambient_strength']").replace('d.energy=750','d.energy=C[\'daylight_energy\']').replace('S.view_settings.exposure=.3',"S.view_settings.exposure=C['exposure']")
# normals sanity before saving, colliders via dedicated own module
s=s.replace("json.dump(dict(objects=records)","for r in records:r['component_names']=list(r['components'])\njson.dump(dict(objects=records)")
a=s.index("json.dump(dict(colliders=");b=s.index("json.dump(dict(objects=[",a)
s=s[:a]+"exec(compile((R/'repair_colliders.py').read_text(),str(R/'repair_colliders.py'),'exec'))\n"+s[b:]
a=s.index("bpy.ops.wm.save_as_mainfile")
s=s[:a]+"exec(compile((R/'repair_mesh_audit.py').read_text(),str(R/'repair_mesh_audit.py'),'exec'))\n"+s[a:]
p.write_text(s)
