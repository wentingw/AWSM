exec(open(__file__.replace('measure_landmarks.py','analyze_input.py')).read().split('stats=[]')[0])
# Fit main-floor plane from accumulated point measurements, retain valid moderate baseline windows.
xs=[]
for i in range(43,154,2):
 x,c,a=points(i,5);x=x.reshape(-1,3);keep=(abs(x[:,2]-.18*x[:,1]+2.25)<.22)&(x[:,1]>2)&(x[:,1]<14)&(x[:,0]>-4)&(x[:,0]<4);xs.append(x[keep])
x=np.concatenate(xs); A=np.c_[x[:,:2],np.ones(len(x))];coef=np.linalg.lstsq(A,x[:,2],rcond=None)[0]
for _ in range(5):
 e=x[:,2]-A@coef;keep=abs(e)<.1;coef=np.linalg.lstsq(A[keep],x[keep,2],rcond=None)[0]
n=np.array([-coef[0],-coef[1],1]);n/=np.linalg.norm(n);ex=np.array([1.,0,0]);ex-=n*n.dot(ex);ex/=np.linalg.norm(ex);ey=np.cross(n,ex);Rn=np.array([ex,ey,n]);M=np.eye(4);M[:3,:3]=Rn@R;M[2,3]=-coef[2]/np.linalg.norm([-coef[0],-coef[1],1]);print('floor',coef,'M',M)
json.dump({'model_from_input':M.tolist(),'floor_fit':{'plane_z_from_xy':coef.tolist(),'points':len(x),'inliers':int(keep.sum()),'residual_median_m':float(np.median(abs(e[keep]))),'selection':'good-baseline windows 43:153, near common floor plane, direct optical Z; native metric retained'}},open(O/'analysis/transform.json','w'),indent=2)
landmarks={0:{'window_lower':(200,740),'column_base':(527,533),'seat_front':(669,601),'table_top':(785,583),'planter_left':(736,503),'planter_right':(953,525),'far_floor':(1120,545),'back_wall_upper':(1040,240),'ceiling':(840,70)},45:{'window_floor':(120,780),'column_base':(154,669),'front_seat':(400,698),'left_back_chair':(472,638),'middle_bench':(512,610),'right_chair':(620,642),'table':(534,670),'planter_left':(453,588),'planter_right':(625,583),'desk':(495,502),'back_wall':(562,363),'right_wall':(990,270),'floor_right':(850,690),'ceiling':(531,90),'mirror_large':(1230,560)},60:{'wall':(811,225),'mirror':(747,433),'near_seat1':(740,736),'near_seat2':(868,772),'near_seat3':(992,800),'near_table':(780,846),'wall_planter':(530,556),'right_door':(1222,484),'left_door':(419,474)},90:{'near_end_wall':(518,212),'near_chair':(539,401),'planter_left':(430,529),'planter_right':(708,527),'column':(915,470),'floor':(653,783),'ceiling':(617,67)},110:{'glass_center':(567,199),'glass_bottom':(555,445),'door_left':(716,334),'door_right':(798,334),'desk_corner':(1220,568),'column':(256,284),'floor':(900,777)},135:{'window_base':(400,623),'column':(252,404),'floor':(552,751),'back_wall':(814,281),'desk':(733,433),'planter_left':(496,513),'planter_right':(724,540),'chair_left':(365,579),'chair_right':(592,564),'table':(414,603),'right_wall':(1126,286)}}
rows=[]
for i,locs in landmarks.items():
 a=np.load(P/f'geometry/{i:04d}.npz');K=a['intrinsics'];C=np.array(J['frames'][i]['camera_to_world']);h,w=a['depth_z_m'].shape
 for name,(u,v) in locs.items():
  ud=u*w/1280;vd=v*h/960;z=float(np.median(a['depth_z_m'][int(vd)-1:int(vd)+2,int(ud)-1:int(ud)+2]));p=np.linalg.inv(K)@np.array([ud,vd,1])*z;p=M[:3,:3]@(C[:3,:3]@p+C[:3,3])+M[:3,3];r={'sample_index':i,'name':name,'pixel_rgb':[u,v],'depth_z_m':z,'point_model_m':p.tolist()};rows.append(r);print(i,name,np.round(p,2))
json.dump({'landmarks':rows},open(O/'analysis/landmarks.json','w'),indent=2)
