from pathlib import Path
p=Path(__file__).resolve().parent/'build_scene.py'
s=p.read_text()
s=s.replace("VERSION=int(os.environ.get('M1_VERSION','1'))","VERSION=int(os.environ.get('M1_VERSION','2'))")
s=s.replace("mat('black_polished',(0.034,.031,.025),.135,.36,.04,22)","mat('black_polished',(0.024,.022,.018),.055,.46,0,22)")
s=s.replace("mat('wall_oak',(0.39,.365,.31),.48,0,.18,65)","mat('wall_oak',(0.31,.285,.235),.48,0,.32,65)")
s=s.replace("scene.view_settings.exposure=.2","scene.view_settings.exposure=-.15")
a=s.index('# East main mirror wall ends');b=s.index("begin('wall_recess_return'",a)
s=s[:a]+'''# Exact opening splits: panel geometry and wall colliders retain doorways.
for id,x,ya,yb,ev,doorcenters in [('wall_east_main',7.35,0,13.8,[45,62,80,90,135],[4.8,11.3]),('wall_east_recess',8.8,13.8,18,[0,45,80,179],[14.6,16.35])]:
 begin(id,'wall',ev,'Panelled east wall split exactly at opening jambs')
 n=round((yb-ya)/.88)
 for i in range(n):
  low=ya+i*(yb-ya)/n+.01;high=ya+(i+1)*(yb-ya)/n-.01
  for iz,(za,zb) in enumerate([(0,2.05),(2.05,4.1),(4.1,H)]):
   segments=[(low,high)]
   if iz==0:
    for d in doorcenters:
     new=[]
     for aa,bb in segments:
      if bb<=d-.50 or aa>=d+.50:new.append((aa,bb))
      else:
       if aa<d-.50:new.append((aa,d-.50))
       if bb>d+.50:new.append((d+.50,bb))
     segments=new
   for k,(aa,bb) in enumerate(segments):
    if bb-aa>.003:cube(f'panel_{i}_{iz}_{k}',(x,(aa+bb)/2,(za+zb)/2),(.16,bb-aa,zb-za-.02),'wall_oak')
 for j,d in enumerate(doorcenters):
  if id=='wall_east_main' and j==0:
   begin('passage_south','open_passage',ev,'Observed dark open passage beside mirror wall; shallow return geometry is assumed',collider='compound')
   for dy in [-.53,.53]:cube('return_'+str(dy),(x+.55,d+dy,1.015),(1.02,.06,2.03),'reveal')
   cube('lintel',(x+.55,d,2.08),(1.02,1.12,.10),'reveal')
  else:
   begin(f'elevator_{id}_{j}','door',ev,'Closed brushed silver double panel door with exact clear wall opening',relations=[{'relation':'set_in','target':id}])
   for dy in [-.237,.237]:cube('leaf_'+str(dy),(x+.03,d+dy,1.02),(.045,.47,2.04),'brushed_steel')
   cube('center_seam',(x-.004,d,1.02),(.045,.01,2.04),'reveal')
 begin(id+'_reveals','trim',ev,'Horizontal black panel joints above doors',collider='none')
 for z in [2.05,4.1]:cube('rail_'+str(z),(x-.02,(ya+yb)/2,z),(.17,yb-ya,.014),'reveal')
''' +s[b:]
s=s.replace("enumerate([5.4,12.8])","enumerate([1.9,10.6])")
s=s.replace("cyl('shaft',(.72,y,H/2),.38,H","cyl('shaft',(.60,y,H/2),.32,H")
s=s.replace("def seat(id,x,y,r=.40,back=False,angle=0,ev=[0,45,90,135,179]):","def seat(id,x,y,r=.40,back=False,angle=0,ev=[0,45,90,135,179]):\n r*=.80\n if id.startswith('seat_S'):y+=2.6\n if id=='seat_N1':x+=.20")
s=s.replace("cyl('core',(x,y,.245),.25,.43,'black_metal',40)","cyl('core',(x,y,.24175),.25,.4595,'black_metal',40)")
s=s.replace("table('table_south',4.35,3.85,.72,.53","table('table_south',4.35,6.45,.72,.53")
s=s.replace("table('table_north',3.55,9.1,.64,.52","table('table_north',3.40,9.1,.64,.52")
s=s.replace("for k in range(38):","for k in range(64):")
s=s.replace("height=random.uniform(.45,.95)","height=random.uniform(.25,.56)")
s=s.replace("leaves('yellow_sprig_'+str(k),end,.21,50,'yellow_leaf')","leaves('yellow_sprig_'+str(k),end,.20,75,'yellow_leaf')\n  mid=((xx+end[0])/2,(yy+end[1])/2,.88+height*.65)\n  leaves('yellow_mid_'+str(k),mid,.18,55,'yellow_leaf')")
s=s.replace("pot('plant_glass_north',.77,11.93,'grass',.64)","pot('plant_glass_north',.65,9.50,'grass',.70)")
s=s.replace("length=random.uniform(.3,.65)","length=random.uniform(.45,.86)")
s=s.replace("for k,(y,z,r) in enumerate(mirrors):","for k,(y,z,r) in enumerate(mirrors):\n y+=3.3")
# Strong enough underside relief to be seen at check resolution, no source texture used.
s=s.replace("# Concentric rings reproduce visible horizontal ribbing; radial fine ribs provide silhouette detail.","""# Alternating geometric under-dish tiles: scene-native approximation of visible weave.
 vs=[];fs=[]
 for ring in range(4,19):
  rr=r*ring/19;count=max(24,int(110*rr/r))
  for jj in range(count):
   aa=(jj+(ring%2)*.5)*math.tau/count;dr=r*.025;da=math.pi/count*.78
   zz=z+(.42*(rr/r)**2-.25)*r-.018
   k0=len(vs)
   for rad,ang in [(rr-dr,aa-da),(rr+dr,aa-da),(rr+dr,aa+da),(rr-dr,aa+da)]:vs.append((x+rad*math.cos(ang),y+rad*math.sin(ang),zz))
   fs.append((k0,k0+1,k0+2,k0+3))
 mesh('woven_underside',vs,fs,'brass')
 # Concentric rings reinforce the shallow silhouette.
""")
s=s.replace("(.27*r,.014,'lamp_glow'","(.27*r,.014,'lamp_glow'")
# Replace single gross wall collider with per-solid-component compound boxes.
a=s.index("colliders=[{'object_id':");b=s.index("(ROOT/'layout.json')",a)
s=s[:a]+'''colliders=[]
for rec in records.values():
 if rec['collider_type']=='none':continue
 if rec['category']=='wall' or rec['id']=='passage_south':
  parts=[]
  for name in rec['component_names']:
   ob=bpy.data.objects[name];pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
   parts.append({'component_name':name,'type':'box','bounds':{'min':[min(v[k] for v in pts) for k in range(3)],'max':[max(v[k] for v in pts) for k in range(3)]}})
  colliders.append({'object_id':rec['id'],'type':'compound','parts':parts,'door_state':'open passage retained; closed door leaves have separate records'})
 else:colliders.append({'object_id':rec['id'],'type':rec['collider_type'],'bounds':rec['bounds'],'approximation':'Conservative furniture bounds; not contact-accurate physics geometry'})
(ROOT/'colliders.json').write_text(json.dumps({'colliders':colliders,'units':'assumed meters','status':'compound walls preserve openings; furniture approximate'},indent=2))
''' +s[b:]
s=s.replace("'Camera/layout repairs from RGB comparison'","'v2 independent review repairs: openings, compound colliders, support, layout and appearance'")
p.write_text(s)
# Camera fitting remains illustrative. Correct geometry coordinates; add mirror/table landmarks.
p=p.parent/'prepare_cameras.py';s=p.read_text()
s=s.replace("'seat_N1':(2.15,9.2,.575)","'seat_N1':(2.35,9.2,.575)").replace("'table_N':(3.55,9.1,.515)","'table_N':(3.40,9.1,.515)")
s=s.replace("'grass_N':(.77,11.93,.37)","'grass_N':(.65,9.50,.37)").replace("'column_base':(.72,12.8,0)","'column_base':(.60,10.6,0)")
s=s.replace("'mirror_big':(7.22,5.6,2.19)","'mirror_big':(7.22,8.9,2.19)").replace("'mirror_smalltop':(7.22,6.74,2.88)","'mirror_smalltop':(7.22,10.04,2.88)")
s=s.replace("'table_S':(4.35,3.85,.51)","'table_S':(4.35,6.45,.51)")
s=s.replace("'urn_N':[973,641]","'urn_N':[973,641],'mirror_smalltop':[1110,465],'column_base':[179,614]")
s=s.replace("'urn_N':[1080,618]","'urn_N':[1080,618],'mirror_smalltop':[1272,418],'table_S':[664,928],'column_base':[283,523]")
s=s.replace("'urn_N':[1000,700]","'urn_N':[1000,700],'mirror_smalltop':[1226,445],'column_base':[238,554]")
s=s.replace("'south_pot_R':[483,369]","'south_pot_R':[483,369],'mirror_big':[291,334],'column_base':[904,528]")
p.write_text(s)
print('V2_PATCH_WRITTEN')
