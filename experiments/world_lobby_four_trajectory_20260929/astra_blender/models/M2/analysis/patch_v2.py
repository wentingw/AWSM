from pathlib import Path
import json
O=Path(__file__).resolve().parent.parent;p=O/'build_scene.py';s=p.read_text();(O/'analysis/build_v1_snapshot.py.txt').write_text(s)
s=s.replace('VERSION=1','VERSION=2').replace("scene.view_settings.exposure=.25","scene.view_settings.exposure=-.35").replace("default_value=.3\nscene.view", "default_value=.18\nscene.view")
s=s.replace("(.53,.51,.44)","(.43,.41,.35)")
s=s.replace("(.38,.47,.25),.82","(.28,.36,.17),.82")
s=s.replace("(.021,.02,.016),.17,.28","(.015,.014,.011),.055,.25")
s=s.replace("tex.inputs['Scale'].default_value=60;tex.inputs['Roughness'].default_value=.8", "tex.inputs['Scale'].default_value=170;tex.inputs['Roughness'].default_value=.8")
s=s.replace("bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.007", "bump.inputs['Strength'].default_value=.025;bump.inputs['Distance'].default_value=.003")
s=s.replace("(.98,1,1),.35,emission=1.8", "(.98,1,1),.35,emission=1.4")
s=s.replace("p.use_smooth=True\n return o\ndef rod", "p.use_smooth=(len(p.vertices)==4)\n return o\ndef rod")
s=s.replace("def paneled_wall(sid,axis,fixed,start,end,height=4.98,bays=None,evidence=", "def paneled_wall(sid,axis,fixed,start,end,height=4.98,bays=None,backing_sign=1,evidence=")
s=s.replace("fixed+.06 if axis=='x'", "fixed+backing_sign*.12 if axis=='x'").replace("else fixed+.06,(z0+z1)/2)","else fixed+backing_sign*.12,(z0+z1)/2)")
s=s.replace("3.58,evidence=[82,90,100])","3.58,backing_sign=-1,evidence=[82,90,100])")
old="begin('door_side_%d'%k,'interior_door',[45,60,75,82,90],'Flush brushed-metal interior door',confidence='medium');cube('door_leaf',(x,y,.985),(.055,w-.04,1.97),chrome,.008);cube('jamb_top',(x-.03,y,2.02),(.10,w+.04,.05),metal)"
new="""if k==0:
  begin('door_side_0','open_passage',[66,75,90],'Observed open passage at near end of mirror wall',confidence='high',assumptions=['Only 0.8 m visible doorway return is inferred. Unseen connected room extent unknown.','Jamb and header component colliders leave passage free.'])
  for yy in [y-w/2-.018,y+w/2+.018]:cube('return_jamb_'+str(yy),(x+.35,yy,.985),(.8,.036,1.97),wall)
  cube('jamb_top',(x+.35,y,2.02),(.8,w+.072,.05),metal)
  cube('passage_threshold',(x+.35,y,-.085),(.8,w,.16),stone)
 else:
  begin('door_side_%d'%k,'interior_door',[45,60,75,82,90],'Flush brushed-metal interior door',confidence='medium');cube('door_leaf',(x,y,.985),(.055,w-.04,1.97),chrome,.008);cube('jamb_top',(x-.03,y,2.02),(.10,w+.04,.05),metal)"""
assert old in s;s=s.replace(old,new)
s=s.replace("['wall','floor','window_wall']","['wall','floor','window_wall','open_passage']")
# Clip mutually overlapping cushion disks at compatible boundaries to represent modular seats.
pos=s.index('def chair(')
s=s[:pos]+'''SEAT_LAYOUT=[('seat_far_01',-1.43,5.10,.35,None),('seat_far_02',-1.36,5.81,.34,pi*.76),('seat_far_03',-1.00,6.42,.34,pi*.62),('seat_far_04',-.30,6.45,.54,None),('seat_far_05',.27,6.06,.35,None),('seat_far_06',.95,6.08,.35,pi*.36),('seat_near_01',1.03,2.65,.40,None),('seat_near_02',1.04,1.88,.38,pi*.12),('seat_near_03',1.07,1.10,.39,pi*.08),('seat_near_04',1.14,.30,.38,None),('seat_end_01',-.55,-.1,.37,None),('seat_end_02',.20,-.30,.37,pi*1.5)]
def cushion(name,x,y,r,sid):
 poly=[(x+r*cos(2*pi*k/64),y+r*sin(2*pi*k/64)) for k in range(64)]
 for other,xx,yy,rr,_ in SEAT_LAYOUT:
  if other==sid:continue
  dx=xx-x;dy=yy-y;d=math.hypot(dx,dy)
  if d>=r+rr or d<.001:continue
  nx=dx/d;ny=dy/d;limit=(d*d+r*r-rr*rr)/(2*d)-.004
  result=[]
  for a,b in zip(poly,poly[1:]+poly[:1]):
   fa=(a[0]-x)*nx+(a[1]-y)*ny-limit;fb=(b[0]-x)*nx+(b[1]-y)*ny-limit
   if fa<=0:result.append(a)
   if (fa<=0)!=(fb<=0):t=fa/(fa-fb);result.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
  poly=result
 N=len(poly);verts=[(xx,yy,z) for z in [.155,.47] for xx,yy in poly];faces=[tuple(reversed(range(N))),tuple(range(N,2*N))]+[(k,(k+1)%N,(k+1)%N+N,k+N) for k in range(N)]
 o=mesh(name,verts,faces,green)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 m=o.modifiers.new('soft upholstery edge','BEVEL');m.width=.023;m.segments=3;o.modifiers.new('weighted cushion normals','WEIGHTED_NORMAL');return o
''' +s[pos:]
s=s.replace("cylinder('padded_seat',(x,y,.37),r,.43,green,scale=(1,sy,1),bevel=.035)","cushion('padded_seat',x,y,r,sid)")
s=s.replace("y+r*.7*sin(a),.04)","y+r*.7*sin(a),.015)")
s=s.replace("r*.85,.55,.89","r*.85,.445,.755")
a=s.index("for args in [('seat_far_01'");b=s.index("yellow_planter('planter_yellow_left'",a)
s=s[:a]+'''for args in SEAT_LAYOUT:
 chair(*args,evidence=[0,45,60,90,135,179] if 'far' in args[0] else [45,60,75,90,135,150])
table('table_far',-.52,5.27,.86,.70,bowl=True)
table('table_near',.12,2.45,1.02,.76,evidence=[45,60,90,135,150])
table('table_end',-.45,-.8,.75,.7,evidence=[90,100])
''' +s[b:]
s=s.replace("(x,y,.47),.64,.045", "(x,y,.40),.64,.035")
s=s.replace("(.03,.39),(.12,.30),(.39,.21),(.44,.27)","(.015,.34),(.11,.27),(.34,.19),(.38,.24)")
s=s.replace("(x,y,.23),.24,.38", "(x,y,.2025),.19,.375")
s=s.replace("lathe('bowl',(x,y,.50)", "lathe('bowl',(x,y,.423)")
# Subtract the exact floor contact offset from planter bottom vertices only (top unchanged).
s=s.replace("[(0,.02),(.25*size,.02)","[(0,-.005),(.25*size,-.005)")
s=s.replace("[(0,.01),(.22*size,.01)","[(0,-.005),(.22*size,-.005)")
# Grass blades follow bowed paths, each as thin triangulated strips.
a=s.index(' leaves=[]\n for k in range(260):');b=s.index('\ndef yellow_planter',a)
s=s[:a]+''' verts=[];faces=[]
 for k in range(620):
  a=random.random()*2*pi;rr=r*random.random()**.5;L=size*random.uniform(.38,.85);start=Vector((x+rr*cos(a),y+rr*sin(a),z));side=Vector((-sin(a),cos(a),0));idx=len(verts)
  for q in range(7):
   t=q/6;pos=start+Vector((L*.78*t*cos(a),L*.78*t*sin(a),L*(1.6*t-1.2*t*t)));w=.006*size*(1-t)+.0003
   verts.extend([pos-side*w,pos+side*w])
  for q in range(6):faces.append((idx+2*q,idx+2*q+1,idx+2*q+3,idx+2*q+2))
 mesh('arching_blades',verts,faces,leaflight,True)
''' +s[b:]
s=s.replace('for k in range(60):','for k in range(90):').replace('h=random.uniform(.45,1.05)','h=random.uniform(.35,.83)').replace('dx=random.uniform(-.5,.5);dy=random.uniform(-.33,.33)','dx=random.uniform(-.38,.38);dy=random.uniform(-.26,.26)')
s=s.replace('Vector((.20*cos(aa),.20*sin(aa),.12))','Vector((.13*cos(aa),.13*sin(aa),.09))').replace('leaves.append((base,end,.024))','leaves.append((base,end,.0045))').replace('end+Vector((0,0,.06)),.018','end+Vector((0,0,.045)),.004')
s=s.replace('for k in range(650):','for k in range(3400):').replace('leaves.append((pos,end,.032))','leaves.append((pos,end,.047))')
s=s.replace("(-3.98,6.75,2.77),(.08,18.55,.065),charcoal", "(-3.98,6.75,2.77),(.08,18.55,.065),charcoal")
s=s.replace("(.055,.035,4.96),chrome)","(.055,.035,4.96),charcoal)")
s=s.replace(",650,4.0,",",420,4.0,").replace(",120,3,",",80,3,")
# Prevent random initial-file logs from being reset on rebuild.
s=s.replace("'checking_render_count':0,'input_packet_sha256'", "'checking_render_count':5,'input_packet_sha256'")
s=s.replace("log={'versions':[{'version':VERSION,'purpose':'Initial independent semantic reconstruction','object_count':len(records),'render_attempts':[]}],'checking_render_count':0,'max_versions':5,'max_checking_renders':60,'input_consistency_passes':0}","log=json.load(open(O/'iteration_log.json'));log['versions'].append({'version':VERSION,'purpose':'Repair nine independent review issues; preserve cameras and metric units','object_count':len(records),'render_attempts':[]})")
s=s.replace("log['versions'][0]['render_attempts'].append(attempt)","log['versions'][-1]['render_attempts'].append(attempt)")
s=s.replace("manifest['status']='ready_for_independent_review'", "manifest['status']='ready_for_final_review'")
# Relief across each bowl in one mesh; physical small woven bands rather than smooth broad rings.
a=s.index(" for k in range(8):\n  rr=r*(.27");b=s.index(" cylinder('warm_diffuser'",a)
s=s[:a]+''' verts=[];faces=[]
 for ring in range(13):
  rr=r*(.27+.71*ring/12);count=max(20,int(2*pi*rr/.037))
  for k in range(count):
   aa=2*pi*(k+.5*(ring%2))/count;da=pi*.74/count;dr=.020*r;idx=len(verts)
   for rrr,aaa,up in [(rr-dr,aa-da,0),(rr+dr,aa-da,0),(rr+dr,aa+da,0),(rr-dr,aa+da,0),(rr,aa,-.023*r)]:
    zz=.24*r*((rrr/r-.22)/.78)**2+up;verts.append((x+rrr*cos(aaa),y+rrr*sin(aaa),z+zz))
   faces.extend([(idx,idx+1,idx+4),(idx+1,idx+2,idx+4),(idx+2,idx+3,idx+4),(idx+3,idx,idx+4)])
 mesh('woven_relief',verts,faces,woven)
''' +s[b:]
# Correct front left source pendant projection, initially fully clipped in v1.
s=s.replace("(-2.25,-1.0,.72),(0.10,-.9,.84),(2.1,-.8,.71),(-2.1,2.0,.74)","(-2.25,-.35,.72),(0.10,-.3,.84),(2.1,-.25,.71),(-2.1,3.0,.74)")
s=s.replace("'Individual woven geometry represented by concentric ribs and procedural surface relief.'", "'Woven relief uses explicit staggered cells; exact interlacing inferred.'")
p.write_text(s)
print('v2 patched',len(s))
